# Radio News Configuration Extension Plan

## Overview
Extend the radio station definition to add new fields for configuring radio news generation. Group all news-related fields under a "Radio News" section and improve the form layout consistency.

---

## Current Implementation Analysis

### Files to Modify:
1. **Backend Model**: `backend/app/models/station.py` - Add new database columns
2. **Backend Schema**: `backend/app/schemas/station.py` - Add new Pydantic fields
3. **Frontend HTML**: `frontend/index.html` - Update station modal form
4. **Frontend CSS**: `frontend/css/styles.css` - Improve layout and styling
5. **Frontend JS**: `frontend/js/app.js` - Handle new fields in form logic

### Current News Fields:
- `play_news` (boolean)
- `play_news_at_start` (boolean) 
- `news_interval_minutes` (integer: 15, 30, or 60)

### Current Issues to Fix:
- "Play News" and "At start of every" have inconsistent formatting
- No section grouping for news-related fields

---

## Implementation Todo List

### Phase 1: Backend Changes

#### 1.1 Update Station Model
**File**: `backend/app/models/station.py`

Add two new columns after `news_interval_minutes`:
- `news_top_stories_count`: Integer, range 1-10, default 3
- `news_max_length_minutes`: Integer, range 2-10, default 3

```python
# New fields to add
news_top_stories_count: Mapped[int] = mapped_column(Integer, default=3)
news_max_length_minutes: Mapped[int] = mapped_column(Integer, default=3)
```

#### 1.2 Update Station Schema
**File**: `backend/app/schemas/station.py`

Add new fields to all schemas:
- `StationCreate` - Add optional fields with defaults
- `StationUpdate` - Add optional fields
- `StationRead` - Add fields with defaults

---

### Phase 2: Frontend HTML Changes

#### 2.1 Restructure News Section
**File**: `frontend/index.html` (lines 504-530)

Replace the current news section with a grouped "Radio News" section:

```html
<!-- Radio News Section -->
<div class="form-group station-news-section">
    <h3 class="section-header">📰 Radio News</h3>
    
    <label class="checkbox-label play-news-label">
        <input type="checkbox" id="station-play-news" name="play_news">
        <span class="checkbox-icon">📰</span>
        <span class="checkbox-text">Play News</span>
    </label>
    
    <div class="news-options hidden" id="news-options">
        <!-- At Start Option -->
        <label class="checkbox-label sub-option">
            <input type="checkbox" id="station-news-at-start" name="play_news_at_start">
            <span>At start</span>
        </label>
        
        <!-- Interval Dropdown -->
        <div class="form-row">
            <label for="station-news-interval">Every</label>
            <select id="station-news-interval" name="news_interval_minutes" class="interval-select">
                <option value="">-</option>
                <option value="15">15</option>
                <option value="30">30</option>
                <option value="60">60</option>
            </select>
            <span class="interval-unit">min</span>
        </div>
        
        <!-- Number of Top Stories Dropdown -->
        <div class="form-row">
            <label for="station-news-top-stories">Top Stories</label>
            <select id="station-news-top-stories" name="news_top_stories_count" class="number-select">
                <option value="1">1</option>
                <option value="2">2</option>
                <option value="3" selected>3</option>
                <option value="4">4</option>
                <option value="5">5</option>
                <option value="6">6</option>
                <option value="7">7</option>
                <option value="8">8</option>
                <option value="9">9</option>
                <option value="10">10</option>
            </select>
            <span class="interval-unit">stories</span>
        </div>
        
        <!-- Max Length Dropdown -->
        <div class="form-row">
            <label for="station-news-max-length">Max Length</label>
            <select id="station-news-max-length" name="news_max_length_minutes" class="number-select">
                <option value="2">2</option>
                <option value="3" selected>3</option>
                <option value="4">4</option>
                <option value="5">5</option>
                <option value="6">6</option>
                <option value="7">7</option>
                <option value="8">8</option>
                <option value="9">9</option>
                <option value="10">10</option>
            </select>
            <span class="interval-unit">min</span>
        </div>
    </div>
</div>
```

---

### Phase 3: Frontend CSS Updates

#### 3.1 Add Section Header Styling
**File**: `frontend/css/styles.css`

Add styles for the new section header and improve form consistency:

```css
/* Radio News Section Header */
.station-news-section .section-header {
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 0.75rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border);
}

/* Consistent Form Rows */
.news-options .form-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-top: 0.75rem;
    flex-wrap: wrap;
}

.news-options .form-row label {
    font-size: 0.9rem;
    color: var(--text-secondary);
    min-width: 70px;
}

.news-options .number-select {
    width: 60px;
    padding: 0.35rem 0.5rem;
    font-size: 0.9rem;
    border-radius: var(--radius);
}

/* Ensure consistent spacing */
.news-options-grid {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}
```

---

### Phase 4: Frontend JavaScript Updates

#### 4.1 Update Reset Function
**File**: `frontend/js/app.js` (around line 226)

Add reset for new fields:

```javascript
// Reset news fields
document.getElementById('station-play-news').checked = false;
document.getElementById('station-news-at-start').checked = false;
document.getElementById('station-news-interval').value = '';
document.getElementById('station-news-top-stories').value = '3';  // Default
document.getElementById('station-news-max-length').value = '3';   // Default
document.getElementById('news-options').classList.add('hidden');
```

#### 4.2 Update Open Station Function
**File**: `frontend/js/app.js` (around line 250)

Add population of new fields:

```javascript
// Populate news fields
document.getElementById('station-play-news').checked = station.play_news || false;
document.getElementById('station-news-at-start').checked = station.play_news_at_start || false;
document.getElementById('station-news-interval').value = station.news_interval_minutes || '';
document.getElementById('station-news-top-stories').value = station.news_top_stories_count || 3;
document.getElementById('station-news-max-length').value = station.news_max_length_minutes || 3;
```

#### 4.3 Update Save Station Function
**File**: `frontend/js/app.js` (around line 360)

Add new fields to station data:

```javascript
const stationData = {
    name,
    description: description || null,
    example_songs,
    duration,
    image_url: imageUrl || null,
    play_news: document.getElementById('station-play-news').checked,
    play_news_at_start: document.getElementById('station-news-at-start').checked,
    news_interval_minutes: document.getElementById('station-news-interval').value 
        ? parseInt(document.getElementById('station-news-interval').value, 10) 
        : null,
    news_top_stories_count: parseInt(document.getElementById('station-news-top-stories').value, 10),
    news_max_length_minutes: parseInt(document.getElementById('station-news-max-length').value, 10)
};
```

#### 4.4 Update Checkbox Listener
**File**: `frontend/js/app.js` (around line 316)

Ensure new dropdowns are disabled when news is unchecked:

```javascript
setupNewsCheckboxListener() {
    const playNewsCheckbox = document.getElementById('station-play-news');
    const newsOptions = document.getElementById('news-options');
    const startCheckbox = document.getElementById('station-news-at-start');
    const intervalSelect = document.getElementById('station-news-interval');
    const topStoriesSelect = document.getElementById('station-news-top-stories');
    const maxLengthSelect = document.getElementById('station-news-max-length');
    
    playNewsCheckbox.onchange = null;
    
    playNewsCheckbox.addEventListener('change', (e) => {
        if (e.target.checked) {
            newsOptions.classList.remove('hidden');
            topStoriesSelect.disabled = false;
            maxLengthSelect.disabled = false;
        } else {
            newsOptions.classList.add('hidden');
            startCheckbox.checked = false;
            intervalSelect.value = '';
            topStoriesSelect.disabled = true;
            maxLengthSelect.disabled = true;
        }
    });
}
```

---

### Phase 5: Database Migration

#### 5.1 Create Migration Script
Create a new migration file to add the new columns to the database:

```sql
-- Migration: add_news_config_columns.sql
ALTER TABLE station 
ADD COLUMN news_top_stories_count INTEGER NOT NULL DEFAULT 3,
ADD COLUMN news_max_length_minutes INTEGER NOT NULL DEFAULT 3;
```

---

## UI Mockup (Text-based)

```
┌─────────────────────────────────────────┐
│ Create Radio Station                     │
├─────────────────────────────────────────┤
│ Name *                    [____________] │
│ Station Image            [Choose Image] │
│ Describe the music...    [____________] │
│ 3-5 song examples        [____________] │
│ Duration                 [1 hour    ▼] │
│                                          │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                          │
│ 📰 Radio News                            │
│                                          │
│ [✓] Play News                            │
│ ┌────────────────────────────────────┐   │
│ │ [ ] At start                       │   │
│ │ Every [  15 ▼] min                 │   │
│ │ Top Stories [  3 ▼] stories        │   │
│ │ Max Length  [  3 ▼] min            │   │
│ └────────────────────────────────────┘   │
│                                          │
│ [Cancel]                    [Save]       │
└─────────────────────────────────────────┘
```

---

## Summary of Changes

| Component | Changes |
|-----------|---------|
| Backend Model | Add `news_top_stories_count` and `news_max_length_minutes` columns |
| Backend Schema | Add fields to StationCreate, StationUpdate, StationRead |
| Frontend HTML | Restructure news section with header, add two dropdowns |
| Frontend CSS | Add section header styling, consistent form row styling |
| Frontend JS | Handle new fields in reset, populate, save, and checkbox listener |
| Database | Run migration to add new columns |

---

## Implementation Order

1. Create database migration script
2. Update backend model (`station.py`)
3. Update backend schema (`station.py`)
4. Update frontend HTML form
5. Update frontend CSS styling
6. Update frontend JavaScript logic
7. Test the complete flow

---

## Notes

- The new dropdowns will automatically be disabled when "Play News" is unchecked (same behavior as existing interval field)
- Default values: Top Stories = 3, Max Length = 3 minutes
- These new fields will be used by the news generator service in the future to customize the news output
