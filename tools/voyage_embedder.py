#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Voyage AI Ultra-Lightweight Embedding Client (voyage-4-lite)
2026 SOTA Semantic Deduplication Module
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional

VOYAGE_API_URL = "https://api.voyageai.com/v1/embeddings"
DEFAULT_MODEL = "voyage-4-lite"
DEFAULT_DIM = 512
CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "voyage_embeddings_cache.json")


def load_env():
    """Load environment variables from .env file if present."""
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip("'\"")
                    if k not in os.environ:
                        os.environ[k] = v


load_env()
VOYAGE_API_KEY = os.environ.get("VOYAGE_API_KEY") or os.environ.get("VOYAGEAI_API_KEY")


def load_cache() -> Dict[str, List[float]]:
    """Load local embedding cache to prevent redundant API calls."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_cache(cache: Dict[str, List[float]]):
    """Save embeddings cache to disk safely."""
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        tmp_file = CACHE_FILE + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(cache, f)
        if os.path.exists(CACHE_FILE):
            os.replace(tmp_file, CACHE_FILE)
        else:
            os.rename(tmp_file, CACHE_FILE)
    except Exception as e:
        print(f"[!] Warning: Failed to save embedding cache: {e}", file=sys.stderr)


def get_embeddings(texts: List[str], model: str = DEFAULT_MODEL, dimension: int = DEFAULT_DIM) -> List[List[float]]:
    """
    Generate dense embeddings using Voyage AI REST API.
    Utilizes local memory cache to maximize efficiency and conserve quota.
    """
    if not texts:
        return []

    cache = load_cache()
    results: List[Optional[List[float]]] = [None] * len(texts)
    missing_indices = []
    missing_texts = []

    for i, text in enumerate(texts):
        norm_key = f"{model}:{dimension}:{text.strip()}"
        if norm_key in cache:
            results[i] = cache[norm_key]
        else:
            missing_indices.append(i)
            missing_texts.append(text.strip())

    if not missing_texts:
        return [r for r in results if r is not None]

    api_key = VOYAGE_API_KEY or os.environ.get("VOYAGE_API_KEY")
    if not api_key:
        raise ValueError("VOYAGE_API_KEY is not set in environment or .env file.")

    # Voyage API supports up to 128 inputs per batch
    batch_size = 64
    for b_start in range(0, len(missing_texts), batch_size):
        b_texts = missing_texts[b_start:b_start + batch_size]
        payload = {
            "input": b_texts,
            "model": model,
            "output_dimension": dimension
        }

        req = urllib.request.Request(
            VOYAGE_API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "AIFactcheck/1.0 (voyage-embedder)"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                embeddings = [item["embedding"] for item in sorted(data.get("data", []), key=lambda x: x["index"])]
                
                for offset, emb in enumerate(embeddings):
                    orig_idx = missing_indices[b_start + offset]
                    results[orig_idx] = emb
                    norm_key = f"{model}:{dimension}:{missing_texts[b_start + offset]}"
                    cache[norm_key] = emb

        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            print(f"[!] Voyage API HTTPError {e.code}: {err_body}", file=sys.stderr)
            raise
        except Exception as e:
            print(f"[!] Voyage API Request Failed: {e}", file=sys.stderr)
            raise

    save_cache(cache)
    return [r for r in results if r is not None]


def get_single_embedding(text: str, model: str = DEFAULT_MODEL, dimension: int = DEFAULT_DIM) -> List[float]:
    """Convenience function to get embedding for a single text."""
    res = get_embeddings([text], model=model, dimension=dimension)
    return res[0] if res else []


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculate cosine similarity between two normalized vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm_a = sum(a * a for a in v1) ** 0.5
    norm_b = sum(b * b for b in v2) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


if __name__ == "__main__":
    print("[*] Testing Voyage AI Embedder...")
    sample1 = "[qwen-image-2.1] Alibaba announces Qwen-Image-2.1 open weights"
    sample2 = "[qwen-image-2.1] Qwen-Image-2.1 released on HuggingFace Spaces"
    sample3 = "[jev] Jev System One Decision Engine Architecture Guide"

    try:
        t0 = time.time()
        embs = get_embeddings([sample1, sample2, sample3])
        dt = time.time() - t0
        print(f"[+] Successfully fetched {len(embs)} embeddings in {dt*1000:.1f}ms! Dim: {len(embs[0])}")
        sim12 = cosine_similarity(embs[0], embs[1])
        sim13 = cosine_similarity(embs[0], embs[2])
        print(f"[*] Sim(Sample1, Sample2) [Same Event Qwen]: {sim12:.4f} (Expected > 0.85)")
        print(f"[*] Sim(Sample1, Sample3) [Different Event Jev]: {sim13:.4f} (Expected < 0.60)")
    except Exception as ex:
        print(f"[!] Test failed: {ex}")
