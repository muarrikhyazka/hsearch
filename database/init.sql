-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Drop existing table if exists to ensure clean structure
DROP TABLE IF EXISTS hs_codes CASCADE;
DROP TABLE IF EXISTS search_analytics CASCADE;
DROP TABLE IF EXISTS user_sessions CASCADE;

-- Create main HS codes table with updated structure
CREATE TABLE hs_codes (
    id SERIAL PRIMARY KEY,
    no INTEGER,
    hs_code VARCHAR(20) UNIQUE NOT NULL,
    description_en TEXT NOT NULL,
    description_id TEXT,
    section VARCHAR(10),
    chapter VARCHAR(10),
    heading VARCHAR(10),
    subheading VARCHAR(20),
    chapter_desc TEXT,
    heading_desc TEXT,
    subheading_desc TEXT,
    section_name TEXT,
    chapter_desc_id TEXT,
    heading_desc_id TEXT,
    subheading_desc_id TEXT,
    section_name_id TEXT,
    level INTEGER NOT NULL,
    
    -- Auto-categorization
    category VARCHAR(50),
    keywords_en TEXT[],
    keywords_id TEXT[],
    
    -- Vector embeddings
    embedding_en VECTOR(384),
    embedding_id VECTOR(384),
    embedding_combined VECTOR(384),
    
    -- Full-text search
    search_vector_en TSVECTOR,
    search_vector_id TSVECTOR,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for optimal performance
CREATE INDEX idx_hs_no ON hs_codes (no);
CREATE INDEX idx_hs_section ON hs_codes (section);
CREATE INDEX idx_hs_chapter ON hs_codes (chapter);
CREATE INDEX idx_hs_heading ON hs_codes (heading);
CREATE INDEX idx_hs_subheading ON hs_codes (subheading);
CREATE INDEX idx_hs_level ON hs_codes (level);
CREATE INDEX idx_hs_category ON hs_codes (category);
CREATE INDEX idx_hs_code ON hs_codes (hs_code);

-- Note: Vector indexes and full-text search indexes are created by import_data.py 
-- after data is loaded for better performance

-- Create user sessions table for analytics
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create search analytics table
CREATE TABLE search_analytics (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100),
    query TEXT,
    category VARCHAR(50),
    result_count INTEGER,
    response_time_ms INTEGER,
    ai_enabled BOOLEAN,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for analytics
CREATE INDEX idx_analytics_session ON search_analytics (session_id);
CREATE INDEX idx_analytics_created ON search_analytics (created_at);
CREATE INDEX idx_analytics_query ON search_analytics (query);

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO hsearch_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO hsearch_user;
