# Feature Plan: "Get My News" Personalized News Feed

## Overview
Add a "Get My News" button that fetches fresh RSS articles, uses Perplexity to rank them based on user preferences, stores the top 5 for the user, and displays them in a popup modal.

## Workflow

```mermaid
flowchart TD
    A[User clicks "Get My News" button] --> B[Refresh RSS Feed]
    B --> C[Fetch user preferences]
    C --> D[Send articles + preferences to Perplexity]
    D --> E[Perplexity ranks/scores top 5 articles]
    E --> F[Store top 5 in database with timestamp]
    F --> G[Display top 5 in popup modal]
    G --> H[User can close modal]
```

## Components to Implement

### 1. Database Changes
- **New Model**: `UserPersonalizedNews` - stores personalized news selections per user
  - Fields: id, user_id, article_id, selected_at, rank_position

### 2. Backend API Changes
- **New Endpoint**: `POST /api/articles/personalized`
  - Refreshes RSS feed
  - Fetches user preferences
  - Calls Perplexity to rank articles
  - Stores top 5 for user
  - Returns top 5 articles

- **New Perplexity Method**: `rank_articles()` - takes articles + preferences, returns ranked top 5

### 3. Frontend Changes

#### HTML (index.html)
- Add "Get My News" button above article list (in header-actions or main-content)
- Add new modal for personalized news display:
  - Close button (X)
  - List of 5 news items with title, description, date
  - Each item links to original article

#### JavaScript (api.js)
- Add new API method: `getPersonalizedNews()`

#### JavaScript (app.js)
- Add event listener for "Get My News" button
- Handle response and open personalized news modal
- Render top 5 articles in modal

#### CSS (styles.css)
- Style the new "Get My News" button
- Style the personalized news modal
- Style the top 5 article list

## Data Models

### New Table: user_personalized_news
```python
class UserPersonalizedNews(Base):
    __tablename__ = "user_personalized_news"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"), nullable=False)
    article_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("article.id"), nullable=False)
    rank_position: Mapped[int] = mapped_column(nullable=False)  # 1-5
    selected_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
```

## Implementation Steps

### Step 1: Backend - Database Model
- Create new model `UserPersonalizedNews` in `backend/app/models/`

### Step 2: Backend - Perplexity Service
- Add `rank_articles()` method to `PerplexityClient`
- Takes list of articles + user preferences
- Returns top 5 ranked articles with scores

### Step 3: Backend - API Endpoint
- Create `POST /api/articles/personalized` endpoint in articles router
- Orchestrates: refresh → get prefs → perplexity → store → return

### Step 4: Frontend - Button
- Add "Get My News" button in index.html above article list

### Step 5: Frontend - Modal
- Add personalized news modal HTML in index.html

### Step 6: Frontend - API & App Logic
- Add API method in api.js
- Add button handler and modal display logic in app### Step 7.js

: Frontend - Styling
- Add CSS for button and modal in styles.css

## Acceptance Criteria

1. ✅ "Get My News" button visible above news list (only when authenticated)
2. ✅ Clicking button triggers RSS refresh
3. ✅ Perplexity processes articles with user preferences
4. ✅ Top 5 stored in database with user link and timestamp
5. ✅ Popup modal displays top 5 news items
6. ✅ Modal has working close button
7. ✅ Each news item shows title, description preview, date
8. ✅ User can click to read full article
