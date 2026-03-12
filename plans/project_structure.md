# Project Structure

```
npr-news-summarizer/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app entry point
│   │   ├── config.py               # Settings & environment variables
│   │   ├── database.py             # SQLAlchemy setup
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py             # User model (fastapi-users)
│   │   │   ├── article.py          # Article model
│   │   │   ├── summary.py          # Summary model
│   │   │   └── user_article.py     # User-Article join model
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── article.py          # Article Pydantic schemas
│   │   │   ├── summary.py          # Summary schemas
│   │   │   └── tts.py              # TTS request/response schemas
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── articles.py         # Article endpoints
│   │   │   └── tts.py              # TTS endpoints
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── rss_fetcher.py      # NPR RSS fetching
│   │   │   ├── perplexity.py       # Perplexity AI client
│   │   │   └── speechify.py        # Speechify TTS client
│   │   └── admin/
│   │       ├── __init__.py
│   │       └── admin.py            # SQLAdmin configuration
│   ├── requirements.txt
│   ├── .env.example
│   └── alembic/                    # Database migrations
│       ├── versions/
│       └── env.py
├── frontend/
│   ├── index.html                  # Main HTML page
│   ├── manifest.json               # PWA manifest
│   ├── sw.js                       # Service worker
│   ├── css/
│   │   └── styles.css              # App styles
│   └── js/
│       ├── app.js                  # Main app logic
│       ├── api.js                  # API client
│       ├── auth.js                 # Authentication
│       └── ui.js                   # UI components
├── docker-compose.yml              # PostgreSQL setup
└── README.md                       # Setup instructions
```

## File Purposes

### Backend

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app factory, includes startup/shutdown events |
| `config.py` | Pydantic Settings with env var validation |
| `database.py` | SQLAlchemy engine, session, base model |
| `models/*.py` | SQLAlchemy ORM models |
| `schemas/*.py` | Pydantic request/response models |
| `routers/*.py` | FastAPI route handlers |
| `services/*.py` | Business logic & external API clients |
| `admin/admin.py` | SQLAdmin views |

### Frontend

| File | Purpose |
|------|---------|
| `index.html` | Single-page app shell |
| `manifest.json` | PWA install metadata |
| `sw.js` | Service worker for offline/cache |
| `css/styles.css` | Responsive styling |
| `js/app.js` | App initialization & routing |
| `js/api.js` | Fetch wrapper with auth |
| `js/auth.js` | Login/register/logout logic |
| `js/ui.js` | DOM manipulation & components |

## Environment Variables (.env)

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/npr_news

# # Security
# SECRET_KEY=your-secret-key-here

# # APIs
# PERPLEXITY_API_KEY=your-perplexity-api-key-here
# SPEECHIFY_API_KEY=your-speechify-api-key-here

# App
APP_PORT=8000
RSS_REFRESH_MINUTES=10
MAX_ARTICLES=20
```

## Dependencies

### Backend (requirements.txt)
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy[asyncio]==2.0.25
asyncpg==0.29.0
fastapi-users[sqlalchemy]==12.1.0
sqladmin==0.16.0
httpx==0.26.0
feedparser==6.0.11
python-dotenv==1.0.0
pydantic-settings==2.1.0
alembic==1.13.1
```

### Frontend
- No build tools - vanilla JS
- CDN: None required (pure fetch API)
