# Taste & Trails Korea 🌸

A vibrant South Korean travel assistant application that combines AI-powered recommendations with interactive maps and cultural insights.

## ✨ Features

### 🗺️ Interactive Maps
- **Location Mapping**: View exact locations of Korean attractions
- **Nearby Amenities**: Discover restaurants, hotels, and transport options
- **Real-time Data**: Powered by Google Maps Places API
- **Distance Calculations**: See how far amenities are from attractions

### 🤖 AI-Powered Chatbot
- **Gemini Integration**: Advanced language model for cultural insights
- **TasteDive API**: Cultural similarity matching and entertainment recommendations
- **Algolia Search**: Fast, intelligent search for Korean places and experiences
- **Smart Entity Detection**: Automatically identifies places, foods, and cultural elements
- **Conversational Responses**: Natural, helpful answers about Korean culture

### 👤 User Management
- **Personalized Profiles**: Save preferences, visited places, and favorites
- **MongoDB Integration**: Secure user data storage
- **Authentication System**: Login/signup with password hashing

### 🎨 Beautiful UI
- **Seoul Night Theme**: Bright, cheerful design inspired by Korean nightlife
- **Smooth Animations**: Engaging user experience with CSS animations
- **Responsive Design**: Works perfectly on desktop and mobile
- **Interactive Cards**: Hover effects and dynamic content

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- MongoDB
- Google Maps API Key
- Gemini API Key
- TasteDive API Key
- Algolia API Key & Application ID

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd "Taste & Trails Korea"
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up MongoDB**
   ```bash
   # Start MongoDB service
   mongod
   
   # In another terminal, connect to MongoDB
   mongosh
   use taste_trails_korea
   db.createCollection("users")
   ```

4. **Configure API Keys**
   
   Create a `.env` file in the project root:
   ```env
   GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
   GEMINI_API_KEY=your_gemini_api_key_here
   TASTE_DIVE_API_KEY=your_tastedive_api_key_here
   ALGOLIA_API_KEY=your_algolia_api_key_here
   ALGOLIA_APP_ID=your_algolia_app_id_here
   SECRET_KEY=your_secret_key_here
   MONGO_URI=mongodb://localhost:27017/taste_trails_korea
   ```

5. **Get Google Maps API Key**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable these APIs:
     - Maps JavaScript API
     - Places API
     - Geocoding API
   - Create credentials (API Key)
   - Add the key to your `.env` file

6. **Get TasteDive API Key**
   - Visit [TasteDive API](https://tastedive.com/read/api)
   - Sign up for a free account
   - Request an API key from your account dashboard
   - Add the key to your `.env` file as `TASTE_DIVE_API_KEY`

7. **Get Algolia API Keys**
   - Sign up at [Algolia](https://www.algolia.com/)
   - Create a new application
   - Go to API Keys section in your dashboard
   - Copy your Application ID and Search-Only API Key
   - Add both to your `.env` file

8. **Run the application**
   ```bash
   python app.py
   ```

9. **Access the application**
   - Open your browser and go to `http://localhost:5000`
   - You'll be redirected to the login page
   - Create an account and start exploring!

## 🗺️ Interactive Maps Setup

The interactive maps feature requires a Google Maps API key with the following APIs enabled:

### Required APIs:
1. **Maps JavaScript API** - For displaying the map
2. **Places API** - For finding nearby restaurants, hotels, and transport
3. **Geocoding API** - For address/coordinate conversion

### Features Included:
- **Location Markers**: Exact coordinates for Korean attractions
- **Nearby Search**: Find restaurants, hotels, and transit stations within 1km
- **Distance Display**: Shows distance from attraction to each amenity
- **Responsive Design**: Works on desktop and mobile devices

### Current Locations:
- **Gyeongbokgung Palace** (37.5796, 126.9770)
- **Namsan Seoul Tower** (37.5512, 126.9882)
- **Myeongdong Street Food** (37.5636, 126.9834)

## 🤖 AI Integration

### Gemini API
- **Entity Extraction**: Identifies main topics from user questions
- **Conversational Replies**: Generates natural responses from cultural data
- **Fallback Responses**: Provides helpful answers when external APIs aren't available

### TasteDive API
- **Cultural Similarity Matching**: Finds related cultural entities and experiences
- **Entertainment Recommendations**: Discovers similar music, movies, books, and shows
- **Korean Cultural Context**: Specialized matching for Korean entertainment and culture

### Algolia Search
- **Fast Search**: Lightning-fast search across Korean places and experiences
- **Intelligent Filtering**: Advanced filtering by location, type, and preferences
- **Real-time Results**: Instant search results as you type

## 📁 Project Structure

```
Taste & Trails Korea/
├── app.py                 # Main Flask application
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── run_tests.py         # Test runner script
├── .gitignore           # Git ignore rules
├── logs/                # Application logs
│   ├── taste_trails_korea.log
│   └── README.md
├── tests/               # Test files
│   ├── integration_test.py
│   ├── test_services.py
│   ├── test_ui_fixes.py
│   └── README.md
├── templates/           # HTML templates
│   ├── index.html      # Main page with maps and chatbot
│   ├── login.html      # Login page
│   ├── signup.html     # Registration page
│   ├── profile.html    # User preferences
│   └── profile_edit.html # Profile editing
└── utils/              # Utility modules
    ├── gemini_api.py   # Gemini API integration
    ├── tastedive_api.py # TasteDive API integration
    ├── algolia_api.py  # Algolia search integration
    ├── googlemaps_api.py # Google Maps integration
    ├── local_guide_system.py # AI orchestration
    ├── service_manager.py # Service coordination
    ├── user_profile_manager.py # User management
    └── config.py       # Configuration management
```

## 🎨 UI Features

### Seoul Night Theme
- **Color Palette**: Vibrant gradients inspired by Korean nightlife
- **Animations**: Smooth transitions and hover effects
- **Typography**: Modern, readable fonts
- **Icons**: Font Awesome integration for consistent iconography

### Interactive Elements
- **Hover Effects**: Cards lift and glow on hover
- **Modal Windows**: Full-screen chatbot and map interfaces
- **Side Panel**: Collapsible settings menu
- **Responsive Grid**: Adaptive layout for different screen sizes

## 🔧 Configuration

### Environment Variables
- `GOOGLE_MAPS_API_KEY`: Your Google Maps API key
- `GEMINI_API_KEY`: Your Google Gemini API key
- `TASTE_DIVE_API_KEY`: Your TasteDive API key
- `ALGOLIA_API_KEY`: Your Algolia search API key
- `ALGOLIA_APP_ID`: Your Algolia application ID
- `SECRET_KEY`: Flask secret key for sessions
- `MONGO_URI`: MongoDB connection string

### Customization
- **Colors**: Modify CSS variables in templates for different themes
- **Locations**: Add new Korean attractions in `index.html`
- **API Limits**: Adjust search radius and result limits in JavaScript

## 🧪 Testing

The project includes comprehensive tests organized in the `tests/` directory:

### Running Tests

**Individual Tests:**
```bash
python tests/test_services.py
python tests/test_ui_fixes.py
python tests/integration_test.py
```

**All Tests:**
```bash
python run_tests.py
```

**With Environment Setup:**
```bash
PYTHONPATH=. python tests/test_services.py
```

### Test Categories
- **Service Tests**: API integration and service functionality
- **UI Tests**: Frontend functionality and user interface
- **Integration Tests**: End-to-end system testing
- **Security Tests**: Authentication and data protection

## 🚀 Deployment

### Local Development
```bash
python app.py
```

### Production Deployment
1. Set up a production MongoDB instance
2. Configure environment variables
3. Use a production WSGI server (Gunicorn, uWSGI)
4. Set up reverse proxy (Nginx)
5. Configure SSL certificates

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- **Google Maps API** for interactive mapping
- **Google Gemini** for AI-powered responses
- **TasteDive API** for cultural similarity matching and recommendations
- **Algolia** for fast, intelligent search capabilities
- **Font Awesome** for beautiful icons
- **Korean Culture and Information Service** for inspiration

---

**Enjoy exploring the vibrant culture of South Korea! 🇰🇷** 