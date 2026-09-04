-- ==============================================================================
-- Neon Serverless Postgres Enterprise Schema for AI Fact-Check Intelligence Hub
-- Architecture: Two-Tier Hybrid Knowledge Graph & Audit Engine (2026 SOTA)
-- Core Focus: SUSTAINABILITY, IMMUTABILITY, AUDIT TRAIL, SCALABILITY
-- ==============================================================================

-- 0. Extensions & Helper Functions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- ==============================================================================
-- TIER 1: RAW HARVESTING & STAGING TABLES (불변 수집 레이어)
-- ==============================================================================

-- 1. Raw Trends Inbox
CREATE TABLE IF NOT EXISTS raw_trends_inbox (
    id BIGSERIAL PRIMARY KEY,
    inbox_id VARCHAR(255) UNIQUE NOT NULL,
    source_fingerprint VARCHAR(64) UNIQUE NOT NULL, -- SHA-256 (Normalized URL/Repo identifier)
    source_platform VARCHAR(100) NOT NULL,          -- 'Hugging Face Spaces', 'GitHub Official', 'ArXiv', 'Hacker News', 'Reddit'
    source_url TEXT NOT NULL,
    title TEXT NOT NULL,
    item_type VARCHAR(50) DEFAULT 'repo',           -- 'repo', 'space', 'paper', 'sns'
    description TEXT,
    viral_metric VARCHAR(100),                      -- e.g. '★ 420 Stars', '❤️ 1,628 Likes', '350 HN pts'
    viral_score NUMERIC(10,2) DEFAULT 0.0,          -- Calculated weighted ranking score
    matched_user_domains JSONB DEFAULT '[]'::jsonb, -- User persona alignment categories
    raw_payload JSONB DEFAULT '{}'::jsonb,          -- Original untouched JSON payload
    triage_status VARCHAR(50) DEFAULT 'PENDING_REVIEW', -- 'PENDING_REVIEW', 'PROMOTED', 'REJECTED', 'ARCHIVED'
    is_classified BOOLEAN DEFAULT FALSE,            -- AI 분류 및 다국어 번역 완료 여부 (Boolean)
    is_deep_analyzed BOOLEAN DEFAULT FALSE,         -- 심층 팩트체크 검증 완료 여부 (Boolean)
    harvested_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Trend Cross Posts (동일 기술의 여러 플랫폼 동시 바이럴 추적)
CREATE TABLE IF NOT EXISTS trend_cross_posts (
    id BIGSERIAL PRIMARY KEY,
    inbox_id VARCHAR(255) REFERENCES raw_trends_inbox(inbox_id) ON DELETE CASCADE,
    platform VARCHAR(100) NOT NULL,
    external_url TEXT NOT NULL,
    spotted_metric VARCHAR(100),
    captured_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================================================
-- TIER 2: VERIFIED FACT-CHECK KNOWLEDGE CORE (정본 팩트체크 레이어)
-- ==============================================================================

-- 3. Verified Factchecks (Main Entity)
CREATE TABLE IF NOT EXISTS verified_factchecks (
    id BIGSERIAL PRIMARY KEY,
    case_id VARCHAR(255) UNIQUE NOT NULL,
    origin_inbox_id VARCHAR(255) REFERENCES raw_trends_inbox(inbox_id) ON DELETE SET NULL,
    
    title TEXT NOT NULL,
    category VARCHAR(100) NOT NULL,
    
    -- Curation & Intent
    discovery_mode VARCHAR(50) DEFAULT 'USER_CURATED', -- 'USER_CURATED', 'AUTO_HARVESTED'
    curator_name VARCHAR(100) DEFAULT 'Anyong Cheong',
    personal_motivation TEXT,                         -- 내가 왜 궁금증/필요성을 갖고 직접 발굴했는가?
    target_workflow TEXT,                             -- E.F.M 마케팅, 사내 RAG, 스마트스토어 등
    
    -- Clustering
    cluster_id VARCHAR(100) NOT NULL,                 -- 'cluster_web_scraping', 'cluster_doc_parsing', etc.
    cluster_name TEXT NOT NULL,
    
    -- Overall Verdict
    verdict VARCHAR(50) NOT NULL,                     -- 'VERIFIED_TRUE', 'HALF_TRUE_CONTEXT_REQUIRED', 'MISLEADING_GAMED', 'CONFIRMED_FALSE'
    confidence_score NUMERIC(5,2) DEFAULT 95.0,
    
    -- Hands-on Empirical Proof (Zero-Hallucination)
    hands_on_status VARCHAR(50) DEFAULT 'PENDING_RESEARCH', -- 'ACTIVE_DEVELOPED', 'EVALUATED_HALTED', 'PENDING_RESEARCH'
    hands_on_pipeline TEXT,
    hands_on_env TEXT,
    hands_on_metrics TEXT,
    hands_on_details TEXT,
    
    -- Storytelling Core
    the_hook TEXT,
    marketing_hype_anatomy TEXT,
    engineering_takeaways TEXT,
    future_applications TEXT,
    
    -- Sources & References (Array of {tier, type, name, url})
    sources JSONB DEFAULT '[]'::jsonb,
    
    -- Revision & Versioning
    version INT DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Atomic Claims & Proofs (1:N 명제별 분해 검증)
CREATE TABLE IF NOT EXISTS factcheck_atomic_claims (
    id BIGSERIAL PRIMARY KEY,
    case_id VARCHAR(255) REFERENCES verified_factchecks(case_id) ON DELETE CASCADE,
    claim_number INT NOT NULL,
    claim_title VARCHAR(255) NOT NULL,
    claim_text TEXT NOT NULL,
    claim_verdict VARCHAR(50) NOT NULL, -- 'VERIFIED_TRUE', 'HALF_TRUE', 'MISLEADING', 'FALSE'
    verification_evidence TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Technology Alternatives Matrix (1:N 유사 기술/대체재 비교)
CREATE TABLE IF NOT EXISTS factcheck_alternatives (
    id BIGSERIAL PRIMARY KEY,
    case_id VARCHAR(255) REFERENCES verified_factchecks(case_id) ON DELETE CASCADE,
    tool_name VARCHAR(100) NOT NULL,
    tech_stack VARCHAR(255),
    pros TEXT NOT NULL,
    cons TEXT NOT NULL,
    best_for TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. Community Sentiment Signals & Security Alerts (1:N 여론/보안 신호 - last30days)
CREATE TABLE IF NOT EXISTS factcheck_community_signals (
    id BIGSERIAL PRIMARY KEY,
    case_id VARCHAR(255) REFERENCES verified_factchecks(case_id) ON DELETE CASCADE,
    platform VARCHAR(100) NOT NULL,        -- 'Reddit', 'Hacker News', 'GitHub Issues', 'X', 'YouTube'
    author_type VARCHAR(100),              -- 'Inference Engineer', 'Security Auditor', 'Practitioner'
    quote TEXT NOT NULL,                   -- 날것의 사용자 피드백
    source_url TEXT NOT NULL,
    signal_type VARCHAR(50) DEFAULT 'REVIEW', -- 'REVIEW', 'CRITICAL_BUG', 'SECURITY_ALERT', 'BENCHMARK_DOUBT'
    captured_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. Unit Economics & Cost Audit (1:1 파이프라인 원가 분석)
CREATE TABLE IF NOT EXISTS factcheck_unit_economics (
    id BIGSERIAL PRIMARY KEY,
    case_id VARCHAR(255) UNIQUE REFERENCES verified_factchecks(case_id) ON DELETE CASCADE,
    unit_cost_per_run NUMERIC(10,4),       -- 1편당 / 1회 실행 원가 ($)
    monthly_estimated_cost NUMERIC(10,2),  -- 월 30회/100회 배치 시 원가 ($)
    reject_ratio NUMERIC(4,2) DEFAULT 1.0, -- 실패 재시도 승수 (예: 1.5x)
    component_breakdown JSONB DEFAULT '{}'::jsonb, -- { "llm": 0.002, "tts": 0.015, "video": 18.0 }
    commercial_viability VARCHAR(50),      -- 'HIGHLY_VIABLE', 'MARGINAL', 'UNVIABLE_HIGH_COST'
    analysis_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 8. Audit Logs & Version History (수정 및 버전 추적)
CREATE TABLE IF NOT EXISTS factcheck_audit_logs (
    id BIGSERIAL PRIMARY KEY,
    case_id VARCHAR(255) NOT NULL,
    version INT NOT NULL,
    changed_by VARCHAR(100) DEFAULT 'Antigravity AI Agent',
    change_reason TEXT,
    previous_snapshot JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================================================
-- TIER 3: SYSTEM MONITORING & TELEMETRY TABLES (시스템 감사 레이어)
-- ==============================================================================

-- 9. Harvester Job Runs
CREATE TABLE IF NOT EXISTS harvest_runs (
    id BIGSERIAL PRIMARY KEY,
    run_id VARCHAR(255) UNIQUE NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    finished_at TIMESTAMP WITH TIME ZONE NOT NULL,
    total_fetched INT DEFAULT 0,
    new_saved INT DEFAULT 0,
    duplicates_skipped INT DEFAULT 0,
    errors_count INT DEFAULT 0,
    status VARCHAR(50) DEFAULT 'SUCCESS'
);

-- 10. Source-level Telemetry Metrics
CREATE TABLE IF NOT EXISTS harvest_source_metrics (
    id BIGSERIAL PRIMARY KEY,
    run_id VARCHAR(255) REFERENCES harvest_runs(run_id) ON DELETE CASCADE,
    source_name VARCHAR(100) NOT NULL,
    items_count INT DEFAULT 0,
    latency_seconds NUMERIC(6,3) DEFAULT 0.0,
    http_status VARCHAR(50) DEFAULT 'SUCCESS',
    error_message TEXT,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================================================
-- INDEXES FOR HIGH PERFORMANCE & TIME-SERIES SCALING
-- ==============================================================================

CREATE INDEX IF NOT EXISTS idx_inbox_triage ON raw_trends_inbox(triage_status);
CREATE INDEX IF NOT EXISTS idx_inbox_date ON raw_trends_inbox(harvested_date DESC);
CREATE INDEX IF NOT EXISTS idx_inbox_platform ON raw_trends_inbox(source_platform);
CREATE INDEX IF NOT EXISTS idx_inbox_domains_gin ON raw_trends_inbox USING GIN (matched_user_domains);

CREATE INDEX IF NOT EXISTS idx_factchecks_category ON verified_factchecks(category);
CREATE INDEX IF NOT EXISTS idx_factchecks_mode ON verified_factchecks(discovery_mode);
CREATE INDEX IF NOT EXISTS idx_factchecks_cluster ON verified_factchecks(cluster_id);
CREATE INDEX IF NOT EXISTS idx_factchecks_verdict ON verified_factchecks(verdict);
CREATE INDEX IF NOT EXISTS idx_factchecks_hands_on ON verified_factchecks(hands_on_status);
CREATE INDEX IF NOT EXISTS idx_factchecks_sources_gin ON verified_factchecks USING GIN (sources);

CREATE INDEX IF NOT EXISTS idx_claims_case ON factcheck_atomic_claims(case_id);
CREATE INDEX IF NOT EXISTS idx_alternatives_case ON factcheck_alternatives(case_id);
CREATE INDEX IF NOT EXISTS idx_signals_case ON factcheck_community_signals(case_id);

-- Trigger Binding
DROP TRIGGER IF EXISTS trg_raw_trends_inbox_updated_at ON raw_trends_inbox;
CREATE TRIGGER trg_raw_trends_inbox_updated_at BEFORE UPDATE ON raw_trends_inbox FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_verified_factchecks_updated_at ON verified_factchecks;
CREATE TRIGGER trg_verified_factchecks_updated_at BEFORE UPDATE ON verified_factchecks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
