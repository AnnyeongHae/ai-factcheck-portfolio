"""
Trend RAG SDK - Official Python Client
Single Source of Truth (SSOT) client for 20,000+ Tech Trends & Factchecks Database
"""

import os
import sys
import json
import math
import re
from datetime import datetime, timezone
import urllib.request
import psycopg2
from typing import List, Dict, Any, Optional

try:
    from dotenv import load_dotenv
    # Load environment files
    load_dotenv('.env')
    load_dotenv('.env.local')
    # Also attempt loading from workspace root if running from child directories
    workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    load_dotenv(os.path.join(workspace_root, '.env'))
    load_dotenv(os.path.join(workspace_root, '.env.local'))
except ImportError:
    pass

VOYAGE_API_URL = "https://api.voyageai.com/v1/embeddings"
DEFAULT_VOYAGE_MODEL = "voyage-4-lite"
VOYAGE_DIM = 1024


class TrendItem:
    def __init__(self, item_id: int, title: str, platform: str, url: str, 
                 description: str, similarity: float, category: str, 
                 raw_payload: Dict[str, Any], peak_score: float = 0.0,
                 live_score: float = 0.0, created_at: Optional[datetime] = None):
        self.id = item_id
        self.title = title
        self.platform = platform
        self.url = url
        self.description = description
        self.similarity = round(float(similarity), 4)
        self.category = category
        self.raw_payload = raw_payload or {}
        self.peak_score = round(float(peak_score or 0.0), 2)
        self.live_score = round(float(live_score or 0.0), 2)
        self.created_at = created_at
        
        # Enriched fields
        enrich = self.raw_payload.get('ai_enrichment', {}) or {}
        self.title_ko = enrich.get('title_ko', '') or self.raw_payload.get('title_ko', '')
        self.hook_ko = enrich.get('hook_ko', '') or self.raw_payload.get('hook_ko', '')
        self.hook_en = enrich.get('hook_en', '') or self.raw_payload.get('hook_en', '')
        self.is_cross_spiking = bool(self.raw_payload.get('is_cross_spiking', False))
        
        # Parse stability signals (Stars, Forks, Comments, Points)
        vm = self.raw_payload.get('viral_metric', {}) or {}
        if isinstance(vm, str):
            try: vm = json.loads(vm)
            except: vm = {}
        elif not isinstance(vm, dict):
            vm = {}
            
        self.stars = int(vm.get('stars') or 0)
        self.forks = int(vm.get('forks') or 0)
        self.comments = int(vm.get('comments') or 0)
        self.points = int(vm.get('score') or vm.get('points') or 0)
        
        if description:
            if not self.stars:
                m_s = re.search(r'Stars:\s*(\d+)', description)
                if m_s: self.stars = int(m_s.group(1))
            if not self.forks:
                m_f = re.search(r'Forks:\s*(\d+)', description)
                if m_f: self.forks = int(m_f.group(1))
            if not self.points:
                m_p = re.search(r'(\d+)\s*points', description)
                if m_p: self.points = int(m_p.group(1))
            if not self.comments:
                m_c = re.search(r'(\d+)\s*comments', description)
                if m_c: self.comments = int(m_c.group(1))

        # Computed scoring attributes (populated by reranker)
        self.hvd_norm = 0.0
        self.stability_score = 0.0
        self.recency_score = 0.0
        self.hybrid_score = self.similarity

    def compute_composite_scores(self, mode: str = "balanced"):
        """Compute normalized H-V-D, Engineering Stability, and Recency scores."""
        # 1. H-V-D normalized (log10 scaling prevents 800-point gossip from crushing 50-point repos)
        hvd_base = math.log10(1.0 + max(0.0, self.peak_score)) / math.log10(1.0 + 300.0)
        self.hvd_norm = min(1.0, hvd_base + (0.15 if self.is_cross_spiking else 0.0))

        # 2. Engineering Stability & Maturity (Stars, Forks ratio, Comments depth)
        star_sig = min(1.0, math.log10(1.0 + self.stars) / math.log10(1.0 + 3000.0)) if self.stars > 0 else 0.0
        fork_sig = min(0.2, (self.forks / max(1, self.stars)) * 0.5) if self.stars > 50 else 0.0
        comm_sig = min(1.0, math.log10(1.0 + self.comments) / math.log10(1.0 + 150.0)) if self.comments > 0 else 0.0
        pts_sig = min(1.0, math.log10(1.0 + self.points) / math.log10(1.0 + 300.0)) if self.points > 0 else 0.0
        
        raw_stab = max(star_sig + fork_sig, (comm_sig * 0.6 + pts_sig * 0.4))
        if self.is_cross_spiking:
            raw_stab += 0.15
        self.stability_score = min(1.0, raw_stab)

        # 3. Recency (30-day half-life decay)
        if self.created_at:
            now = datetime.now(timezone.utc)
            dt = self.created_at if self.created_at.tzinfo else self.created_at.replace(tzinfo=timezone.utc)
            days_old = max(0.0, (now - dt).total_seconds() / 86400.0)
            self.recency_score = math.exp(- (math.log(2) / 30.0) * days_old)
        else:
            self.recency_score = 0.5

        # 4. Final Weighted Hybrid Score based on sort_mode
        if mode == "similarity":
            self.hybrid_score = self.similarity
        elif mode == "hvd":
            self.hybrid_score = (0.35 * self.similarity) + (0.55 * self.hvd_norm) + (0.10 * self.recency_score)
        elif mode == "stable_tech":
            # Prioritizes verified, high-stability engineering artifacts + recent relevance
            self.hybrid_score = (0.40 * self.similarity) + (0.20 * self.hvd_norm) + (0.25 * self.stability_score) + (0.15 * self.recency_score)
        else:  # "balanced" (Default)
            self.hybrid_score = (0.45 * self.similarity) + (0.25 * self.hvd_norm) + (0.15 * self.stability_score) + (0.15 * self.recency_score)
        
        self.hybrid_score = round(self.hybrid_score, 4)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "title_ko": self.title_ko,
            "hook_ko": self.hook_ko,
            "platform": self.platform,
            "category": self.category,
            "url": self.url,
            "similarity": self.similarity,
            "peak_score": self.peak_score,
            "live_score": self.live_score,
            "hybrid_score": self.hybrid_score,
            "stability_score": round(self.stability_score, 3),
            "hvd_norm": round(self.hvd_norm, 3),
            "recency_score": round(self.recency_score, 3),
            "is_cross_spiking": self.is_cross_spiking,
            "stars": self.stars,
            "comments": self.comments,
            "description": (self.description or "")[:250]
        }


class TrendRAGClient:
    """
    Python SDK Client to query the 20,000+ pgvector Tech Trends database.
    """
    def __init__(self, database_url: Optional[str] = None, voyage_api_key: Optional[str] = None):
        self.db_url = database_url or os.environ.get("DATABASE_URL")
        self.voyage_api_key = voyage_api_key or os.environ.get("VOYAGE_API_KEY")
        self._embedding_cache: Dict[str, List[float]] = {}
        
        if not self.db_url:
            raise ValueError("DATABASE_URL is not set. Please provide it or configure .env")
        if not self.voyage_api_key:
            raise ValueError("VOYAGE_API_KEY is not set. Please provide it or configure .env")

    def _get_connection(self):
        return psycopg2.connect(self.db_url)

    def get_embedding(self, text: str, input_type: str = "query") -> List[float]:
        """Fetch 1024-dim embedding from Voyage AI with in-memory caching."""
        cache_key = f"{input_type}:{text.strip()}"
        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]

        req = urllib.request.Request(
            VOYAGE_API_URL,
            data=json.dumps({
                "input": [text],
                "model": DEFAULT_VOYAGE_MODEL,
                "input_type": input_type
            }).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.voyage_api_key}",
                "Content-Type": "application/json"
            }
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            vec = data["data"][0]["embedding"]
            self._embedding_cache[cache_key] = vec
            return vec

    def search(self, query: str, top_k: int = 5, platform: Optional[str] = None, 
               category: Optional[str] = None, min_similarity: float = 0.35,
               sort_mode: str = "balanced") -> List[TrendItem]:
        """
        2-Stage Hybrid Vector Search & Reranking over raw_trends_inbox.
        
        sort_mode:
          - 'balanced' (default): 0.45*Sim + 0.25*HVD + 0.15*Stability + 0.15*Recency
          - 'stable_tech': Prioritizes high-stability, mature tech (Stars/Forks/Comments/Cross-Spike)
          - 'hvd': Prioritizes H-V-D viral spike intensity
          - 'similarity': Pure cosine similarity ranking
        """
        q_vec = self.get_embedding(query, input_type="query")
        conn = self._get_connection()
        cur = conn.cursor()

        conditions = ["embedding IS NOT NULL"]
        params: List[Any] = [q_vec, q_vec]

        if platform:
            conditions.append("source_platform ILIKE %s")
            params.append(f"%{platform}%")
        if category:
            conditions.append("category_primary = %s")
            params.append(category)

        where_clause = " AND ".join(conditions)
        # Stage 1: Recall broad candidate pool (at least 50 or top_k*6)
        candidate_limit = max(50, top_k * 6) if sort_mode != "similarity" else top_k
        params.append(candidate_limit)

        sql = f"""
            SELECT id, title, source_platform, source_url, description, 
                   1 - (embedding <=> %s::vector) AS similarity,
                   category_primary, raw_payload, peak_spike_score, live_spike_score, created_at
            FROM raw_trends_inbox
            WHERE {where_clause}
            ORDER BY embedding <=> %s::vector ASC
            LIMIT %s;
        """
        cur.execute(sql, tuple(params))
        rows = cur.fetchall()

        candidates = []
        for r in rows:
            sim = float(r[5])
            if sim >= min_similarity:
                item = TrendItem(
                    item_id=r[0],
                    title=r[1],
                    platform=r[2],
                    url=r[3],
                    description=r[4],
                    similarity=sim,
                    category=r[6],
                    raw_payload=r[7] if isinstance(r[7], dict) else {},
                    peak_score=float(r[8] or 0.0),
                    live_score=float(r[9] or 0.0),
                    created_at=r[10]
                )
                item.compute_composite_scores(mode=sort_mode)
                candidates.append(item)

        cur.close()
        conn.close()

        # Stage 2: Rerank candidates by hybrid_score
        if sort_mode != "similarity":
            candidates.sort(key=lambda x: x.hybrid_score, reverse=True)

        return candidates[:top_k]

    def compare_technologies(self, tech_a: str, tech_b: str, top_k: int = 4) -> Dict[str, Any]:
        """
        A/B comparative analysis between two technologies/frameworks using database trends and feedback.
        """
        res_a = self.search(f"{tech_a} architecture performance benchmark ecosystem", top_k=top_k)
        res_b = self.search(f"{tech_b} architecture performance benchmark ecosystem", top_k=top_k)

        return {
            "tech_a": {
                "name": tech_a,
                "matches": [item.to_dict() for item in res_a],
                "avg_similarity": round(sum(i.similarity for i in res_a) / max(1, len(res_a)), 4),
                "peak_spike_highest": max([i.peak_score for i in res_a] or [0.0])
            },
            "tech_b": {
                "name": tech_b,
                "matches": [item.to_dict() for item in res_b],
                "avg_similarity": round(sum(i.similarity for i in res_b) / max(1, len(res_b)), 4),
                "peak_spike_highest": max([i.peak_score for i in res_b] or [0.0])
            },
            "summary_recommendation": f"Data retrieved for comparative A/B evaluation between '{tech_a}' ({len(res_a)} citations) and '{tech_b}' ({len(res_b)} citations)."
        }

    def get_deep_dive(self, keyword_or_repo: str) -> Dict[str, Any]:
        """Get deep-dive details on a specific project or topic."""
        conn = self._get_connection()
        cur = conn.cursor()

        # Hybrid search: exact title match or high semantic match
        sql = """
            SELECT id, title, source_platform, source_url, description, category_primary, 
                   raw_payload, peak_spike_score, viral_score, created_at
            FROM raw_trends_inbox
            WHERE title ILIKE %s OR description ILIKE %s
            ORDER BY COALESCE(peak_spike_score, viral_score, 0) DESC
            LIMIT 5;
        """
        pattern = f"%{keyword_or_repo}%"
        cur.execute(sql, (pattern, pattern))
        rows = cur.fetchall()

        items = []
        for r in rows:
            payload = r[6] if isinstance(r[6], dict) else {}
            enrich = payload.get('ai_enrichment', {}) or {}
            items.append({
                "id": r[0],
                "title": r[1],
                "title_ko": enrich.get('title_ko', ''),
                "hook_ko": enrich.get('hook_ko', ''),
                "platform": r[2],
                "url": r[3],
                "category": r[5],
                "peak_spike_score": float(r[7] or 0.0),
                "created_at": str(r[9])
            })

        cur.close()
        conn.close()
        return {
            "query": keyword_or_repo,
            "matched_records_count": len(items),
            "records": items
        }

    def get_daily_viral_spikes(self, target_date: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve cross-viral spike rankings for a given date or recent active window."""
        conn = self._get_connection()
        cur = conn.cursor()

        if target_date:
            sql = """
                SELECT r.id, r.title, r.source_platform, r.source_url, r.live_spike_score, 
                       r.peak_spike_score, r.raw_payload
                FROM raw_trends_inbox r
                WHERE r.harvested_date = %s OR r.created_at::date = %s::date
                ORDER BY r.peak_spike_score DESC
                LIMIT %s;
            """
            cur.execute(sql, (target_date, target_date, limit))
        else:
            sql = """
                SELECT r.id, r.title, r.source_platform, r.source_url, r.live_spike_score, 
                       r.peak_spike_score, r.raw_payload
                FROM raw_trends_inbox r
                WHERE r.created_at >= NOW() - INTERVAL '7 days'
                ORDER BY r.peak_spike_score DESC NULLS LAST
                LIMIT %s;
            """
            cur.execute(sql, (limit,))

        rows = cur.fetchall()
        results = []
        for r in rows:
            payload = r[6] if isinstance(r[6], dict) else {}
            enrich = payload.get('ai_enrichment', {}) or {}
            results.append({
                "id": r[0],
                "title": r[1],
                "title_ko": enrich.get('title_ko', ''),
                "hook_ko": enrich.get('hook_ko', ''),
                "platform": r[2],
                "url": r[3],
                "live_score": float(r[4] or 0.0),
                "peak_score": float(r[5] or 0.0)
            })

        cur.close()
        conn.close()
        return results

    def query_factchecks(self, topic: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Query curated verified factcheck reports."""
        conn = self._get_connection()
        cur = conn.cursor()

        sql = """
            SELECT id, case_id, title, category, verdict, the_hook, engineering_takeaways, sources
            FROM verified_factchecks
            WHERE title ILIKE %s OR the_hook ILIKE %s OR engineering_takeaways ILIKE %s
            ORDER BY updated_at DESC
            LIMIT %s;
        """
        pattern = f"%{topic}%"
        cur.execute(sql, (pattern, pattern, pattern, limit))
        rows = cur.fetchall()

        results = []
        for r in rows:
            results.append({
                "id": r[0],
                "case_id": r[1],
                "title": r[2],
                "category": r[3],
                "verdict": r[4],
                "the_hook": r[5],
                "engineering_takeaways": r[6],
                "sources": r[7]
            })

        cur.close()
        conn.close()
        return results

    def verify_claim_4pillar(
        self,
        claim_or_topic: str,
        repo_name: str = "",
        academic_query: str = "",
        community_query: str = ""
    ) -> Dict[str, Any]:
        """
        Track B: On-Demand 4-Pillar Technical Fact-Check & Verification.
        Integrates:
          1. Academic (ArXiv API)
          2. Developer Community (Hacker News Algolia API)
          3. Remote Code Inspection (GitHub REST API - Zero Clone)
          4. News & Internal RAG Cross-Check (Internal 24k+ DB)
          5. Token-Diet Semantic Cards
        """
        from .factcheck import FactcheckEngine
        engine = FactcheckEngine()
        data = engine.verify_claim(
            claim_or_topic=claim_or_topic,
            repo_name=repo_name,
            academic_query=academic_query,
            community_query=community_query,
            rag_client=self
        )
        data["report_markdown"] = engine.format_report(data)
        return data
