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
# ShortMax Crawler (Playwright — intercept decrypted API data)
# ============================================================

def crawl_shortmax(top_n=None):
    """Crawl ShortMax hot dramas via Playwright browser automation.

    ShortMax is a pure SPA with encrypted API responses. The web app
    decrypts data client-side. We use Playwright to:
    1. Open the site in a headless browser
    2. Hook JSON.parse to intercept the decrypted channelIndexPage response
    3. Extract film data from the decrypted JSON

    API: GET https://api.shortmax.app/2320/film/v2/channelIndexPage
    Auth: Auto-generated JWT from fastLogin (visitor mode, no account needed)
    Data: filmId, filmName, watchCount, coverImagePath, shortPlayCode
    """
    import asyncio

    top_n = top_n or TOP_N

    async def _crawl():
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            print("  ❌ ShortMax requires playwright: pip install playwright && playwright install chromium")
            return []

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox', '--disable-gpu',
                    '--disable-software-rasterizer',
                    '--disable-dev-shm-usage',
                    '--single-process',
                ],
            )
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) '
                           'AppleWebKit/605.1.15 (KHTML, like Gecko) '
                           'Version/17.0 Mobile/15E148 Safari/604.1'
            )
            page = await context.new_page()

            # Hook JSON.parse to capture decrypted channelIndexPage data
            await page.add_init_script("""
                const origParse = JSON.parse;
                window.__SHORTMAX_FILMS__ = null;
                JSON.parse = function(text) {
                    const result = origParse(text);
                    try {
                        if (result && result.data && result.data.records
                            && Array.isArray(result.data.records)
                            && result.data.records.length > 5) {
                            window.__SHORTMAX_FILMS__ = result;
                        }
                    } catch(e) {}
                    return result;
                };
            """)

            try:
                await page.goto('https://www.shortmax.app/',
                                timeout=30000, wait_until='networkidle')
            except Exception:
                pass
            await page.wait_for_timeout(6000)

            data = await page.evaluate('window.__SHORTMAX_FILMS__')
            await browser.close()
            return data

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                data = pool.submit(lambda: asyncio.run(_crawl())).result(timeout=60)
        else:
            data = loop.run_until_complete(_crawl())
    except RuntimeError:
        data = asyncio.run(_crawl())

    if not data:
        print("  ❌ ShortMax: failed to capture decrypted data")
        return []

    records = data.get('data', {}).get('records', [])
    if not records:
        print("  ❌ ShortMax: no sections in response")
        return []

    # Collect unique films across all sections
    seen_ids = set()
    all_dramas = []

    for section in records:
        section_title = section.get('title', '')
        for film in section.get('filmList', []):
            fid = str(film.get('filmId', ''))
            if not fid or fid in seen_ids:
                continue
            seen_ids.add(fid)

            watch_count = film.get('watchCount', 0) or 0

            all_dramas.append({
                'drama_id': fid,
                'title': film.get('filmName', ''),
                'description': '',
                'theme': json.dumps([section_title], ensure_ascii=False) if section_title else None,
                'episode_count': film.get('totalEpisodeQuantity', 0),
                'collect_count': None,
                'read_count': watch_count,
                'like_count': None,
                'score': watch_count,  # Use watchCount for ranking
                'cover_url': film.get('coverImagePath', ''),
                'extra_json': json.dumps({
                    'section': section_title,
                    'short_play_code': film.get('shortPlayCode', ''),
                }, ensure_ascii=False),
            })

    # Sort by watchCount descending
    all_dramas.sort(key=lambda x: (x.get('score') or 0), reverse=True)

    results = []
    for i, drama in enumerate(all_dramas[:top_n], 1):
        drama['rank'] = i
        results.append(drama)

    print(f"  📍 {len(results)} dramas (from {len(seen_ids)} unique across {len(records)} sections)")
    return results


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
# TopShort Crawler (public API)
# ============================================================

def crawl_topshort(top_n=None):
    """Crawl TopShort (TikShorts) hot dramas from public H5 API.

    TopShort's website at topshortapp.com loads data from a public API:
      https://api-ios.tikshortsbox.com/h5/Home/{hot|bestSeller|trending}

    No authentication required. Returns full drama metadata:
    vid, name, videoDetails, category_label, total_episode_number,
    videoHotNum, praiseCnt, publish_at, cover images.
    """
    top_n = top_n or TOP_N
    base = "https://api-ios.tikshortsbox.com/h5/Home"

    seen_ids = set()
    all_dramas = []

    for endpoint in ['hot', 'bestSeller', 'trending']:
        try:
            resp = requests.get(f"{base}/{endpoint}", headers=HEADERS, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"  ⚠️ TopShort/{endpoint}: {e}")
            continue

        films = data.get('data', {}).get('list', [])
        for film in films:
            vid = str(film.get('vid', ''))
            if not vid or vid in seen_ids:
                continue
            seen_ids.add(vid)

            hot_num = film.get('videoHotNum', 0) or 0
            praise_cnt = film.get('praiseCnt', 0) or 0
            categories = film.get('category_label', []) or []
            theme_str = json.dumps(categories, ensure_ascii=False) if categories else None

            all_dramas.append({
                'drama_id': vid,
                'title': film.get('name', ''),
                'description': (film.get('videoDetails', '') or '')[:500],
                'theme': theme_str,
                'episode_count': film.get('total_episode_number', 0),
                'collect_count': None,
                'read_count': hot_num,
                'like_count': praise_cnt,
                'score': hot_num,  # Use hotNum for ranking
                'cover_url': film.get('thumb', ''),
                'extra_json': json.dumps({
                    'source_endpoint': endpoint,
                    'publish_at': film.get('publish_at', ''),
                    'screen_mode': film.get('screen_mode', ''),
                    'free_episodes': film.get('free_cnum', 0),
                    'category_id': film.get('category_id', []),
                }, ensure_ascii=False),
            })

    # Sort by hotNum descending
    all_dramas.sort(key=lambda x: (x.get('score') or 0), reverse=True)

    results = []
    for i, drama in enumerate(all_dramas[:top_n], 1):
        drama['rank'] = i
        results.append(drama)

    print(f"  📍 {len(results)} dramas (from {len(seen_ids)} unique)")
    return results


# ============================================================
# 红果短剧 Crawler (Playwright — DOM extraction)
# ============================================================

def crawl_hongguo(top_n=None):
    """Crawl 红果短剧 (Hongguo) hot dramas via Playwright browser automation.

    红果短剧 is a ByteDance/Fanqie product. The website at hongguoduanju.com
    is a full SPA that renders 500+ dramas with titles, episode counts, tags,
    descriptions, and cover images. No API authentication is needed — all data
    is rendered in the DOM after the JS executes.

    We use Playwright to:
    1. Open https://www.hongguoduanju.com/ in headless browser
    2. Scroll down to trigger lazy loading
    3. Extract drama data from <a href="...?series_id=XXX"> elements

    Data fields: series_id, title, episode_count, tags (genre), description,
    cover image URL. Position on page is used as rank proxy (editorial ranking).
    """
    import asyncio

    top_n = top_n or TOP_N

    JS_EXTRACT = r"""
    () => {
        const items = [];
        const seen = new Set();
        const links = document.querySelectorAll('a[href*="series_id"]');

        const genreTags = new Set([
            '都市情感','女性成长','民国爱情','奇幻爱情','宫斗宅斗',
            '玄幻仙侠','都市日常','都市脑洞','家庭伦理','古风言情',
            '现代言情','古风权谋','都市玄幻','萌宝','种田经营',
            '奇幻脑洞','年代爱情','现言甜宠','战神归来','历史古代',
            '悬疑情感','剧情','东方玄幻','热血逆袭'
        ]);

        for (const a of links) {
            const href = a.href || '';
            const match = href.match(/series_id=(\d+)/);
            if (!match) continue;
            const seriesId = match[1];
            if (seen.has(seriesId)) continue;
            seen.add(seriesId);

            const text = a.innerText.trim();
            const img = a.querySelector('img');
            const imgSrc = img ? img.src : '';
            const lines = text.split('\n').map(l => l.trim()).filter(l => l);

            let episodes = 0;
            let title = '';
            let tags = [];
            let description = '';

            for (const line of lines) {
                const epMatch = line.match(/全(\d+)集/);
                if (epMatch) {
                    episodes = parseInt(epMatch[1]);
                } else if (line.length > 50) {
                    description = line;
                } else if (!title && line.length > 1 && !genreTags.has(line)) {
                    title = line;
                } else if (line.length > 1) {
                    tags.push(line);
                }
            }

            if (seriesId && (title || tags.length > 0)) {
                items.push({
                    series_id: seriesId,
                    title: title,
                    episodes: episodes,
                    tags: tags,
                    description: description.substring(0, 500),
                    cover: imgSrc,
                });
            }
        }
        return items;
    }
    """

    async def _crawl():
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            print("  ❌ 红果短剧 requires playwright: pip install playwright && playwright install chromium")
            return []

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox', '--disable-gpu',
                    '--disable-software-rasterizer',
                    '--disable-dev-shm-usage',
                    '--single-process',
                ],
            )
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) '
                           'AppleWebKit/605.1.15 (KHTML, like Gecko) '
                           'Version/17.0 Mobile/15E148 Safari/604.1'
            )
            page = await context.new_page()

            try:
                await page.goto('https://www.hongguoduanju.com/',
                                timeout=30000, wait_until='networkidle')
            except Exception:
                pass
            await page.wait_for_timeout(5000)

            # Scroll to trigger lazy loading
            for _ in range(8):
                await page.evaluate('window.scrollBy(0, 1000)')
                await page.wait_for_timeout(800)

            data = await page.evaluate(JS_EXTRACT)
            await browser.close()
            return data

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                data = pool.submit(lambda: asyncio.run(_crawl())).result(timeout=90)
        else:
            data = loop.run_until_complete(_crawl())
    except RuntimeError:
        data = asyncio.run(_crawl())

    if not data:
        print("  ❌ 红果短剧: failed to extract data from page")
        return []

    # Filter: only items with a real title (skip banner/genre-only items)
    valid = [d for d in data if d.get('title') and d.get('episodes', 0) > 0]

    all_dramas = []
    for rank, item in enumerate(valid, 1):
        tags = item.get('tags', [])
        theme_str = json.dumps(tags, ensure_ascii=False) if tags else None

        all_dramas.append({
            'drama_id': item['series_id'],
            'title': item['title'],
            'description': item.get('description', ''),
            'theme': theme_str,
            'episode_count': item.get('episodes', 0),
            'collect_count': None,
            'read_count': None,
            'like_count': None,
            'score': len(valid) - rank + 1,  # Position-based score (higher = earlier on page)
            'rank': rank,
            'cover_url': item.get('cover', ''),
            'extra_json': json.dumps({
                'source': 'hongguoduanju.com',
                'position_rank': rank,
            }, ensure_ascii=False),
        })

    results = all_dramas[:top_n]
    print(f"  📍 {len(results)} dramas (from {len(valid)} valid, {len(data)} total on page)")
    return results


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
