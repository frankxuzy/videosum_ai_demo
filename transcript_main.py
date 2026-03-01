#!/usr/bin/env python3
"""
YouTube 字幕获取和翻译工具
直接使用 YouTube 字幕 API，无需下载视频
"""
import argparse
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

from src.transcript_fetcher import YouTubeTranscriptFetcher
from src.markdown_writer import MarkdownWriter


def extract_video_id(url: str) -> str:
    """从 URL 提取视频 ID"""
    import re
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return url  # 假设直接传入的是 video_id


def save_transcript(transcript_data: dict, output_dir: str = "./output") -> str:
    """保存字幕到文件"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    video_id = transcript_data["video_id"]
    safe_name = video_id  # 可以使用视频标题，但这里简单用 ID

    # 获取语言信息
    lang_code = transcript_data.get("language_code", "unknown")
    is_chinese = transcript_data.get("is_chinese", False)

    # 保存原文
    if is_chinese:
        # 如果是中文视频，原文保存为中文文件
        original_file = output_path / f"{safe_name}_zh.txt"
        with open(original_file, "w", encoding="utf-8") as f:
            f.write("# 中文字幕\n\n")
            f.write(transcript_data["full_text"])
        print(f"\n✓ 中文字幕已保存: {original_file}")
    else:
        # 非中文视频，原文保存为对应语言文件
        original_file = output_path / f"{safe_name}_{lang_code}.txt"
        with open(original_file, "w", encoding="utf-8") as f:
            f.write(f"# Original Transcript ({lang_code})\n\n")
            f.write(transcript_data["full_text"])
        print(f"\n✓ 原文字幕 ({lang_code}) 已保存: {original_file}")

    # 保存中文翻译（如果有）
    if "chinese_text" in transcript_data:
        zh_file = output_path / f"{safe_name}_zh.txt"
        with open(zh_file, "w", encoding="utf-8") as f:
            f.write("# 中文翻译\n\n")
            f.write(transcript_data["chinese_text"])
        print(f"✓ 中文翻译已保存: {zh_file}")
        return str(zh_file)

    return str(original_file)


def main():
    # 加载环境变量
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="YouTube 字幕获取和翻译工具 - 无需下载视频，直接获取字幕",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本使用（自动检测语言并翻译）
  python transcript_main.py "https://www.youtube.com/watch?v=xxxxx"

  # 只获取原文字幕，不翻译
  python transcript_main.py "URL" --no-translate

  # 指定字幕语言（如英语）
  python transcript_main.py "URL" --language en

  # 指定输出目录
  python transcript_main.py "URL" -o ./my_transcripts/
        """
    )

    parser.add_argument(
        'url',
        help='YouTube 视频 URL 或视频 ID'
    )

    parser.add_argument(
        '-o', '--output',
        default='./output',
        help='输出目录 (默认: ./output)'
    )

    parser.add_argument(
        '--no-translate',
        action='store_true',
        help='不翻译成中文，只保存原文字幕'
    )

    parser.add_argument(
        '--language',
        default=None,
        help='指定字幕语言代码（如 en, zh, ja, ko），不指定则自动检测'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='显示详细输出'
    )

    args = parser.parse_args()

    # 提取视频 ID
    video_id = extract_video_id(args.url)
    print(f"视频 ID: {video_id}")
    print("-" * 50)

    # 检查 API key（如果需要翻译）
    if not args.no_translate and not os.getenv('OPENAI_API_KEY'):
        print("❌ 错误: 需要 OPENAI_API_KEY 来翻译字幕")
        print("请在 .env 文件中设置 OPENAI_API_KEY，或使用 --no-translate 只获取英文字幕")
        sys.exit(1)

    # 获取字幕
    fetcher = YouTubeTranscriptFetcher()
    transcript = fetcher.fetch_transcript(
        video_id,
        translate_to_chinese=not args.no_translate,
        language=args.language
    )

    if transcript is None:
        print("\n❌ 无法获取字幕，程序结束")
        print("提示: 此视频可能没有字幕，或尝试指定 --language 参数")
        sys.exit(1)

    # 保存文件
    print("\n" + "-" * 50)
    output_file = save_transcript(transcript, args.output)

    print("\n✅ 完成!")
    print(f"输出文件: {output_file}")

    # 显示预览
    if args.verbose:
        print("\n" + "=" * 50)
        print("中文翻译预览（前500字符）:")
        print("=" * 50)
        preview = transcript.get("chinese_text", transcript["full_text"])[:500]
        print(preview + "...")


if __name__ == '__main__':
    main()
