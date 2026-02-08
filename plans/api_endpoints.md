# API Endpoints

## Authentication (fastapi-users)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/register` | Register new user | No |
| POST | `/auth/login` | Login, get JWT token | No |
| POST | `/auth/logout` | Logout | Yes |
| POST | `/auth/forgot-password` | Request password reset | No |
| POST | `/auth/reset-password` | Reset password | No |
| GET | `/auth/me` | Get current user | Yes |
| PATCH | `/auth/me` | Update current user | Yes |

## Articles

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/articles` | List articles (latest 20) | Yes |
| POST | `/api/articles/refresh` | Force RSS refresh | Yes |
| GET | `/api/articles/{id}` | Get single article | Yes |
| GET | `/api/articles/{id}/summary` | Get/cached summary | Yes |
| POST | `/api/articles/{id}/summary` | Generate new summary | Yes |
| POST | `/api/articles/{id}/read` | Mark as read | Yes |
| POST | `/api/articles/{id}/favorite` | Toggle favorite | Yes |

## TTS (Text-to-Speech)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/tts/speak` | Generate TTS audio | Yes |
| GET | `/api/tts/voices` | List available voices | Yes |

## Admin (SQLAdmin)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/admin/` | SQLAdmin dashboard | Superuser |

## Request/Response Examples

### GET /api/articles
```json
{
  "items": [
    {
      "id": "uuid",
      "guid": "npr-guid-123",
      "title": "Article Title",
      "link": "https://npr.org/...",
      "description": "Article excerpt...",
      "published_at": "2026-01-31T12:00:00Z",
      "author": "Jane Doe",
      "category": "Politics",
      "has_summary": true,
      "is_read": false,
      "is_favorite": false
    }
  ],
  "total": 20,
  "last_updated": "2026-01-31T16:50:00Z"
}
```

### POST /api/articles/refresh
```json
// Response
{
  "new_articles": 5,
  "total_articles": 20,
  "fetched_at": "2026-01-31T16:50:00Z"
}
```

### GET /api/articles/{id}/summary
```json
{
  "id": "uuid",
  "article_id": "uuid",
  "content": "Summary text...",
  "model_used": "sonar-pro",
  "tokens_used": 150,
  "created_at": "2026-01-31T16:50:00Z"
}
```

### POST /api/tts/speak
```json
// Request
{
  "text": "Summary text to speak...",
  "voice_id": "matthew"
}

// Response
{
  "audio_url": "https://speechify.com/audio/...",
  "duration_seconds": 45
}
```

## Background Tasks

- **RSS Auto-Refresh**: Runs every 10 minutes via `asyncio` background task
- **Cleanup**: Daily cleanup of articles older than 100 most recent

## Error Responses

```json
{
  "detail": "Error message",
  "code": "ERROR_CODE"
}
```

Common codes:
- `ARTICLE_NOT_FOUND`: Article doesn't exist
- `SUMMARY_FAILED`: Perplexity API error
- `TTS_FAILED`: Speechify API error
- `RSS_FETCH_FAILED`: NPR feed unavailable
