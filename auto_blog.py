#!/usr/bin/env python3
"""
自动化博客生成器 - 从 videos.yaml 读取配置，自动生成博客文件.

使用方法:
    python auto_blog.py              # 处理新视频（跳过已处理的）
    python auto_blog.py --rebuild    # 重新处理所有视频
    python auto_blog.py --dry-run    # 仅显示将要处理的视频

环境变量:
    ANTHROPIC_API_KEY - 用于 Claude API 生成摘要（推荐）
    OPENAI_API_KEY - 用于 OpenAI API 生成摘要（备选）
"""
import argparse
import sys
from pathlib import Path

from src.config_parser import parse_config_file
from src.blog_generator import BlogGenerator


def main():
    parser = argparse.ArgumentParser(
        description="自动化博客生成器 - 从 videos.yaml 生成视频摘要博客",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python auto_blog.py              # 处理新视频
    python auto_blog.py --rebuild    # 重新处理所有视频
    python auto_blog.py --dry-run    # 预览模式
        """
    )

    parser.add_argument(
        '--config', '-c',
        default='videos.yaml',
        help='配置文件路径（默认: videos.yaml）'
    )

    parser.add_argument(
        '--output', '-o',
        help='输出博客文件路径（覆盖配置文件中的设置）'
    )

    parser.add_argument(
        '--rebuild',
        action='store_true',
        help='强制重建：重新处理所有视频'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='试运行：仅显示将要处理的视频，不实际执行'
    )

    parser.add_argument(
        '--no-ai',
        action='store_true',
        help='禁用 AI 自动摘要（仅获取字幕，不生成摘要）'
    )

    args = parser.parse_args()

    # 解析配置文件
    try:
        print(f"📄 读取配置文件: {args.config}")
        config = parse_config_file(args.config)
    except FileNotFoundError:
        print(f"❌ 配置文件不存在: {args.config}")
        return 1
    except Exception as e:
        print(f"❌ 解析配置失败: {e}")
        return 1

    # 显示配置信息
    print(f"\n📋 配置信息:")
    print(f"  视频数量: {len(config.videos)}")
    print(f"  默认模式: {config.settings.default_mode}")
    print(f"  输出文件: {config.settings.output_file}")

    # 统计模式
    brief_count = sum(1 for v in config.videos if v.mode == "brief")
    detailed_count = len(config.videos) - brief_count
    if brief_count > 0:
        print(f"  Brief 模式: {brief_count} 个视频")
    if detailed_count > 0:
        print(f"  Detailed 模式: {detailed_count} 个视频")

    # 试运行模式
    if args.dry_run:
        print("\n🏃 试运行模式 - 不实际处理视频")
        for i, video in enumerate(config.videos, 1):
            print(f"  {i}. {video.url} (mode: {video.mode})")
            if video.notes:
                print(f"     备注: {video.notes}")
        return 0

    # 确定处理模式
    if args.rebuild:
        process_mode = "rebuild"
        print("\n🔄 强制重建模式：将重新处理所有视频")
    else:
        process_mode = "update"
        print("\n📌 默认模式：自动跳过已存在的视频（使用 --rebuild 可强制重新处理）")

    # 命令行参数覆盖配置文件
    output_file = args.output or config.settings.output_file

    # 创建博客生成器并执行
    generator = BlogGenerator(output_file=output_file)

    success_count = generator.process_videos(
        videos=config.videos,
        mode=process_mode,
        auto_summary=not args.no_ai
    )

    # 输出结果
    print(f"\n{'='*50}")
    print(f"✅ 处理完成！成功处理 {success_count}/{len(config.videos)} 个视频")
    print(f"📄 博客文件: {Path(output_file).resolve()}")

    return 0


if __name__ == '__main__':
    sys.exit(main())