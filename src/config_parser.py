"""Configuration parser for blog mode - supports JSON and YAML formats."""
import json
from pathlib import Path
from typing import Dict, List, Optional, Any


class VideoConfig:
    """Single video configuration."""

    def __init__(self, url: str, mode: str = "brief", notes: Optional[str] = None):
        self.url = url
        self.mode = mode  # "brief" or "detailed"
        self.notes = notes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "mode": self.mode,
            "notes": self.notes
        }


class BlogSettings:
    """Blog generation settings."""

    def __init__(self, default_mode: str = "brief", output_file: str = "blog.md"):
        self.default_mode = default_mode
        self.output_file = output_file

    def to_dict(self) -> Dict[str, Any]:
        return {
            "default_mode": self.default_mode,
            "output_file": self.output_file
        }


class BlogConfig:
    """Complete blog configuration."""

    def __init__(self, videos: List[VideoConfig], settings: BlogSettings):
        self.videos = videos
        self.settings = settings

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BlogConfig":
        """Parse configuration from dictionary."""
        # Parse settings
        settings_data = data.get("settings", {})
        settings = BlogSettings(
            default_mode=settings_data.get("default_mode", "brief"),
            output_file=settings_data.get("output_file", "blog.md")
        )

        # Parse videos
        videos = []
        for video_data in data.get("videos", []):
            if isinstance(video_data, str):
                # Simple URL string
                videos.append(VideoConfig(url=video_data, mode=settings.default_mode))
            else:
                # Full video config object
                mode = video_data.get("mode", settings.default_mode)
                videos.append(VideoConfig(
                    url=video_data["url"],
                    mode=mode,
                    notes=video_data.get("notes")
                ))

        return cls(videos=videos, settings=settings)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "videos": [v.to_dict() for v in self.videos],
            "settings": self.settings.to_dict()
        }


def parse_config_file(config_path: str) -> BlogConfig:
    """Parse a configuration file (JSON or YAML).

    Args:
        config_path: Path to the configuration file

    Returns:
        BlogConfig object

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If format is invalid
    """
    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    content = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()

    if suffix == ".json":
        data = json.loads(content)
    elif suffix in (".yaml", ".yml"):
        try:
            import yaml
            data = yaml.safe_load(content)
        except ImportError:
            raise ImportError("读取 YAML 需要安装 pyyaml: pip install pyyaml")
    else:
        # Try JSON first, then YAML
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            try:
                import yaml
                data = yaml.safe_load(content)
            except ImportError:
                raise ValueError("无法解析配置文件。JSON 格式错误，且未安装 pyyaml")

    if not isinstance(data, dict):
        raise ValueError("配置文件必须是对象格式（包含 videos 和 settings）")

    if "videos" not in data:
        raise ValueError("配置文件必须包含 'videos' 字段")

    return BlogConfig.from_dict(data)


def create_urls_from_list(urls: List[str], output_file: str = "blog.md",
                          default_mode: str = "brief") -> BlogConfig:
    """Create a BlogConfig from a simple list of URLs.

    Args:
        urls: List of YouTube URLs
        output_file: Output blog file path
        default_mode: Default processing mode

    Returns:
        BlogConfig object
    """
    videos = [VideoConfig(url=url, mode=default_mode) for url in urls]
    settings = BlogSettings(default_mode=default_mode, output_file=output_file)
    return BlogConfig(videos=videos, settings=settings)
