"""Tests for YouTube video summarizer."""

import unittest
from src.downloader import YouTubeDownloader
from src.markdown_writer import MarkdownWriter


class TestYouTubeDownloader(unittest.TestCase):
    """Test YouTube downloader."""

    def setUp(self):
        self.downloader = YouTubeDownloader()

    def test_extract_video_id_standard(self):
        """Test extracting video ID from standard URL."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        video_id = self.downloader.extract_video_id(url)
        self.assertEqual(video_id, "dQw4w9WgXcQ")

    def test_extract_video_id_short(self):
        """Test extracting video ID from short URL."""
        url = "https://youtu.be/dQw4w9WgXcQ"
        video_id = self.downloader.extract_video_id(url)
        self.assertEqual(video_id, "dQw4w9WgXcQ")

    def test_extract_video_id_embed(self):
        """Test extracting video ID from embed URL."""
        url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        video_id = self.downloader.extract_video_id(url)
        self.assertEqual(video_id, "dQw4w9WgXcQ")

    def test_extract_video_id_invalid(self):
        """Test extracting video ID from invalid URL."""
        url = "https://example.com/video"
        video_id = self.downloader.extract_video_id(url)
        self.assertIsNone(video_id)


class TestMarkdownWriter(unittest.TestCase):
    """Test Markdown writer."""

    def setUp(self):
        self.writer = MarkdownWriter()

    def test_sanitize_filename(self):
        """Test filename sanitization."""
        filename = 'Test: "Video" | Title <script>'
        sanitized = self.writer._sanitize_filename(filename)
        self.assertEqual(sanitized, "Test Video  Title script")

    def test_format_duration(self):
        """Test duration formatting."""
        # Test hours
        self.assertEqual(self.writer._format_duration(3661), "1:01:01")
        # Test minutes only
        self.assertEqual(self.writer._format_duration(125), "2:05")
        # Test seconds only
        self.assertEqual(self.writer._format_duration(45), "0:45")


if __name__ == '__main__':
    unittest.main()
