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
# DramaBox Crawler
# ============================================================

def crawl_dramabox(top_n=None):
    """Crawl DramaBox hot dramas from web page __NEXT_DATA__

    DramaBox embeds data in Next.js page props at:
      __NEXT_DATA__.props.pageProps.bigList (banner/featured)
      __NEXT_DATA__.props.pageProps.smallData[].items (shelf items)

    Fields: bookId, bookName, introduction, viewCount, chapterCount,
            tags, typeOneNames, typeTwoNames, cover, viewCountDisplay
    Note: DramaBox doesn't expose score/collect_count/read_count directly,
          viewCount is the primary popularity metric.
    """
    top_n = top_n or TOP_N
    url = "https://www.dramaboxapp.com/"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"  ❌ Failed to fetch DramaBox: {e}")
        return []

    match = re.search(
        r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',
        resp.text, re.DOTALL
    )
    if not match:
        print("  ❌ No __NEXT_DATA__ found in DramaBox page")
        return []

    try:
        next_data = json.loads(match.group(1))
    except json.JSONDecodeError as e:
        print(f"  ❌ Failed to parse __NEXT_DATA__: {e}")
        return []

    try:
        props = next_data['props']['pageProps']
    except (KeyError, TypeError) as e:
        print(f"  ❌ Unexpected __NEXT_DATA__ structure: {e}")
        return []

    # Collect all unique dramas from bigList + smallData shelves
    seen_ids = set()
    all_dramas = []

    def _process_item(item, shelf_name=""):
        bid = str(item.get('bookId', ''))
        if not bid or bid in seen_ids:
            return
        seen_ids.add(bid)

        tags = item.get('tags', []) or []
        type2 = item.get('typeTwoNames', []) or []
        all_tags = tags + [t for t in type2 if t not in tags]
        theme_str = json.dumps(all_tags, ensure_ascii=False) if all_tags else None

        view_count = item.get('viewCount', 0) or 0

        all_dramas.append({
            'drama_id': bid,
            'title': item.get('bookName', ''),
            'description': (item.get('introduction', '') or '')[:500],
            'theme': theme_str,
            'episode_count': item.get('chapterCount', 0),
            'collect_count': None,  # DramaBox doesn't expose this
            'read_count': view_count,  # viewCount as read proxy
            'like_count': None,
            'score': view_count,  # Use viewCount as score for ranking
            'cover_url': item.get('cover', ''),
            'extra_json': json.dumps({
                'shelf_name': shelf_name,
                'type_one': item.get('typeOneNames', []),
                'type_two': type2,
                'tags': tags,
                'author': item.get('author', ''),
                'view_display': item.get('viewCountDisplay', ''),
                'last_update': item.get('lastUpdateTimeDisplay', ''),
            }, ensure_ascii=False),
        })

    # bigList (banner/featured)
    for item in props.get('bigList', []):
        _process_item(item, shelf_name="Featured")

    # smallData (shelves)
    for shelf in props.get('smallData', []):
        shelf_name = shelf.get('name', '')
        for item in shelf.get('items', []):
            _process_item(item, shelf_name=shelf_name)

    # Sort by viewCount descending, assign ranks
    all_dramas.sort(key=lambda x: (x.get('score') or 0), reverse=True)

    results = []
    for i, drama in enumerate(all_dramas[:top_n], 1):
        drama['rank'] = i
        results.append(drama)

    print(f"  📍 {len(results)} dramas (from {len(seen_ids)} unique)")
    return results


# ============================================================
# ShortMax Crawler (SPA — no SSR data available)
# ============================================================

def crawl_shortmax(top_n=None):
    """Crawl ShortMax hot dramas

    ⚠️ ShortMax is a pure SPA (Vite + React) with no server-side rendered data.
    The website loads all content via authenticated API calls from the client JS.
    No public API endpoints have been found.

    Possible future approaches:
    - Intercept mobile app API via mitmproxy
    - Use Playwright/browser automation to render and extract
    - Monitor their App Store/Google Play listing for ranking data
    """
    print("  ⚠️ ShortMax: pure SPA, no public API. Crawler not available.")
    return []


# ============================================================
# FlexTV Crawler (website unreachable)
# ============================================================

def crawl_flextv(top_n=None):
    """Crawl FlexTV hot dramas

    ⚠️ FlexTV website (flextv.co / flextvapp.com) is currently unreachable
    from most regions. The platform is primarily app-based.

    Possible future approaches:
    - Intercept mobile app API
    - Check if they have a web presence in specific regions
    """
    print("  ⚠️ FlexTV: website unreachable. Crawler not available.")
    return []


# ============================================================
# GoodShort Crawler (website unreachable)
# ============================================================

def crawl_goodshort(top_n=None):
    """Crawl GoodShort hot dramas

    ⚠️ GoodShort website is currently unreachable.
    The platform is primarily app-based.
    """
    print("  ⚠️ GoodShort: website unreachable. Crawler not available.")
    return []


# ============================================================
# TopShort Crawler (no data on website)
# ============================================================

def crawl_topshort(top_n=None):
    """Crawl TopShort hot dramas

    ⚠️ TopShort website is a static landing page with no drama data.
    All content is served through the mobile app only.
    """
    print("  ⚠️ TopShort: static landing page only. Crawler not available.")
    return []


# ============================================================
# 红果短剧 Crawler (requires auth / China-only API)
# ============================================================

def crawl_hongguo(top_n=None):
    """Crawl 红果短剧 (Hongguo) hot dramas

    ⚠️ 红果短剧 is a ByteDance/Fanqie product. The website is a pure SPA
    that loads data from internal APIs (fqnovel.com) which require:
    - China mainland network access
    - App-specific authentication tokens
    - Device fingerprinting

    The web version at hongguoduanju.com is primarily a download landing page
    with limited content.

    Possible future approaches:
    - Run from a China-based server with proper API tokens
    - Intercept mobile app API via mitmproxy
    - Use third-party data aggregation services
    """
    print("  ⚠️ 红果短剧: China-only API with auth required. Crawler not available.")
    return []


# ============================================================
# Main Crawl Orchestrator
# ============================================================

CRAWLERS = {
    "reelshort": crawl_reelshort,
    "dramabox": crawl_dramabox,
    "shortmax": crawl_shortmax,
    "flextv": crawl_flextv,
    "goodshort": crawl_goodshort,
    "topshort": crawl_topshort,
    "hongguo": crawl_hongguo,
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
