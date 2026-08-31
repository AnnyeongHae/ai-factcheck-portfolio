#!/usr/bin/env python3
"""
FastAPI Enterprise REST API Server for AI Fact-Check Intelligence Hub (2026 SOTA)
Provides authenticated and public endpoints to read and trigger fact-checks on Neon Postgres DB.
"""

import os
import sys
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Security, Depends, status, Query
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from tools.db_bridge import get_db_connection

app = FastAPI(
    title="AI & Tech Fact-Check Intelligence API",
    description="Enterprise REST API to access verified AI fact-checks, technology alternatives matrix, and trigger automated analysis.",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security & API Key
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
BEARER_AUTH = HTTPBearer(auto_error=False)

def verify_api_key(
    api_key_header: Optional[str] = Security(API_KEY_HEADER),
    bearer_token: Optional[HTTPAuthorizationCredentials] = Security(BEARER_AUTH)
):
    master_key = os.environ.get("FACTCHECK_API_KEY") or "factcheck-secret-key-2026"
    
    token = None
    if api_key_header:
        token = api_key_header
    elif bearer_token:
        token = bearer_token.credentials

    if not token or token != master_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key. Provide via 'X-API-Key' header or 'Authorization: Bearer <KEY>'."
        )
    return token

# Pydantic Models
class TriggerRequest(BaseModel):
    inbox_id: str
    target_cluster: Optional[str] = None
    notes: Optional[str] = None

@app.get("/api/v1/health", tags=["System"])
def health_check():
    """System health check and connection status."""
    conn = get_db_connection()
    db_status = "CONNECTED" if conn else "LOCAL_FALLBACK"
    if conn: conn.close()
    return {
        "status": "HEALTHY",
        "database": db_status,
        "api_version": "1.0.0",
        "engine": "Neon Serverless Postgres"
    }

@app.get("/api/v1/factchecks", tags=["Fact-Checks (Public)"])
def list_factchecks(
    discovery_mode: Optional[str] = Query(None, description="Filter by 'USER_CURATED' or 'AUTO_HARVESTED'"),
    verdict: Optional[str] = Query(None, description="Filter by verdict e.g. 'VERIFIED_TRUE'"),
    limit: int = Query(20, ge=1, le=100)
):
    """Retrieve all verified fact-check portfolio projects."""
    conn = get_db_connection()
    if not conn:
        # Fallback to local data.json
        data_path = os.path.join(base_dir, "docs", "data.json")
        if os.path.exists(data_path):
            import json
            with open(data_path, "r", encoding="utf-8") as fp:
                d = json.load(fp)
                return {"total": len(d.get("cases", [])), "items": d.get("cases", [])[:limit]}
        return {"total": 0, "items": []}

    try:
        with conn.cursor() as cur:
            query = "SELECT case_id, title, category, discovery_mode, curator_name, verdict, confidence_score, hands_on_status, created_at FROM verified_factchecks WHERE 1=1"
            params = []
            if discovery_mode:
                query += " AND discovery_mode = %s"
                params.append(discovery_mode)
            if verdict:
                query += " AND verdict = %s"
                params.append(verdict)
            query += " ORDER BY id DESC LIMIT %s;"
            params.append(limit)
            
            cur.execute(query, tuple(params))
            rows = cur.fetchall()
            items = []
            for r in rows:
                items.append({
                    "case_id": r[0],
                    "title": r[1],
                    "category": r[2],
                    "discovery_mode": r[3],
                    "curator": r[4],
                    "verdict": r[5],
                    "confidence_score": float(r[6]) if r[6] else 95.0,
                    "hands_on_status": r[7],
                    "created_at": r[8].isoformat() if r[8] else None
                })
            return {"total": len(items), "items": items}
    finally:
        conn.close()

@app.get("/api/v1/factchecks/{case_id}", tags=["Fact-Checks (Public)"])
def get_factcheck_detail(case_id: str):
    """Retrieve detailed fact-check report, alternatives matrix, and community sentiment."""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection unavailable")

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT case_id, title, category, discovery_mode, curator_name, personal_motivation, target_workflow,
                       cluster_id, cluster_name, verdict, confidence_score, hands_on_status, hands_on_pipeline,
                       the_hook, marketing_hype_anatomy, engineering_takeaways, future_applications, sources
                FROM verified_factchecks WHERE case_id = %s;
            """, (case_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail=f"Factcheck '{case_id}' not found.")

            # Fetch Alternatives
            cur.execute("SELECT tool_name, tech_stack, pros, cons, best_for FROM factcheck_alternatives WHERE case_id = %s;", (case_id,))
            alts = [{"name": a[0], "tech_stack": a[1], "pros": a[2], "cons": a[3], "best_for": a[4]} for a in cur.fetchall()]

            # Fetch Signals
            cur.execute("SELECT platform, author_type, quote, source_url, signal_type FROM factcheck_community_signals WHERE case_id = %s;", (case_id,))
            signals = [{"platform": s[0], "author_type": s[1], "quote": s[2], "source_url": s[3], "signal_type": s[4]} for s in cur.fetchall()]

            return {
                "case_id": row[0],
                "title": row[1],
                "category": row[2],
                "curation": {
                    "discovery_mode": row[3],
                    "curator": row[4],
                    "personal_motivation": row[5],
                    "target_workflow": row[6]
                },
                "clustering": {
                    "cluster_id": row[7],
                    "cluster_name": row[8],
                    "alternatives": alts
                },
                "verdict": row[9],
                "confidence_score": float(row[10]) if row[10] else 95.0,
                "hands_on_status": row[11],
                "pipeline_url": row[12],
                "story": {
                    "the_hook": row[13],
                    "marketing_hype_anatomy": row[14],
                    "engineering_takeaways": row[15],
                    "future_applications": row[16]
                },
                "community_signals": signals,
                "sources": row[17]
            }
    finally:
        conn.close()

@app.get("/api/v1/inbox", tags=["Inbox (Public)"])
def list_inbox_candidates(limit: int = Query(50, ge=1, le=200)):
    """Retrieve pending trend candidates from the raw inbox queue."""
    conn = get_db_connection()
    if not conn:
        return {"total": 0, "items": []}

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT inbox_id, title, source_platform, source_url, viral_metric, matched_user_domains, triage_status, harvested_date
                FROM raw_trends_inbox
                ORDER BY id DESC LIMIT %s;
            """, (limit,))
            rows = cur.fetchall()
            items = []
            for r in rows:
                items.append({
                    "inbox_id": r[0],
                    "title": r[1],
                    "source_platform": r[2],
                    "source_url": r[3],
                    "viral_metric": r[4],
                    "matched_user_domains": r[5],
                    "triage_status": r[6],
                    "harvested_date": r[7].isoformat() if r[7] else None
                })
            return {"total": len(items), "items": items}
    finally:
        conn.close()

@app.post("/api/v1/factcheck/trigger", tags=["Admin Operations (Protected)"])
def trigger_factcheck_analysis(payload: TriggerRequest, api_key: str = Depends(verify_api_key)):
    """Protected Endpoint: Authenticate with API Key to trigger immediate fact-check synthesis on an inbox item."""
    from tools.triage import promote_candidate
    success = promote_candidate(payload.inbox_id)
    if not success:
        raise HTTPException(status_code=400, detail=f"Failed to promote '{payload.inbox_id}'. Check if inbox_id exists.")
    
    # Rebuild dashboard
    from tools.build_dashboard import build_dashboard
    build_dashboard()

    return {
        "status": "SUCCESS",
        "message": f"Successfully triggered and promoted '{payload.inbox_id}' to verified portfolio!",
        "inbox_id": payload.inbox_id
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
