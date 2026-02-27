"""Report generator for short drama rankings"""

import json
from datetime import datetime
from collections import Counter

from analyzer import generate_full_analysis
from database import get_dramas_at, get_latest_crawl_time
from config import REPORT_MAX_ITEMS
from platforms import get_platform_display


def _fmt_reads(n):
    """Format read count for display"""
    if not n:
        return "0"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def _fmt_change(change):
    if change > 0:
        return f"⬆️+{change}"
    elif change < 0:
        return f"⬇️{change}"
    return "→"


def _parse_theme(theme_str):
    """Parse theme JSON string to display"""
    if not theme_str:
        return ""
    try:
        themes = json.loads(theme_str)
        if isinstance(themes, list):
            return ", ".join(themes[:2])
    except:
        pass
    return theme_str


def _generate_first_crawl_report(analysis):
    """First crawl: snapshot overview"""
    lines = []
    lines.append("📸 **首次抓取快照**")
    lines.append("*尚无历史对比数据，以下为当前热门短剧概览。下次抓取后将生成完整变动分析。*")
    lines.append("")

    ct = analysis['crawl_time']

    for platform, data in analysis['platforms'].items():
        pname = get_platform_display(platform)
        dramas = get_dramas_at(ct, platform)
        if not dramas:
            continue

        lines.append(f"**📺 {pname}** ({len(dramas)}部)")
        lines.append("")

        # Top 10
        lines.append("🏆 **热度 Top 10**")
        for d in dramas[:10]:
            theme = _parse_theme(d.get('theme'))
            theme_tag = f" [{theme}]" if theme else ""
            reads = _fmt_reads(d.get('read_count'))
            lines.append(
                f"  #{d['rank']} **{d['title']}**{theme_tag}"
                f" — 播放 {reads} | 收藏 {_fmt_reads(d.get('collect_count'))}"
            )
        lines.append("")

        # Theme distribution
        theme_counter = Counter()
        for d in dramas:
            t = _parse_theme(d.get('theme'))
            if t:
                for tag in t.split(", "):
                    theme_counter[tag] += 1

        if theme_counter:
            top_themes = theme_counter.most_common(8)
            theme_str = " | ".join(f"{t}: {n}部" for t, n in top_themes)
            lines.append(f"📂 **题材分布**: {theme_str}")
            lines.append("")

        # Most collected
        by_collects = sorted(dramas, key=lambda x: x.get('collect_count') or 0, reverse=True)
        lines.append("❤️ **最多收藏**")
        for d in by_collects[:5]:
            lines.append(
                f"  **{d['title']}** — {_fmt_reads(d.get('collect_count'))}收藏"
                f" | 播放 {_fmt_reads(d.get('read_count'))}"
            )
        lines.append("")

    return "\n".join(lines)


def _generate_change_report(analysis):
    """With comparison data: focus on changes"""
    lines = []

    for platform, data in analysis['platforms'].items():
        pname = get_platform_display(platform)
        changes = data.get('changes', {})

        total_surges = len(changes.get('rank_surges', []))
        total_drops = len(changes.get('rank_drops', []))
        total_new = len(changes.get('new_entries', []))
        total_exits = len(changes.get('exits', []))

        lines.append(f"**📺 {pname}**")
        lines.append(
            f"📈 飙升 {total_surges} | 📉 下跌 {total_drops}"
            f" | 🆕 新上榜 {total_new} | 🚪 跌出 {total_exits}"
        )
        lines.append("")

        # Rank surges
        surges = changes.get('rank_surges', [])
        if surges:
            lines.append("**🔥 排名飙升**")
            for s in surges[:REPORT_MAX_ITEMS]:
                theme = _parse_theme(s.get('theme'))
                tag = f" [{theme}]" if theme else ""
                lines.append(
                    f"  {_fmt_change(s['rank_change'])} **{s['title']}**{tag}"
                    f" #{s['prev_rank']}→#{s['rank']}"
                )
            lines.append("")

        # Read count surges
        read_surges = changes.get('read_surges', [])
        if read_surges:
            lines.append("**📊 播放量飙升**")
            for r in read_surges[:6]:
                lines.append(
                    f"  **{r['title']}** +{r['read_change_pct']}%"
                    f" ({_fmt_reads(r.get('prev_read_count'))}→{_fmt_reads(r.get('read_count'))})"
                )
            lines.append("")

        # New entries
        new_entries = changes.get('new_entries', [])
        if new_entries:
            lines.append("**🆕 新上榜**")
            for n in new_entries[:6]:
                theme = _parse_theme(n.get('theme'))
                tag = f" [{theme}]" if theme else ""
                lines.append(
                    f"  #{n['rank']} **{n['title']}**{tag}"
                    f" — 播放 {_fmt_reads(n.get('read_count'))}"
                )
            remaining = len(new_entries) - 6
            if remaining > 0:
                lines.append(f"  ...及其他 {remaining} 部")
            lines.append("")

        # Drops
        drops = changes.get('rank_drops', [])
        if drops:
            lines.append("**📉 排名下跌**")
            for d in drops[:6]:
                lines.append(
                    f"  {_fmt_change(d['rank_change'])} **{d['title']}**"
                    f" #{d['prev_rank']}→#{d['rank']}"
                )
            lines.append("")

        # Theme trends
        theme_trends = analysis.get('theme_trends', {}).get(platform, [])
        rising = [t for t in theme_trends if t['change'] > 0]
        falling = [t for t in theme_trends if t['change'] < 0]
        if rising or falling:
            lines.append("**📂 题材趋势**")
            for t in rising[:3]:
                lines.append(
                    f"  📈 **{t['theme']}** +{t['change']}部"
                    f" ({t['previous_count']}→{t['current_count']})"
                )
            for t in falling[:2]:
                lines.append(
                    f"  📉 **{t['theme']}** {t['change']}部"
                    f" ({t['previous_count']}→{t['current_count']})"
                )
            lines.append("")

        if total_surges == 0 and total_drops == 0 and total_new == 0:
            lines.append("💤 本轮排行相对稳定，无显著变动。")
            lines.append("")

    return "\n".join(lines)


def generate_report(crawl_time=None):
    """Generate analysis-focused report"""
    analysis = generate_full_analysis(crawl_time)
    if not analysis:
        return "❌ 没有数据可分析。请先运行爬虫。"

    ct = analysis['crawl_time']
    try:
        dt = datetime.fromisoformat(ct.replace('Z', '+00:00'))
        time_str = dt.strftime("%Y-%m-%d %H:%M UTC")
    except:
        time_str = ct

    header = []
    header.append(f"📊 **短剧排行分析报告** — {time_str}")
    header.append("")

    has_comparison = False
    for platform, data in analysis['platforms'].items():
        if data.get('previous_time'):
            changes = data.get('changes', {})
            if (changes.get('rank_surges') or changes.get('rank_drops') or
                    changes.get('top_movers_up') or changes.get('top_movers_down')):
                has_comparison = True
                break

    if has_comparison:
        body = _generate_change_report(analysis)
    else:
        body = _generate_first_crawl_report(analysis)

    report = "\n".join(header) + body

    if len(report) > 1950:
        report = report[:1950] + "\n\n_(报告较长，完整版见 latest_report.txt)_"

    return report


if __name__ == "__main__":
    print(generate_report())
