<h1 align="center">📺 Short Drama Tracker</h1>

<p align="center">
  <strong>自动追踪国内外短剧平台热门内容，发现爆款短剧</strong>
</p>

<p align="center">
  <b>🔧 项目调优中 — 功能持续完善，欢迎 Star 关注更新</b>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge" alt="MIT License"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10+-green.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+"></a>
</p>

<p align="center">
  <a href="#快速上手">快速开始</a> · <a href="#支持的平台">支持平台</a> · <a href="#分析能力">分析能力</a> · <a href="#通知渠道">通知渠道</a> · <a href="#ai-分析">AI 分析</a>
</p>

---

## 为什么需要 Short Drama Tracker？

短剧赛道火爆，ReelShort、DramaBox、红果短剧等平台上每周上新几十部——但要发现爆款趋势，你得：

- 📊 "哪部剧最近播放量暴涨？" → **手动翻平台**，一个个点进去看
- 🆕 "最近有什么新剧上热门了？" → **得记住昨天的排名**，人脑对比
- 📉 "哪些题材在走下坡路？" → **凭感觉判断**，容易误判
- 🔔 "竞品出爆款了我想第一时间知道" → **没有自动提醒**，全靠刷
- 📱 "国内外平台都想看" → **平台分散**，数据格式不统一

**Short Drama Tracker 帮你自动搞定这些。** 定时抓取各平台热门短剧数据，对比历史变动，把**值得关注的变化**推送到飞书、Discord 或任何你常用的工具。

> ⭐ **Star 这个项目**——排行榜数据的价值在于长期积累，越早开始追踪越好。

### ✅ 在你用之前，你可能想知道

| | |
|---|---|
| 💰 **完全免费** | 不需要任何 API Key，数据来源全部是公开网页 |
| 🔄 **全自动运行** | 设置好定时任务后就不用管了，有变动自动推送 |
| 📡 **6 个通知渠道** | Discord、Telegram、Slack、飞书、钉钉、企业微信 |
| 📊 **不只是列表** | 分析变动：热度飙升、新上榜、播放量暴涨、题材趋势 |
| 💾 **历史可追溯** | SQLite 存储所有历史数据，随时可以回溯 |
| 🔌 **可扩展** | 新增平台只需实现一个爬虫函数 |

---

## 支持的平台

| 平台 | 状态 | 数据量 | 数据来源 | 覆盖地区 |
|------|:----:|--------|---------|---------|
| 📺 **ReelShort** | ✅ 可用 | 热门 Top 50+ | 网页 API (Next.js SSR) | 🌍 全球 |
| 📺 **DramaBox** | 🚧 开发中 | — | — | 🌍 全球 |
| 📺 **ShortMax** | 📋 计划中 | — | — | 🌍 全球 |
| 📺 **FlexTV** | 📋 计划中 | — | — | 🌍 全球 |
| 📺 **红果短剧** | 📋 计划中 | — | — | 🇨🇳 中国 |
| 📺 **河马剧场** | 📋 计划中 | — | — | 🇨🇳 中国 |

> **想支持新平台？** 在 `crawler.py` 里实现一个爬虫函数，在 `platforms.py` 里注册即可。

---

## 分析能力

> ⚠️ **重要提示：第一次抓取不会有分析结果！**
>
> 变动分析（热度飙升、新上榜、播放量暴涨等）需要**至少两次抓取数据**进行对比。第一次运行只会保存当前快照，**从第二次运行开始**才会生成完整的变动分析报告。建议设置定时任务（每 12 小时一次），第二次运行后即可看到完整分析。

| 分析维度 | 说明 | 触发条件 |
|---------|------|---------|
| 🔥 **排名飙升** | 热度排名大幅上升 | 排名上升 ≥10 名（可配置） |
| 🆕 **新上榜** | 上次不在榜、这次出现 | 对比前后两次抓取 |
| 📊 **播放量暴涨** | 播放量增长百分比突出 | 增长 ≥50%（可配置） |
| ❤️ **收藏飙升** | 收藏数增长百分比突出 | 增长 ≥30%（可配置） |
| 📉 **排名下跌** | 热度排名大幅下降 | 排名下降 ≥10 名 |
| 🚪 **跌出排行** | 上次在榜、这次没了 | 对比前后两次抓取 |
| 📂 **题材趋势** | 哪些题材在上升/下降 | 7 天窗口内的题材分布变化 |

---

## 通知渠道

| 渠道 | 推送方式 | 配置难度 |
|------|---------|---------|
| 🟣 **Discord** | Webhook | ⭐ 最简单 |
| 🔵 **Telegram** | Bot API | ⭐⭐ |
| 🟠 **Slack** | Incoming Webhook | ⭐ |
| 🔷 **飞书 (Feishu)** | 自定义机器人 | ⭐⭐ |
| 🔷 **钉钉 (DingTalk)** | 自定义机器人 + 加签 | ⭐⭐ |
| 🟢 **企业微信 (WeCom)** | 群机器人 | ⭐ |

> **不知道怎么配？** 运行 `python setup_wizard.py`，交互式引导完成。

---

## 快速上手

### 1. 安装依赖

```bash
pip install requests
```

### 2. 配置通知渠道（可选）

```bash
python setup_wizard.py
```

### 3. 运行

```bash
# 完整流程：抓取 → 分析 → 生成报告 → 推送通知
python run.py

# 也可以分步执行
python run.py --crawl      # 仅抓取数据
python run.py --report     # 从最新数据生成报告
python run.py --notify     # 推送最新报告到已配置渠道
```

### 4. 设置定时任务（推荐每 12 小时）

```bash
# Linux crontab
0 */12 * * * cd /path/to/drama-tracker && python3 run.py >> /var/log/drama-tracker.log 2>&1
```

---

## AI Agent 一键安装

复制这句话给你的 AI Agent：

```
帮我安装 Short Drama Tracker：克隆仓库后运行 pip install requests && python run.py
```

---

## 报告示例

```
📊 短剧排行分析报告 — 2026-02-27 09:00 UTC

📺 ReelShort
📈 飙升 3 | 📉 下跌 2 | 🆕 新上榜 5 | 🚪 跌出 1

🔥 排名飙升
  ⬆️+15 In the Palm of His Hand [Female] #18→#3
  ⬆️+12 Dear Brother, You Loved Me Too Late [Female] #21→#9

📊 播放量飙升
  My Sister Is the Warlord Queen +85.3% (145.9M→270.4M)

🆕 新上榜
  #2 The Billionaire and the Baby Trap — 播放 3.5M
  #8 Tutoring my Rival Boy [LGBT] — 播放 15.5M

📂 题材趋势
  📈 Female +3部 (7→10)
  📈 Young Adult +2部 (3→5)
  📉 Pregnancy -1部 (4→3)
```

---

## AI 分析能力

### 导出数据给 AI

```bash
python run.py --export-analysis
# 生成 analysis_data.json
```

### 分析思路

| 方向 | 适用场景 |
|------|---------|
| **爆款预测** | 哪些新剧有爆款潜质？播放量增长曲线、收藏转化率 |
| **题材分析** | 哪类题材最受欢迎？甜宠 vs 复仇 vs 悬疑的市场表现 |
| **竞品监控** | 特定制作公司的作品表现追踪 |
| **市场趋势** | 短剧市场整体热度变化，新平台崛起信号 |

---

## 配置说明

### settings.json

```json
{
  "platforms": ["reelshort"],
  "top_n": 50,
  "rank_surge_threshold": 10,
  "read_count_surge_pct": 50,
  "collect_surge_pct": 30,
  "report_max_items": 10,
  "report_language": "zh",
  "notify_channels": ["discord"],
  "channel_config": {
    "discord": {
      "webhook_url": "https://discord.com/api/webhooks/..."
    }
  }
}
```

| 配置项 | 说明 | 默认值 |
|-------|------|-------|
| `platforms` | 追踪哪些平台 | `["reelshort"]` |
| `top_n` | 追踪前多少名 | `50` |
| `rank_surge_threshold` | 排名变动多少算"飙升" | `10` |
| `read_count_surge_pct` | 播放量增长多少算"暴涨" | `50%` |
| `collect_surge_pct` | 收藏增长多少算"飙升" | `30%` |

---

## 模块化架构

```
drama-tracker/
├── config.py          → 配置管理
├── settings.json      → 用户配置 (自动生成)
├── platforms.py       → 平台定义
├── crawler.py         → 数据抓取 (各平台爬虫)
├── database.py        → SQLite 数据存储
├── analyzer.py        → 变动分析
├── report.py          → 报告生成
├── notify.py          → 多渠道推送
├── export.py          → AI 分析数据导出
├── setup_wizard.py    → 配置向导
└── run.py             → 主入口
```

想加新平台？改 `crawler.py` 和 `platforms.py`。想加新分析维度？改 `analyzer.py`。想换通知渠道？改 `notify.py`。

---

## 常见问题

<details>
<summary><strong>ReelShort 抓不到数据？</strong></summary>

ReelShort 数据是从网页的 `__NEXT_DATA__` JSON 中提取的。如果网站改版导致结构变化，需要更新 `crawler.py` 中的解析逻辑。服务器在国内的话，可能需要配置代理。

</details>

<details>
<summary><strong>怎么添加新平台？</strong></summary>

1. 在 `platforms.py` 的 `PLATFORMS` dict 中注册平台信息
2. 在 `crawler.py` 中实现 `crawl_xxx()` 函数，返回标准格式的 drama 列表
3. 在 `crawler.py` 的 `CRAWLERS` dict 中注册爬虫
4. 完成！运行 `python setup_wizard.py platforms` 选择新平台

</details>

<details>
<summary><strong>数据保存在哪里？</strong></summary>

所有数据保存在 `rankings.db`（SQLite）。可以用任何 SQLite 工具查询：

```sql
-- 查看某部剧的排名历史
SELECT crawl_time, rank, read_count, collect_count
FROM dramas WHERE title LIKE '%Warlord Queen%'
ORDER BY crawl_time;

-- 查看最新的 Top 10
SELECT rank, title, read_count, collect_count, score
FROM dramas WHERE crawl_time = (SELECT MAX(crawl_time) FROM dramas)
ORDER BY rank LIMIT 10;
```

</details>

---

## Roadmap

- [ ] DramaBox 爬虫实现
- [ ] ShortMax / FlexTV 支持
- [ ] 国内平台支持（红果短剧、河马剧场）
- [ ] 多地区追踪（不同语言版本的排行）
- [ ] 周报 / 月报汇总模式
- [ ] 自定义监控名单（指定追踪某些短剧）
- [ ] Web Dashboard（可选）

---

## License

[MIT](LICENSE)
