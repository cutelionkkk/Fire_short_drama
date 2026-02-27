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
    },
    "dramabox": {
        "name_zh": "DramaBox",
        "name_en": "DramaBox",
        "region": "global",
        "url": "https://www.dramaboxapp.com/",
        "company": "StoryMatrix (枫叶互动)",
        "description_zh": "枫叶互动旗下短剧平台",
        "description_en": "Short drama platform by StoryMatrix",
    },
    # === 待扩展 ===
    # "shortmax": {
    #     "name_zh": "ShortMax",
    #     "name_en": "ShortMax",
    #     "region": "global",
    # },
    # "flextv": {
    #     "name_zh": "FlexTV",
    #     "name_en": "FlexTV",
    #     "region": "global",
    # },
    # "hongguoduanju": {
    #     "name_zh": "红果短剧",
    #     "name_en": "Hongguo Short Drama",
    #     "region": "cn",
    # },
    # "hemajuchang": {
    #     "name_zh": "河马剧场",
    #     "name_en": "Hippo Theater",
    #     "region": "cn",
    # },
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
