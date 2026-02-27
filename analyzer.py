"""Analyzer for short drama ranking changes and trends"""

import json
from datetime import datetime, timedelta, timezone
from collections import defaultdict

from database import (
    get_dramas_at, get_previous_crawl_time, get_latest_crawl_time,
    get_drama_history, get_theme_stats, get_all_crawl_times,
    get_all_platforms_at
)
from config import RANK_SURGE_THRESHOLD, READ_COUNT_SURGE_PCT, COLLECT_SURGE_PCT, REPORT_MAX_ITEMS


def analyze_platform_changes(platform, current_time, previous_time):
    """Compare two crawls and find changes"""
    current = get_dramas_at(current_time, platform)
    previous = get_dramas_at(previous_time, platform) if previous_time else []

    prev_map = {d['drama_id']: d for d in previous}
    curr_map = {d['drama_id']: d for d in current}

    changes = {
        'new_entries': [],
        'rank_surges': [],
        'rank_drops': [],
        'read_surges': [],
        'collect_surges': [],
        'exits': [],
        'top_movers_up': [],
        'top_movers_down': [],
    }

    for drama in current:
        did = drama['drama_id']
        if did not in prev_map:
            # New entry
            changes['new_entries'].append(drama)
        else:
            prev = prev_map[did]
            prev_rank = prev['rank']
            curr_rank = drama['rank']
            rank_diff = prev_rank - curr_rank  # positive = moved up

            # Rank surge
            if rank_diff >= RANK_SURGE_THRESHOLD:
                changes['rank_surges'].append({
                    **drama, 'prev_rank': prev_rank, 'rank_change': rank_diff
                })
            elif rank_diff <= -RANK_SURGE_THRESHOLD:
                changes['rank_drops'].append({
                    **drama, 'prev_rank': prev_rank, 'rank_change': rank_diff
                })

            if rank_diff > 0:
                changes['top_movers_up'].append({
                    **drama, 'prev_rank': prev_rank, 'rank_change': rank_diff
                })
            elif rank_diff < 0:
                changes['top_movers_down'].append({
                    **drama, 'prev_rank': prev_rank, 'rank_change': rank_diff
                })

            # Read count surge
            prev_reads = prev.get('read_count') or 0
            curr_reads = drama.get('read_count') or 0
            if prev_reads > 0:
                read_pct = ((curr_reads - prev_reads) / prev_reads) * 100
                if read_pct >= READ_COUNT_SURGE_PCT:
                    changes['read_surges'].append({
                        **drama,
                        'prev_read_count': prev_reads,
                        'read_change_pct': round(read_pct, 1),
                    })

            # Collect count surge
            prev_collects = prev.get('collect_count') or 0
            curr_collects = drama.get('collect_count') or 0
            if prev_collects > 0:
                collect_pct = ((curr_collects - prev_collects) / prev_collects) * 100
                if collect_pct >= COLLECT_SURGE_PCT:
                    changes['collect_surges'].append({
                        **drama,
                        'prev_collect_count': prev_collects,
                        'collect_change_pct': round(collect_pct, 1),
                    })

    # Exits: was in previous, not in current
    for did, drama in prev_map.items():
        if did not in curr_map:
            changes['exits'].append(drama)

    # Sort
    changes['rank_surges'].sort(key=lambda x: x['rank_change'], reverse=True)
    changes['rank_drops'].sort(key=lambda x: x['rank_change'])
    changes['read_surges'].sort(key=lambda x: x['read_change_pct'], reverse=True)
    changes['collect_surges'].sort(key=lambda x: x['collect_change_pct'], reverse=True)
    changes['new_entries'].sort(key=lambda x: x['rank'])
    changes['top_movers_up'].sort(key=lambda x: x['rank_change'], reverse=True)
    changes['top_movers_down'].sort(key=lambda x: x['rank_change'])

    return changes


def analyze_theme_trends(platform, days=7):
    """Analyze theme distribution trends over time"""
    crawl_times = get_all_crawl_times(days=days)
    if len(crawl_times) < 2:
        return []

    latest = crawl_times[-1]
    earliest = crawl_times[0]

    latest_themes = get_theme_stats(platform, latest)
    earliest_themes = get_theme_stats(platform, earliest)

    latest_map = {t['theme']: t for t in latest_themes}
    earliest_map = {t['theme']: t for t in earliest_themes}

    all_themes = set(list(latest_map.keys()) + list(earliest_map.keys()))
    trends = []

    for theme in all_themes:
        if not theme:
            continue
        now_count = latest_map.get(theme, {}).get('count', 0)
        then_count = earliest_map.get(theme, {}).get('count', 0)
        diff = now_count - then_count
        trends.append({
            'theme': theme,
            'current_count': now_count,
            'previous_count': then_count,
            'change': diff,
            'avg_rank': latest_map.get(theme, {}).get('avg_rank'),
        })

    trends.sort(key=lambda x: x['change'], reverse=True)
    return trends


def generate_full_analysis(crawl_time=None):
    """Generate complete analysis for all platforms"""
    if not crawl_time:
        crawl_time = get_latest_crawl_time()
    if not crawl_time:
        return None

    platforms = get_all_platforms_at(crawl_time)
    analysis = {
        'crawl_time': crawl_time,
        'platforms': {},
        'theme_trends': {},
    }

    for platform in platforms:
        prev_time = get_previous_crawl_time(crawl_time, platform)
        changes = analyze_platform_changes(platform, crawl_time, prev_time)
        analysis['platforms'][platform] = {
            'changes': changes,
            'previous_time': prev_time,
        }

        theme_trends = analyze_theme_trends(platform)
        analysis['theme_trends'][platform] = theme_trends

    return analysis


if __name__ == "__main__":
    analysis = generate_full_analysis()
    if analysis:
        print(f"Analysis for crawl at {analysis['crawl_time']}")
        for platform, data in analysis['platforms'].items():
            changes = data['changes']
            print(f"\n--- {platform} ---")
            print(f"  New entries: {len(changes['new_entries'])}")
            print(f"  Rank surges: {len(changes['rank_surges'])}")
            print(f"  Rank drops: {len(changes['rank_drops'])}")
            print(f"  Exits: {len(changes['exits'])}")
    else:
        print("No data to analyze. Run crawler first.")
