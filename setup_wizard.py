#!/usr/bin/env python3
"""Interactive setup wizard for Short Drama Tracker"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import load_settings, save_settings, CHANNEL_TEMPLATES
from platforms import PLATFORMS, get_platform_display


def _input(prompt, default=None):
    if default:
        val = input(f"{prompt} [{default}]: ").strip()
        return val if val else default
    return input(f"{prompt}: ").strip()


def _yes_no(prompt, default=True):
    d = "Y/n" if default else "y/N"
    val = input(f"{prompt} [{d}]: ").strip().lower()
    if not val:
        return default
    return val in ('y', 'yes')


def setup_platforms():
    settings = load_settings()

    print("\n📺 选择追踪平台")
    print("=" * 40)

    for i, (pid, info) in enumerate(PLATFORMS.items(), 1):
        active = "✅" if pid in settings.get('platforms', []) else "  "
        region = "🌍" if info.get('region') == 'global' else "🇨🇳"
        print(f"  {active} {i}. {region} {info['name_zh']} ({info['name_en']})")
        print(f"       {info.get('description_zh', '')}")

    print()
    print("输入编号选择，多选用逗号分隔（如: 1,2）")
    choice = _input("选择平台", "1")

    selected = []
    pids = list(PLATFORMS.keys())
    for part in choice.split(','):
        try:
            idx = int(part.strip()) - 1
            if 0 <= idx < len(pids):
                selected.append(pids[idx])
        except ValueError:
            if part.strip() in PLATFORMS:
                selected.append(part.strip())

    if not selected:
        selected = ["reelshort"]

    settings['platforms'] = selected
    save_settings(settings)
    print(f"\n✅ 已选择: {', '.join(get_platform_display(p) for p in selected)}")


def add_channel(channel_name=None):
    settings = load_settings()

    if not channel_name:
        print("\n📡 可用通知渠道：")
        for i, (name, _) in enumerate(CHANNEL_TEMPLATES.items(), 1):
            active = "✅" if name in settings.get('notify_channels', []) else "  "
            print(f"  {active} {i}. {name}")
        idx = _input("\n选择渠道编号")
        try:
            channel_name = list(CHANNEL_TEMPLATES.keys())[int(idx) - 1]
        except (ValueError, IndexError):
            print("❌ 无效选择")
            return

    if channel_name not in CHANNEL_TEMPLATES:
        print(f"❌ 未知渠道: {channel_name}")
        return

    template = CHANNEL_TEMPLATES[channel_name]
    config = settings.get('channel_config', {}).get(channel_name, {})

    print(f"\n🔧 配置 {channel_name}")
    for key, default in template.items():
        current = config.get(key, default)
        hint = f" (当前: {current[:30]}...)" if current else ""
        val = _input(f"  {key}{hint}")
        if val:
            config[key] = val
        elif current:
            config[key] = current

    if 'channel_config' not in settings:
        settings['channel_config'] = {}
    settings['channel_config'][channel_name] = config

    if channel_name not in settings.get('notify_channels', []):
        settings.setdefault('notify_channels', []).append(channel_name)

    save_settings(settings)
    print(f"✅ {channel_name} 已配置")


def show_status():
    settings = load_settings()

    print("\n📺 Short Drama Tracker 配置状态")
    print("=" * 40)

    platforms = settings.get('platforms', ['reelshort'])
    print(f"\n📺 追踪平台: {len(platforms)} 个")
    for p in platforms:
        info = PLATFORMS.get(p, {})
        print(f"  ✅ {get_platform_display(p)} — {info.get('description_zh', '')}")

    channels = settings.get('notify_channels', [])
    print(f"\n📡 通知渠道: {len(channels)} 个")
    for ch in channels:
        config = settings.get('channel_config', {}).get(ch, {})
        has_url = any(v for v in config.values())
        status = "✅ 已配置" if has_url else "⚠️ 未配置"
        print(f"  {status} {ch}")

    if not channels:
        print("  (未配置任何渠道)")

    print(f"\n⚙️ 其他设置:")
    print(f"  Top N: {settings.get('top_n', 50)}")
    print(f"  排名飙升阈值: ≥{settings.get('rank_surge_threshold', 10)} 名")
    print(f"  播放量飙升阈值: ≥{settings.get('read_count_surge_pct', 50)}%")
    print()


def interactive_setup():
    print("\n📺 Short Drama Tracker 配置向导")
    print("=" * 40)

    while True:
        print("\n选择操作：")
        print("  1. 选择追踪平台")
        print("  2. 添加通知渠道")
        print("  3. 查看当前配置")
        print("  4. 退出")

        choice = _input("\n选择", "4")

        if choice == "1":
            setup_platforms()
        elif choice == "2":
            add_channel()
        elif choice == "3":
            show_status()
        else:
            break

    print("\n👋 配置完成！运行 python run.py 开始追踪。")


def main():
    args = sys.argv[1:]

    if not args:
        interactive_setup()
        return

    cmd = args[0]
    if cmd == 'platforms':
        setup_platforms()
    elif cmd == 'add':
        channel = args[1] if len(args) > 1 else None
        add_channel(channel)
    elif cmd == 'status':
        show_status()
    else:
        print(f"Unknown command: {cmd}")
        print("Commands: platforms, add, status")


if __name__ == "__main__":
    main()
