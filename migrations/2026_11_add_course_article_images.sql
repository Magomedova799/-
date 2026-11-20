-- DevSpace: add optional cover images to courses and articles.
-- Run once against the existing PostgreSQL database before starting the updated app.
ALTER TABLE courses ADD COLUMN IF NOT EXISTS image_url VARCHAR(500);
ALTER TABLE articles ADD COLUMN IF NOT EXISTS image_url VARCHAR(500);
