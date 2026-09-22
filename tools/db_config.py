#!/usr/bin/env python3
"""
tools/db_config.py - Centralized Database Configuration for Python Tools (SSOT)
Single Source of Truth for Database Connections across all automation & ETL tools.
"""

import os
import re
import sys
from urllib.parse import urlparse
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def get_base_dir() -> Path:
    return Path(__file__).resolve().parent.parent

def load_env_variables():
    """Parse .env file if environment variables are not already set."""
    env_file = get_base_dir() / ".env"
    if env_file.exists():
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k and k not in os.environ:
                        os.environ[k] = v
        except Exception:
            pass

def get_db_url() -> str:
    """
    Returns the primary PostgreSQL database connection URL (SSOT: Aiven PostgreSQL).
    Priority:
    1. AIVEN_SERVICE_URI (Primary SSOT)
    2. DATABASE_URL (if NOT pointing to frozen Neon DB)
    3. Frozen Neon DB blocked by default to prevent 5GB quota exhaustion.
    """
    load_env_variables()

    # 1. Primary Aiven SSOT
    if os.environ.get("AIVEN_SERVICE_URI"):
        return os.environ.get("AIVEN_SERVICE_URI")

    # 2. DATABASE_URL (check if pointing to Neon)
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        if "neon.tech" not in db_url:
            return db_url
        if os.environ.get("ALLOW_FROZEN_NEON") == "true":
            print("[!] Warning: Using frozen Neon DB (ALLOW_FROZEN_NEON=true).")
            return db_url
        print("[!] ⛔ Warning: Neon PostgreSQL is FROZEN (100% bandwidth quota exhausted). Active queries blocked. Please configure AIVEN_SERVICE_URI.")
        return ""

    if os.environ.get("ALLOW_FROZEN_NEON") == "true":
        return os.environ.get("NEON_KEY") or os.environ.get("NEON_BACKUP_KEY") or ""

    return ""

def get_db_info(url: str = None) -> dict:
    """Inspects the connection string and returns safe provider metadata."""
    target_url = url or get_db_url()
    if not target_url:
        return {
            "provider": "Not Configured",
            "host": None,
            "port": None,
            "database": None,
            "user": None,
            "masked_url": ""
        }

    try:
        parsed = urlparse(target_url)
        host = parsed.hostname or ""
        provider = "PostgreSQL"

        if "aivencloud.com" in host:
            provider = "Aiven PostgreSQL"
        elif "neon.tech" in host:
            provider = "Neon PostgreSQL"
        elif "supabase.co" in host:
            provider = "Supabase PostgreSQL"
        elif host in ("localhost", "127.0.0.1"):
            provider = "Local PostgreSQL"

        masked_url = target_url
        if parsed.password:
            masked_url = target_url.replace(f":{parsed.password}@", ":******@")

        return {
            "provider": provider,
            "host": host,
            "port": parsed.port or 5432,
            "database": (parsed.path or "").lstrip("/"),
            "user": parsed.username or "",
            "masked_url": masked_url
        }
    except Exception as e:
        return {
            "provider": "Unknown",
            "host": "Unknown",
            "port": None,
            "database": None,
            "user": None,
            "masked_url": "",
            "error": str(e)
        }

def get_db_connection(cursor_factory=None):
    """Creates and returns a psycopg2 connection using the centralized configuration."""
    db_url = get_db_url()
    if not db_url:
        print("[!] Error: No database URL configured in environment or .env file.")
        return None

    try:
        import psycopg2
        kwargs = {}
        if cursor_factory:
            kwargs["cursor_factory"] = cursor_factory
        return psycopg2.connect(db_url, **kwargs)
    except ImportError:
        print("[!] Warning: psycopg2 not installed.")
        return None
    except Exception as e:
        info = get_db_info()
        print(f"[!] Error connecting to {info.get('provider')}: {e}")
        return None

if __name__ == "__main__":
    info = get_db_info()
    print("=================================================")
    print("📡 [DB CONFIG SSOT CHECK]")
    print(f"  • Provider: {info['provider']}")
    print(f"  • Host    : {info['host']}")
    print(f"  • Port    : {info['port']}")
    print(f"  • Database: {info['database']}")
    print(f"  • User    : {info['user']}")
    print(f"  • URL     : {info['masked_url']}")
    print("=================================================")
