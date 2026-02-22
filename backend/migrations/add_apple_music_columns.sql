-- Migration: Add Apple Music columns to user_preferences table
-- Run this SQL against your PostgreSQL database

ALTER TABLE user_preferences 
ADD COLUMN IF NOT EXISTS apple_music_connected BOOLEAN DEFAULT FALSE;

ALTER TABLE user_preferences 
ADD COLUMN IF NOT EXISTS apple_music_subscription_type VARCHAR(50);

ALTER TABLE user_preferences 
ADD COLUMN IF NOT EXISTS apple_music_authorized_at TIMESTAMP;

ALTER TABLE user_preferences 
ADD COLUMN IF NOT EXISTS apple_music_storefront VARCHAR(10);
