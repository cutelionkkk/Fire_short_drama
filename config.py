"""Short Drama Tracker Configuration"""

import os
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# === 数据库 ===
DB_PATH = os.path.join(SCRIPT_DIR, "rankings.db")

# === 用户配置文件 ===
CONFIG_FILE = os.path.join(SCRIPT_DIR, "settings.json")

# === 默认配置 ===
DEFAULTS = {
    # 平台
    "platforms": ["reelshort"],

    # 抓取
    "top_n": 50,

    # 分析阈值
    "rank_surge_threshold": 10,
    "read_count_surge_pct": 50,       # 播放量增长百分比
    "collect_surge_pct": 30,          # 收藏增长百分比

    # 报告
    "report_max_items": 10,
    "report_language": "zh",  # zh | en

    # 通知渠道 (可多选)
    "notify_channels": [],
    "channel_config": {},
}

# === 渠道配置模板 ===
CHANNEL_TEMPLATES = {
    "discord": {
        "webhook_url": "",
        "mention_role": "",
    },
    "telegram": {
        "bot_token": "",
        "chat_id": "",
    },
    "slack": {
        "webhook_url": "",
        "channel": "",
    },
    "feishu": {
        "webhook_url": "",
        "secret": "",
    },
    "dingtalk": {
        "webhook_url": "",
        "secret": "",
    },
    "wechat": {
        "webhook_url": "",
    },
}


def load_settings():
    """Load user settings, merge with defaults"""
    settings = DEFAULTS.copy()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                user = json.load(f)
            settings.update(user)
        except Exception as e:
            print(f"⚠️ Failed to load {CONFIG_FILE}: {e}")
    return settings


def save_settings(settings):
    """Save settings to file"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)


def get_setting(key, default=None):
    """Get a single setting value"""
    s = load_settings()
    return s.get(key, default)


# === 兼容旧代码的全局变量 ===
_settings = load_settings()
TOP_N = _settings["top_n"]
RANK_SURGE_THRESHOLD = _settings["rank_surge_threshold"]
READ_COUNT_SURGE_PCT = _settings["read_count_surge_pct"]
COLLECT_SURGE_PCT = _settings["collect_surge_pct"]
REPORT_MAX_ITEMS = _settings["report_max_items"]
