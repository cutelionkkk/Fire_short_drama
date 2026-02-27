"""Crawlers for short drama platforms"""

import json
import os
import re
import time
import traceback
from datetime import datetime, timezone

import requests

from config import TOP_N, load_settings
from database import insert_dramas, log_crawl, init_db
from platforms import PLATFORMS, get_platform_display

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}


# ============================================================
# ReelShort Crawler
# ============================================================

def crawl_reelshort(top_n=None):
    """Crawl ReelShort hot dramas from web page __NEXT_DATA__

    ReelShort embeds its full catalog in the Next.js page props at:
      __NEXT_DATA__.props.pageProps.fallback["/api/video/hall/info"]
    which contains bookShelfList → each shelf has books with full metadata.
    """
    top_n = top_n or TOP_N
    url = "https://www.reelshort.com/"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"  ❌ Failed to fetch ReelShort: {e}")
        return []

    # Extract __NEXT_DATA__
    match = re.search(
        r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',
        resp.text, re.DOTALL
    )
    if not match:
        print("  ❌ No __NEXT_DATA__ found in ReelShort page")
        return []

    try:
        next_data = json.loads(match.group(1))
    except json.JSONDecodeError as e:
        print(f"  ❌ Failed to parse __NEXT_DATA__: {e}")
        return []

    # Navigate to the API data
    try:
        fallback = next_data['props']['pageProps']['fallback']
        api_data = fallback.get('/api/video/hall/info', {})
    except (KeyError, TypeError) as e:
        print(f"  ❌ Unexpected __NEXT_DATA__ structure: {e}")
        return []

    shelves = api_data.get('bookShelfList', [])
    if not shelves:
        print("  ❌ No bookShelfList found")
        return []

    # Collect all unique dramas from all shelves
    seen_ids = set()
    all_dramas = []

    for shelf in shelves:
        books = shelf.get('books', [])
        for book in books:
            book_id = book.get('book_id') or book.get('t_book_id', '')
            if not book_id or book_id in seen_ids:
                continue
            seen_ids.add(book_id)

            # Calculate total likes across episodes
            total_likes = 0
            chapter_base = book.get('chapter_base', [])
            for ch in chapter_base:
                total_likes += (ch.get('like_count', 0) or 0)

            theme_list = book.get('theme', [])
            theme_str = json.dumps(theme_list, ensure_ascii=False) if theme_list else None

            all_dramas.append({
                'drama_id': book_id,
                'title': book.get('book_title', ''),
                'description': book.get('special_desc', ''),
                'theme': theme_str,
                'episode_count': book.get('chapter_count', 0),
                'collect_count': book.get('collect_count', 0),
                'read_count': book.get('read_count', 0),
                'like_count': total_likes,
                'score': book.get('score', 0),
                'cover_url': book.get('book_pic', ''),
                'extra_json': json.dumps({
                    'book_type': book.get('book_type'),
                    'share_text': book.get('share_text', ''),
                    'shelf_name': shelf.get('bookshelf_name', ''),
                    'paid_start': book.get('paid_start'),
                    'init_collect_count': book.get('init_collect_count', 0),
                }, ensure_ascii=False),
            })

    # Sort by score descending, assign ranks
    all_dramas.sort(key=lambda x: (x.get('score') or 0), reverse=True)

    results = []
    for i, drama in enumerate(all_dramas[:top_n], 1):
        drama['rank'] = i
        results.append(drama)

    print(f"  📍 {len(results)} dramas (from {len(seen_ids)} unique across {len(shelves)} shelves)")
    return results


# ============================================================
# DramaBox Crawler (TODO)
# ============================================================

def crawl_dramabox(top_n=None):
    """Crawl DramaBox hot dramas

    TODO: DramaBox website is SPA, need to find API endpoint.
    Possible approaches:
    - Reverse engineer mobile app API
    - Use Playwright to render the page
    - Find RSS/sitemap
    """
    print("  ⚠️ DramaBox crawler not yet implemented")
    return []


# ============================================================
# Main Crawl Orchestrator
# ============================================================

CRAWLERS = {
    "reelshort": crawl_reelshort,
    "dramabox": crawl_dramabox,
}


def run_full_crawl():
    """Run a full crawl of all configured platforms"""
    init_db()
    settings = load_settings()
    crawl_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    platforms = settings.get("platforms", ["reelshort"])
    top_n = settings.get("top_n", TOP_N)

    print(f"\n🕐 Crawl started at {crawl_time}")
    print(f"📋 Platforms: {', '.join(platforms)}")
    print("=" * 50)

    total = 0
    errors = []

    for platform in platforms:
        crawler = CRAWLERS.get(platform)
        if not crawler:
            print(f"\n❌ Unknown platform: {platform}")
            errors.append(f"{platform}: unknown")
            continue

        display = get_platform_display(platform)
        print(f"\n📺 {display}")

        t0 = time.time()
        try:
            items = crawler(top_n)
            dt = time.time() - t0

            if items:
                n = insert_dramas(crawl_time, platform, items)
                log_crawl(crawl_time, platform, n, 'ok', duration=dt)
                print(f"  ✅ {n} dramas saved ({dt:.1f}s)")
                total += n
            else:
                log_crawl(crawl_time, platform, 0, 'error', 'No results', duration=dt)
                errors.append(f"{display}: no results")
                print(f"  ⚠️ No results")
        except Exception as e:
            dt = time.time() - t0
            log_crawl(crawl_time, platform, 0, 'error', str(e), duration=dt)
            errors.append(f"{display}: {e}")
            print(f"  ❌ {e}")
            traceback.print_exc()

    print(f"\n{'=' * 50}")
    print(f"📊 Done: {total} total entries across {len(platforms)} platforms")
    if errors:
        print(f"⚠️ {len(errors)} errors:")
        for e in errors:
            print(f"   - {e}")

    return crawl_time, total, errors


if __name__ == "__main__":
    run_full_crawl()
