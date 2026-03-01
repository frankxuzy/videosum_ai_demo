"""Blog generator for multi-video summary blog."""
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


class BlogEntry:
    """Single blog entry for a video."""

    def __init__(self,
                 video_id: str,
                 url: str,
                 title: str,
                 language: str,
                 processed_at: str,
                 mode: str,
                 full_text: str,
                 chinese_text: Optional[str] = None,
                 notes: Optional[str] = None,
                 video_metadata: Optional[Dict] = None,
                 summary: Optional[str] = None):
        self.video_id = video_id
        self.url = url
        self.title = title
        self.language = language
        self.processed_at = processed_at
        self.mode = mode
        self.full_text = full_text
        self.chinese_text = chinese_text or full_text
        self.notes = notes
        self.video_metadata = video_metadata or {}
        self.summary = summary  # AI-generated summary for brief mode

    def to_dict(self) -> Dict[str, Any]:
        return {
            "video_id": self.video_id,
            "url": self.url,
            "title": self.title,
            "language": self.language,
            "processed_at": self.processed_at,
            "mode": self.mode,
            "notes": self.notes,
            "video_metadata": self.video_metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], full_text: str = "",
                  chinese_text: str = "") -> "BlogEntry":
        return cls(
            video_id=data["video_id"],
            url=data["url"],
            title=data["title"],
            language=data["language"],
            processed_at=data["processed_at"],
            mode=data["mode"],
            full_text=full_text,
            chinese_text=chinese_text,
            notes=data.get("notes"),
            video_metadata=data.get("video_metadata", {})
        )


class BlogMetadata:
    """Metadata for the blog."""

    def __init__(self,
                 output_file: str,
                 processed_videos: List[Dict],
                 last_updated: Optional[str] = None):
        self.output_file = output_file
        self.processed_videos = processed_videos
        self.last_updated = last_updated or datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "output_file": self.output_file,
            "last_updated": self.last_updated,
            "processed_videos": self.processed_videos
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BlogMetadata":
        return cls(
            output_file=data["output_file"],
            processed_videos=data.get("processed_videos", []),
            last_updated=data.get("last_updated")
        )

    def get_video_ids(self) -> set:
        """Get set of processed video IDs."""
        return {v["video_id"] for v in self.processed_videos}

    def add_video(self, entry: BlogEntry):
        """Add a new video entry (prepend to keep newest first)."""
        # Remove existing entry with same video_id if exists
        self.processed_videos = [
            v for v in self.processed_videos if v.get("video_id") != entry.video_id
        ]
        video_dict = entry.to_dict()
        self.processed_videos.insert(0, video_dict)
        self.last_updated = datetime.now().isoformat()


class BlogGenerator:
    """Generator for multi-video blog."""

    def __init__(self, output_file: str = "blog.md", verbose: bool = False):
        self.output_file = Path(output_file)
        self.verbose = verbose
        self.metadata_file = self._get_metadata_path()
        self.metadata = self._load_metadata()

    def _get_metadata_path(self) -> Path:
        """Get the metadata file path based on output file."""
        stem = self.output_file.stem
        suffix = self.output_file.suffix
        parent = self.output_file.parent
        return parent / f"{stem}_meta{suffix.replace('.md', '.json')}"

    def _load_metadata(self) -> BlogMetadata:
        """Load existing metadata or create new."""
        if self.metadata_file.exists():
            try:
                data = json.loads(self.metadata_file.read_text(encoding="utf-8"))
                metadata = BlogMetadata.from_dict(data)
                # Deduplicate processed_videos
                seen_ids = set()
                unique_videos = []
                for video in metadata.processed_videos:
                    vid = video.get("video_id")
                    if vid and vid not in seen_ids:
                        seen_ids.add(vid)
                        unique_videos.append(video)
                metadata.processed_videos = unique_videos
                return metadata
            except (json.JSONDecodeError, KeyError) as e:
                print(f"⚠️  无法加载元数据文件: {e}，将创建新的元数据")

        return BlogMetadata(
            output_file=str(self.output_file),
            processed_videos=[]
        )

    def _save_metadata(self):
        """Save metadata to file."""
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
        self.metadata_file.write_text(
            json.dumps(self.metadata.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    def is_video_processed(self, video_id: str) -> bool:
        """Check if a video has already been processed."""
        return video_id in self.metadata.get_video_ids()

    def generate_entry(self, entry: BlogEntry) -> str:
        """Generate markdown content for a single entry."""
        lines = []

        # Entry header with title and processing time
        title = entry.title or f"Video {entry.video_id}"
        lines.append(f"## {title}")
        lines.append(f"- **处理时间**: {entry.processed_at}")
        lines.append(f"- **视频链接**: [YouTube]({entry.url})")
        lines.append(f"- **原语言**: {entry.language}")

        # User notes if present
        if entry.notes:
            lines.append(f"- **用户备注**: {entry.notes}")

        # Add metadata if available
        if entry.video_metadata:
            if "author" in entry.video_metadata:
                lines.append(f"- **频道**: {entry.video_metadata['author']}")
            if "duration" in entry.video_metadata:
                duration_min = entry.video_metadata['duration'] // 60
                lines.append(f"- **时长**: {duration_min} 分钟")

        lines.append("")

        # Check if content is translated
        is_translated = entry.chinese_text != entry.full_text

        # Content section
        if entry.mode == "detailed":
            # Detailed mode: Show study notes (no original text)
            lines.append("### 学习笔记")
            lines.append("")
            if entry.summary:
                lines.append(entry.summary)
            else:
                lines.append("> ⚠️ 暂无学习笔记")
        else:
            # Brief mode - AI generated summary
            lines.append("### 内容简述")
            lines.append("")
            if entry.summary:
                # Use AI-generated summary
                lines.append(entry.summary)
            elif entry.chinese_text and entry.chinese_text != entry.full_text:
                # Fallback: use chinese_text if available
                lines.append(entry.chinese_text)
            else:
                # Fallback: show truncated original text with prompt
                lines.append("> ⚠️ AI 简述生成失败，显示原文摘要：")
                lines.append("")
                preview_text = entry.full_text[:1500] if len(entry.full_text) > 1500 else entry.full_text
                lines.append(preview_text)
                if len(entry.full_text) > 1500:
                    lines.append("")
                    lines.append(f"*... (内容已截断，完整内容共 {len(entry.full_text)} 字符) ...*")

        lines.append("")
        lines.append("---")
        lines.append("")

        return "\n".join(lines)

    def generate_blog_header(self) -> str:
        """Generate the blog header."""
        lines = [
            "# 视频摘要博客",
            "",
            f"*最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
            "",
            "> 本文档收集 YouTube 视频内容用于学习笔记。",
            "> - Brief 模式：使用 Claude AI 自动生成 3-5 句中文简述",
            "> - Detailed 模式：保留完整字幕原文，供后期手动整理",
            "",
            "## 处理流程",
            "",
            "```",
            "YouTube URL → 下载字幕 → Claude AI 总结/翻译 → 保存学习笔记",
            "```",
            "",
            "## 使用说明",
            "",
            "| 视频类型 | 处理方式 |",
            "|---------|---------|",
            "| 中文视频 | 直接保留字幕作为学习笔记 |",
            "| 非中文视频 | 复制原文 → Claude AI 总结翻译 → 粘贴学习笔记 |",
            "",
            "### Claude AI 提问模板",
            "",
            "**Brief 模式：**",
            "> \"请总结这段视频的核心要点（3-5条），并翻译成中文\"",
            "",
            "**Detailed 模式：**",
            "> \"请将这段视频内容整理成学习笔记格式，分章节总结要点，并翻译成中文。不要直接拷贝原文，要用自己的话总结。\"",
            "",
            "## 目录",
            "",
        ]

        # Add table of contents from processed videos
        for video in self.metadata.processed_videos:
            title = video.get("title", f"Video {video['video_id']}")
            processed_at = video.get("processed_at", "")[:10]  # Just the date part
            lines.append(f"- [{title}](#{self._anchor_link(title)}) - {processed_at}")

        lines.append("")
        lines.append("---")
        lines.append("")

        return "\n".join(lines)

    def _anchor_link(self, title: str) -> str:
        """Convert title to markdown anchor link."""
        # Remove special characters and convert spaces to hyphens
        anchor = re.sub(r'[^\w\s-]', '', title.lower())
        anchor = re.sub(r'[-\s]+', '-', anchor)
        return anchor

    def create_new_blog(self, entries: List[BlogEntry]) -> str:
        """Create a new blog with the given entries."""
        # Update metadata with new entries
        for entry in entries:
            self.metadata.add_video(entry)

        # Generate full blog content
        lines = [self.generate_blog_header()]

        for entry in entries:
            lines.append(self.generate_entry(entry))

        return "\n".join(lines)

    def update_blog(self, new_entries: List[BlogEntry]) -> str:
        """Update existing blog with new entries (prepend, newest first)."""
        if not new_entries:
            return ""

        # Generate content for new entries
        new_content = []
        for entry in new_entries:
            self.metadata.add_video(entry)
            new_content.append(self.generate_entry(entry))

        # If blog file exists, we need to prepend new entries
        if self.output_file.exists():
            existing_content = self.output_file.read_text(encoding="utf-8")

            # Split after the header to insert new entries
            lines = existing_content.split("\n")

            # Find where entries start (after the last --- in header)
            header_end = 0
            separator_count = 0
            for i, line in enumerate(lines):
                if line.strip() == "---":
                    separator_count += 1
                    if separator_count >= 2:  # After header TOC separator
                        header_end = i + 1
                        break

            # Reconstruct with new header and entries
            result_lines = [
                "# 视频摘要博客",
                "",
                f"*最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
                "",
                "> 本文档收集 YouTube 视频内容用于学习笔记。",
                "> - Brief 模式：使用 Claude AI 自动生成 3-5 句中文简述",
                "> - Detailed 模式：保留完整字幕原文，供后期手动整理",
                "",
                "## 处理流程",
                "",
                "```",
                "YouTube URL → 获取字幕 → Claude AI 总结 → 保存学习笔记",
                "```",
                "",
                "## 使用说明",
                "",
                "| 模式 | 处理方式 | 适用场景 |",
                "|------|---------|---------|",
                "| brief | AI 生成 3-5 句中文简述，不保留原文 | 快速了解视频内容 |",
                "| detailed | 保留完整字幕原文 | 深度学习，手动整理笔记 |",
                "",
                "## 目录",
                "",
            ]

            # Add updated TOC
            for video in self.metadata.processed_videos:
                title = video.get("title", f"Video {video['video_id']}")
                processed_at = video.get("processed_at", "")[:10]
                result_lines.append(f"- [{title}](#{self._anchor_link(title)}) - {processed_at}")

            result_lines.append("")
            result_lines.append("---")
            result_lines.append("")

            # Add new entries
            result_lines.extend("\n".join(new_content).split("\n"))

            # Add old entries (skip old header)
            if header_end > 0:
                result_lines.extend(lines[header_end:])
            else:
                result_lines.extend(lines)

            return "\n".join(result_lines)
        else:
            # No existing file, create new
            return self.create_new_blog(new_entries)

    def save_blog(self, content: str):
        """Save blog content to file."""
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        self.output_file.write_text(content, encoding="utf-8")
        self._save_metadata()

    def get_existing_content(self, video_id: str) -> Optional[BlogEntry]:
        """Get existing entry for a video if it exists."""
        for video in self.metadata.processed_videos:
            if video["video_id"] == video_id:
                # Try to find the content in the blog file
                if self.output_file.exists():
                    content = self.output_file.read_text(encoding="utf-8")
                    # This is a simplified retrieval - in practice we'd store full text separately
                    return BlogEntry.from_dict(video, full_text="", chinese_text="")
        return None

    def process_videos(self, videos: List, mode: str = "normal",
                       translate: bool = True, auto_summary: bool = True) -> int:
        """Process a list of videos and generate/update blog.

        Args:
            videos: List of VideoConfig objects
            mode: "normal", "update", or "rebuild"
            translate: Whether to translate to Chinese
            auto_summary: Whether to auto-generate summaries using AI

        Returns:
            Number of successfully processed videos
        """
        from src.config_parser import VideoConfig
        from src.transcript_fetcher import YouTubeTranscriptFetcher, extract_video_id
        from src.summary_generator import SummaryGenerator

        fetcher = YouTubeTranscriptFetcher()
        summary_gen = SummaryGenerator() if auto_summary else None
        new_entries = []
        success_count = 0

        # Check if auto summary is available
        if auto_summary and summary_gen and summary_gen.is_available():
            print(f"🤖 AI 自动摘要已启用 (使用 {summary_gen.provider})")
        elif auto_summary:
            print(f"⚠️ AI 自动摘要不可用，请设置 ANTHROPIC_API_KEY 或 OPENAI_API_KEY")
            auto_summary = False

        for video_config in videos:
            video_id = extract_video_id(video_config.url)
            if not video_id:
                print(f"  ⚠️  无法提取视频 ID: {video_config.url}")
                continue

            print(f"\n🎬 处理视频: {video_id}")
            print(f"  模式: {video_config.mode}")
            if video_config.notes:
                print(f"  备注: {video_config.notes}")

            # Check if already processed (skip in update mode)
            if mode != "rebuild" and self.is_video_processed(video_id):
                print(f"  ⏭️  已处理过，跳过")
                continue

            # Fetch transcript
            print(f"  📥 获取字幕...")
            transcript = fetcher.fetch_transcript(
                video_id,
                translate_to_chinese=False  # Don't auto-translate, we'll summarize instead
            )

            if not transcript:
                print(f"  ❌ 无法获取字幕，跳过")
                continue

            # Fetch video metadata
            print(f"  📋 获取视频信息...")
            metadata = fetcher.fetch_video_metadata(video_id)

            # Create blog entry based on mode
            title = metadata.get("title", f"Video {video_id}") if metadata else f"Video {video_id}"
            processed_at = datetime.now().strftime("%Y-%m-%d %H:%M")
            full_text = transcript.get("full_text", "")

            if video_config.mode == "brief":
                # Brief mode: Generate short summary
                if auto_summary and summary_gen:
                    print(f"  🤖 生成 AI 摘要...")
                    summary = summary_gen.generate_brief_summary(full_text, title)
                    if not summary:
                        print(f"  ⚠️ AI 摘要生成失败")
                        summary = "[待添加简述 - 请手动编辑添加]"
                else:
                    summary = "[待添加简述 - 请手动编辑添加]"

                entry = BlogEntry(
                    video_id=video_id,
                    url=video_config.url,
                    title=title,
                    language=transcript.get("language_name", "Unknown"),
                    processed_at=processed_at,
                    mode=video_config.mode,
                    full_text="",
                    chinese_text=summary,
                    notes=video_config.notes,
                    video_metadata=metadata,
                    summary=summary
                )
                print(f"  ✅ 简述已生成")
            else:
                # Detailed mode: Generate study notes
                if auto_summary and summary_gen:
                    print(f"  🤖 生成学习笔记...")
                    study_notes = summary_gen.generate_detailed_notes(full_text, title)
                    if not study_notes:
                        print(f"  ⚠️ 学习笔记生成失败")
                        study_notes = "[待添加学习笔记 - 请手动编辑添加]"
                else:
                    study_notes = "[待添加学习笔记 - 请手动编辑添加]"

                entry = BlogEntry(
                    video_id=video_id,
                    url=video_config.url,
                    title=title,
                    language=transcript.get("language_name", "Unknown"),
                    processed_at=processed_at,
                    mode=video_config.mode,
                    full_text="",
                    chinese_text=study_notes,
                    notes=video_config.notes,
                    video_metadata=metadata,
                    summary=study_notes
                )
                print(f"  ✅ 学习笔记已生成")

            new_entries.append(entry)
            success_count += 1
            print(f"  ✅ 完成")

        # Generate blog content
        if new_entries:
            print(f"\n📝 生成博客...")
            if mode == "update":
                content = self.update_blog(new_entries)
            else:
                content = self.create_new_blog(new_entries)

            self.save_blog(content)
            print(f"  ✅ 博客已保存: {self.output_file}")
            print(f"  📄 元数据已保存: {self.metadata_file}")

        return success_count
