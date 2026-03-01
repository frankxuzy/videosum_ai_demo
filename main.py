"""YouTube Video Summarizer - Main Entry Point."""

import argparse
import os
import sys
import logging
from pathlib import Path

from dotenv import load_dotenv

from src.downloader import YouTubeDownloader
from src.transcriber import AudioTranscriber
from src.summarizer import ContentSummarizer
from src.translator import ContentTranslator
from src.markdown_writer import MarkdownWriter


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)


def process_video(
    url: str,
    output_dir: str,
    temp_dir: str,
    include_transcript: bool,
    cleanup: bool,
    download_only: bool,
    logger: logging.Logger
) -> str:
    """Process a single YouTube video.

    Args:
        url: YouTube video URL
        output_dir: Output directory for Markdown files
        temp_dir: Temporary directory for audio files
        include_transcript: Whether to include full transcript
        cleanup: Whether to clean up temporary files
        download_only: Only download audio without processing
        logger: Logger instance

    Returns:
        Path to saved file
    """
    # Initialize components
    downloader = YouTubeDownloader(temp_dir=temp_dir)

    try:
        # Step 1: Download audio
        logger.info(f"📥 Downloading audio from: {url}")
        video_info = downloader.download_audio(url)
        logger.info(f"   ✓ Title: {video_info['title']}")
        logger.info(f"   ✓ Author: {video_info['author']}")
        logger.info(f"   ✓ Duration: {video_info['duration'] // 60}:{video_info['duration'] % 60:02d}")

        audio_path = video_info['audio_path']

        if download_only:
            logger.info("")
            logger.info("✅ Download complete!")
            logger.info(f"   Audio saved to: {audio_path}")
            return audio_path

        # Initialize API-dependent components
        transcriber = AudioTranscriber()
        summarizer = ContentSummarizer()
        translator = ContentTranslator()
        writer = MarkdownWriter(output_dir=output_dir)

        # Step 2: Transcribe audio
        logger.info("🎤 Transcribing audio...")
        transcript = transcriber.transcribe(audio_path)
        logger.info(f"   ✓ Transcript length: {len(transcript)} characters")

        # Step 3: Summarize content
        logger.info("📝 Summarizing content...")
        english_summary = summarizer.summarize(transcript, video_info)
        logger.info(f"   ✓ Generated summary with {len(english_summary['key_points'])} key points")

        # Step 4: Translate to Chinese
        logger.info("🌐 Translating to Chinese...")
        chinese_summary = translator.translate_to_chinese(english_summary)
        logger.info("   ✓ Translation complete")

        # Step 5: Generate Markdown
        logger.info("📄 Generating Markdown file...")
        output_path = writer.save(
            video_info=video_info,
            chinese_summary=chinese_summary,
            english_summary=english_summary,
            transcript=transcript,
            include_transcript=include_transcript
        )
        logger.info(f"   ✓ Saved to: {output_path}")

        # Cleanup
        if cleanup:
            logger.info("🧹 Cleaning up temporary files...")
            downloader.cleanup(audio_path)
            logger.info("   ✓ Cleanup complete")

        return output_path

    except Exception as e:
        logger.error(f"❌ Error processing video: {str(e)}")
        raise


def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="YouTube Video Summarizer - Automatically summarize YouTube videos in Chinese",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python main.py "https://www.youtube.com/watch?v=xxxxx"

  # Specify output directory
  python main.py "https://www.youtube.com/watch?v=xxxxx" -o ./my_summaries/

  # Without full transcript (smaller file)
  python main.py "https://www.youtube.com/watch?v=xxxxx" --no-transcript

  # Keep temporary files for debugging
  python main.py "https://www.youtube.com/watch?v=xxxxx" --no-cleanup

  # Download only (no API key required)
  python main.py "https://www.youtube.com/watch?v=xxxxx" --download-only
        """
    )

    parser.add_argument(
        'url',
        help='YouTube video URL'
    )

    parser.add_argument(
        '-o', '--output',
        default=os.getenv('DEFAULT_OUTPUT_DIR', './output'),
        help='Output directory for Markdown files (default: ./output)'
    )

    parser.add_argument(
        '-t', '--temp',
        default=os.getenv('TEMP_DIR', './temp'),
        help='Temporary directory for audio files (default: ./temp)'
    )

    parser.add_argument(
        '--no-transcript',
        action='store_true',
        help='Exclude full transcript from output (smaller file)'
    )

    parser.add_argument(
        '--no-cleanup',
        action='store_true',
        help='Keep temporary audio files after processing'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '--download-only',
        action='store_true',
        help='Only download audio, skip transcription and summarization (no API key required)'
    )

    args = parser.parse_args()

    # Setup logging
    logger = setup_logging(args.verbose)

    # Validate API keys (skip if download-only mode)
    if not args.download_only and not os.getenv('OPENAI_API_KEY'):
        logger.error("❌ OPENAI_API_KEY environment variable is not set!")
        logger.error("   Please set it in your .env file or environment.")
        logger.error("   Or use --download-only to just download the audio.")
        sys.exit(1)

    # Process video
    try:
        output_path = process_video(
            url=args.url,
            output_dir=args.output,
            temp_dir=args.temp,
            include_transcript=not args.no_transcript,
            cleanup=not args.no_cleanup,
            download_only=args.download_only,
            logger=logger
        )

        if args.download_only:
            logger.info("")
            logger.info("✅ Download complete!")
        else:
            logger.info("")
            logger.info("✅ Success! Summary saved to:")
            logger.info(f"   {output_path}")

    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"\n❌ Failed: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
