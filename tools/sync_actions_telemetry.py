#!/usr/bin/env python3
"""
tools/sync_actions_telemetry.py
================================
Syncs GitHub Actions run logs and monthly runner quota into Neon PostgreSQL.
Can be executed in GitHub Actions workflows (using GITHUB_TOKEN / gh CLI) or locally.
"""

import os
import sys
import json
import datetime
import subprocess
import urllib.request

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from tools.db_bridge import load_env_db_url
import psycopg2

def fetch_runs_from_github():
    """Fetches recent workflow runs via gh CLI or GitHub REST API."""
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY", "AnnyeongHae/ai-factcheck-portfolio")
    
    # 1. Try gh CLI
    try:
        cmd = ["gh", "api", f"/repos/{repo}/actions/runs?per_page=35"]
        out = subprocess.check_output(cmd, encoding="utf-8", errors="replace", timeout=12)
        data = json.loads(out)
        return data.get("workflow_runs", [])
    except Exception:
        pass

    # 2. Try urllib with token
    if token:
        try:
            url = f"https://api.github.com/repos/{repo}/actions/runs?per_page=35"
            req = urllib.request.Request(url, headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "FactCheckHub-TelemetrySync"
            })
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("workflow_runs", [])
        except Exception as e:
            print(f"[!] Warning: GitHub REST API failed: {e}")

    return []

def ensure_tables_exist(cur):
    """Ensures telemetry tables exist in Neon DB."""
    cur.execute("""
    CREATE TABLE IF NOT EXISTS github_actions_monthly_usage (
        year_month VARCHAR(7) PRIMARY KEY, -- '2026-09'
        total_minutes NUMERIC(8, 2) NOT NULL DEFAULT 0,
        total_job_runs INTEGER NOT NULL DEFAULT 0,
        deploy_pages_minutes NUMERIC(8, 2) DEFAULT 0,
        deploy_pages_runs INTEGER DEFAULT 0,
        deploy_pages_avg_sec INTEGER DEFAULT 241,
        deploy_pages_failure_rate NUMERIC(5, 2) DEFAULT 10.0,
        pages_build_minutes NUMERIC(8, 2) DEFAULT 0,
        pages_build_runs INTEGER DEFAULT 0,
        deploy_only_minutes NUMERIC(8, 2) DEFAULT 0,
        daily_eod_minutes NUMERIC(8, 2) DEFAULT 0,
        quota_limit_minutes INTEGER DEFAULT 2000,
        remaining_minutes NUMERIC(8, 2) DEFAULT 758.0,
        burn_rate_percent NUMERIC(5, 2) DEFAULT 62.1,
        alert_level VARCHAR(20) DEFAULT 'WARNING',
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS github_actions_run_logs (
        run_id BIGINT PRIMARY KEY,
        workflow_name VARCHAR(100) NOT NULL,
        event_trigger VARCHAR(50) NOT NULL,
        status VARCHAR(30) NOT NULL,
        conclusion VARCHAR(30),
        duration_seconds INTEGER NOT NULL,
        duration_str VARCHAR(30),
        started_at TIMESTAMP WITH TIME ZONE NOT NULL,
        completed_at TIMESTAMP WITH TIME ZONE,
        timeline_slot VARCHAR(20),
        error_count INTEGER DEFAULT 0,
        error_details TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """)

def sync_telemetry():
    db_url = load_env_db_url()
    if not db_url:
        print("[!] Note: No Neon DB URL found. Skipping telemetry sync.")
        return False

    runs = fetch_runs_from_github()
    if not runs:
        print("[!] Warning: Could not fetch runs from GitHub Actions API.")
        return False

    conn = psycopg2.connect(db_url)
    with conn.cursor() as cur:
        ensure_tables_exist(cur)
        
        kst_tz = datetime.timezone(datetime.timedelta(hours=9))
        inserted_runs = 0
        
        for r in runs:
            rid = r.get("id")
            name = r.get("name", "")
            event = r.get("event", "")
            status = r.get("status", "")
            conclusion = r.get("conclusion") or status
            created_str = r.get("created_at")
            updated_str = r.get("updated_at")
            if not created_str or not updated_str:
                continue
                
            created = datetime.datetime.fromisoformat(created_str.replace("Z", "+00:00"))
            updated = datetime.datetime.fromisoformat(updated_str.replace("Z", "+00:00"))
            dur_sec = max(1, int((updated - created).total_seconds()))
            dur_str = f"{dur_sec // 60}분 {dur_sec % 60}초"
            
            # Determine timeline slot based on KST start hour
            kst_created = created.astimezone(kst_tz)
            h = kst_created.hour
            if "Daily 23:30" in name or (h == 23 and kst_created.minute >= 25):
                slot = "23:30"
            elif 0 <= h < 6:
                slot = "00:17"
            elif 6 <= h < 12:
                slot = "06:17"
            elif 12 <= h < 18:
                slot = "12:17"
            else:
                slot = "18:17"
                
            err_cnt = 1 if conclusion in ["failure", "timed_out"] else 0
            
            cur.execute("""
                INSERT INTO github_actions_run_logs (
                    run_id, workflow_name, event_trigger, status, conclusion,
                    duration_seconds, duration_str, started_at, completed_at,
                    timeline_slot, error_count
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (run_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    conclusion = EXCLUDED.conclusion,
                    duration_seconds = EXCLUDED.duration_seconds,
                    duration_str = EXCLUDED.duration_str,
                    completed_at = EXCLUDED.completed_at,
                    error_count = EXCLUDED.error_count;
            """, (rid, name, event, status, conclusion, dur_sec, dur_str, created, updated, slot, err_cnt))
            inserted_runs += 1

        # Calculate live monthly quota
        # Baseline measured from GitHub Billing: 1,242.0 min at 2026-09-07T17:32:00Z
        base_time = datetime.datetime(2026, 9, 7, 17, 32, 0, tzinfo=datetime.timezone.utc)
        cur.execute("""
            SELECT COALESCE(SUM(duration_seconds), 0)
            FROM github_actions_run_logs
            WHERE started_at > %s;
        """, (base_time,))
        delta_sec = cur.fetchone()[0]
        delta_min = round(float(delta_sec) / 60.0, 1)
        
        total_used = round(1242.0 + delta_min, 1)
        remaining = max(0.0, round(2000.0 - total_used, 1))
        burn_rate = round((total_used / 2000.0) * 100.0, 1)
        alert = "CRITICAL_HIGH" if burn_rate >= 75 else ("WARNING" if burn_rate >= 50 else "SAFE")
        
        cur.execute("""
            UPDATE github_actions_monthly_usage
            SET total_minutes = %s,
                remaining_minutes = %s,
                burn_rate_percent = %s,
                alert_level = %s,
                total_job_runs = (SELECT COUNT(*) FROM github_actions_run_logs),
                updated_at = CURRENT_TIMESTAMP
            WHERE year_month = '2026-09';
        """, (total_used, remaining, burn_rate, alert))
        
        conn.commit()
        print(f"[+] Successfully synced {inserted_runs} runs to Neon DB!")
        print(f"[+] Monthly Actions Quota: {total_used}m used / {remaining}m remaining ({burn_rate}%, {alert})")

    conn.close()
    return True

if __name__ == "__main__":
    sync_telemetry()
