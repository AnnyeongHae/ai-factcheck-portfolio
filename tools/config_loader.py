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
            "model_id": "gemini-3.8-flash",
            "full_model_tag": "google/gemini-3.8-flash",
            "display_name": "gemini-3.8-flash"
        }
    }
    return _CACHED_CONFIG

def get_canonical_model_id():
    cfg = get_enrichment_config()
    return cfg.get("canonical_engine", {}).get("model_id", "gemini-3.8-flash")

def get_canonical_model_tag():
    cfg = get_enrichment_config()
    return cfg.get("canonical_engine", {}).get("full_model_tag", "google/gemini-3.8-flash")

def get_canonical_display_name():
    cfg = get_enrichment_config()
    return cfg.get("canonical_engine", {}).get("display_name", "gemini-3.8-flash")
