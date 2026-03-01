"""主程序入口"""
import argparse
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from downloader import YouTubeDownloader
from transcriber import AudioTranscriber
from markdown_writer import MarkdownWriter


def main():
    parser = argparse.ArgumentParser(
        description="YouTube 视频转录工具 - 下载音频并生成转录文本"
    )
    parser.add_argument(
        "url",
        help="YouTube 视频 URL"
    )
    parser.add_argument(
        "-o", "--output",
        default="./output",
        help="输出目录 (默认: ./output)"
    )
    parser.add_argument(
        "-t", "--temp",
        default="./temp",
        help="临时文件目录 (默认: ./temp)"
    )
    parser.add_argument(
        "-m", "--model",
        default="base",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper 模型大小 (默认: base)"
    )
    parser.add_argument(
        "--keep-audio",
        action="store_true",
        help="保留下载的音频文件"
    )

    args = parser.parse_args()

    try:
        # 步骤 1: 下载音频
        print("=" * 50)
        print("步骤 1: 下载 YouTube 音频")
        print("=" * 50)
        downloader = YouTubeDownloader(temp_dir=args.temp)
        video_info = downloader.download_audio(args.url)
        print(f"视频标题: {video_info['title']}")
        print(f"频道: {video_info['author']}")
        print(f"时长: {video_info['duration'] // 60}分{video_info['duration'] % 60}秒")

        # 步骤 2: 语音转录
        print("\n" + "=" * 50)
        print("步骤 2: 语音转录")
        print("=" * 50)
        transcriber = AudioTranscriber(model_size=args.model)
        transcript_text = transcriber.transcribe(
            video_info['audio_path'],
            output_dir=args.output
        )

        # 步骤 3: 生成 Markdown 模板
        print("\n" + "=" * 50)
        print("步骤 3: 生成 Markdown 文件")
        print("=" * 50)
        writer = MarkdownWriter(output_dir=args.output)

        transcript_path = Path(args.output) / f"{video_info['video_id']}_transcript.txt"
        md_path = writer.create_summary_template(
            video_info=video_info,
            transcript_path=str(transcript_path)
        )

        # 清理临时文件
        if not args.keep_audio:
            print("\n" + "=" * 50)
            print("清理临时文件")
            print("=" * 50)
            downloader.cleanup(video_info['audio_path'])

        # 输出下一步指引
        print("\n" + "=" * 50)
        print("处理完成!")
        print("=" * 50)
        print(f"\n转录文件: {transcript_path}")
        print(f"Markdown 文件: {md_path}")
        print("\n下一步:")
        print(f"1. 查看转录内容: cat {transcript_path}")
        print(f"2. 将转录内容提供给 Claude，请求总结并翻译成中文")
        print(f"3. 将 Claude 的回复填入 Markdown 文件中")

    except Exception as e:
        print(f"\n错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
