#!/usr/bin/env python3
"""
High-Signal Multi-Tier RSS/Atom Catalog & Parallel Harvester Module (v2.0)
Derived from critical audit of fuxiaoai/tidings-rss + Korean Big-Tech + Chinese AI Ecosystem (DeepSeek, Qwen, Kimi, Zhipu, Hunyuan, StepFun, Jiqizhixin, etc.).

Architectural & Legal Safeguards:
1. Dual-Layer Content Extraction (Public Preview vs. Private Full-Text Vault):
   - Public `description`: Strictly <=180 chars metadata snippet for dashboard cards (Compliance with AP v. Meltwater, EU DSM Art. 15, KR Copyright Act).
   - Private `full_text_raw`: Complete article body text (up to 50,000 chars) extracted from <content:encoded>, <atom:content>, or <description>,
     stored ONLY in the private `raw_content_vault` SQL table (GZIP level-9 BYTEA) and local `.jsonl.gz` vault — NEVER exposed via public APIs.
2. Smart Per-Feed Window (`max_items = 10~15` + `max_age_days = 14` Recency Gate):
   - Captures up to 15 items per feed on busy news/release days without missing bursts, while automatically dropping stale historical posts (>14 days old) on cold start.
3. Latency & Straggler Protection (4-Layer Defense):
   - ThreadPoolExecutor(max_workers=12), socket timeout=6.5s, XML stream cap (1.8MB), and overall futures timeout guard.
"""

import concurrent.futures
import datetime
import email.utils
import re
import time
import xml.etree.ElementTree as ET

# Keyword pre-filter for broad science/media feeds to avoid non-tech/non-AI noise
TECH_AI_RELEVANCE_KEYWORDS = re.compile(
    r'\b(ai|llm|gpt|claude|gemini|deepseek|qwen|kimi|glm|hunyuan|stepfun|llama|mistral|openai|anthropic|deepmind|'
    r'nvidia|gpu|tpu|npu|transformer|diffusion|agent|agentic|mcp|rag|vector|embedding|quantum|robot|robotics|'
    r'autonomous|chip|semiconductor|cyber|security|vulnerability|cve|zero-day|hack|malware|encryption|neural|'
    r'brain|protein|alphafold|crispr|genome|fusion|algorithm|compute|datacenter|cloud|kubernetes|rust|python|'
    r'compiler|open-source|benchmark|reasoning|multimodal|vision|speech|tts|asr|fine-tun|rlhf|quantiz|inference)\b|'
    r'(인공지능|생성형|모델|반도체|양자|로봇|보안|취약점|해킹|알고리즘|클라우드|오픈소스|데이터센터|신경망|딥러닝|머신러닝|에이전트|'
    r'大模型|人工智能|算力|芯片|开源|智能体|算法|量子|机器人|深度求索|通义|千问|混元|智谱|月之暗面|阶跃|多模态|微调|推理)',
    re.IGNORECASE
)

# ==============================================================================
# CURATED MULTI-TIER RSS/ATOM CATALOG (72 Feeds across 7 Tiers)
# ==============================================================================
FIRST_PARTY_RSS_CATALOG = [
    # --------------------------------------------------------------------------
    # TIER 1: Global Official AI Frontier Labs & Big-Tech Research (14 Feeds)
    # --------------------------------------------------------------------------
    {
        "name": "OpenAI News",
        "url": "https://openai.com/news/rss.xml",
        "tier": "official_lab",
        "category_type": "NEWS",
        "lang": "EN",
        "max_items": 15,
        "badge": "🏛️ OpenAI 공식 발표",
        "require_keyword_filter": False,
    },
    {
        "name": "Google AI Blog",
        "url": "https://blog.google/technology/ai/rss/",
        "tier": "official_lab",
        "category_type": "NEWS",
        "lang": "EN",
        "max_items": 12,
        "badge": "🏛️ Google AI 공식",
        "require_keyword_filter": False,
    },
    {
        "name": "Google DeepMind",
        "url": "https://deepmind.com/blog/feed/basic/",
        "tier": "official_lab",
        "category_type": "PAPER",
        "lang": "EN",
        "max_items": 12,
        "badge": "🔬 DeepMind 리서치",
        "require_keyword_filter": False,
    },
    {
        "name": "Google Research",
        "url": "https://research.google/blog/rss/",
        "tier": "official_lab",
        "category_type": "PAPER",
        "lang": "EN",
        "max_items": 12,
        "badge": "🔬 Google Research",
        "require_keyword_filter": False,
    },
    {
        "name": "Hugging Face Blog",
        "url": "https://huggingface.co/blog/feed.xml",
        "tier": "official_lab",
        "category_type": "TECH",
        "lang": "EN",
        "max_items": 15,
        "badge": "🤗 HF 공식 블로그",
        "require_keyword_filter": False,
    },
    {
        "name": "Apple ML Research",
        "url": "https://machinelearning.apple.com/rss.xml",
        "tier": "official_lab",
        "category_type": "PAPER",
        "lang": "EN",
        "max_items": 10,
        "badge": "🍎 Apple ML 리서치",
        "require_keyword_filter": False,
    },
    {
        "name": "AWS Machine Learning",
        "url": "https://aws.amazon.com/blogs/amazon-ai/feed/",
        "tier": "official_lab",
        "category_type": "TECH",
        "lang": "EN",
        "max_items": 12,
        "badge": "☁️ AWS AI 공식",
        "require_keyword_filter": False,
    },
    {
        "name": "Amazon Science",
        "url": "https://www.amazon.science/index.rss",
        "tier": "official_lab",
        "category_type": "PAPER",
        "lang": "EN",
        "max_items": 10,
        "badge": "🔬 Amazon Science",
        "require_keyword_filter": False,
    },
    {
        "name": "Microsoft Azure Blog",
        "url": "https://azure.microsoft.com/en-us/blog/feed/",
        "tier": "official_lab",
        "category_type": "TECH",
        "lang": "EN",
        "max_items": 12,
        "badge": "☁️ MS Azure 공식",
        "require_keyword_filter": True,
    },
    {
        "name": "Engineering at Meta",
        "url": "https://engineering.fb.com/feed/",
        "tier": "official_lab",
        "category_type": "TECH",
        "lang": "EN",
        "max_items": 10,
        "badge": "🏛️ Meta Engineering",
        "require_keyword_filter": False,
    },
    {
        "name": "MIT News AI",
        "url": "https://news.mit.edu/rss/topic/artificial-intelligence2",
        "tier": "official_lab",
        "category_type": "PAPER",
        "lang": "EN",
        "max_items": 12,
        "badge": "🎓 MIT AI 리서치",
        "require_keyword_filter": False,
    },
    {
        "name": "BAIR Blog",
        "url": "https://bair.berkeley.edu/blog/feed.xml",
        "tier": "official_lab",
        "category_type": "PAPER",
        "lang": "EN",
        "max_items": 8,
        "badge": "🎓 Berkeley AI (BAIR)",
        "require_keyword_filter": False,
    },
    {
        "name": "NVIDIA Technical Blog",
        "url": "https://developer.nvidia.com/blog/feed/",
        "tier": "official_lab",
        "category_type": "TECH",
        "lang": "EN",
        "max_items": 12,
        "badge": "🟢 NVIDIA Tech Blog",
        "require_keyword_filter": False,
    },
    {
        "name": "Databricks Blog",
        "url": "https://www.databricks.com/feed",
        "tier": "official_lab",
        "category_type": "TECH",
        "lang": "EN",
        "max_items": 10,
        "badge": "🧱 Databricks 공식",
        "require_keyword_filter": False,
    },

    # --------------------------------------------------------------------------
    # TIER 2: Agentic / SDK / Framework Official Release Notes (14 GitHub Native Atom Feeds)
    # --------------------------------------------------------------------------
    {
        "name": "OpenAI Codex Releases",
        "url": "https://github.com/openai/codex/releases.atom",
        "tier": "release_notes",
        "category_type": "TECH",
        "lang": "EN",
        "max_items": 8,
        "badge": "🚀 Codex 릴리스",
        "require_keyword_filter": False,
    },
    {
        "name": "Claude Code Releases",
        "url": "https://github.com/anthropics/claude-code/releases.atom",
        "tier": "release_notes",
        "category_type": "TECH",
        "lang": "EN",
        "max_items": 8,
        "badge": "🚀 Claude Code 릴리스",
        "require_keyword_filter": False,
    },
    {
        "name": "Gemini CLI Releases",
        "url": "https://github.com/google-gemini/gemini-cli/releases.atom",
        "tier": "release_notes",
        "category_type": "TECH",
        "lang": "EN",
        "max_items": 8,
        "badge": "🚀 Gemini CLI 릴리스",
        "require_keyword_filter": False,
    },
    {
        "name": "MCP Specification Releases",
        "url": "https://github.com/modelcontextprotocol/specification/releases.atom",
        "tier": "release_notes",
        "category_type": "TECH",
        "lang": "EN",
        "max_items": 8,
        "badge": "🔌 MCP 표준 릴리스",
        "require_keyword_filter": False,
    },
    {
        "name": "MCP Servers Releases",
        "url": "https://github.com/modelcontextprotocol/servers/releases.atom",
        "tier": "release_notes",
        "category_type": "TECH",
        "lang": "EN",
        "max_items": 8,
        "badge": "🔌 MCP 서버 릴리스",
        "require_keyword_filter": False,
    },
    {
        "name": "LangChain Releases",
        "url": "https://github.com/langchain-ai/langchain/releases.atom",
        "tier": "release_notes",
        "category_type": "TECH",
        "lang": "EN",
        "max_items": 8,
        "badge": "🦜 LangChain 릴리스",
        "require_keyword_filter": False,
    },
    {
        "name": "vLLM Releases",
        "url": "https://github.com/vllm-project/vllm/releases.atom",
        "tier": "release_notes",
        "category_type": "TECH",
        "lang": "EN",
        "max_items": 8,
        "badge": "⚡ vLLM 릴리스",
        "require_keyword_filter": False,
    },
    {
        "name": "Ollama Releases",
        "url": "https://github.com/ollama/ollama/releases.atom",
        "tier": "release_notes",
        "category_type": "TECH",
        "lang": "EN",
        "max_items": 8,
        "badge": "🦙 Ollama 릴리스",
        "require_keyword_filter": False,
    },
    {
        "name": "llama.cpp Releases",
        "url": "https://github.com/ggml-org/llama.cpp/releases.atom",
        "tier": "release_notes",
        "category_type": "TECH",
        "lang": "EN",
        "max_items": 8,
        "badge": "⚡ llama.cpp 릴리스",
        "require_keyword_filter": False,
    },
    {
        "name": "DeepSeek-V3 Releases",
        "url": "https://github.com/deepseek-ai/DeepSeek-V3/releases.atom",
        "tier": "release_notes",
        "category_type": "TECH",
        "lang": "EN",
        "max_items": 6,
        "badge": "🐋 DeepSeek GitHub 릴리스",
        "require_keyword_filter": False,
    },
    {
        "name": "Qwen GitHub Releases",
        "url": "https://github.com/QwenLM/Qwen2.5/releases.atom",
        "tier": "release_notes",
        "category_type": "TECH",
        "lang": "EN",
        "max_items": 6,
        "badge": "💜 Qwen GitHub 릴리스",
        "require_keyword_filter": False,
    },
    {
        "name": "GitHub Changelog",
        "url": "https://github.blog/changelog/feed/",
        "tier": "release_notes",
        "category_type": "TECH",
        "lang": "EN",
        "max_items": 10,
        "badge": "🐙 GitHub Changelog",
        "require_keyword_filter": False,
    },
    {
        "name": "GitHub Copilot Changelog",
        "url": "https://github.blog/changelog/label/copilot/feed/",
        "tier": "release_notes",
        "category_type": "TECH",
        "lang": "EN",
        "max_items": 8,
        "badge": "🤖 Copilot Changelog",
        "require_keyword_filter": False,
    },
    {
        "name": "Zed Editor Releases",
        "url": "https://github.com/zed-industries/zed/releases.atom",
        "tier": "release_notes",
        "category_type": "TECH",
        "lang": "EN",
        "max_items": 6,
        "badge": "⚡ Zed 릴리스",
        "require_keyword_filter": False,
    },

    # --------------------------------------------------------------------------
    # TIER 3: Cloud, Infra, Architecture & Practitioner Thoughts (13 Feeds)
    # --------------------------------------------------------------------------
    {
        "name": "Simon Willison Weblog",
        "url": "https://simonwillison.net/atom/everything/",
        "tier": "eng_blog",
        "category_type": "TECH",
        "lang": "EN",
        "max_items": 12,
        "badge": "🛠️ Simon Willison",
        "require_keyword_filter": False,
    },
    {
        "name": "Cloudflare Blog",
        "url": "https://blog.cloudflare.com/rss",
        "tier": "eng_blog",
        "category_type": "TECH",
        "lang": "EN",
        "max_items": 10,
        "badge": "☁️ Cloudflare Blog",
        "require_keyword_filter": False,
    },
    {
        "name": "Vercel News",
        "url": "https://vercel.com/atom",
        "tier": "eng_blog",
        "category_type": "TECH",
        "lang": "EN",
        "max_items": 10,
        "badge": "▲ Vercel 공식",
        "require_keyword_filter": False,
    },
    {
        "name": "Supabase Blog",
        "url": "https://supabase.com/rss.xml",
        "tier": "eng_blog",
        "category_type": "TECH",
        "lang": "EN",
        "max_items": 8,
        "badge": "⚡ Supabase Blog",
        "require_keyword_filter": False,
    },
    {
        "name": "Replicate Blog",
        "url": "https://replicate.com/blog/rss",
        "tier": "eng_blog",
        "category_type": "TECH",
        "lang": "EN",
        "max_items": 8,
        "badge": "🚀 Replicate Blog",
        "require_keyword_filter": False,
    },
    {
        "name": "The GitHub Blog",
        "url": "https://github.blog/feed/",
        "tier": "eng_blog",
        "category_type": "TECH",
        "lang": "EN",
        "max_items": 10,
        "badge": "🐙 GitHub Blog",
        "require_keyword_filter": False,
    },
    {
        "name": "Martin Fowler",
        "url": "https://martinfowler.com/feed.atom",
        "tier": "eng_blog",
        "category_type": "TECH",
        "lang": "EN",
        "max_items": 8,
        "badge": "📐 Martin Fowler",
        "require_keyword_filter": False,
    },
    {
        "name": "Netflix TechBlog",
        "url": "https://netflixtechblog.com/feed",
        "tier": "eng_blog",
        "category_type": "TECH",
        "lang": "EN",
        "max_items": 8,
        "badge": "🎬 Netflix Tech",
        "require_keyword_filter": False,
    },
    {
        "name": "Stripe Engineering",
        "url": "https://stripe.com/blog/feed.rss",
        "tier": "eng_blog",
        "category_type": "TECH",
        "lang": "EN",
        "max_items": 8,
        "badge": "💳 Stripe Blog",
        "require_keyword_filter": False,
    },
    {
        "name": "Last Week in AI",
        "url": "https://lastweekin.ai/feed",
        "tier": "eng_blog",
        "category_type": "NEWS",
        "lang": "EN",
        "max_items": 8,
        "badge": "🗞️ Last Week in AI",
        "require_keyword_filter": False,
    },
    {
        "name": "Lilian Weng Blog",
        "url": "https://lilianweng.github.io/index.xml",
        "tier": "eng_blog",
        "category_type": "PAPER",
        "lang": "EN",
        "max_items": 6,
        "badge": "🧠 Lilian Weng",
        "require_keyword_filter": False,
    },
    {
        "name": "Ahead of AI (Sebastian Raschka)",
        "url": "https://magazine.sebastianraschka.com/feed",
        "tier": "eng_blog",
        "category_type": "PAPER",
        "lang": "EN",
        "max_items": 8,
        "badge": "🧠 Ahead of AI",
        "require_keyword_filter": False,
    },
    {
        "name": "Interconnects (Nathan Lambert)",
        "url": "https://www.interconnects.ai/feed",
        "tier": "eng_blog",
        "category_type": "TECH",
        "lang": "EN",
        "max_items": 8,
        "badge": "🧠 Interconnects AI",
        "require_keyword_filter": False,
    },

    # --------------------------------------------------------------------------
    # TIER 4: Cybersecurity, Vulnerability & AI Safety Advisories (5 Feeds)
    # --------------------------------------------------------------------------
    {
        "name": "BleepingComputer Security",
        "url": "https://www.bleepingcomputer.com/feed/",
        "tier": "security",
        "category_type": "NEWS",
        "lang": "EN",
        "max_items": 8,
        "badge": "🛡️ BleepingComputer 보안",
        "require_keyword_filter": False,
    },
    {
        "name": "The Hacker News (Security)",
        "url": "https://feeds.feedburner.com/TheHackersNews",
        "tier": "security",
        "category_type": "NEWS",
        "lang": "EN",
        "max_items": 10,
        "badge": "🛡️ The Hacker News 보안",
        "require_keyword_filter": False,
    },
    {
        "name": "Krebs on Security",
        "url": "https://krebsonsecurity.com/feed/",
        "tier": "security",
        "category_type": "NEWS",
        "lang": "EN",
        "max_items": 8,
        "badge": "🛡️ Krebs Security",
        "require_keyword_filter": False,
    },
    {
        "name": "Schneier on Security",
        "url": "https://www.schneier.com/blog/index.rdf",
        "tier": "security",
        "category_type": "NEWS",
        "lang": "EN",
        "max_items": 8,
        "badge": "🛡️ Bruce Schneier",
        "require_keyword_filter": False,
    },
    {
        "name": "Security Affairs",
        "url": "https://securityaffairs.co/wordpress/feed",
        "tier": "security",
        "category_type": "NEWS",
        "lang": "EN",
        "max_items": 8,
        "badge": "🛡️ Security Affairs",
        "require_keyword_filter": True,
    },

    # --------------------------------------------------------------------------
    # TIER 5: Deep Science & Global Tech Media (4 Feeds)
    # --------------------------------------------------------------------------
    {
        "name": "ScienceDaily AI",
        "url": "https://www.sciencedaily.com/rss/computers_math/artificial_intelligence.xml",
        "tier": "science",
        "category_type": "PAPER",
        "lang": "EN",
        "max_items": 10,
        "badge": "🔬 ScienceDaily AI",
        "require_keyword_filter": False,
    },
    {
        "name": "Quanta Magazine",
        "url": "https://www.quantamagazine.org/feed/",
        "tier": "science",
        "category_type": "PAPER",
        "lang": "EN",
        "max_items": 8,
        "badge": "🔬 Quanta Magazine",
        "require_keyword_filter": False,
    },
    {
        "name": "MIT Technology Review",
        "url": "https://www.technologyreview.com/feed/",
        "tier": "media",
        "category_type": "NEWS",
        "lang": "EN",
        "max_items": 12,
        "badge": "📰 MIT Tech Review",
        "require_keyword_filter": False,
    },
    {
        "name": "WIRED",
        "url": "https://www.wired.com/feed/rss",
        "tier": "media_broad",
        "category_type": "NEWS",
        "lang": "EN",
        "max_items": 12,
        "badge": "📰 WIRED",
        "require_keyword_filter": True,
    },

    # --------------------------------------------------------------------------
    # TIER 6: Korean (KO) First-Party Big-Tech Engineering Blogs (6 Feeds)
    # --------------------------------------------------------------------------
    {
        "name": "Naver D2",
        "url": "https://d2.naver.com/d2.atom",
        "tier": "eng_blog_ko",
        "category_type": "TECH",
        "lang": "KO",
        "max_items": 10,
        "badge": "🇰🇷 네이버 D2",
        "require_keyword_filter": False,
    },
    {
        "name": "Kakao Tech",
        "url": "https://tech.kakao.com/feed/",
        "tier": "eng_blog_ko",
        "category_type": "TECH",
        "lang": "KO",
        "max_items": 10,
        "badge": "🇰🇷 카카오테크",
        "require_keyword_filter": False,
    },
    {
        "name": "Toss Tech",
        "url": "https://toss.tech/rss.xml",
        "tier": "eng_blog_ko",
        "category_type": "TECH",
        "lang": "KO",
        "max_items": 10,
        "badge": "🇰🇷 토스테크",
        "require_keyword_filter": False,
    },
    {
        "name": "Woowahan Tech",
        "url": "https://techblog.woowahan.com/feed/",
        "tier": "eng_blog_ko",
        "category_type": "TECH",
        "lang": "KO",
        "max_items": 8,
        "badge": "🇰🇷 우아한형제들 테크",
        "require_keyword_filter": False,
    },
    {
        "name": "Daangn Tech",
        "url": "https://medium.com/feed/daangn",
        "tier": "eng_blog_ko",
        "category_type": "TECH",
        "lang": "KO",
        "max_items": 8,
        "badge": "🇰🇷 당근 테크블로그",
        "require_keyword_filter": False,
    },
    {
        "name": "PyTorchKR",
        "url": "https://discuss.pytorch.kr/latest.rss",
        "tier": "eng_blog_ko",
        "category_type": "TECH",
        "lang": "KO",
        "max_items": 12,
        "badge": "🇰🇷 PyTorchKR 커뮤니티",
        "require_keyword_filter": False,
    },

    # --------------------------------------------------------------------------
    # TIER 7: Chinese (ZH) AI Frontier Labs, WeChat Channels & Tech Media (16 Feeds)
    # --------------------------------------------------------------------------
    {
        "name": "DeepSeek (深度求索)",
        "url": "https://wechat2rss.bestblogs.dev/feed/1709da4f538d4ce4fb6d7a8ba1a5a1c297919601.xml",
        "tier": "official_lab_zh",
        "category_type": "TECH",
        "lang": "ZH",
        "max_items": 12,
        "badge": "🇨🇳 DeepSeek 공식(WeChat)",
        "require_keyword_filter": False,
    },
    {
        "name": "Qwen (通义千问 / 通义实验室)",
        "url": "https://wechat2rss.bestblogs.dev/feed/4ebee6222ae08705b8aabc9116f0defbcb6b17c6.xml",
        "tier": "official_lab_zh",
        "category_type": "TECH",
        "lang": "ZH",
        "max_items": 12,
        "badge": "🇨🇳 알리바바 Qwen(통의실험실)",
        "require_keyword_filter": False,
    },
    {
        "name": "Kimi (月之暗面 Moonshot AI)",
        "url": "https://wechat2rss.bestblogs.dev/feed/c5c43d4bc17bae656763859ed0903bb6314ec6fe.xml",
        "tier": "official_lab_zh",
        "category_type": "TECH",
        "lang": "ZH",
        "max_items": 12,
        "badge": "🇨🇳 Moonshot Kimi 공식",
        "require_keyword_filter": False,
    },
    {
        "name": "Zhipu AI (智谱 GLM)",
        "url": "https://wechat2rss.bestblogs.dev/feed/433d2134dca54d80804daf32e8be546155be3300.xml",
        "tier": "official_lab_zh",
        "category_type": "TECH",
        "lang": "ZH",
        "max_items": 12,
        "badge": "🇨🇳 Zhipu AI (GLM) 공식",
        "require_keyword_filter": False,
    },
    {
        "name": "Tencent Hunyuan (腾讯混元)",
        "url": "https://wechat2rss.bestblogs.dev/feed/306ce19a1ca590c9c2df781789e828d1acfa1356.xml",
        "tier": "official_lab_zh",
        "category_type": "TECH",
        "lang": "ZH",
        "max_items": 12,
        "badge": "🇨🇳 텐센트 Hunyuan 공식",
        "require_keyword_filter": False,
    },
    {
        "name": "StepFun (阶跃星辰)",
        "url": "https://wechat2rss.bestblogs.dev/feed/3e2714d06aa36142e8ed6b3f4e5cf9090a069dd2.xml",
        "tier": "official_lab_zh",
        "category_type": "TECH",
        "lang": "ZH",
        "max_items": 10,
        "badge": "🇨🇳 StepFun 공식",
        "require_keyword_filter": False,
    },
    {
        "name": "Jiqizhixin (机器之心)",
        "url": "https://wechat2rss.bestblogs.dev/feed/8d97af31b0de9e48da74558af128a4673d78c9a3.xml",
        "tier": "media_zh",
        "category_type": "NEWS",
        "lang": "ZH",
        "max_items": 15,
        "badge": "🇨🇳 机器之心 (Synced)",
        "require_keyword_filter": False,
    },
    {
        "name": "Jiqizhixin SOTA (机器之心SOTA模型)",
        "url": "https://wechat2rss.bestblogs.dev/feed/2f520471856d56c7b3a95cd09eb777149b32828a.xml",
        "tier": "media_zh",
        "category_type": "PAPER",
        "lang": "ZH",
        "max_items": 12,
        "badge": "🇨🇳 机器之心 SOTA모델",
        "require_keyword_filter": False,
    },
    {
        "name": "Xinzhiyuan (新智元)",
        "url": "https://wechat2rss.xlab.app/feed/ede30346413ea70dbef5d485ea5cbb95cca446e7.xml",
        "tier": "media_zh",
        "category_type": "NEWS",
        "lang": "ZH",
        "max_items": 15,
        "badge": "🇨🇳 新智元 (AI Era)",
        "require_keyword_filter": False,
    },
    {
        "name": "QbitAI (量子位)",
        "url": "https://www.qbitai.com/feed",
        "tier": "media_zh",
        "category_type": "NEWS",
        "lang": "ZH",
        "max_items": 15,
        "badge": "🇨🇳 量子位 QbitAI",
        "require_keyword_filter": False,
    },
    {
        "name": "AI Dev Daily (AI 开发者日报)",
        "url": "https://ainews.liduos.com/rss.xml",
        "tier": "media_zh",
        "category_type": "TECH",
        "lang": "ZH",
        "max_items": 10,
        "badge": "🇨🇳 AI 开发者日报",
        "require_keyword_filter": False,
    },
    {
        "name": "Tencent Research (腾讯研究院)",
        "url": "https://wechat2rss.bestblogs.dev/feed/6152301e0978bffb0a8284cab339262b9764dcfb.xml",
        "tier": "official_lab_zh",
        "category_type": "PAPER",
        "lang": "ZH",
        "max_items": 10,
        "badge": "🇨🇳 텐센트 연구원",
        "require_keyword_filter": False,
    },
    {
        "name": "Alibaba Research (阿里研究院)",
        "url": "https://wechat2rss.bestblogs.dev/feed/e2f1190c120f7f3d74b630bfcfe9e58296bd535c.xml",
        "tier": "official_lab_zh",
        "category_type": "PAPER",
        "lang": "ZH",
        "max_items": 10,
        "badge": "🇨🇳 알리바바 연구원",
        "require_keyword_filter": False,
    },
    {
        "name": "36Kr (36氪)",
        "url": "https://www.36kr.com/feed",
        "tier": "media_zh",
        "category_type": "NEWS",
        "lang": "ZH",
        "max_items": 12,
        "badge": "🇨🇳 36氪 Tech",
        "require_keyword_filter": True,
    },
    {
        "name": "sspai (少数派)",
        "url": "https://sspai.com/feed",
        "tier": "media_zh",
        "category_type": "TECH",
        "lang": "ZH",
        "max_items": 10,
        "badge": "🇨🇳 少数派 sspai",
        "require_keyword_filter": True,
    },
    {
        "name": "Ruan Yifeng Blog (阮一峰)",
        "url": "https://www.ruanyifeng.com/blog/atom.xml",
        "tier": "eng_blog_zh",
        "category_type": "TECH",
        "lang": "ZH",
        "max_items": 8,
        "badge": "🇨🇳 阮一峰 Weekly",
        "require_keyword_filter": False,
    },
]


def _extract_full_text_and_snippet(item_elem: ET.Element) -> tuple[str, str]:
    """
    Extracts both:
    1) Public metadata snippet (<=180 chars) for safe dashboard display.
    2) Complete plain-text article body (up to 50,000 chars) from <content:encoded>, <atom:content>, <description>, or <atom:summary>
       for the Private Full-Text Vault (never exposed to public frontend APIs).
    """
    raw_chunks = []
    # Check <content:encoded>, <atom:content>, <description>, <atom:summary>
    tag_candidates = [
        '{http://purl.org/rss/1.0/modules/content/}encoded',
        '{http://www.w3.org/2005/Atom}content',
        'description',
        '{http://www.w3.org/2005/Atom}summary',
        '{http://purl.org/rss/1.0/}description',
    ]
    for tag in tag_candidates:
        node = item_elem.find(tag)
        if node is not None and node.text and node.text.strip():
            raw_chunks.append(node.text.strip())

    if not raw_chunks:
        return ("", "")

    # Pick the longest text block as the full-text body source
    best_raw = max(raw_chunks, key=len)
    # Convert block-level HTML tags to newlines before stripping HTML tags so paragraph structure is preserved in vault
    structured = re.sub(r'</?(p|div|br|li|h[1-6]|tr|blockquote)[^>]*>', '\n', best_raw, flags=re.IGNORECASE)
    clean_full = re.sub(r'<[^>]+>', ' ', structured)
    clean_full = re.sub(r'[ \t]+', ' ', clean_full)
    clean_full = re.sub(r'\n\s*\n+', '\n\n', clean_full).strip()[:50000]

    # Single-line compact snippet (<=180 chars) for public metadata
    snippet = re.sub(r'\s+', ' ', clean_full).strip()[:180]
    return (snippet, clean_full)


def _is_within_recency_window(pub_dt: datetime.datetime | None, max_age_days: int = 14) -> bool:
    """
    Returns True if the item was published within `max_age_days` (default 14 days),
    or if no parseable date was provided. Prevents cold-start historical floods while allowing high `max_items` (10~15).
    """
    if pub_dt is None:
        return True
    try:
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        if pub_dt.tzinfo is None:
            pub_dt = pub_dt.replace(tzinfo=datetime.timezone.utc)
        age = now_utc - pub_dt
        return age.total_seconds() <= (max_age_days * 86400)
    except Exception:
        return True


def _parse_single_rss_or_atom(feed_meta: dict, fetch_xml_fn, max_age_days: int = 14) -> tuple[str, list[dict], str | None]:
    """
    Worker function executed in ThreadPoolExecutor.
    Parses RSS 2.0, RDF/RSS 1.0, or Atom 1.0 XML and returns candidates with both public snippet and private full_text_raw.
    """
    sname = feed_meta["name"]
    sfeed = feed_meta["url"]
    tier = feed_meta.get("tier", "eng_blog")
    cat_type = feed_meta.get("category_type", "TECH")
    lang = feed_meta.get("lang", "EN")
    max_items = feed_meta.get("max_items", 10)
    badge = feed_meta.get("badge", f"🌍 {sname}")
    require_kw = feed_meta.get("require_keyword_filter", False)

    candidates = []
    try:
        xml_raw = fetch_xml_fn(sfeed, timeout=6.5)
        root = ET.fromstring(xml_raw)

        # Support RSS 2.0 (<item>), Atom (<entry>), and RDF/RSS 1.0
        items = root.findall('.//item')
        if not items:
            ns = {'atom': 'http://www.w3.org/2005/Atom', 'rdf': 'http://purl.org/rss/1.0/'}
            items = (
                root.findall('atom:entry', ns)
                or root.findall('.//{http://www.w3.org/2005/Atom}entry')
                or root.findall('.//{http://purl.org/rss/1.0/}item')
            )

        for it in items[:max_items * 2]:
            if len(candidates) >= max_items:
                break

            t_node = (
                it.find('title')
                if it.find('title') is not None
                else (
                    it.find('{http://www.w3.org/2005/Atom}title')
                    if it.find('{http://www.w3.org/2005/Atom}title') is not None
                    else it.find('{http://purl.org/rss/1.0/}title')
                )
            )
            l_node = (
                it.find('link')
                if it.find('link') is not None
                else (
                    it.find('{http://www.w3.org/2005/Atom}link')
                    if it.find('{http://www.w3.org/2005/Atom}link') is not None
                    else it.find('{http://purl.org/rss/1.0/}link')
                )
            )

            if t_node is None or not t_node.text:
                continue

            title = re.sub(r'\s+', ' ', t_node.text).strip()
            if not title:
                continue

            url = ""
            if l_node is not None:
                url = l_node.attrib.get('href') if 'href' in l_node.attrib else (l_node.text or "").strip()
            if not url:
                id_n = it.find('{http://www.w3.org/2005/Atom}id') or it.find('guid')
                if id_n is not None and id_n.text and id_n.text.strip().startswith('http'):
                    url = id_n.text.strip()

            if not url or not url.startswith('http'):
                continue

            pub_n = (
                it.find('pubDate')
                or it.find('{http://www.w3.org/2005/Atom}published')
                or it.find('{http://www.w3.org/2005/Atom}updated')
                or it.find('{http://purl.org/dc/elements/1.1/}date')
            )
            pub_iso = None
            pub_dt = None
            if pub_n is not None and pub_n.text:
                raw_pub = pub_n.text.strip()
                try:
                    pub_dt = email.utils.parsedate_to_datetime(raw_pub)
                    pub_iso = pub_dt.isoformat()
                except Exception:
                    try:
                        clean_iso = raw_pub.replace("Z", "+00:00")
                        pub_dt = datetime.datetime.fromisoformat(clean_iso)
                        pub_iso = pub_dt.isoformat()
                    except Exception:
                        pub_iso = raw_pub

            # Enforce 14-day recency gate so increasing max_items to 10~15 never imports stale historical posts
            if not _is_within_recency_window(pub_dt, max_age_days=max_age_days):
                continue

            desc_snippet, full_text_raw = _extract_full_text_and_snippet(it)

            # Optional keyword pre-filter for general science/media feeds
            if require_kw:
                combined_text = f"{title} {desc_snippet}"
                if not TECH_AI_RELEVANCE_KEYWORDS.search(combined_text):
                    continue

            cand_data = {
                "title": f"{sname}: {title}",
                "source_platform": sname,
                "source_url": url,
                "article_url": url,
                "published_at": pub_iso,
                "type": "sns",
                "category_type": cat_type,
                "source_tier": tier,
                "source_lang": lang,
                "description": desc_snippet or f"{sname}: {title}",
                "full_text_raw": full_text_raw or desc_snippet or title,
                "viral_metric": badge,
            }
            if lang == "KO":
                cand_data["title_ko"] = title
                cand_data["description_ko"] = desc_snippet or title

            candidates.append(cand_data)

        return (sname, candidates, None)
    except Exception as err:
        return (sname, [], str(err))


def fetch_catalog_feeds_parallel(fetch_xml_fn, max_workers: int = 12, max_age_days: int = 14) -> dict:
    """
    Concurrently fetches all 72 feeds in FIRST_PARTY_RSS_CATALOG using ThreadPoolExecutor(max_workers=12).
    Includes overall wall-clock timeout protection against slow straggler servers.
    """
    t0 = time.time()
    all_cands = []
    succeeded = 0
    failed = 0
    errors = []

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
    try:
        future_map = {
            executor.submit(_parse_single_rss_or_atom, feed_meta, fetch_xml_fn, max_age_days): feed_meta["name"]
            for feed_meta in FIRST_PARTY_RSS_CATALOG
        }
        try:
            for future in concurrent.futures.as_completed(future_map, timeout=22.0):
                fname = future_map[future]
                try:
                    sname, cands, err = future.result(timeout=1.0)
                    if err:
                        failed += 1
                        errors.append({"feed": sname, "error": err[:120]})
                    else:
                        succeeded += 1
                        all_cands.extend(cands)
                except Exception as exc:
                    failed += 1
                    errors.append({"feed": fname, "error": str(exc)[:120]})
        except concurrent.futures.TimeoutError:
            for fut, fname in future_map.items():
                if not fut.done():
                    fut.cancel()
                    failed += 1
                    errors.append({"feed": fname, "error": "Global catalog timeout (22s) exceeded"})
    finally:
        executor.shutdown(wait=False, cancel_futures=True)

    return {
        "candidates": all_cands,
        "feeds_total": len(FIRST_PARTY_RSS_CATALOG),
        "feeds_succeeded": succeeded,
        "feeds_failed": failed,
        "errors": errors,
        "duration_sec": round(time.time() - t0, 2),
    }
