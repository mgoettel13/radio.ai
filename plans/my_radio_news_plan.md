# Feature Plan: "My Radio News"

## Overview

Add a new "My Radio News" feature that creates a personalized radio news broadcast from the user's top 5 news stories. The feature will be triggered through a new button on the main screen.

## User Flow

```mermaid
flowchart TD
    A[User clicks "My Radio News" button] --> B[Reuse "Get My News" logic - retrieve top 5 personalized news]
    B --> C[Ask Perplexity to create radio news script with announcer style]
    C --> D[Display modal with radio script]
    D --> E[User clicks "Play" button]
    E --> F[TTS plays the radio script]
```

## Reuse Analysis

The following existing functionality will be **reused**:

1. **Personalized News Logic** ([`articles.py:321`](backend/app/routers/articles.py:321))
   - The existing `POST /api/articles/personalized` endpoint already:
     - Refreshes RSS feed
     - Fetches user preferences
     - Uses Perplexity to rank articles
     - Stores top 5 in database
     - Returns the personalized news

2. **Perplexity Client** ([`perplexity.py`](backend/app/services/perplexity.py))
   - Existing `rank_articles()` method for ranking
   - Will add new `create_radio_script()` method

3. **TTS Service** ([`tts.py`](backend/app/routers/tts.py) + [`speechifyService.py`](backend/app/services/speechifyService.py))
   - Existing `POST /api/tts/speak` endpoint for text-to-speech

4. **Frontend UI Components**
   - Modal infrastructure (already exists)
   - Toast notifications
   - API client

---

## Implementation Steps

### Step 1: Backend - Add Perplexity Radio Script Method

**File:** [`backend/app/services/perplexity.py`](backend/app/services/perplexity.py)

Add new method `create_radio_script()` to the `PerplexityClient` class:

```python
async def create_radio_script(
    self,
    articles: List[Dict[str, Any]]
) -> tuple[str, str, Optional[int]]:
    """
    Create a radio news script from top 5 articles.
    
    Returns:
        Tuple of (radio_script, model_used, tokens_used)
    """
```

**System Prompt:** "You are a professional radio news announcer. Create a 60-90 second news broadcast script reading the top 5 news stories. Start with a friendly greeting and intro, then present each story in a clear, engaging manner. End with a smooth closing."

### Step 2: Backend - Add New Schema

**File:** [`backend/app/schemas/article.py`](backend/app/schemas/article.py)

Add new response schema:

```python
class RadioNewsResponse(BaseModel):
    """Response schema for radio news."""
    articles: list[ArticleRead]
    radio_script: str
    selected_at: datetime
    total_selected: int
```

### Step 3: Backend - Add New API Endpoint

**File:** [`backend/app/routers/articles.py`](backend/app/routers/articles.py)

Add new endpoint `POST /api/articles/radio-news`:

```python
@router.post("/radio-news", response_model=RadioNewsResponse)
async def get_radio_news(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get personalized radio news broadcast.
    
    1. Gets top 5 personalized news (reuses /personalized logic)
    2. Creates radio script using Perplexity
    3. Returns script + articles
    
    Requires authentication.
    """
```

**Refactoring Opportunity:** Extract the personalized news logic from `/personalized` into a shared helper function to avoid code duplication.

### Step 4: Frontend - Add API Method

**File:** [`frontend/js/api.js`](frontend/js/api.js)

Add new method:

```javascript
async getRadioNews() {
    return this.request('/api/articles/radio-news', { method: 'POST' });
}
```

### Step 5: Frontend - Add Button

**File:** [`frontend/index.html`](frontend/index.html)

Add new button in the header-actions section, next to the existing "Get My News" button:

```html
<button id="my-radio-news-btn" class="btn btn-primary hidden">
    📻 My Radio News
</button>
```

### Step 6: Frontend - Add Radio News Modal

**File:** [`frontend/index.html`](frontend/index.html)

Add new modal for displaying the radio script:

```html
<div id="radio-news-modal" class="modal hidden">
    <div class="modal-content radio-news-modal-content">
        <div class="modal-header">
            <h2>📻 My Radio News</h2>
            <button id="close-radio-modal" class="btn btn-icon">✕</button>
        </div>
        <div class="modal-body">
            <div id="radio-script-content" class="radio-script-content"></div>
            <div class="radio-news-actions">
                <button id="play-radio-btn" class="btn btn-primary">
                    ▶️ Play Radio News
                </button>
            </div>
            <div id="radio-audio-section" class="audio-section hidden">
                <audio id="radio-audio-player" controls></audio>
            </div>
        </div>
    </div>
</div>
```

### Step 7: Frontend - Add App Logic

**File:** [`frontend/js/app.js`](frontend/js/app.js)

Add event listener and handler for the new button:

```javascript
document.getElementById('my-radio-news-btn').addEventListener('click', () => this.getRadioNews());

async getRadioNews() {
    const btn = document.getElementById('my-radio-news-btn');
    btn.disabled = true;
    btn.textContent = '⏳ Generating...';

    try {
        const data = await api.getRadioNews();
        this.displayRadioNewsModal(data);
        showToast('Radio news ready!', 'success');
    } catch (error) {
        showToast('Failed to generate radio news: ' + error.message, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = '📻 My Radio News';
    }
}

displayRadioNewsModal(data) {
    // Populate and open modal
    document.getElementById('radio-script-content').textContent = data.radio_script;
    // Show articles list from data.articles
    this.radioNewsModal.open();
}
```

### Step 8: Frontend - Add CSS Styles

**File:** [`frontend/css/styles.css`](frontend/css/styles.css)

Add styles for:
- New "My Radio News" button
- Radio news modal
- Radio script content display

---

## Acceptance Criteria

1. ✅ "My Radio News" button visible on main screen (only when authenticated)
2. ✅ Clicking button triggers personalized news retrieval (reuses existing logic)
3. ✅ Perplexity generates a radio announcer-style script from top 5 news
4. ✅ Modal displays the radio script text
5. ✅ "Play" button in modal plays the script via TTS
6. ✅ Modal has working close button
7. ✅ Code is refactored to reuse existing personalized news logic

## Code Changes Summary

| File | Changes |
|------|---------|
| `backend/app/services/perplexity.py` | Add `create_radio_script()` method |
| `backend/app/schemas/article.py` | Add `RadioNewsResponse` schema |
| `backend/app/routers/articles.py` | Add `/radio-news` endpoint, refactor to reuse code |
| `frontend/js/api.js` | Add `getRadioNews()` API method |
| `frontend/index.html` | Add button and modal HTML |
| `frontend/js/app.js` | Add button handler and modal display logic |
| `frontend/css/styles.css` | Add styles for new UI elements |
