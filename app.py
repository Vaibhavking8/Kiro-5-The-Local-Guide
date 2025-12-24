from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_pymongo import PyMongo
from passlib.hash import pbkdf2_sha256
import os
import logging
import traceback
from datetime import datetime, timedelta
from utils.service_manager import service_manager
from utils.config import config
from utils.user_profile_manager import UserProfileManager
from bson.objectid import ObjectId
from functools import wraps
import json

app = Flask(__name__)
app.secret_key = config.get('SECRET_KEY')

# Configure comprehensive logging for production readiness
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/taste_trails_korea.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Log application startup
logger.info("=== Taste & Trails Korea Application Starting ===")
logger.info(f"Environment: {config.get('FLASK_ENV')}")
logger.info(f"Debug mode: {config.is_development()}")

# Print configuration status for monitoring
config.print_config_status()

# Log service manager status
service_status = service_manager.get_service_status()
logger.info("Service Manager Status:")
for service_name, status in service_status.items():
    logger.info(f"  {service_name}: {status.get('state', 'unknown')} ({'available' if status.get('available', False) else 'unavailable'})")

# Session configuration for security
app.config['SESSION_COOKIE_SECURE'] = not config.is_development()  # HTTPS only in production
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent XSS access to session cookie
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)  # 24-hour session timeout

# MongoDB config with error handling
try:
    app.config["MONGO_URI"] = config.get_database_uri()
    mongo = PyMongo(app)
    
    # Test database connection
    mongo.cx.admin.command('ping')
    logger.info("MongoDB connection established successfully")
    
    # Initialize User Profile Manager
    user_profile_manager = UserProfileManager(mongo.cx)
    logger.info("User Profile Manager initialized successfully")
    
except Exception as e:
    logger.error(f"Database initialization failed: {e}")
    # Continue without database for graceful degradation
    mongo = None
    user_profile_manager = None

# Google Maps API Key for templates
GOOGLE_MAPS_API_KEY = config.get_api_key('googlemaps')

# Comprehensive error handling decorators
def handle_errors(f):
    """Decorator to handle errors gracefully across all endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            # Log the full error with traceback
            logger.error(f"Error in {f.__name__}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Return appropriate error response based on request type
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({
                    'success': False,
                    'error': 'An internal error occurred. Please try again.',
                    'error_code': 'INTERNAL_ERROR'
                }), 500
            else:
                flash('An unexpected error occurred. Please try again.', 'error')
                return redirect(url_for('index') if is_authenticated() else url_for('login'))
    return decorated_function

def require_database(f):
    """Decorator to ensure database is available for database-dependent operations."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not mongo or not user_profile_manager:
            logger.error(f"Database unavailable for {f.__name__}")
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({
                    'success': False,
                    'error': 'Database temporarily unavailable. Please try again later.',
                    'error_code': 'DATABASE_UNAVAILABLE'
                }), 503
            else:
                flash('Service temporarily unavailable. Please try again later.', 'error')
                return render_template('error.html', 
                                     error_message="Database service is temporarily unavailable.")
        return f(*args, **kwargs)
    return decorated_function

def log_request_info(f):
    """Decorator to log request information for monitoring."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = datetime.utcnow()
        user_id = session.get('user_id', 'anonymous')
        
        logger.info(f"Request: {request.method} {request.path} - User: {user_id}")
        
        try:
            result = f(*args, **kwargs)
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Request completed: {request.method} {request.path} - Duration: {duration:.3f}s")
            return result
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Request failed: {request.method} {request.path} - Duration: {duration:.3f}s - Error: {str(e)}")
            raise
    return decorated_function

def require_auth(f):
    """Decorator to require authentication for protected routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            if not is_authenticated():
                logger.warning(f"Unauthorized access attempt to {request.path}")
                flash('Please log in to access this feature.', 'error')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Authentication check failed: {e}")
            flash('Authentication error. Please log in again.', 'error')
            return redirect(url_for('login'))
    return decorated_function

def is_authenticated():
    """Check if user is authenticated and session is valid."""
    try:
        if 'user_id' not in session:
            return False
        
        # Check session expiration
        if 'last_activity' in session:
            try:
                last_activity = datetime.fromisoformat(session['last_activity'])
                if datetime.utcnow() - last_activity > timedelta(hours=24):
                    logger.info(f"Session expired for user {session.get('user_id')}")
                    session.clear()
                    return False
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid session timestamp: {e}")
                session.clear()
                return False
        
        # Update last activity timestamp
        session['last_activity'] = datetime.utcnow().isoformat()
        session.permanent = True
        
        return True
    except Exception as e:
        logger.error(f"Session validation error: {e}")
        session.clear()
        return False

def get_current_user():
    """Get current authenticated user with session validation."""
    try:
        if not is_authenticated():
            return None
        
        if not user_profile_manager:
            logger.error("User profile manager unavailable")
            return None
        
        user = user_profile_manager.get_user_by_id(session['user_id'])
        if not user:
            # User no longer exists, clear session
            logger.warning(f"User {session['user_id']} no longer exists, clearing session")
            session.clear()
            return None
        return user
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        session.clear()
        return None

@app.before_request
def check_session_security():
    """Check session security before each request."""
    try:
        # Skip security checks for static files and login/signup pages
        if request.endpoint in ['static', 'login', 'signup'] or request.path.startswith('/static'):
            return
        
        # For authenticated routes, validate session
        if 'user_id' in session and not is_authenticated():
            flash('Your session has expired. Please log in again.', 'info')
            return redirect(url_for('login'))
    except Exception as e:
        logger.error(f"Session security check failed: {e}")
        # Continue with request to avoid breaking the application

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    logger.warning(f"404 error: {request.path}")
    if request.is_json or request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'error': 'Resource not found',
            'error_code': 'NOT_FOUND'
        }), 404
    return render_template('error.html', 
                         error_message="Page not found",
                         error_code=404), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"500 error: {str(error)}")
    if request.is_json or request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'error_code': 'INTERNAL_ERROR'
        }), 500
    return render_template('error.html', 
                         error_message="Internal server error",
                         error_code=500), 500

@app.errorhandler(503)
def service_unavailable_error(error):
    """Handle 503 errors."""
    logger.error(f"503 error: {str(error)}")
    if request.is_json or request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'error': 'Service temporarily unavailable',
            'error_code': 'SERVICE_UNAVAILABLE'
        }), 503
    return render_template('error.html', 
                         error_message="Service temporarily unavailable",
                         error_code=503), 503

@app.route('/', methods=['GET', 'POST'])
@require_auth
@require_database
@handle_errors
@log_request_info
def index():
    """Main page with AI-powered Korean cultural recommendations."""
    answer = ""
    recommendation_metadata = {}
    
    if request.method == 'POST':
        user_question = request.form.get('question', '').strip()
        
        if not user_question:
            flash('Please enter a question to get recommendations.', 'error')
            return render_template('index.html', answer=answer, google_maps_api_key=GOOGLE_MAPS_API_KEY)
        
        logger.info(f"Processing recommendation request: '{user_question}' for user {session['user_id']}")
        
        try:
            # Get user profile for personalization
            user = get_current_user()
            if not user:
                logger.error("Failed to get current user for recommendation")
                flash('Session error. Please log in again.', 'error')
                return redirect(url_for('login'))
            
            # Track search history
            try:
                user_profile_manager.update_search_history(session['user_id'], user_question)
                logger.debug(f"Search history updated for user {session['user_id']}")
            except Exception as e:
                logger.warning(f"Failed to update search history: {e}")
                # Continue without search history tracking
            
            # Use Local Guide System for authentic Korean recommendations
            start_time = datetime.utcnow()
            recommendation_result = service_manager.get_local_guide_recommendation(
                user_question, 
                user_profile=user,
                location=(37.5665, 126.9780)  # Default to Seoul center
            )
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Extract the response from the recommendation result
            answer = recommendation_result.get('response', 'I apologize, but I could not generate a response.')
            
            # Log recommendation quality for monitoring
            authenticity_score = recommendation_result.get('authenticity_score', 0)
            personalization_applied = recommendation_result.get('personalization_applied', False)
            fallback_used = recommendation_result.get('fallback_used', False)
            cultural_context = recommendation_result.get('cultural_context', [])
            
            recommendation_metadata = {
                'authenticity_score': authenticity_score,
                'personalization_applied': personalization_applied,
                'fallback_used': fallback_used,
                'cultural_context': cultural_context,
                'processing_time': processing_time,
                'recommendations_count': len(recommendation_result.get('recommendations', []))
            }
            
            logger.info(f"Recommendation generated - Authenticity: {authenticity_score:.2f}, "
                       f"Personalized: {personalization_applied}, Fallback: {fallback_used}, "
                       f"Processing time: {processing_time:.3f}s")
            
            # Log performance metrics
            if processing_time > 5.0:
                logger.warning(f"Slow recommendation generation: {processing_time:.3f}s for query '{user_question}'")
            
        except Exception as e:
            logger.error(f"Recommendation generation failed for '{user_question}': {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Provide fallback response
            answer = """
            <div class="error-fallback">
                <p>I apologize, but I'm having trouble generating recommendations right now.</p>
                <p>Here are some popular Korean experiences to explore:</p>
                <ul>
                    <li><strong>Hongdae</strong> - Youth culture and nightlife</li>
                    <li><strong>Myeongdong</strong> - Shopping and street food</li>
                    <li><strong>Itaewon</strong> - International district</li>
                    <li><strong>Insadong</strong> - Traditional arts and tea culture</li>
                </ul>
                <p><em>Please try your question again in a moment.</em></p>
            </div>
            """
            
            recommendation_metadata = {
                'authenticity_score': 0.0,
                'personalization_applied': False,
                'fallback_used': True,
                'error': True,
                'processing_time': 0.0
            }
    
    return render_template('index.html', 
                         answer=answer, 
                         google_maps_api_key=GOOGLE_MAPS_API_KEY,
                         recommendation_metadata=recommendation_metadata)

@app.route('/login', methods=['GET', 'POST'])
@require_database
@handle_errors
@log_request_info
def login():
    """User login with comprehensive security and error handling."""
    # Redirect if already authenticated
    if is_authenticated():
        logger.info(f"Already authenticated user {session.get('user_id')} redirected from login")
        return redirect(url_for('profile'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Input validation
        if not username or not password:
            logger.warning(f"Login attempt with missing credentials from IP: {request.remote_addr}")
            flash('Username and password are required.', 'error')
            return render_template('login.html')
        
        # Rate limiting check (basic implementation)
        session_key = f"login_attempts_{request.remote_addr}"
        login_attempts = session.get(session_key, 0)
        
        if login_attempts >= 5:
            logger.warning(f"Too many login attempts from IP: {request.remote_addr}")
            flash('Too many login attempts. Please try again later.', 'error')
            return render_template('login.html')
        
        try:
            user = user_profile_manager.get_user_by_username(username)
            
            if user and user_profile_manager.verify_password(user, password):
                # Successful login
                session['user_id'] = str(user['_id'])
                session['username'] = user['username']
                session['last_activity'] = datetime.utcnow().isoformat()
                session.permanent = True
                
                # Clear login attempts
                session.pop(session_key, None)
                
                logger.info(f"Successful login for user: {username}")
                flash('Successfully logged in!', 'success')
                return redirect(url_for('profile'))
            else:
                # Failed login
                session[session_key] = login_attempts + 1
                logger.warning(f"Failed login attempt for username: {username} from IP: {request.remote_addr}")
                flash('Invalid username or password.', 'error')
                
        except Exception as e:
            logger.error(f"Login error for username {username}: {str(e)}")
            flash('Login error. Please try again.', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
@require_database
@handle_errors
@log_request_info
def signup():
    """User registration with comprehensive validation and error handling."""
    # Redirect if already authenticated
    if is_authenticated():
        logger.info(f"Already authenticated user {session.get('user_id')} redirected from signup")
        return redirect(url_for('profile'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        # Input validation
        if not username or not email or not password:
            logger.warning(f"Signup attempt with missing fields from IP: {request.remote_addr}")
            flash('All fields are required.', 'error')
            return render_template('signup.html')
        
        # Enhanced password validation
        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'error')
            return render_template('signup.html')
        
        # Email format validation (basic)
        if '@' not in email or '.' not in email:
            flash('Please enter a valid email address.', 'error')
            return render_template('signup.html')
        
        try:
            # Check if user already exists
            if user_profile_manager.get_user_by_username(username):
                logger.info(f"Signup attempt with existing username: {username}")
                flash('Username already taken.', 'error')
                return render_template('signup.html')
            
            if mongo.db.users.find_one({'email': email}):
                logger.info(f"Signup attempt with existing email: {email}")
                flash('Email already registered.', 'error')
                return render_template('signup.html')
            
            # Get additional preferences from form with defaults
            food_restrictions = [x.strip() for x in request.form.get('food_restrictions', '').split(',') if x.strip()]
            interests = [x.strip() for x in request.form.get('interests', '').split(',') if x.strip()]
            cultural_preferences = [x.strip() for x in request.form.get('cultural_preferences', '').split(',') if x.strip()]
            
            user_data = {
                'username': username,
                'email': email,
                'password': password,
                'phone': request.form.get('phone', '').strip(),
                'address': request.form.get('address', '').strip(),
                'food_restrictions': food_restrictions,
                'interests': interests,
                'cultural_preferences': cultural_preferences,
                'budget_range': request.form.get('budget_range', 'mid-range'),
                'travel_style': request.form.get('travel_style', 'solo')
            }
            
            # Create user profile
            user_id = user_profile_manager.create_user_profile(user_data)
            
            logger.info(f"New user created successfully: {username} (ID: {user_id})")
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            logger.error(f"User creation failed for {username}: {str(e)}")
            flash('Account creation failed. Please try again.', 'error')
            return render_template('signup.html')
    
    return render_template('signup.html')

@app.route('/api/map/attractions')
@require_auth
@handle_errors
@log_request_info
def get_korean_attractions():
    """API endpoint to get Korean attractions with accurate positioning."""
    try:
        query = request.args.get('query', 'korean attractions')
        lat = request.args.get('lat', type=float)
        lng = request.args.get('lng', type=float)
        
        # Validate coordinates if provided
        if lat is not None and lng is not None:
            if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                return jsonify({
                    'success': False,
                    'error': 'Invalid coordinates provided',
                    'error_code': 'INVALID_COORDINATES'
                }), 400
            location = (lat, lng)
        else:
            location = None
        
        # Check if Google Maps service is available
        googlemaps_service = service_manager.get_service('googlemaps')
        if not googlemaps_service or not googlemaps_service.is_available():
            logger.warning("Google Maps service unavailable for attractions request")
            return jsonify({
                'success': False,
                'error': 'Map service temporarily unavailable',
                'error_code': 'SERVICE_UNAVAILABLE',
                'attractions': []
            }), 503
        
        # Get enhanced Korean attractions
        start_time = datetime.utcnow()
        attractions = googlemaps_service.get_accurate_korean_attractions(query, location)
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        logger.info(f"Attractions request processed: {len(attractions)} results in {processing_time:.3f}s")
        
        return jsonify({
            'success': True,
            'attractions': attractions,
            'total': len(attractions),
            'processing_time': processing_time
        })
        
    except Exception as e:
        logger.error(f"Attractions API error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve attractions',
            'error_code': 'ATTRACTIONS_ERROR',
            'attractions': []
        }), 500

@app.route('/api/map/amenities')
@require_auth
@handle_errors
@log_request_info
def get_nearby_amenities():
    """API endpoint to discover nearby amenities with cultural context."""
    try:
        lat = request.args.get('lat', type=float)
        lng = request.args.get('lng', type=float)
        amenity_types = request.args.getlist('types')  # Can specify multiple types
        
        # Validate required coordinates
        if not lat or not lng:
            return jsonify({
                'success': False,
                'error': 'Location coordinates (lat, lng) are required',
                'error_code': 'MISSING_COORDINATES'
            }), 400
        
        # Validate coordinate ranges
        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            return jsonify({
                'success': False,
                'error': 'Invalid coordinate values',
                'error_code': 'INVALID_COORDINATES'
            }), 400
        
        # Default amenity types if none specified
        if not amenity_types:
            amenity_types = ['restaurant', 'lodging', 'subway_station', 'bus_station']
        
        # Validate amenity types
        valid_types = ['restaurant', 'lodging', 'subway_station', 'bus_station', 'tourist_attraction', 'shopping_mall']
        invalid_types = [t for t in amenity_types if t not in valid_types]
        if invalid_types:
            return jsonify({
                'success': False,
                'error': f'Invalid amenity types: {invalid_types}',
                'error_code': 'INVALID_AMENITY_TYPES',
                'valid_types': valid_types
            }), 400
        
        # Check if Google Maps service is available
        googlemaps_service = service_manager.get_service('googlemaps')
        if not googlemaps_service or not googlemaps_service.is_available():
            logger.warning("Google Maps service unavailable for amenities request")
            return jsonify({
                'success': False,
                'error': 'Map service temporarily unavailable',
                'error_code': 'SERVICE_UNAVAILABLE',
                'amenities': {}
            }), 503
        
        # Discover nearby amenities with cultural context
        start_time = datetime.utcnow()
        amenities = googlemaps_service.discover_nearby_amenities((lat, lng), amenity_types)
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        total_amenities = sum(len(amenities_list) for amenities_list in amenities.values())
        logger.info(f"Amenities request processed: {total_amenities} results in {processing_time:.3f}s")
        
        return jsonify({
            'success': True,
            'amenities': amenities,
            'location': {'lat': lat, 'lng': lng},
            'processing_time': processing_time,
            'total_amenities': total_amenities
        })
        
    except Exception as e:
        logger.error(f"Amenities API error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve nearby amenities',
            'error_code': 'AMENITIES_ERROR',
            'amenities': {}
        }), 500

@app.route('/api/map/optimize-view')
@require_auth
@handle_errors
@log_request_info
def optimize_map_view():
    """API endpoint to get optimized map view with clustering configuration."""
    try:
        # Get locations from request (can be sent as JSON in POST or query params)
        locations_param = request.args.get('locations')
        
        if not locations_param:
            return jsonify({
                'success': False,
                'error': 'Locations parameter is required',
                'error_code': 'MISSING_LOCATIONS'
            }), 400
        
        try:
            locations = json.loads(locations_param)
            
            # Validate locations format
            if not isinstance(locations, list):
                return jsonify({
                    'success': False,
                    'error': 'Locations must be an array',
                    'error_code': 'INVALID_LOCATIONS_FORMAT'
                }), 400
            
            # Validate each location
            for i, location in enumerate(locations):
                if not isinstance(location, dict) or 'lat' not in location or 'lng' not in location:
                    return jsonify({
                        'success': False,
                        'error': f'Invalid location format at index {i}. Expected {{lat: number, lng: number}}',
                        'error_code': 'INVALID_LOCATION_FORMAT'
                    }), 400
                
                lat, lng = location['lat'], location['lng']
                if not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
                    return jsonify({
                        'success': False,
                        'error': f'Invalid coordinates at index {i}. Lat and lng must be numbers',
                        'error_code': 'INVALID_COORDINATES'
                    }), 400
                
                if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                    return jsonify({
                        'success': False,
                        'error': f'Coordinates out of range at index {i}',
                        'error_code': 'COORDINATES_OUT_OF_RANGE'
                    }), 400
            
        except json.JSONDecodeError as e:
            return jsonify({
                'success': False,
                'error': f'Invalid JSON format: {str(e)}',
                'error_code': 'INVALID_JSON'
            }), 400
        
        # Check if Google Maps service is available
        googlemaps_service = service_manager.get_service('googlemaps')
        if not googlemaps_service or not googlemaps_service.is_available():
            logger.warning("Google Maps service unavailable for map optimization request")
            return jsonify({
                'success': False,
                'error': 'Map service temporarily unavailable',
                'error_code': 'SERVICE_UNAVAILABLE'
            }), 503
        
        # Get optimized map view configuration
        start_time = datetime.utcnow()
        map_config = googlemaps_service.get_optimized_map_view(locations)
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        logger.info(f"Map optimization processed: {len(locations)} locations in {processing_time:.3f}s")
        
        return jsonify({
            'success': True,
            'map_config': map_config,
            'processing_time': processing_time,
            'locations_count': len(locations)
        })
        
    except Exception as e:
        logger.error(f"Map optimization API error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to optimize map view',
            'error_code': 'MAP_OPTIMIZATION_ERROR'
        }), 500

# Health check and monitoring endpoints
@app.route('/api/health')
@handle_errors
def health_check():
    """Health check endpoint for monitoring."""
    try:
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'environment': config.get('FLASK_ENV'),
            'services': {}
        }
        
        # Check database connection
        try:
            if mongo:
                mongo.cx.admin.command('ping')
                health_status['services']['database'] = {'status': 'healthy', 'type': 'mongodb'}
            else:
                health_status['services']['database'] = {'status': 'unavailable', 'type': 'mongodb'}
                health_status['status'] = 'degraded'
        except Exception as e:
            health_status['services']['database'] = {'status': 'unhealthy', 'error': str(e), 'type': 'mongodb'}
            health_status['status'] = 'degraded'
        
        # Check service manager status
        try:
            service_status = service_manager.get_service_status()
            health_status['services'].update(service_status)
            
            # Determine overall health based on service availability
            available_services = sum(1 for status in service_status.values() if status.get('available', False))
            total_services = len(service_status)
            
            if available_services == 0:
                health_status['status'] = 'unhealthy'
            elif available_services < total_services:
                health_status['status'] = 'degraded'
                
        except Exception as e:
            health_status['services']['service_manager'] = {'status': 'unhealthy', 'error': str(e)}
            health_status['status'] = 'degraded'
        
        # Return appropriate HTTP status code
        status_code = 200 if health_status['status'] == 'healthy' else 503
        
        return jsonify(health_status), status_code
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': 'Health check failed'
        }), 503

@app.route('/api/status')
@require_auth
@handle_errors
def system_status():
    """Detailed system status for authenticated users."""
    try:
        status = {
            'timestamp': datetime.utcnow().isoformat(),
            'uptime': 'N/A',  # Would need to track application start time
            'environment': config.get('FLASK_ENV'),
            'database': {},
            'services': {},
            'configuration': {}
        }
        
        # Database status
        try:
            if mongo:
                db_stats = mongo.cx.taste_trails_korea.command('dbStats')
                status['database'] = {
                    'status': 'connected',
                    'name': 'taste_trails_korea',
                    'collections': db_stats.get('collections', 0),
                    'data_size': db_stats.get('dataSize', 0),
                    'storage_size': db_stats.get('storageSize', 0)
                }
            else:
                status['database'] = {'status': 'unavailable'}
        except Exception as e:
            status['database'] = {'status': 'error', 'error': str(e)}
        
        # Service status
        status['services'] = service_manager.get_service_status()
        
        # Configuration status (without sensitive data)
        status['configuration'] = {
            'api_keys_configured': {
                'tastedive': bool(config.get_api_key('tastedive')),
                'algolia': bool(config.get_api_key('algolia')),
                'googlemaps': bool(config.get_api_key('googlemaps')),
                'gemini': bool(config.get_api_key('gemini'))
            },
            'circuit_breaker_threshold': config.get('CIRCUIT_BREAKER_FAILURE_THRESHOLD'),
            'api_timeout': config.get('API_REQUEST_TIMEOUT'),
            'max_retries': config.get('MAX_RETRIES')
        }
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"System status check failed: {str(e)}")
        return jsonify({
            'error': 'Failed to retrieve system status',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@app.route('/map')
@require_auth
@require_database
@handle_errors
@log_request_info
def interactive_map():
    """Interactive map page with enhanced Korean attractions and amenities."""
    try:
        user = get_current_user()
        if not user:
            flash('Session error. Please log in again.', 'error')
            return redirect(url_for('login'))
        
        # Get user's favorite places for map initialization
        favorites = user.get('history', {}).get('favorites', [])
        visited_places = user.get('history', {}).get('visited_places', [])
        
        # Validate and sanitize data
        safe_favorites = []
        for fav in favorites:
            if isinstance(fav, dict) and fav.get('name'):
                safe_favorites.append({
                    'name': str(fav.get('name', '')),
                    'category': str(fav.get('category', 'attraction')),
                    'place_id': str(fav.get('place_id', ''))
                })
        
        safe_visited = []
        for place in visited_places:
            if isinstance(place, dict) and place.get('name'):
                safe_visited.append({
                    'name': str(place.get('name', '')),
                    'location': place.get('location', {}),
                    'visited_date': str(place.get('visited_date', '')),
                    'rating': place.get('rating', 0)
                })
        
        logger.info(f"Interactive map loaded for user {session['user_id']}: {len(safe_favorites)} favorites, {len(safe_visited)} visited places")
        
        return render_template('map.html', 
                             google_maps_api_key=GOOGLE_MAPS_API_KEY,
                             user_favorites=safe_favorites,
                             visited_places=safe_visited)
                             
    except Exception as e:
        logger.error(f"Interactive map error for user {session.get('user_id')}: {str(e)}")
        flash('Error loading map. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/logout')
@log_request_info
def logout():
    """Secure logout with complete session cleanup."""
    user_id = session.get('user_id', 'unknown')
    logger.info(f"User logout: {user_id}")
    
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/settings')
@require_auth
@require_database
@handle_errors
@log_request_info
def settings():
    """Settings page with personalized recommendations using Local Guide System."""
    try:
        user = get_current_user()
        if not user:
            flash('Session error. Please log in again.', 'error')
            return redirect(url_for('login'))
        
        # Get personalized recommendations using Local Guide System
        personalized_prefs = user_profile_manager.get_personalized_preferences(session['user_id'])
        
        filtered_recs = []
        
        if personalized_prefs:
            interests = personalized_prefs.get('interests', [])
            visited = set([place['name'] for place in user.get('history', {}).get('visited_places', [])])
            favorites = set([fav['name'] for fav in user.get('history', {}).get('favorites', [])])
            
            # Use Local Guide System for personalized recommendations
            try:
                # Create a query based on user interests
                interest_query = f"korean culture {' '.join(interests)}" if interests else "korean culture recommendations"
                
                start_time = datetime.utcnow()
                recommendation_result = service_manager.get_local_guide_recommendation(
                    interest_query,
                    user_profile=user,
                    location=(37.5665, 126.9780)  # Seoul center
                )
                processing_time = (datetime.utcnow() - start_time).total_seconds()
                
                # Extract recommendation names for the settings page
                recommendations = recommendation_result.get('recommendations', [])
                
                for rec in recommendations:
                    rec_name = rec.get('Name', rec.get('name', ''))
                    if rec_name and rec_name not in visited and rec_name not in favorites:
                        filtered_recs.append(str(rec_name))
                
                # Limit to 8 recommendations
                filtered_recs = filtered_recs[:8]
                
                logger.info(f"Settings recommendations generated for user {session['user_id']}: {len(filtered_recs)} recommendations in {processing_time:.3f}s")
                
            except Exception as e:
                logger.warning(f"Local Guide System failed in settings for user {session['user_id']}: {e}")
                
                # Fallback to legacy system
                try:
                    recommendations = []
                    if interests:
                        cultural_recs = service_manager.get_cultural_recommendations("korean culture", interests)
                        recommendations.extend(cultural_recs)
                    
                    # Get place recommendations
                    place_recs = service_manager.search_places("korean attractions", location=(37.5665, 126.9780))
                    recommendations.extend(place_recs[:5])  # Add top 5 places
                    
                    # Filter out already visited and favorited items
                    for rec in recommendations:
                        rec_name = rec.get('Name') or rec.get('name', '')
                        if rec_name and rec_name not in visited and rec_name not in favorites:
                            filtered_recs.append(str(rec_name))
                    
                    # Limit to 8 recommendations
                    filtered_recs = filtered_recs[:8]
                    
                    logger.info(f"Fallback recommendations generated for user {session['user_id']}: {len(filtered_recs)} recommendations")
                    
                except Exception as fallback_error:
                    logger.error(f"Both Local Guide System and fallback failed for user {session['user_id']}: {fallback_error}")
                    filtered_recs = []
        
        return render_template('settings.html', 
                             user=user, 
                             recommendations=filtered_recs, 
                             personalized_prefs=personalized_prefs)
                             
    except Exception as e:
        logger.error(f"Settings page error for user {session.get('user_id')}: {str(e)}")
        flash('Error loading settings. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
@require_auth
@require_database
@handle_errors
@log_request_info
def profile():
    """User profile management with comprehensive error handling."""
    try:
        user = get_current_user()
        if not user:
            flash('Session error. Please log in again.', 'error')
            return redirect(url_for('login'))
        
        if request.method == 'POST':
            # Update preferences using enhanced profile manager
            try:
                food_restrictions = [x.strip() for x in request.form.get('food_restrictions', '').split(',') if x.strip()]
                interests = [x.strip() for x in request.form.get('interests', '').split(',') if x.strip()]
                cultural_preferences = [x.strip() for x in request.form.get('cultural_preferences', '').split(',') if x.strip()]
                budget_range = request.form.get('budget_range', 'mid-range')
                travel_style = request.form.get('travel_style', 'solo')
                
                # Validate inputs
                valid_budget_ranges = ['budget', 'mid-range', 'luxury']
                valid_travel_styles = ['solo', 'couple', 'family', 'group']
                
                if budget_range not in valid_budget_ranges:
                    budget_range = 'mid-range'
                if travel_style not in valid_travel_styles:
                    travel_style = 'solo'
                
                new_preferences = {
                    'food_restrictions': food_restrictions,
                    'interests': interests,
                    'cultural_preferences': cultural_preferences,
                    'budget_range': budget_range,
                    'travel_style': travel_style
                }
                
                user_profile_manager.update_preferences(session['user_id'], new_preferences)
                
                logger.info(f"Preferences updated for user {session['user_id']}")
                flash('Preferences updated! Your recommendations will be updated immediately.', 'success')
                return redirect(url_for('profile'))
                
            except Exception as e:
                logger.error(f"Failed to update preferences for user {session['user_id']}: {str(e)}")
                flash('Failed to update preferences. Please try again.', 'error')
        
        # Get personalized preferences for display
        try:
            personalized_prefs = user_profile_manager.get_personalized_preferences(session['user_id'])
        except Exception as e:
            logger.warning(f"Failed to get personalized preferences for user {session['user_id']}: {str(e)}")
            personalized_prefs = None
        
        return render_template('profile.html', user=user, personalized_prefs=personalized_prefs)
        
    except Exception as e:
        logger.error(f"Profile page error for user {session.get('user_id')}: {str(e)}")
        flash('Error loading profile. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/profile_edit', methods=['GET', 'POST'])
@require_auth
@require_database
@handle_errors
@log_request_info
def profile_edit():
    """Profile editing with comprehensive validation and error handling."""
    try:
        user = get_current_user()
        if not user:
            flash('Session error. Please log in again.', 'error')
            return redirect(url_for('login'))
        
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip().lower()
            phone = request.form.get('phone', '').strip()
            address = request.form.get('address', '').strip()
            
            # Input validation
            if not username or not email:
                flash('Username and email are required.', 'error')
                return render_template('profile_edit.html', user=user)
            
            # Email format validation
            if '@' not in email or '.' not in email:
                flash('Please enter a valid email address.', 'error')
                return render_template('profile_edit.html', user=user)
            
            # Check if username/email already exists (excluding current user)
            try:
                existing_user = user_profile_manager.get_user_by_username(username)
                if existing_user and str(existing_user['_id']) != session['user_id']:
                    flash('Username already taken by another user.', 'error')
                    return render_template('profile_edit.html', user=user)
                
                existing_email = mongo.db.users.find_one({'email': email, '_id': {'$ne': user['_id']}})
                if existing_email:
                    flash('Email already registered by another user.', 'error')
                    return render_template('profile_edit.html', user=user)
                    
            except Exception as e:
                logger.error(f"Error checking existing user data: {str(e)}")
                flash('Error validating user data. Please try again.', 'error')
                return render_template('profile_edit.html', user=user)
            
            update_fields = {
                'username': username,
                'email': email,
                'phone': phone,
                'address': address
            }
            
            # Handle password update with validation
            new_password = request.form.get('password', '').strip()
            if new_password:
                if len(new_password) < 8:
                    flash('Password must be at least 8 characters long.', 'error')
                    return render_template('profile_edit.html', user=user)
                update_fields['password_hash'] = pbkdf2_sha256.hash(new_password)
                logger.info(f"Password updated for user {session['user_id']}")
            
            try:
                mongo.db.users.update_one({'_id': user['_id']}, {'$set': update_fields})
                
                # Update session username if changed
                if username != session.get('username'):
                    session['username'] = username
                
                logger.info(f"Profile updated for user {session['user_id']}")
                flash('Profile updated successfully!', 'success')
                return redirect(url_for('profile_edit'))
                
            except Exception as e:
                logger.error(f"Failed to update profile for user {session['user_id']}: {str(e)}")
                flash('Failed to update profile. Please try again.', 'error')
        
        return render_template('profile_edit.html', user=user)
        
    except Exception as e:
        logger.error(f"Profile edit error for user {session.get('user_id')}: {str(e)}")
        flash('Error loading profile editor. Please try again.', 'error')
        return redirect(url_for('profile'))

@app.route('/add_visited', methods=['POST'])
@require_auth
@require_database
@handle_errors
@log_request_info
def add_visited():
    """Add visited place with comprehensive validation and error handling."""
    try:
        user = get_current_user()
        if not user:
            flash('Session error. Please log in again.', 'error')
            return redirect(url_for('login'))
        
        place_name = request.form.get('place', '').strip()
        if not place_name:
            flash('Place name is required.', 'error')
            return redirect(url_for('settings'))
        
        # Validate and sanitize input data
        rating = request.form.get('rating', type=int)
        if rating is not None and not (1 <= rating <= 5):
            rating = None  # Invalid rating, set to None
        
        category = request.form.get('category', 'attraction').strip()
        valid_categories = ['attraction', 'restaurant', 'hotel', 'transport', 'shopping', 'entertainment']
        if category not in valid_categories:
            category = 'attraction'
        
        notes = request.form.get('notes', '').strip()
        if len(notes) > 500:  # Limit notes length
            notes = notes[:500]
        
        # Create enhanced place data
        visited_place = {
            'name': place_name,
            'category': category,
            'location': {
                'lat': request.form.get('lat', type=float),
                'lng': request.form.get('lng', type=float),
                'neighborhood': request.form.get('neighborhood', '').strip()
            },
            'notes': notes
        }
        
        # Validate coordinates if provided
        if visited_place['location']['lat'] is not None and visited_place['location']['lng'] is not None:
            lat, lng = visited_place['location']['lat'], visited_place['location']['lng']
            if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                # Invalid coordinates, remove them
                visited_place['location'] = {'neighborhood': visited_place['location']['neighborhood']}
        
        try:
            user_profile_manager.update_user_history(session['user_id'], visited_place, rating)
            logger.info(f"Added visited place '{place_name}' for user {session['user_id']}")
            flash(f'Added {place_name} to visited places with enhanced tracking.', 'success')
        except Exception as e:
            logger.error(f"Failed to add visited place for user {session['user_id']}: {str(e)}")
            flash('Failed to add visited place. Please try again.', 'error')
        
        return redirect(url_for('settings'))
        
    except Exception as e:
        logger.error(f"Add visited place error for user {session.get('user_id')}: {str(e)}")
        flash('Error adding visited place. Please try again.', 'error')
        return redirect(url_for('settings'))

@app.route('/remove_visited', methods=['POST'])
@require_auth
@require_database
@handle_errors
@log_request_info
def remove_visited():
    """Remove visited place with error handling."""
    try:
        user = get_current_user()
        if not user:
            flash('Session error. Please log in again.', 'error')
            return redirect(url_for('login'))
        
        place_name = request.form.get('place', '').strip()
        if not place_name:
            flash('Place name is required.', 'error')
            return redirect(url_for('settings'))
        
        try:
            # Remove from visited places using direct MongoDB update for now
            # TODO: Add method to user_profile_manager for removing visited places
            result = mongo.db.users.update_one(
                {'_id': user['_id']}, 
                {'$pull': {'history.visited_places': {'name': place_name}}}
            )
            
            if result.modified_count > 0:
                user_profile_manager._clear_user_cache(session['user_id'])
                logger.info(f"Removed visited place '{place_name}' for user {session['user_id']}")
                flash(f'Removed {place_name} from visited places.', 'success')
            else:
                flash(f'Place {place_name} was not found in visited places.', 'warning')
                
        except Exception as e:
            logger.error(f"Failed to remove visited place for user {session['user_id']}: {str(e)}")
            flash('Failed to remove visited place. Please try again.', 'error')
        
        return redirect(url_for('settings'))
        
    except Exception as e:
        logger.error(f"Remove visited place error for user {session.get('user_id')}: {str(e)}")
        flash('Error removing visited place. Please try again.', 'error')
        return redirect(url_for('settings'))

@app.route('/add_favorite', methods=['POST'])
@require_auth
@require_database
@handle_errors
@log_request_info
def add_favorite():
    """Add favorite place with comprehensive validation and error handling."""
    try:
        user = get_current_user()
        if not user:
            flash('Session error. Please log in again.', 'error')
            return redirect(url_for('login'))
        
        place_name = request.form.get('fav', '').strip()
        if not place_name:
            flash('Place name is required.', 'error')
            return redirect(url_for('settings'))
        
        # Validate and sanitize input data
        category = request.form.get('category', 'attraction').strip()
        valid_categories = ['attraction', 'restaurant', 'hotel', 'transport', 'shopping', 'entertainment']
        if category not in valid_categories:
            category = 'attraction'
        
        place_id = request.form.get('place_id', '').strip()
        
        favorite_place = {
            'name': place_name,
            'category': category,
            'place_id': place_id
        }
        
        try:
            user_profile_manager.add_favorite(session['user_id'], favorite_place)
            logger.info(f"Added favorite place '{place_name}' for user {session['user_id']}")
            flash(f'Added {place_name} to favorites with enhanced tracking.', 'success')
        except Exception as e:
            logger.error(f"Failed to add favorite place for user {session['user_id']}: {str(e)}")
            flash('Failed to add favorite place. Please try again.', 'error')
        
        return redirect(url_for('settings'))
        
    except Exception as e:
        logger.error(f"Add favorite place error for user {session.get('user_id')}: {str(e)}")
        flash('Error adding favorite place. Please try again.', 'error')
        return redirect(url_for('settings'))

@app.route('/remove_favorite', methods=['POST'])
@require_auth
@require_database
@handle_errors
@log_request_info
def remove_favorite():
    """Remove favorite place with error handling."""
    try:
        user = get_current_user()
        if not user:
            flash('Session error. Please log in again.', 'error')
            return redirect(url_for('login'))
        
        place_name = request.form.get('fav', '').strip()
        if not place_name:
            flash('Place name is required.', 'error')
            return redirect(url_for('settings'))
        
        try:
            user_profile_manager.remove_favorite(session['user_id'], place_name)
            logger.info(f"Removed favorite place '{place_name}' for user {session['user_id']}")
            flash(f'Removed {place_name} from favorites.', 'success')
        except Exception as e:
            logger.error(f"Failed to remove favorite place for user {session['user_id']}: {str(e)}")
            flash('Failed to remove favorite place. Please try again.', 'error')
        
        return redirect(url_for('settings'))
        
    except Exception as e:
        logger.error(f"Remove favorite place error for user {session.get('user_id')}: {str(e)}")
        flash('Error removing favorite place. Please try again.', 'error')
        return redirect(url_for('settings'))

# New API endpoints for enhanced functionality
@app.route('/api/user/preferences', methods=['GET'])
@require_auth
@require_database
@handle_errors
@log_request_info
def get_user_preferences():
    """API endpoint to get user's personalized preferences."""
    try:
        personalized_prefs = user_profile_manager.get_personalized_preferences(session['user_id'])
        if personalized_prefs:
            # Remove sensitive information before returning
            safe_prefs = {
                'interests': personalized_prefs.get('interests', []),
                'cultural_preferences': personalized_prefs.get('cultural_preferences', []),
                'budget_range': personalized_prefs.get('budget_range', 'mid-range'),
                'travel_style': personalized_prefs.get('travel_style', 'solo'),
                'preferred_neighborhoods': personalized_prefs.get('preferred_neighborhoods', []),
                'recommendation_weights': personalized_prefs.get('recommendation_weights', {})
            }
            
            logger.debug(f"User preferences retrieved for user {session['user_id']}")
            return jsonify({
                'success': True,
                'preferences': safe_prefs
            })
        else:
            return jsonify({
                'success': False,
                'error': 'User preferences not found',
                'error_code': 'USER_NOT_FOUND'
            }), 404
            
    except Exception as e:
        logger.error(f"Failed to get user preferences for user {session['user_id']}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve user preferences',
            'error_code': 'PREFERENCES_ERROR'
        }), 500

@app.route('/api/user/recommendation_weights', methods=['GET'])
@require_auth
@require_database
@handle_errors
@log_request_info
def get_recommendation_weights():
    """API endpoint to get user's current recommendation weights."""
    try:
        personalized_prefs = user_profile_manager.get_personalized_preferences(session['user_id'])
        if personalized_prefs:
            weights_data = {
                'recommendation_weights': personalized_prefs.get('recommendation_weights', {}),
                'preferred_neighborhoods': personalized_prefs.get('preferred_neighborhoods', []),
                'last_updated': personalized_prefs.get('last_recommendation_update', '')
            }
            
            logger.debug(f"Recommendation weights retrieved for user {session['user_id']}")
            return jsonify({
                'success': True,
                'data': weights_data
            })
        else:
            return jsonify({
                'success': False,
                'error': 'User not found',
                'error_code': 'USER_NOT_FOUND'
            }), 404
            
    except Exception as e:
        logger.error(f"Failed to get recommendation weights for user {session['user_id']}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve recommendation weights',
            'error_code': 'WEIGHTS_ERROR'
        }), 500

# Create error template if it doesn't exist
@app.route('/error')
def error_page():
    """Generic error page."""
    error_message = request.args.get('message', 'An unexpected error occurred')
    error_code = request.args.get('code', '500')
    return render_template('error.html', 
                         error_message=error_message, 
                         error_code=error_code)

# Application startup and monitoring
def log_startup_summary():
    """Log comprehensive startup summary for monitoring."""
    logger.info("=== Application Startup Summary ===")
    
    # Database status
    db_status = "Connected" if mongo and user_profile_manager else "Unavailable"
    logger.info(f"Database: {db_status}")
    
    # Service status
    service_status = service_manager.get_service_status()
    healthy_services = [name for name, status in service_status.items() if status.get('available', False)]
    logger.info(f"Healthy Services: {len(healthy_services)}/{len(service_status)} - {healthy_services}")
    
    # Configuration status
    api_keys_configured = sum([
        1 for service in ['tastedive', 'algolia', 'googlemaps', 'gemini']
        if config.get_api_key(service)
    ])
    logger.info(f"API Keys Configured: {api_keys_configured}/4")
    
    # Overall health
    overall_health = "Healthy" if db_status == "Connected" and len(healthy_services) > 0 else "Degraded"
    logger.info(f"Overall Application Health: {overall_health}")
    
    logger.info("=== End Startup Summary ===")

if __name__ == '__main__':
    # Log startup summary
    log_startup_summary()
    
    # Start application
    debug_mode = config.is_development()
    logger.info(f"Starting Flask application in {'development' if debug_mode else 'production'} mode")
    
    try:
        app.run(debug=debug_mode, host='0.0.0.0', port=5000)
    except Exception as e:
        logger.critical(f"Failed to start Flask application: {str(e)}")
        raise 