-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create main HS codes table
CREATE TABLE hs_codes (
    id SERIAL PRIMARY KEY,
    section VARCHAR(10),
    hscode VARCHAR(20) UNIQUE NOT NULL,
    description_en TEXT NOT NULL,
    description_id TEXT,
    parent_code VARCHAR(20),
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
CREATE INDEX idx_hs_section ON hs_codes (section);
CREATE INDEX idx_hs_parent ON hs_codes (parent_code);  
CREATE INDEX idx_hs_level ON hs_codes (level);
CREATE INDEX idx_hs_category ON hs_codes (category);
CREATE INDEX idx_hs_code ON hs_codes (hscode);

-- Vector indexes (crucial for performance)
CREATE INDEX idx_hs_embedding_en ON hs_codes 
    USING ivfflat (embedding_en vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_hs_embedding_id ON hs_codes 
    USING ivfflat (embedding_id vector_cosine_ops) WITH (lists = 100);

-- Full-text search indexes
CREATE INDEX idx_hs_search_en ON hs_codes USING GIN (search_vector_en);
CREATE INDEX idx_hs_search_id ON hs_codes USING GIN (search_vector_id);

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
