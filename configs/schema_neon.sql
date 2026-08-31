-- Neon Postgres Database Schema for AI Fact-Check Intelligence Hub (2026 SOTA)

-- 1. Raw Trends Inbox (수집 원본 대기 큐)
CREATE TABLE IF NOT EXISTS raw_trends_inbox (
    id SERIAL PRIMARY KEY,
    inbox_id VARCHAR(255) UNIQUE NOT NULL,
    harvested_date DATE NOT NULL,
    source_platform VARCHAR(100) NOT NULL,
    source_url TEXT NOT NULL,
    title TEXT NOT NULL,
    item_type VARCHAR(50) DEFAULT 'repo',
    description TEXT,
    viral_metric VARCHAR(100),
    matched_user_domains JSONB DEFAULT '[]'::jsonb,
    raw_payload JSONB DEFAULT '{}'::jsonb,
    status VARCHAR(50) DEFAULT 'PENDING_REVIEW', -- 'PENDING_REVIEW', 'PROMOTED', 'REJECTED'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Verified Fact-Check Portfolio (AI 심층 분석 및 판정 완료 데이터)
CREATE TABLE IF NOT EXISTS verified_factchecks (
    id SERIAL PRIMARY KEY,
    case_id VARCHAR(255) UNIQUE NOT NULL,
    title TEXT NOT NULL,
    category VARCHAR(100) NOT NULL,
    discovery_mode VARCHAR(50) DEFAULT 'USER_CURATED', -- 'USER_CURATED', 'AUTO_HARVESTED'
    curator VARCHAR(100) DEFAULT 'Anyong Cheong',
    personal_motivation TEXT,
    target_workflow TEXT,
    
    -- Clustering & Alternatives
    cluster_id VARCHAR(100),
    cluster_name TEXT,
    alternatives_matrix JSONB DEFAULT '[]'::jsonb,
    
    -- Verdict & Audit
    verdict VARCHAR(50) NOT NULL, -- 'VERIFIED_TRUE', 'HALF_TRUE_CONTEXT_REQUIRED', 'MISLEADING_GAMED', 'CONFIRMED_FALSE'
    confidence_score NUMERIC(5,2) DEFAULT 95.0,
    sources JSONB DEFAULT '[]'::jsonb,
    community_reactions JSONB DEFAULT '[]'::jsonb,
    
    -- Hands-on Empirical Proof
    hands_on_status VARCHAR(50) DEFAULT 'PENDING_RESEARCH', -- 'ACTIVE_DEVELOPED', 'EVALUATED_HALTED', 'PENDING_RESEARCH'
    hands_on_pipeline TEXT,
    hands_on_env TEXT,
    hands_on_metrics TEXT,
    hands_on_details TEXT,
    
    -- Storytelling
    the_hook TEXT,
    marketing_hype_anatomy TEXT,
    engineering_takeaways TEXT,
    future_applications TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Harvester Health & Error Monitoring Logs
CREATE TABLE IF NOT EXISTS harvest_health_logs (
    id SERIAL PRIMARY KEY,
    run_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    harvest_date DATE NOT NULL,
    total_fetched INT DEFAULT 0,
    new_saved INT DEFAULT 0,
    duplicates_skipped INT DEFAULT 0,
    errors_count INT DEFAULT 0,
    sources_detail JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_inbox_status ON raw_trends_inbox(status);
CREATE INDEX IF NOT EXISTS idx_inbox_harvested_date ON raw_trends_inbox(harvested_date);
CREATE INDEX IF NOT EXISTS idx_factchecks_case_id ON verified_factchecks(case_id);
CREATE INDEX IF NOT EXISTS idx_factchecks_cluster ON verified_factchecks(cluster_id);
