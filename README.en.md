<h1 align="center">📺 Short Drama Tracker</h1>

<p align="center">
  <strong>Automatically track trending short dramas across global platforms and discover viral hits</strong>
</p>

<p align="center">
  <b>🔧 Under active development — star to follow updates</b>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge" alt="MIT License"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10+-green.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+"></a>
</p>

<p align="center">
  <a href="README.md">中文</a> | <b>English</b>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> · <a href="#supported-platforms">Platforms</a> · <a href="#analysis">Analysis</a> · <a href="#notifications">Notifications</a>
</p>

---

## Why Short Drama Tracker?

The short drama market is exploding. ReelShort, DramaBox, ShortMax, and dozens of other platforms release new titles every week — but spotting viral trends means manually checking each platform, remembering yesterday's rankings, and comparing by memory.

**Short Drama Tracker automates all of this.** It crawls hot drama rankings, compares against history, and pushes **meaningful changes** to Feishu, Discord, or wherever your team hangs out.

### ✅ Things you might want to know

| | |
|---|---|
| 💰 **Completely free** | No API keys required. All data from public web pages |
| 🔄 **Fully automated** | Set a cron job and let it run — alerts only when something moves |
| 📡 **6 notification channels** | Discord, Telegram, Slack, Feishu, DingTalk, WeCom |
| 📊 **Analysis, not just lists** | Detects surges, new entries, view count spikes, genre trends |
| 💾 **Full history** | SQLite stores all snapshots — query any past date |
| 🔌 **Extensible** | Add a new platform by implementing one crawler function |

---

## Supported Platforms

| Platform | Status | Coverage | Approach | Region |
|----------|:------:|----------|----------|--------|
| 📺 **ReelShort** | ✅ Live | Top 100+ | SSR `__NEXT_DATA__` parse | 🌍 Global |
| 📺 **DramaBox** | ✅ Live | ~20+ titles | SSR `__NEXT_DATA__` parse | 🌍 Global |
| 📺 **ShortMax** | ✅ Live | ~100 titles | Playwright intercept + decrypt | 🌍 Global |
| 📺 **TopShort** | ✅ Live | 40+ titles | Public H5 API (tikshortsbox.com) | 🌍 Global |
| 📺 **HongGuo (红果)** | ✅ Live | 500+ titles | Playwright DOM scraping | 🇨🇳 China |
| 📺 **FlexTV** | ⛔ Unavailable | — | App-only, no web | 🌍 Global |
| 📺 **GoodShort** | ⛔ Unavailable | — | App-only, no web | 🌍 Global |

### Crawler Tech Details

| Platform | Method | Dependency | Notes |
|----------|--------|------------|-------|
| **ReelShort** | SSR parse | requests | Extracts `__NEXT_DATA__` JSON incl. score/views/likes |
| **DramaBox** | SSR parse | requests | Same; fields: viewCount/chapterCount/tags |
| **ShortMax** | Browser intercept | playwright | API response encrypted; hook `JSON.parse` to capture decrypted data |
| **TopShort** | Public API | requests | `tikshortsbox.com/h5/Home/{hot,bestSeller,trending}` — no auth needed |
| **HongGuo** | DOM scraping | playwright | Scroll-load 500+ titles, extract via DOM parsing |

> ⚠️ **ShortMax and HongGuo** require Playwright + Chromium:
> ```bash
> pip install playwright
> playwright install chromium
> ```

---

## Analysis

> ⚠️ **No analysis on the first run!** Change detection requires at least two crawls. The first run saves a baseline snapshot; full analysis starts from the second run onward.

| Signal | Description | Trigger |
|--------|-------------|---------|
| 🔥 **Rank Surge** | Drama climbed significantly | ≥10 positions up (configurable) |
| 🆕 **New Entry** | Not in last snapshot, now present | Per-crawl comparison |
| 📊 **View Spike** | View count grew sharply | ≥50% increase (configurable) |
| ❤️ **Collect Spike** | Collect count grew sharply | ≥30% increase (configurable) |
| 📉 **Rank Drop** | Drama fell significantly | ≥10 positions down |
| 🚪 **Fell Off** | Was in chart, now gone | Per-crawl comparison |
| 📂 **Genre Trend** | Genre rising or falling | 7-day window |

---

## Notifications

| Channel | Method | Difficulty |
|---------|--------|-----------|
| 🟣 **Discord** | Webhook | ⭐ Easiest |
| 🔵 **Telegram** | Bot API | ⭐⭐ |
| 🟠 **Slack** | Incoming Webhook | ⭐ |
| 🔷 **Feishu** | Custom Bot | ⭐⭐ |
| 🔷 **DingTalk** | Custom Bot + HMAC | ⭐⭐ |
| 🟢 **WeCom** | Group Bot | ⭐ |

> Run `python setup_wizard.py` for interactive step-by-step configuration.

---

## Quick Start

### 1. Install dependencies

```bash
pip install requests
# If using ShortMax or HongGuo:
pip install playwright && playwright install chromium
```

### 2. Configure notifications (optional)

```bash
python setup_wizard.py
```

### 3. Run

```bash
# Full pipeline: crawl → analyze → report → notify
python run.py

# Step by step
python run.py --crawl      # crawl only
python run.py --report     # generate report from latest data
python run.py --notify     # push latest report
```

### 4. Set up cron (recommended every 12h)

```bash
0 */12 * * * cd /path/to/drama-tracker && python3 run.py >> /var/log/drama-tracker.log 2>&1
```

---

## Sample Report

```
📊 Short Drama Report — 2026-02-27 09:00 UTC

📺 ReelShort
📈 Surged 3 | 📉 Dropped 2 | 🆕 New 5 | 🚪 Fell off 1

🔥 Rank Surges
  ⬆️+15 In the Palm of His Hand [Female]  #18→#3
  ⬆️+12 Dear Brother, You Loved Me Too Late  #21→#9

📊 View Count Spikes
  My Sister Is the Warlord Queen  +85.3%  (145.9M→270.4M)

🆕 New Entries
  #2 The Billionaire and the Baby Trap — 3.5M views
  #8 Tutoring my Rival Boy [LGBT] — 15.5M views

📂 Genre Trends
  📈 Female +3 titles (7→10)
  📉 Pregnancy -1 title (4→3)
```

---

## Architecture

```
drama-tracker/
├── config.py          → configuration
├── settings.json      → user settings (auto-generated)
├── platforms.py       → platform registry
├── crawler.py         → crawlers for each platform
├── database.py        → SQLite storage
├── analyzer.py        → change detection
├── report.py          → report formatting
├── notify.py          → multi-channel push
├── export.py          → AI analysis data export
├── setup_wizard.py    → interactive setup
└── run.py             → main entrypoint
```

Want to add a new platform? Implement a crawler in `crawler.py` and register it in `platforms.py`. New analysis signal? Edit `analyzer.py`. New notification channel? Edit `notify.py`.

---

## Configuration

Key settings in `settings.json`:

| Key | Description | Default |
|-----|-------------|---------|
| `platforms` | Which platforms to track | `["reelshort"]` |
| `top_n` | Track top N dramas | `50` |
| `rank_surge_threshold` | Min positions to count as a surge | `10` |
| `read_count_surge_pct` | View count growth % to flag as spike | `50` |
| `collect_surge_pct` | Collect count growth % to flag as spike | `30` |

---

## Roadmap

- [x] ReelShort crawler ✅
- [x] DramaBox crawler ✅
- [x] ShortMax crawler ✅ (Playwright intercept)
- [x] TopShort crawler ✅ (public H5 API)
- [x] HongGuo crawler ✅ (Playwright DOM, 500+ titles)
- [ ] FlexTV / GoodShort App API reverse engineering
- [ ] Multi-region tracking (different language versions)
- [ ] Weekly / monthly summary reports
- [ ] Custom watchlist (track specific dramas)
- [ ] Web Dashboard (optional)

---

## License

[MIT](LICENSE)
