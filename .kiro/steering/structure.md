# Project Structure

## Directory Organization

```
Taste & Trails Korea/
├── app.py                 # Main Flask application with all routes
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
├── quickguide.txt        # Qloo API reference guide
├── templates/            # Jinja2 HTML templates
│   ├── index.html        # Main page (maps + chatbot)
│   ├── login.html        # User authentication
│   ├── signup.html       # User registration
│   ├── profile.html      # User preferences management
│   ├── profile_edit.html # Profile editing form
│   ├── base.html         # Base for common header and footer.
│   ├── chat.html
│   ├── explore.html
│   ├── food.html
│   └── settings.html     # User dashboard with recommendations
└── utils/                # API integration modules
    ├── __init__.py       # Package initialization (empty)
    ├── gemini_api.py     # Google Gemini API integration
    ├── kiro_agent.py        # Kiro reasoning with product.md
    ├── tastedive_api.py    # Cultural similarity & discovery
    ├── algolia_api.py      # Fast place search
```

## File Responsibilities

### Core Application
- **app.py**: Single-file Flask application containing all routes, database operations, and business logic
- **requirements.txt**: Minimal dependency list for the application

### Templates Directory
- **Consistent naming**: All templates use lowercase with underscores
- **Template inheritance**: Base layout patterns shared across pages
- **Embedded CSS**: Styling included directly in templates for simplicity
- **JavaScript integration**: Client-side code embedded in templates

### Utils Package
- **API abstraction**: Each external API has its own module
- **Error handling**: Graceful degradation when APIs are unavailable
- **Environment configuration**: API keys loaded from environment variables
- **Debug logging**: Print statements for API request/response debugging

## Architectural Patterns

### Route Organization
- Authentication routes: `/login`, `/signup`, `/logout`
- User management: `/profile`, `/profile_edit`, `/settings`
- Core functionality: `/` (main page with chatbot and maps)
- AJAX endpoints: `/add_visited`, `/remove_visited`, `/add_favorite`, `/remove_favorite`

### Data Flow
1. User input → Flask route
2. User intent understanding → Kiro (context-driven)
3. Cultural recommendations → Kiro + TasteDive
4. Local search → Algolia (MongoDB indexed data)
5. Response generation → Gemini API
6. HTML rendering → Jinja2 template

### Configuration Management
- Environment variables for all sensitive data
- Default values provided for development
- API keys stored in `.env` file (not committed)
- MongoDB URI configurable for different environments

## Naming Conventions
- **Files**: lowercase with underscores (`profile_edit.html`)
- **Functions**: snake_case (`get_current_user()`)
- **Variables**: snake_case (`entity_type`, `user_question`)
- **Constants**: UPPER_CASE (`GOOGLE_MAPS_API_KEY`)
- **Database fields**: snake_case (`visited_places`, `food_restrictions`)