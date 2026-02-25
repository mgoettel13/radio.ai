-- Migration: Add News columns to station table
-- Run this SQL against your PostgreSQL database

ALTER TABLE station 
ADD COLUMN IF NOT EXISTS play_news BOOLEAN DEFAULT FALSE;

ALTER TABLE station 
ADD COLUMN IF NOT EXISTS play_news_at_start BOOLEAN DEFAULT FALSE;

ALTER TABLE station 
ADD COLUMN IF NOT EXISTS news_interval_minutes INTEGER;
