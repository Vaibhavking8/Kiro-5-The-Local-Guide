"""
User Profile Manager for Taste & Trails Korea
Handles user authentication, preferences, and personalization data in MongoDB.
"""

from datetime import datetime, timedelta
from bson.objectid import ObjectId
from passlib.hash import pbkdf2_sha256
import hashlib
import json


class UserProfileManager:
    """
    Manages user profiles with enhanced personalization features including:
    - Cultural preferences and recommendation weights
    - User history tracking for visited places and favorites
    - Immediate profile update reflection in recommendations
    - Optimized MongoDB operations for sub-second response times
    """
    
    def __init__(self, mongo_client):
        """Initialize the User Profile Manager with MongoDB client."""
        self.db = mongo_client.taste_trails_korea
        self.users = self.db.users
        self.recommendation_cache = self.db.recommendation_cache
        
        # Create indexes for performance optimization
        self._create_indexes()
    
    def _create_indexes(self):
        """Create MongoDB indexes for optimized query performance."""
        try:
            # User collection indexes
            self.users.create_index("username", unique=True)
            self.users.create_index("email", unique=True)
            self.users.create_index("personalization.last_recommendation_update")
            
            # Recommendation cache indexes
            self.recommendation_cache.create_index("cache_key", unique=True)
            self.recommendation_cache.create_index("user_id")
            self.recommendation_cache.create_index("expires_at")
            
        except Exception as e:
            print(f"Index creation warning: {e}")
    
    def create_user_profile(self, user_data):
        """
        Create new user with enhanced preferences and cultural settings.
        
        Args:
            user_data (dict): User registration data
            
        Returns:
            ObjectId: The created user's ID
        """
        now = datetime.utcnow()
        
        # Validate password strength
        password = user_data["password"]
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        # Enhanced user schema with cultural preferences
        user_profile = {
            "username": user_data["username"],
            "email": user_data["email"].lower(),
            "password_hash": pbkdf2_sha256.hash(password),
            "created_at": now,
            "phone": user_data.get("phone", ""),
            "address": user_data.get("address", ""),
            
            # Security fields
            "last_login": None,
            "failed_login_attempts": 0,
            "account_locked_until": None,
            
            # Enhanced preferences with cultural context
            "preferences": {
                "food_restrictions": user_data.get("food_restrictions", []),
                "interests": user_data.get("interests", []),
                "cultural_preferences": user_data.get("cultural_preferences", []),
                "budget_range": user_data.get("budget_range", "mid-range"),
                "travel_style": user_data.get("travel_style", "solo")
            },
            
            # Enhanced history tracking
            "history": {
                "visited_places": [],
                "favorites": [],
                "search_history": []
            },
            
            # Personalization weights for recommendations
            "personalization": {
                "recommendation_weights": {
                    "food": 1.0,
                    "culture": 1.0,
                    "nightlife": 1.0,
                    "shopping": 1.0,
                    "nature": 1.0
                },
                "preferred_neighborhoods": [],
                "last_recommendation_update": now
            }
        }
        
        result = self.users.insert_one(user_profile)
        return result.inserted_id
    
    def update_user_history(self, user_id, visited_place, rating=None):
        """
        Track user visits and update recommendation weights based on activity.
        
        Args:
            user_id (str): User's ObjectId as string
            visited_place (dict): Place information with name, category, location
            rating (int, optional): User rating 1-5
        """
        now = datetime.utcnow()
        user_oid = ObjectId(user_id)
        
        # Create visited place entry
        place_entry = {
            "place_id": visited_place.get("place_id", ""),
            "name": visited_place["name"],
            "location": visited_place.get("location", {}),
            "visited_date": now,
            "rating": rating,
            "notes": visited_place.get("notes", "")
        }
        
        # Add to visited places
        self.users.update_one(
            {"_id": user_oid},
            {
                "$push": {"history.visited_places": place_entry},
                "$set": {"personalization.last_recommendation_update": now}
            }
        )
        
        # Update recommendation weights based on place category
        self._update_recommendation_weights(user_id, visited_place.get("category"), rating)
        
        # Clear recommendation cache for this user
        self._clear_user_cache(user_id)
    
    def add_favorite(self, user_id, favorite_place):
        """
        Add a place to user's favorites and update personalization.
        
        Args:
            user_id (str): User's ObjectId as string
            favorite_place (dict): Place information
        """
        now = datetime.utcnow()
        user_oid = ObjectId(user_id)
        
        favorite_entry = {
            "place_id": favorite_place.get("place_id", ""),
            "name": favorite_place["name"],
            "category": favorite_place.get("category", ""),
            "added_date": now
        }
        
        # Add to favorites and update recommendation timestamp
        self.users.update_one(
            {"_id": user_oid},
            {
                "$push": {"history.favorites": favorite_entry},
                "$set": {"personalization.last_recommendation_update": now}
            }
        )
        
        # Update recommendation weights
        self._update_recommendation_weights(user_id, favorite_place.get("category"), 5)  # Favorites get high weight
        
        # Clear recommendation cache
        self._clear_user_cache(user_id)
    
    def remove_favorite(self, user_id, place_name):
        """Remove a place from user's favorites."""
        user_oid = ObjectId(user_id)
        
        self.users.update_one(
            {"_id": user_oid},
            {
                "$pull": {"history.favorites": {"name": place_name}},
                "$set": {"personalization.last_recommendation_update": datetime.utcnow()}
            }
        )
        
        self._clear_user_cache(user_id)
    
    def update_search_history(self, user_id, query, results_clicked=None):
        """
        Track user search history for personalization.
        
        Args:
            user_id (str): User's ObjectId as string
            query (str): Search query
            results_clicked (list): List of clicked result names
        """
        user_oid = ObjectId(user_id)
        
        search_entry = {
            "query": query,
            "timestamp": datetime.utcnow(),
            "results_clicked": results_clicked or []
        }
        
        # Keep only last 50 search entries for performance
        self.users.update_one(
            {"_id": user_oid},
            {
                "$push": {
                    "history.search_history": {
                        "$each": [search_entry],
                        "$slice": -50  # Keep only last 50 entries
                    }
                }
            }
        )
    
    def get_personalized_preferences(self, user_id):
        """
        Generate recommendation weights based on user history and preferences.
        
        Args:
            user_id (str): User's ObjectId as string
            
        Returns:
            dict: Personalized preferences and weights
        """
        user_oid = ObjectId(user_id)
        user = self.users.find_one({"_id": user_oid})
        
        if not user:
            return None
        
        # Get base preferences
        preferences = user.get("preferences", {})
        personalization = user.get("personalization", {})
        history = user.get("history", {})
        
        # Calculate dynamic weights based on user activity
        weights = personalization.get("recommendation_weights", {
            "food": 1.0, "culture": 1.0, "nightlife": 1.0, "shopping": 1.0, "nature": 1.0
        })
        
        # Analyze visited places to infer preferred neighborhoods
        visited_places = history.get("visited_places", [])
        neighborhood_counts = {}
        
        for place in visited_places:
            location = place.get("location", {})
            neighborhood = location.get("neighborhood")
            if neighborhood:
                neighborhood_counts[neighborhood] = neighborhood_counts.get(neighborhood, 0) + 1
        
        # Update preferred neighborhoods based on visit frequency
        preferred_neighborhoods = sorted(neighborhood_counts.keys(), 
                                       key=lambda x: neighborhood_counts[x], reverse=True)[:3]
        
        return {
            "preferences": preferences,
            "recommendation_weights": weights,
            "preferred_neighborhoods": preferred_neighborhoods,
            "visit_history_count": len(visited_places),
            "favorites_count": len(history.get("favorites", [])),
            "cultural_preferences": preferences.get("cultural_preferences", []),
            "interests": preferences.get("interests", [])
        }
    
    def update_preferences(self, user_id, new_preferences):
        """
        Update user preferences and immediately reflect in recommendations.
        
        Args:
            user_id (str): User's ObjectId as string
            new_preferences (dict): Updated preference data
        """
        user_oid = ObjectId(user_id)
        now = datetime.utcnow()
        
        # Update preferences
        update_data = {
            "personalization.last_recommendation_update": now
        }
        
        # Update individual preference fields
        for key, value in new_preferences.items():
            if key in ["food_restrictions", "interests", "cultural_preferences", "budget_range", "travel_style"]:
                update_data[f"preferences.{key}"] = value
        
        self.users.update_one(
            {"_id": user_oid},
            {"$set": update_data}
        )
        
        # Clear recommendation cache to force immediate update
        self._clear_user_cache(user_id)
    
    def _update_recommendation_weights(self, user_id, category, rating):
        """
        Update recommendation weights based on user activity.
        
        Args:
            user_id (str): User's ObjectId as string
            category (str): Place category (food, culture, nightlife, etc.)
            rating (int): User rating or implicit rating
        """
        if not category or not rating:
            return
        
        user_oid = ObjectId(user_id)
        
        # Map categories to weight keys
        category_mapping = {
            "restaurant": "food",
            "food": "food",
            "attraction": "culture",
            "cultural": "culture",
            "nightlife": "nightlife",
            "bar": "nightlife",
            "shopping": "shopping",
            "mall": "shopping",
            "nature": "nature",
            "park": "nature"
        }
        
        weight_key = category_mapping.get(category.lower())
        if not weight_key:
            return
        
        # Calculate weight adjustment based on rating
        adjustment = (rating - 3) * 0.1  # -0.2 to +0.2 adjustment
        
        # Update the specific weight
        self.users.update_one(
            {"_id": user_oid},
            {
                "$inc": {f"personalization.recommendation_weights.{weight_key}": adjustment},
                "$set": {"personalization.last_recommendation_update": datetime.utcnow()}
            }
        )
        
        # Ensure weights stay within reasonable bounds (0.1 to 2.0)
        user = self.users.find_one({"_id": user_oid})
        if user:
            weights = user.get("personalization", {}).get("recommendation_weights", {})
            updated_weights = {}
            
            for key, value in weights.items():
                updated_weights[key] = max(0.1, min(2.0, value))
            
            self.users.update_one(
                {"_id": user_oid},
                {"$set": {"personalization.recommendation_weights": updated_weights}}
            )
    
    def _clear_user_cache(self, user_id):
        """Clear recommendation cache for a specific user."""
        user_oid = ObjectId(user_id)
        self.recommendation_cache.delete_many({"user_id": user_oid})
    
    def get_user_by_id(self, user_id):
        """Get user by ObjectId with optimized query."""
        user_oid = ObjectId(user_id)
        return self.users.find_one({"_id": user_oid})
    
    def get_user_by_username(self, username):
        """Get user by username with optimized query."""
        return self.users.find_one({"username": username})
    
    def verify_password(self, user, password):
        """
        Verify user password using PBKDF2-SHA256 with account lockout protection.
        
        Args:
            user (dict): User document from database
            password (str): Plain text password to verify
            
        Returns:
            bool: True if password is correct and account is not locked
        """
        # Check if account is locked
        if user.get('account_locked_until'):
            locked_until = user['account_locked_until']
            if datetime.utcnow() < locked_until:
                return False
            else:
                # Unlock account if lock period has expired
                self.users.update_one(
                    {'_id': user['_id']},
                    {
                        '$unset': {'account_locked_until': ''},
                        '$set': {'failed_login_attempts': 0}
                    }
                )
        
        # Verify password
        is_valid = pbkdf2_sha256.verify(password, user["password_hash"])
        
        if is_valid:
            # Reset failed attempts and update last login
            self.users.update_one(
                {'_id': user['_id']},
                {
                    '$set': {
                        'failed_login_attempts': 0,
                        'last_login': datetime.utcnow()
                    },
                    '$unset': {'account_locked_until': ''}
                }
            )
            return True
        else:
            # Increment failed attempts
            failed_attempts = user.get('failed_login_attempts', 0) + 1
            update_data = {'failed_login_attempts': failed_attempts}
            
            # Lock account after 5 failed attempts for 30 minutes
            if failed_attempts >= 5:
                update_data['account_locked_until'] = datetime.utcnow() + timedelta(minutes=30)
            
            self.users.update_one(
                {'_id': user['_id']},
                {'$set': update_data}
            )
            return False
    
    def cache_recommendations(self, user_id, query_type, recommendations, cache_duration_hours=1):
        """
        Cache recommendations for improved performance.
        
        Args:
            user_id (str): User's ObjectId as string
            query_type (str): Type of query (cultural_discovery, local_search, personalized)
            recommendations (list): List of recommendations
            cache_duration_hours (int): Cache duration in hours
        """
        user_oid = ObjectId(user_id)
        now = datetime.utcnow()
        
        # Create cache key
        cache_key = hashlib.md5(f"{user_id}_{query_type}_{json.dumps(recommendations, sort_keys=True)}".encode()).hexdigest()
        
        cache_entry = {
            "cache_key": cache_key,
            "user_id": user_oid,
            "query_type": query_type,
            "recommendations": recommendations,
            "created_at": now,
            "expires_at": datetime.utcnow().replace(hour=now.hour + cache_duration_hours),
            "hit_count": 0
        }
        
        # Upsert cache entry
        self.recommendation_cache.replace_one(
            {"cache_key": cache_key},
            cache_entry,
            upsert=True
        )
    
    def get_cached_recommendations(self, user_id, query_type):
        """
        Retrieve cached recommendations if available and not expired.
        
        Args:
            user_id (str): User's ObjectId as string
            query_type (str): Type of query
            
        Returns:
            list or None: Cached recommendations or None if not found/expired
        """
        user_oid = ObjectId(user_id)
        now = datetime.utcnow()
        
        cache_entry = self.recommendation_cache.find_one({
            "user_id": user_oid,
            "query_type": query_type,
            "expires_at": {"$gt": now}
        })
        
        if cache_entry:
            # Increment hit count
            self.recommendation_cache.update_one(
                {"_id": cache_entry["_id"]},
                {"$inc": {"hit_count": 1}}
            )
            return cache_entry["recommendations"]
        
        return None
    
    def cleanup_expired_cache(self):
        """Remove expired cache entries for maintenance."""
        now = datetime.utcnow()
        result = self.recommendation_cache.delete_many({"expires_at": {"$lt": now}})
        return result.deleted_count
    
    def validate_security_configuration(self):
        """
        Validate that security configuration meets requirements.
        
        Returns:
            dict: Security validation results
        """
        issues = []
        warnings = []
        
        # Check if using default secret key
        from utils.config import config
        secret_key = config.get('SECRET_KEY')
        if secret_key == 'dev_secret_change_in_production':
            issues.append("Using default SECRET_KEY - change for production")
        elif len(secret_key) < 32:
            warnings.append("SECRET_KEY should be at least 32 characters long")
        
        # Check MongoDB connection security
        mongo_uri = config.get_database_uri()
        if 'localhost' in mongo_uri and not config.is_development():
            warnings.append("Using localhost MongoDB in non-development environment")
        
        # Check API key configuration
        api_keys = ['TASTEDIVE_API_KEY', 'ALGOLIA_API_KEY', 'GOOGLE_MAPS_API_KEY', 'GEMINI_API_KEY']
        missing_keys = []
        for key in api_keys:
            if not config.get(key):
                missing_keys.append(key)
        
        if missing_keys:
            warnings.append(f"Missing API keys: {', '.join(missing_keys)}")
        
        return {
            'secure': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'password_hashing': 'PBKDF2-SHA256',
            'session_security': 'Configured with HTTPOnly, Secure, SameSite',
            'account_lockout': 'Enabled (5 attempts, 30 min lockout)'
        }