# Plan: Modify News Feed Behavior

## Summary of Changes

### 1. Disable Auto-Refresh (Backend)
- Remove the `periodic_rss_refresh()` background task from [`backend/app/main.py`](backend/app/main.py:49)
- Remove the startup code that starts this task ([line 98-100](backend/app/main.py:98))
- Remove related imports (`asyncio`, `RSSFetcher`)

### 2. Don't Load News on Main Screen Load (Frontend)
- In [`frontend/js/app.js`](frontend/js/app.js:40): Modify `loadArticles()` to NOT be called automatically
- In [`frontend/js/auth.js`](frontend/js/auth.js:172): Remove calls to `app.loadArticles()` on login
- Show empty state or welcome message instead of loading articles

### 3. Display Personalized Results on Main Screen (Frontend)
- Modify "Get My News" button to display results in the main article list (not popup)
- Keep the click-to-view modal functionality (with summarize/voice options)
- Remove the popup modal we created earlier
- The button should refresh the main list with personalized articles

### 4. Remove Unnecessary Code/Database Tables
- Delete [`backend/app/models/user_personalized_news.py`](backend/app/models/user_personalized_news.py) (table no longer needed)
- Remove from [`backend/app/models/__init__.py`](backend/app/models/__init__.py)
- Remove relationships from [`backend/app/models/user.py`](backend/app/models/user.py) and [`backend/app/models/article.py`](backend/app/models/article.py)
- Remove the `/api/articles/personalized` endpoint OR modify it to not store in DB (just return ranked articles)

## Implementation Steps

| Step | Task |
|------|------|
| 1 | Remove `periodic_rss_refresh` function and startup code from main.py |
| 2 | Remove `loadArticles()` auto-calls from auth.js |
| 3 | Remove popup modal HTML from index.html |
| 4 | Modify app.js: change "Get My News" to update main article list |
| 5 | Keep modal functionality for article details (summarize/voice) |
| 6 | Delete user_personalized_news.py model file |
| 7 | Clean up model imports and relationships |
| 8 | Optionally simplify/remove the personalized endpoint |

## UI Behavior After Changes
1. User logs in → sees empty state with "Get My News" button
2. User clicks "Get My News" → RSS refreshes, Perplexity ranks, articles show in main list
3. User clicks article → opens modal with summarize/voice options (existing functionality)
4. No automatic loading or refreshing of articles
