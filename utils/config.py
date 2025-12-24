"""
Configuration management for API keys and environment variables.
Centralizes all environment variable loading with validation and defaults.
"""
import os
from typing import Optional, Dict, Any


class Config:
    """Configuration manager for API keys and environment variables."""
    
    def __init__(self):
        """Initialize configuration with environment variables."""
        self.config = self._load_config()
        self._validate_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        return {
            # API Keys
            'TASTEDIVE_API_KEY': os.getenv('TASTEDIVE_API_KEY'),
            'ALGOLIA_APP_ID': os.getenv('ALGOLIA_APP_ID'),
            'ALGOLIA_API_KEY': os.getenv('ALGOLIA_API_KEY'),
            'GOOGLE_MAPS_API_KEY': os.getenv('GOOGLE_MAPS_API_KEY'),
            'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY'),
            
            # Database
            'MONGO_URI': os.getenv('MONGO_URI', 'mongodb://localhost:27017/taste_trails_korea'),
            
            # Flask
            'SECRET_KEY': os.getenv('SECRET_KEY', 'dev_secret_change_in_production'),
            'FLASK_ENV': os.getenv('FLASK_ENV', 'development'),
            
            # Service Configuration
            'CIRCUIT_BREAKER_FAILURE_THRESHOLD': int(os.getenv('CIRCUIT_BREAKER_FAILURE_THRESHOLD', '5')),
            'CIRCUIT_BREAKER_RECOVERY_TIMEOUT': int(os.getenv('CIRCUIT_BREAKER_RECOVERY_TIMEOUT', '60')),
            'API_REQUEST_TIMEOUT': int(os.getenv('API_REQUEST_TIMEOUT', '10')),
            'MAX_RETRIES': int(os.getenv('MAX_RETRIES', '3')),
            
            # Search Configuration
            'DEFAULT_SEARCH_RADIUS': int(os.getenv('DEFAULT_SEARCH_RADIUS', '10000')),
            'MAX_SEARCH_RESULTS': int(os.getenv('MAX_SEARCH_RESULTS', '20')),
            
            # Performance Configuration
            'CACHE_TTL': int(os.getenv('CACHE_TTL', '3600')),  # 1 hour
            'RATE_LIMIT_PER_MINUTE': int(os.getenv('RATE_LIMIT_PER_MINUTE', '60'))
        }
    
    def _validate_config(self):
        """Validate critical configuration values."""
        warnings = []
        
        # Check for missing API keys (warn but don't fail)
        api_keys = ['TASTEDIVE_API_KEY', 'ALGOLIA_API_KEY', 'GOOGLE_MAPS_API_KEY', 'GEMINI_API_KEY']
        for key in api_keys:
            if not self.config.get(key):
                warnings.append(f"Warning: {key} not configured - service will use fallback mode")
        
        # Check for missing Algolia App ID
        if not self.config.get('ALGOLIA_APP_ID'):
            warnings.append("Warning: ALGOLIA_APP_ID not configured - Algolia service will be unavailable")
        
        # Print warnings
        for warning in warnings:
            print(warning)
        
        # Validate numeric values
        numeric_configs = [
            'CIRCUIT_BREAKER_FAILURE_THRESHOLD',
            'CIRCUIT_BREAKER_RECOVERY_TIMEOUT', 
            'API_REQUEST_TIMEOUT',
            'MAX_RETRIES',
            'DEFAULT_SEARCH_RADIUS',
            'MAX_SEARCH_RESULTS',
            'CACHE_TTL',
            'RATE_LIMIT_PER_MINUTE'
        ]
        
        for config_key in numeric_configs:
            value = self.config.get(config_key)
            if value is not None and value <= 0:
                print(f"Warning: {config_key} should be positive, got {value}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        return self.config.get(key, default)
    
    def get_api_key(self, service: str) -> Optional[str]:
        """Get API key for a specific service."""
        key_map = {
            'tastedive': 'TASTEDIVE_API_KEY',
            'algolia': 'ALGOLIA_API_KEY',
            'googlemaps': 'GOOGLE_MAPS_API_KEY',
            'gemini': 'GEMINI_API_KEY'
        }
        
        key_name = key_map.get(service.lower())
        if not key_name:
            return None
        
        return self.config.get(key_name)
    
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.config.get('FLASK_ENV') == 'development'
    
    def get_database_uri(self) -> str:
        """Get MongoDB connection URI."""
        return self.config.get('MONGO_URI')
    
    def get_service_config(self) -> Dict[str, Any]:
        """Get service-specific configuration."""
        return {
            'circuit_breaker': {
                'failure_threshold': self.config.get('CIRCUIT_BREAKER_FAILURE_THRESHOLD'),
                'recovery_timeout': self.config.get('CIRCUIT_BREAKER_RECOVERY_TIMEOUT')
            },
            'api': {
                'timeout': self.config.get('API_REQUEST_TIMEOUT'),
                'max_retries': self.config.get('MAX_RETRIES')
            },
            'search': {
                'default_radius': self.config.get('DEFAULT_SEARCH_RADIUS'),
                'max_results': self.config.get('MAX_SEARCH_RESULTS')
            },
            'cache': {
                'ttl': self.config.get('CACHE_TTL')
            },
            'rate_limit': {
                'per_minute': self.config.get('RATE_LIMIT_PER_MINUTE')
            }
        }
    
    def print_config_status(self):
        """Print configuration status for debugging."""
        print("=== Configuration Status ===")
        
        # API Keys Status
        print("\nAPI Keys:")
        api_services = ['TASTEDIVE_API_KEY', 'ALGOLIA_API_KEY', 'GOOGLE_MAPS_API_KEY', 'GEMINI_API_KEY']
        for service in api_services:
            status = "✓ Configured" if self.config.get(service) else "✗ Missing"
            print(f"  {service}: {status}")
        
        # Special case for Algolia (needs both App ID and API Key)
        algolia_status = "✓ Configured" if (self.config.get('ALGOLIA_APP_ID') and self.config.get('ALGOLIA_API_KEY')) else "✗ Incomplete"
        print(f"  ALGOLIA (App ID + API Key): {algolia_status}")
        
        # Database
        print(f"\nDatabase:")
        print(f"  MONGO_URI: {'✓ Configured' if self.config.get('MONGO_URI') else '✗ Missing'}")
        
        # Flask
        print(f"\nFlask:")
        print(f"  SECRET_KEY: {'✓ Configured' if self.config.get('SECRET_KEY') != 'dev_secret_change_in_production' else '⚠ Using default (change for production)'}")
        print(f"  Environment: {self.config.get('FLASK_ENV')}")
        
        print("\n=== End Configuration Status ===")


# Global configuration instance
config = Config()


def get_config() -> Config:
    """Get the global configuration instance."""
    return config