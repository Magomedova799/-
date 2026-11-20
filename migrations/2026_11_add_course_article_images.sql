-- DevSpace: add optional cover images to courses and articles.
-- Run once against the existing PostgreSQL database before starting the updated app.
ALTER TABLE courses ADD COLUMN IF NOT EXISTS image_url VARCHAR(500);
ALTER TABLE articles ADD COLUMN IF NOT EXISTS image_url VARCHAR(500);
 
-- Enable comments on polls as well as courses, articles and projects.
ALTER TABLE comments ADD COLUMN IF NOT EXISTS poll_id INTEGER REFERENCES polls(id);
ALTER TABLE comments DROP CONSTRAINT IF EXISTS comments_check;
ALTER TABLE comments ADD CONSTRAINT comments_one_target_check CHECK (
    ((course_id IS NOT NULL)::int +
     (article_id IS NOT NULL)::int +
     (project_id IS NOT NULL)::int +
     (poll_id IS NOT NULL)::int) = 1
);
