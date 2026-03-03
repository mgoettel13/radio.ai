-- Migration: add_news_config_columns
-- Adds new columns for radio news configuration: top stories count and max length

ALTER TABLE station 
ADD COLUMN IF NOT EXISTS news_top_stories_count INTEGER NOT NULL DEFAULT 3,
ADD COLUMN IF NOT EXISTS news_max_length_minutes INTEGER NOT NULL DEFAULT 3;

-- Update existing records to have default values if they don't have news enabled
UPDATE station 
SET news_top_stories_count = 3, 
    news_max_length_minutes = 3
WHERE news_top_stories_count IS NULL 
   OR news_max_length_minutes IS NULL;
