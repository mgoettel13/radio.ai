# NPR News Summarizer

A Progressive Web App (PWA) that fetches NPR news articles, summarizes them using Perplexity AI, and reads them aloud using Speechify TTS.

## Features

- 📰 **NPR News Feed**: Fetches the latest 20 articles from NPR's RSS feed
- ✨ **AI Summarization**: Summarizes articles using Perplexity AI (cached to save tokens)
- 🔊 **Text-to-Speech**: Reads summaries aloud using Speechify TTS
- 👤 **User Management**: Registration, login, and read history tracking via fastapi-users
- 📱 **PWA**: Installable on mobile devices with offline support
- 🗄️ **Database**: PostgreSQL with SQLAlchemy ORM and SQLAdmin for management

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   PWA       │────▶│  FastAPI     │────▶│   PostgreSQL    │
│  Frontend   │◀────│   Backend    │◀────│   Database      │
└─────────────┘     └──────────────┘     └─────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  NPR RSS      │   │  Perplexity   │   │   Speechify   │
│  Feed         │   │     AI        │   │     TTS       │
└───────────────┘   └───────────────┘   └───────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL (or use SQLite for local development)
- API keys for Perplexity and Speechify

### Installation

1. **Clone and setup environment:**
```bash
# Create virtual environment
cd backend
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

2. **Configure environment variables:**
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. **Run the application:**
```bash
# Using uvicorn directly
uvicorn app.main:app --reload --port 8000

# Or with the run script
python -m uvicorn app.main:app --reload --port 8000
```

4. **Access the app:**
- PWA: http://localhost:8000
- API Docs: http://localhost:8000/docs
- SQLAdmin: http://localhost:8000/admin

### Using Docker (PostgreSQL)

```bash
# Start PostgreSQL
docker-compose up -d

# Update .env to use PostgreSQL
DATABASE_URL=postgresql+asyncpg://npr_user:npr_password@localhost:5432/npr_news
```

## API Endpoints

### Authentication (fastapi-users)
- `POST /auth/register` - Register new user
- `POST /auth/jwt/login` - Login (returns JWT)
- `POST /auth/jwt/logout` - Logout
- `GET /auth/me` - Get current user

### Articles
- `GET /api/articles` - List articles (latest 20)
- `POST /api/articles/refresh` - Force RSS refresh
- `GET /api/articles/{id}` - Get single article
- `GET /api/articles/{id}/summary` - Get/generate summary
- `POST /api/articles/{id}/read` - Mark as read
- `POST /api/articles/{id}/favorite` - Toggle favorite

### TTS
- `POST /api/tts/speak` - Convert text to speech
- `GET /api/tts/voices` - List available voices

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | SQLite |
| `SECRET_KEY` | JWT secret key | required |
| `PERPLEXITY_API_KEY` | Perplexity API key | required |
| `SPEECHIFY_API_KEY` | Speechify API key | required |
| `RSS_REFRESH_MINUTES` | Auto-refresh interval | 10 |
| `MAX_ARTICLES` | Max articles to display | 20 |

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI entry point
│   │   ├── config.py         # Settings
│   │   ├── database.py       # SQLAlchemy setup
│   │   ├── models/           # Database models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── routers/          # API endpoints
│   │   ├── services/         # Business logic
│   │   └── admin/            # SQLAdmin config
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── index.html            # PWA shell
│   ├── manifest.json         # PWA manifest
│   ├── sw.js                 # Service worker
│   ├── css/styles.css
│   └── js/
│       ├── app.js            # Main app
│       ├── api.js            # API client
│       ├── auth.js           # Auth manager
│       └── ui.js             # UI utilities
├── docker-compose.yml
└── README.md
```

## Development

### Adding fastapi-users Authentication

The backend is prepared for fastapi-users integration. To fully enable it:

1. Add to `main.py`:
```python
from fastapi_users import FastAPIUsers
from app.database import User, get_user_db

fastapi_users = FastAPIUsers(
    get_user_db,
    [authentication_backend],
    User,
    UserCreate,
    UserUpdate,
    UserDB,
)

app.include_router(fastapi_users.get_auth_router(jwt_authentication), prefix="/auth/jwt")
app.include_router(fastapi_users.get_register_router(UserRead, UserCreate), prefix="/auth")
```

### Background Tasks

The app includes automatic RSS refresh every 10 minutes via asyncio background tasks.

## License

MIT
