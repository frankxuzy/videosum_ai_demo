#!/usr/bin/env python3
"""
YouTube 博客生成器 - 批量视频处理与博客生成

支持:
1. 多 URL 批量处理（JSON/YAML 配置文件）
2. 字幕获取、AI 自动总结
3. 生成统一的 Markdown 博客文件
4. 按时间排序（最新的在最前面）
5. 增量更新（添加新视频不重新生成旧内容）

模式说明:
- brief 模式: AI 自动生成 3-5 句中文简述，不保留原文
- detailed 模式: AI 生成详细学习笔记，分章节总结
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

from src.config_parser import parse_config_file, create_urls_from_list
from src.blog_generator import BlogGenerator


def main():
    parser = argparse.ArgumentParser(
        description="YouTube 博客生成器 - 批量视频处理与博客生成（Claude AI 翻译版）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
工作原理:
  1. 从 YouTube 获取视频字幕（免费）
  2. brief 模式: 使用 Claude AI 自动生成 3-5 句中文简述（不保留原文）
  3. detailed 模式: 保留完整字幕原文
  4. 生成 Markdown 博客文件

示例:
  # 从配置文件处理（推荐）
  python blog_main.py --config videos.yaml

  # 直接处理多个 URL
  python blog_main.py --urls "https://youtube.com/watch?v=xxx" "https://youtube.com/watch?v=yyy"

  # 增量更新（添加新视频到现有博客）
  python blog_main.py --config new_videos.yaml --update

  # 强制重建（重新处理所有视频）
  python blog_main.py --config videos.yaml --rebuild

配置文件格式 (YAML):
  videos:
    - url: https://youtube.com/watch?v=xxx
      mode: detailed
      notes: 重要视频，需要详细摘要
    - url: https://youtube.com/watch?v=yyy
      mode: brief

  settings:
    default_mode: brief
    output_file: ./output/blog.md

模式说明:
  - brief:  生成 AI 简述（3-5 句中文），适合快速了解视频内容
  - detailed: 保留完整原文，适合深入学习后手动整理笔记

环境变量:
  ANTHROPIC_API_KEY - 用于 brief 模式的 AI 总结（必需）
        """
    )

    # 输入选项（互斥）
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '--config', '-c',
        help='配置文件路径（JSON 或 YAML）'
    )
    input_group.add_argument(
        '--urls', '-u',
        nargs='+',
        help='直接提供 YouTube URL 列表'
    )

    # 输出选项
    parser.add_argument(
        '--output', '-o',
        help='输出博客文件路径（覆盖配置文件中的设置）'
    )

    # 处理选项
    parser.add_argument(
        '--mode', '-m',
        choices=['brief', 'detailed'],
        help='默认处理模式：brief（简洁）或 detailed（详细）'
    )

    parser.add_argument(
        '--update',
        action='store_true',
        help='增量更新模式：添加新视频到现有博客（不重新生成旧内容）'
    )

    parser.add_argument(
        '--rebuild',
        action='store_true',
        help='强制重建模式：重新处理所有视频（忽略已有内容）'
    )

    # 其他选项
    parser.add_argument(
        '--translate',
        action='store_true',
        help='使用 OpenAI API 自动翻译（需要设置 OPENAI_API_KEY）'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='显示详细输出'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='试运行模式：解析配置但不实际处理视频'
    )

    parser.add_argument(
        '--summaries',
        nargs='+',
        help='为 brief 模式视频提供简述（按顺序，用引号包裹）'
    )

    args = parser.parse_args()

    # 解析配置
    try:
        if args.config:
            print(f"📄 读取配置文件: {args.config}")
            config = parse_config_file(args.config)
        else:
            print(f"📝 处理 {len(args.urls)} 个 URL")
            output_file = args.output or "blog.md"
            default_mode = args.mode or "brief"
            config = create_urls_from_list(args.urls, output_file, default_mode)

        # 命令行参数覆盖配置文件
        if args.output:
            config.settings.output_file = args.output
        if args.mode:
            config.settings.default_mode = args.mode

        print(f"\n📋 配置信息:")
        print(f"  视频数量: {len(config.videos)}")
        print(f"  默认模式: {config.settings.default_mode}")
        print(f"  输出文件: {config.settings.output_file}")

        if args.dry_run:
            print("\n🏃 试运行模式 - 不实际处理视频")
            for i, video in enumerate(config.videos, 1):
                print(f"  {i}. {video.url} (mode: {video.mode})")
                if video.notes:
                    print(f"     备注: {video.notes}")
            return 0

        # 确定处理模式（默认为 update，即跳过已存在的视频）
        if args.rebuild:
            process_mode = "rebuild"
            print("\n🔄 强制重建模式：将重新处理所有视频")
        else:
            # 默认使用 update 模式，跳过已存在的视频
            process_mode = "update"
            if args.update:
                print("\n➕ 增量更新模式：只添加新视频（跳过已存在的视频）")
            else:
                print("\n📌 默认模式：自动跳过已存在的视频（使用 --rebuild 可强制重新处理）")

        # 创建博客生成器并执行
        generator = BlogGenerator(
            output_file=config.settings.output_file
        )

        success_count = generator.process_videos(
            videos=config.videos,
            mode=process_mode,
            translate=args.translate
        )

        print(f"\n{'='*50}")
        print(f"✅ 处理完成！成功处理 {success_count}/{len(config.videos)} 个视频")
        print(f"📄 博客文件: {Path(config.settings.output_file).resolve()}")

        # Show completion message based on modes used
        has_brief = any(v.mode == "brief" for v in config.videos)
        has_detailed = any(v.mode == "detailed" for v in config.videos)

        if has_brief and has_detailed:
            print(f"\n💡 博客包含两种模式的内容:")
            print(f"   - brief 模式: AI 已自动生成中文简述")
            print(f"   - detailed 模式: 保留完整原文，可手动整理笔记")
        elif has_brief:
            print(f"\n💡 brief 模式视频已使用 Claude AI 自动生成中文简述")
        elif has_detailed:
            print(f"\n💡 detailed 模式视频保留了完整原文")
            print(f"   可使用 Claude AI 手动总结翻译:")
            print(f"   1. 打开博客文件: {config.settings.output_file}")
            print(f"   2. 复制原文内容向 Claude 提问")

        print(f"\n📌 提示:")
        print(f"   - 使用 --update 参数添加新视频而不重新生成旧内容")
        print(f"   - 使用 --rebuild 参数重新处理所有视频")

        return 0

    except FileNotFoundError as e:
        print(f"\n❌ 错误: {e}")
        return 1
    except ValueError as e:
        print(f"\n❌ 配置错误: {e}")
        return 1
    except ImportError as e:
        print(f"\n❌ 依赖错误: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断")
        return 130
    except Exception as e:
        print(f"\n❌ 处理失败: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
