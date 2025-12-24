# Technology Stack

## Backend Framework
- **Flask**: Python web framework for the main application
- **Python 3.8+**: Required runtime version

## Database
- **MongoDB**: Document database for user data storage
- **Flask-PyMongo**: MongoDB integration for Flask
- **Collections**: `users` collection with user profiles, preferences, visited places, and favorites

## External APIs
- **Google Gemini API**: Polished Response Generation
- **TasteDive API**: Entertainment recommendation engine for films, TV shows, music, video games, and books.
- **Algolia API**: Fast local search, Filtering places, Area-based results
- **Google Maps API**: Interactive maps, Places API, and Geocoding API

## Authentication & Security
- **Passlib**: Password hashing using PBKDF2-SHA256
- **Flask Sessions**: User session management
- **Environment Variables**: API keys and sensitive configuration

## Frontend
- **Jinja2 Templates**: Server-side HTML rendering
- **Font Awesome 6.4.0**: Icon library
- **Vanilla JavaScript**: Client-side interactivity
- **CSS3**: Custom styling with Seoul night theme (gradients, animations)

## Dependencies
```
Flask
requests
google-generativeai
Flask-PyMongo
passlib
```

## Common Commands

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Start development server
python app.py

# Access application
http://localhost:5000
```

### Database Setup
```bash
# Start MongoDB
mongod

# Connect and create database
mongosh
use taste_trails_korea
db.createCollection("users")
```

### Environment Configuration
Create `.env` file with:
- `GOOGLE_MAPS_API_KEY`
- `GEMINI_API_KEY` 
- `TASTE_DIVE_API_KEY`
- `ALGOLIA_API_KEY`
- `SECRET_KEY`
- `MONGO_URI`

## API Integration Patterns
- **Response Generation**: Gemini generates responses from the context(recommendation) received by kiro
- **Recommendations**: TasteDive API
- **Searching and Indexing**: Algolia API
- **Error Handling**: Graceful degradation with try/catch blocks