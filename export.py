"""Export structured analysis data for AI agents"""

import json
import os
from datetime import datetime, timezone

from analyzer import generate_full_analysis
from database import get_dramas_at, get_latest_crawl_time, get_previous_crawl_time, init_db
from config import load_settings

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXPORT_PATH = os.path.join(SCRIPT_DIR, "analysis_data.json")


def export_analysis_data(crawl_time=None):
    """Export full analysis data as structured JSON for AI consumption"""
    init_db()
    settings = load_settings()

    if not crawl_time:
        crawl_time = get_latest_crawl_time()
    if not crawl_time:
        return None

    analysis = generate_full_analysis(crawl_time)
    if not analysis:
        return None

    export = {
        "metadata": {
            "crawl_time": crawl_time,
            "top_n": settings.get("top_n", 50),
            "export_time": datetime.now(timezone.utc).isoformat(),
        },
        "platforms": {},
        "theme_trends": analysis.get("theme_trends", {}),
    }

    for platform, data in analysis['platforms'].items():
        current = get_dramas_at(crawl_time, platform)
        prev_time = data.get('previous_time')

        current_clean = []
        for d in current:
            entry = {
                "rank": d["rank"],
                "drama_id": d["drama_id"],
                "title": d["title"],
                "description": d.get("description") or "",
                "theme": d.get("theme") or "",
                "episode_count": d.get("episode_count"),
                "collect_count": d.get("collect_count"),
                "read_count": d.get("read_count"),
                "like_count": d.get("like_count"),
                "score": d.get("score"),
            }
            try:
                entry["extra"] = json.loads(d.get("extra_json", "{}") or "{}")
            except:
                entry["extra"] = {}
            current_clean.append(entry)

        changes = data.get('changes', {})
        changes_clean = {}
        for change_type in ['new_entries', 'rank_surges', 'rank_drops', 'read_surges',
                            'collect_surges', 'exits']:
            items = changes.get(change_type, [])
            changes_clean[change_type] = [
                {
                    "rank": item.get("rank"),
                    "drama_id": item.get("drama_id"),
                    "title": item.get("title"),
                    "theme": item.get("theme", ""),
                    "prev_rank": item.get("prev_rank"),
                    "rank_change": item.get("rank_change"),
                    "read_change_pct": item.get("read_change_pct"),
                    "collect_change_pct": item.get("collect_change_pct"),
                }
                for item in items
            ]

        export["platforms"][platform] = {
            "current": current_clean,
            "changes": changes_clean,
            "previous_crawl_time": prev_time,
        }

    with open(EXPORT_PATH, 'w', encoding='utf-8') as f:
        json.dump(export, f, indent=2, ensure_ascii=False)

    return export


if __name__ == "__main__":
    data = export_analysis_data()
    if data:
        for platform, pdata in data["platforms"].items():
            n = len(pdata["current"])
            print(f"  {platform}: {n} dramas exported")
        print(f"✅ Exported to {EXPORT_PATH}")
    else:
        print("❌ No data to export. Run crawler first.")
