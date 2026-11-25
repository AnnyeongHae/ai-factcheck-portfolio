import os
import json

_CACHED_CONFIG = None

def get_enrichment_config():
    global _CACHED_CONFIG
    if _CACHED_CONFIG is not None:
        return _CACHED_CONFIG
    
    # Try finding configs/ai_enrichment_modes.json relative to project root
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(cur_dir, "..", "configs", "ai_enrichment_modes.json"),
        os.path.join(cur_dir, "configs", "ai_enrichment_modes.json"),
        os.path.abspath("configs/ai_enrichment_modes.json")
    ]
    
    for path in candidates:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    _CACHED_CONFIG = json.load(f)
                    return _CACHED_CONFIG
            except Exception:
                pass
                
    # Safe default fallback
    _CACHED_CONFIG = {
        "canonical_engine": {
            "model_id": os.getenv("ENRICH_MODEL") or os.getenv("ACTIVE_AI_MODEL") or "in-session-agent",
            "full_model_tag": os.getenv("ENRICH_MODEL") or os.getenv("ACTIVE_AI_MODEL") or "in-session-agent",
            "display_name": os.getenv("ENRICH_MODEL") or os.getenv("ACTIVE_AI_MODEL") or "in-session-agent"
        }
    }
    return _CACHED_CONFIG

def get_canonical_model_id():
    env_model = os.getenv("ENRICH_MODEL") or os.getenv("ACTIVE_AI_MODEL")
    if env_model:
        return env_model
    cfg = get_enrichment_config()
    return cfg.get("canonical_engine", {}).get("model_id", "in-session-agent")

def get_canonical_model_tag():
    env_model = os.getenv("ENRICH_MODEL") or os.getenv("ACTIVE_AI_MODEL")
    if env_model:
        return env_model
    cfg = get_enrichment_config()
    return cfg.get("canonical_engine", {}).get("full_model_tag", "in-session-agent")

def get_canonical_display_name():
    env_model = os.getenv("ENRICH_MODEL") or os.getenv("ACTIVE_AI_MODEL")
    if env_model:
        return env_model
    cfg = get_enrichment_config()
    return cfg.get("canonical_engine", {}).get("display_name", "in-session-agent")
