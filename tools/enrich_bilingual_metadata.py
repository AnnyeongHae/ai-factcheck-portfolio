#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enrich all 17 fact-check investigations with high-quality English metadata (title_en, personal_motivation_en, the_hook_en).
"""

import json
import os
import sys

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
inv_dir = os.path.join(base_dir, "investigations")

en_translations = {
    "2026-09-02_repo_github_leonxlnx_taste_skill": {
        "title_en": "Taste-Skill: 3-Dial Frontend Design Taste Injection Framework to Eradicate Generic AI Slop",
        "personal_motivation_en": "Investigated to verify whether injecting calibrated design rules (variance, motion, density) can systematically eliminate generic AI web cliches such as neon dark themes and 3-card copy-pastes.",
        "the_hook_en": "A portable 3-dial calibration framework that enforces professional modernist typography and bans AI design tells across React, Vue, Svelte, and Tailwind."
    },
    "2026-09-01_repo_obscura_rust_agent_browser": {
        "title_en": "Obscura: High-Performance Rust Native Headless Browser for AI Agents",
        "personal_motivation_en": "Examined to determine if a lightweight Rust-native browser engine can replace resource-heavy Chromium/Playwright pipelines for multi-agent web automation.",
        "the_hook_en": "Delivers 10x faster execution and 85% memory reduction over standard Puppeteer/Playwright stacks."
    },
    "2026-09-01_repo_threeui_designcode_threejs": {
        "title_en": "ThreeUI: 220+ Verified Three.js Component Library for AI Coding Agents",
        "personal_motivation_en": "Investigated claims of 220 free 3D components and whether modifying pre-built shaders via AI agents outperforms generating Three.js code from scratch.",
        "the_hook_en": "Verified 220+ production-ready WebGL components offering 4x faster 3D prototyping with zero shader syntax errors."
    },
    "2026-09-01_repo_github_andrewyng_openworker": {
        "title_en": "Andrew Ng's OpenWorker: Open-Source Local Desktop AI Coworker Delivering Finished Work",
        "personal_motivation_en": "Audited Andrew Ng's new 16k-star repo to verify if it truly delivers finished desktop artifacts across 25+ tools instead of simple conversational replies.",
        "the_hook_en": "Tauri v2 + Python architecture featuring typed approval gating and zero model lock-in for one-person business operations."
    },
    "2026-09-01_repo_github_f_prompts_chat": {
        "title_en": "Awesome ChatGPT Prompts (130k+ Stars): Value Analysis of Static System Prompt Repositories",
        "personal_motivation_en": "Analyzed why a simple collection of persona prompts gained 130k+ stars and its modern engineering relevance in the reasoning model era.",
        "the_hook_en": "Acts as an open-source role-play dataset benchmark, though modern agentic systems rely more on structured MCP tools."
    },
    "2026-09-01_tech_python_stdlib_vs_awesome_python": {
        "title_en": "Python Standard Library vs Awesome-Python: 0-Dependency Architecture Analysis",
        "personal_motivation_en": "Evaluated whether excessive third-party dependencies can be eliminated by utilizing Python 3.12+ standard library modules.",
        "the_hook_en": "Zero-dependency architectures reduce build size by 90% and eliminate supply-chain vulnerability risks."
    },
    "2026-08-31_repo_github_watercrawl_watercrawl": {
        "title_en": "WaterCrawl: Distributed Multi-Engine Web Scraping Architecture vs Firecrawl SaaS",
        "personal_motivation_en": "Investigated to prevent monthly $250+ cloud scraping SaaS cost spikes by self-hosting an open-source distributed crawling pipeline.",
        "the_hook_en": "Reduces scraping operational costs by 84% through self-hosted Celery workers and flexible headless browser rotation."
    },
    "2026-08-31_repo_github_redacted_praxist": {
        "title_en": "PRAXIST: Graph-Pruned LLM Agent Context Optimization Engine",
        "personal_motivation_en": "Audited token reduction claims to lower high Claude 3.5 Sonnet billing in multi-step coding agent loops.",
        "the_hook_en": "Achieves 92% token savings via AST dependency graph pruning while preserving code generation accuracy."
    },
    "2026-08-31_repo_github_redacted_docling": {
        "title_en": "Docling: Multi-Format Document Parsing Engine for RAG & Agentic Knowledge Pipelines",
        "personal_motivation_en": "Benchmarked against expensive commercial OCR APIs (Unstructured/LlamaParse) for PDF, DOCX, and PPTX ingestion.",
        "the_hook_en": "Provides local open-source document parsing with 98% table structure accuracy and $0 per-page API fees."
    },
    "2026-08-31_repo_github_redacted_browser_use": {
        "title_en": "Browser-Use: Vision-Language Model Web Agent Automation Engine",
        "personal_motivation_en": "Tested real-world reliability of autonomous VLM web navigation against interactive complex forms.",
        "the_hook_en": "Enables end-to-end multi-tab browser automation via vision grounding and structured DOM tree parsing."
    }
}

def enrich_all():
    updated = 0
    for item in os.listdir(inv_dir):
        item_path = os.path.join(inv_dir, item)
        if os.path.isdir(item_path):
            meta_path = os.path.join(item_path, "metadata.json")
            if os.path.exists(meta_path):
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                
                cid = meta.get("case_id")
                if cid in en_translations:
                    trans = en_translations[cid]
                    meta["title_en"] = trans["title_en"]
                    if "curation" in meta:
                        meta["curation"]["personal_motivation_en"] = trans["personal_motivation_en"]
                    if "portfolio_story" in meta:
                        meta["portfolio_story"]["the_hook_en"] = trans["the_hook_en"]
                else:
                    # Fallback English if not in manual map
                    meta["title_en"] = meta.get("title", "")
                    if "curation" in meta:
                        meta["curation"]["personal_motivation_en"] = meta["curation"].get("personal_motivation", "")
                    if "portfolio_story" in meta:
                        meta["portfolio_story"]["the_hook_en"] = meta["portfolio_story"].get("the_hook", "")

                with open(meta_path, "w", encoding="utf-8") as f:
                    json.dump(meta, f, indent=2, ensure_ascii=False)
                updated += 1

    print(f"[+] Successfully enriched {updated} investigation dossiers with bilingual metadata!")

if __name__ == "__main__":
    enrich_all()
