"""
Short drama platform definitions.

Each platform has its own crawler implementation in crawler.py.
Users select platforms in settings.json.
"""

PLATFORMS = {
    "reelshort": {
        "name_zh": "ReelShort",
        "name_en": "ReelShort",
        "region": "global",
        "url": "https://www.reelshort.com/",
        "company": "Crazy Maple Studio",
        "description_zh": "海外最大竖屏短剧平台",
        "description_en": "Largest vertical short drama platform globally",
        "status": "available",
    },
    "dramabox": {
        "name_zh": "DramaBox",
        "name_en": "DramaBox",
        "region": "global",
        "url": "https://www.dramaboxapp.com/",
        "company": "StoryMatrix (枫叶互动)",
        "description_zh": "枫叶互动旗下短剧平台",
        "description_en": "Short drama platform by StoryMatrix",
        "status": "available",
    },
    "shortmax": {
        "name_zh": "ShortMax",
        "name_en": "ShortMax",
        "region": "global",
        "url": "https://www.shortmax.app/",
        "company": "ShortMax",
        "description_zh": "海外短剧平台 (Playwright 拦截解密数据)",
        "description_en": "Short drama platform (Playwright intercepts decrypted API data)",
        "status": "available",
    },
    "flextv": {
        "name_zh": "FlexTV",
        "name_en": "FlexTV",
        "region": "global",
        "url": "https://www.flextvapp.com/",
        "company": "FlexTV",
        "description_zh": "海外短剧平台 (网站不可达，仅App)",
        "description_en": "Short drama platform (website unreachable, app-only)",
        "status": "unreachable",
    },
    "goodshort": {
        "name_zh": "GoodShort",
        "name_en": "GoodShort",
        "region": "global",
        "url": "https://www.goodshortapp.com/",
        "company": "GoodShort",
        "description_zh": "海外短剧平台 (网站不可达，仅App)",
        "description_en": "Short drama platform (website unreachable, app-only)",
        "status": "unreachable",
    },
    "topshort": {
        "name_zh": "TopShort",
        "name_en": "TopShort",
        "region": "global",
        "url": "https://www.topshortapp.com/",
        "company": "TikShorts",
        "description_zh": "海外短剧平台 (公开H5 API)",
        "description_en": "Short drama platform (public H5 API at tikshortsbox.com)",
        "status": "available",
    },
    "hongguo": {
        "name_zh": "红果短剧",
        "name_en": "Hongguo",
        "region": "cn",
        "url": "https://www.hongguoduanju.com/",
        "company": "字节跳动 (ByteDance/番茄小说)",
        "description_zh": "国内最大短剧平台 (Playwright DOM抓取, 500+部)",
        "description_en": "Largest CN short drama platform (Playwright DOM extraction, 500+ dramas)",
        "status": "available",
    },
}


def get_platform(platform_id):
    return PLATFORMS.get(platform_id)


def get_platform_display(platform_id, lang="zh"):
    p = PLATFORMS.get(platform_id)
    if not p:
        return platform_id
    return p.get(f"name_{lang}", p["name_en"])


def list_platforms(region=None, lang="zh"):
    result = []
    for pid, info in PLATFORMS.items():
        if region and info.get("region") != region:
            continue
        name = info.get(f"name_{lang}", info["name_en"])
        result.append({"id": pid, "name": name, "info": info})
    return result
