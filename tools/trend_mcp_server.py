#!/usr/bin/env python3
"""
Trend & Tech Intelligence FastMCP Server
Exposes 20,000+ Tech Trends & Factchecks Database over Model Context Protocol (MCP).

Can be used in any project via Claude Desktop, Cursor, Antigravity, or other MCP clients.
"""

import os
import sys
import json
from typing import Optional

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from mcp.server.fastmcp import FastMCP
from trend_rag_sdk.client import TrendRAGClient

SERVER_VERSION = "2.1.0"

# Initialize FastMCP Server
mcp = FastMCP(
    name="TrendIntelligenceServer",
    instructions=f"v{SERVER_VERSION} | Comprehensive real-time Tech Trends, Open-Source Repositories, Research Papers, and Factchecks Intelligence Server backed by 24,200+ pgvector items with 2-Stage Hybrid Reranking and Track B 4-Pillar Fact-Checking Engine."
)

# Initialize Core Client
client: Optional[TrendRAGClient] = None

def get_client() -> TrendRAGClient:
    global client
    if client is None:
        client = TrendRAGClient()
    return client


@mcp.tool()
def search_tech_trends(query: str, top_k: int = 5, platform: str = "", category: str = "", min_similarity: float = 0.35, sort_mode: str = "balanced") -> str:
    """
    Search 24,000+ tech trends, papers, GitHub repos, and community discussions using 2-stage Hybrid RAG + H-V-D Reranking.
    
    Args:
        query: Natural language search query (e.g., 'agent harness loop engineering', 'stealth crawler bypass')
        top_k: Number of relevant items to return (default: 5)
        platform: Optional source filter ('GitHub Official', 'Hacker News', 'ArXiv Preprint', 'GeekNews', etc.)
        category: Optional category filter ('AGENTS_DEVTOOLS', 'INFRA_RAG_SECURITY', 'FOUNDATION_MODELS', etc.)
        min_similarity: Minimum cosine similarity threshold (default: 0.35)
        sort_mode: Ranking mode - 'balanced' (Sim+HVD+Stability+Recency, default), 'stable_tech' (Best for mature/proven tech), 'hvd' (Viral spike first), 'similarity' (Pure vector)
    """
    try:
        rag = get_client()
        plat = platform if platform.strip() else None
        cat = category if category.strip() else None
        items = rag.search(query=query, top_k=top_k, platform=plat, category=cat, min_similarity=min_similarity, sort_mode=sort_mode)
        
        if not items:
            return f"No trend items found matching query '{query}' with similarity >= {min_similarity}."
        
        output_lines = [f"### 🔍 Trend Intelligence Results for '{query}' (Mode: `{sort_mode}`):\n"]
        for i, it in enumerate(items, 1):
            cross_badge = "🔥 [Cross-Spike] " if it.is_cross_spiking else ""
            metrics_str = f"Hybrid: {it.hybrid_score:.3f} | Sim: {it.similarity:.3f} | H-V-D Peak: {it.peak_score} | Stab: {it.stability_score:.2f}"
            if it.stars > 0:
                metrics_str += f" | ⭐ {it.stars}"
            if it.comments > 0:
                metrics_str += f" | 💬 {it.comments}"
                
            output_lines.append(f"**{i}. {cross_badge}[{it.platform}] {it.title}**\n   - **Scores**: `{metrics_str}`")
            if it.title_ko:
                output_lines.append(f"   - **Korean Title**: {it.title_ko}")
            if it.hook_ko:
                output_lines.append(f"   - **Insight**: {it.hook_ko}")
            output_lines.append(f"   - **URL**: {it.url}")
            output_lines.append(f"   - **Snippet**: {(it.description or '')[:180]}...\n")
        
        return "\n".join(output_lines)
    except Exception as e:
        return f"Error executing search_tech_trends: {str(e)}"


@mcp.tool()
def compare_tech_ab_test(tech_a: str, tech_b: str) -> str:
    """
    Perform A/B comparative evaluation between two technologies/frameworks based on real community feedback and metrics.
    
    Args:
        tech_a: Name of the first technology (e.g., 'Jev', 'Playwright', 'FastMCP')
        tech_b: Name of the second technology (e.g., 'Jeva', 'Puppeteer', 'REST')
    """
    try:
        rag = get_client()
        data = rag.compare_technologies(tech_a, tech_b, top_k=4)
        
        a_data = data["tech_a"]
        b_data = data["tech_b"]
        
        lines = [f"# ⚖️ A/B Comparison: {tech_a} vs {tech_b}\n"]
        lines.append(f"## 🔹 Option A: {tech_a} (Avg Relevance: {a_data['avg_similarity']}, Peak Score: {a_data['peak_spike_highest']})")
        for m in a_data["matches"][:3]:
            lines.append(f"- **{m['title']}** ({m['platform']}) [Sim: {m['similarity']}]")
            if m.get("hook_ko"):
                lines.append(f"  *Insight*: {m['hook_ko']}")
            lines.append(f"  *Link*: {m['url']}")
        
        lines.append(f"\n## 🔸 Option B: {tech_b} (Avg Relevance: {b_data['avg_similarity']}, Peak Score: {b_data['peak_spike_highest']})")
        for m in b_data["matches"][:3]:
            lines.append(f"- **{m['title']}** ({m['platform']}) [Sim: {m['similarity']}]")
            if m.get("hook_ko"):
                lines.append(f"  *Insight*: {m['hook_ko']}")
            lines.append(f"  *Link*: {m['url']}")
            
        lines.append(f"\n## 💡 Evaluation Takeaway")
        lines.append(f"DB citations found: {tech_a} ({len(a_data['matches'])} items) vs {tech_b} ({len(b_data['matches'])} items).")
        lines.append("Use these empirical citations to select the optimal stack based on community adoption and architectural maturity.")
        return "\n".join(lines)
    except Exception as e:
        return f"Error comparing {tech_a} vs {tech_b}: {str(e)}"


@mcp.tool()
def get_tech_deep_dive(keyword_or_repo: str) -> str:
    """
    Get deep-dive historical metadata, citations, and metrics for a specific tech entity or GitHub repo.
    
    Args:
        keyword_or_repo: Project or repository name (e.g., 'basic-pitch', 'open-scion', 'omniharvest')
    """
    try:
        rag = get_client()
        res = rag.get_deep_dive(keyword_or_repo)
        records = res.get("records", [])
        
        if not records:
            return f"No deep dive records found for '{keyword_or_repo}'."
            
        lines = [f"# 🔬 Deep-Dive Analysis for '{keyword_or_repo}' ({len(records)} records found)\n"]
        for r in records:
            lines.append(f"### [{r['platform']}] {r['title']} (Score: {r['peak_spike_score']})")
            if r.get("title_ko"):
                lines.append(f"- **Title (KO)**: {r['title_ko']}")
            if r.get("hook_ko"):
                lines.append(f"- **Key Takeaway**: {r['hook_ko']}")
            lines.append(f"- **Category**: {r['category']}")
            lines.append(f"- **Harvested**: {r['created_at']}")
            lines.append(f"- **URL**: {r['url']}\n")
        return "\n".join(lines)
    except Exception as e:
        return f"Error executing get_tech_deep_dive: {str(e)}"


@mcp.tool()
def get_daily_viral_spikes(target_date: str = "", limit: int = 10) -> str:
    """
    Retrieve cross-platform viral spikes and Daily Hot items ranked by the H-V-D formula.
    
    Args:
        target_date: Optional KST date formatted as 'YYYY-MM-DD' (defaults to recent 7-day window)
        limit: Max number of top viral items (default: 10)
    """
    try:
        rag = get_client()
        d_str = target_date.strip() if target_date.strip() else None
        spikes = rag.get_daily_viral_spikes(target_date=d_str, limit=limit)
        
        if not spikes:
            return f"No viral spike records found for date: {target_date or 'Recent 7 days'}."
            
        lines = [f"# 📈 Daily Hot Cross-Viral Spikes ({target_date or 'Recent 7-Day Active Window'})\n"]
        for i, s in enumerate(spikes, 1):
            lines.append(f"**{i}. [{s['platform']}] {s['title']}** (Peak: {s['peak_score']}, Live: {s['live_score']})")
            if s.get("title_ko"):
                lines.append(f"   - **Title (KO)**: {s['title_ko']}")
            if s.get("hook_ko"):
                lines.append(f"   - **Hook**: {s['hook_ko']}")
            lines.append(f"   - **URL**: {s['url']}\n")
        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching daily viral spikes: {str(e)}"


@mcp.tool()
def query_verified_factchecks(topic: str, limit: int = 5) -> str:
    """
    Query official verified factchecks and architectural debunks from the SSOT verified_factchecks database.
    
    Args:
        topic: Topic or claim to check (e.g., 'Gemini', 'DeepSeek', 'Quantum')
        limit: Max number of factcheck cases (default: 5)
    """
    try:
        rag = get_client()
        cases = rag.query_factchecks(topic=topic, limit=limit)
        
        if not cases:
            return f"No verified factcheck records found for topic: '{topic}'."
            
        lines = [f"# 🛡️ Verified Factcheck Reports for '{topic}'\n"]
        for c in cases:
            lines.append(f"### [Case #{c['case_id']}] {c['title']} ({c['category']})")
            lines.append(f"- **Verdict**: {c['verdict']}")
            lines.append(f"- **The Hook**: {c['the_hook']}")
            lines.append(f"- **Engineering Takeaways**: {c['engineering_takeaways']}")
            lines.append(f"- **Sources**: {c['sources']}\n")
        cur.close() if 'cur' in locals() else None
        return "\n".join(lines)
    except Exception as e:
        return f"Error querying verified factchecks: {str(e)}"


@mcp.tool()
def conduct_4pillar_factcheck(
    claim_or_topic: str,
    repo_name: str = "",
    academic_query: str = "",
    community_query: str = ""
) -> str:
    """
    Execute Track B On-Demand 4-Pillar Factcheck and Technical Verification with Token-Diet (~99% noise eliminated).
    
    Harvests verified evidence across:
      1. Academic Pillar (ArXiv API - theoretical bounds & paper claims)
      2. Developer Community Pillar (Hacker News Algolia - real reproduction bugs & controversies)
      3. Remote Code Inspection (GitHub REST API - Strictly Zero-Clone for Host Immunity)
      4. News & Internal RAG Cross-Check (Internal 24,000+ pgvector DB)
    
    Args:
        claim_or_topic: Technical claim, viral rumor, or project to verify (e.g., 'vLLM 10x faster memory', 'Ceph OSD NVMe migration')
        repo_name: Optional GitHub repository in 'owner/repo' format (e.g., 'vllm-project/vllm', 'OpenBB-finance/OpenBB')
        academic_query: Optional targeted keyword for ArXiv (defaults to claim_or_topic)
        community_query: Optional targeted keyword for Hacker News (defaults to claim_or_topic)
    """
    try:
        rag = get_client()
        result = rag.verify_claim_4pillar(
            claim_or_topic=claim_or_topic,
            repo_name=repo_name,
            academic_query=academic_query,
            community_query=community_query
        )
        return result.get("report_markdown", "No report generated.")
    except Exception as e:
        return f"Error executing conduct_4pillar_factcheck: {str(e)}"


if __name__ == "__main__":
    # Run standard stdio MCP transport
    mcp.run()
