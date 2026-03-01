"""Markdown 文件生成模块"""
from pathlib import Path
from datetime import datetime


class MarkdownWriter:
    """生成 Markdown 总结文件"""

    def __init__(self, output_dir: str = "./output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_summary_template(
        self,
        video_info: dict,
        transcript_path: str,
        summary: str = "",
        key_points: list = None,
        output_filename: str = None
    ) -> str:
        """
        创建 Markdown 总结文件（包含待填写的总结部分）

        Args:
            video_info: 视频信息字典
            transcript_path: 转录文本文件路径
            summary: 中文摘要（由 Claude 填写）
            key_points: 关键要点列表（由 Claude 填写）
            output_filename: 输出文件名

        Returns:
            str: 生成的文件路径
        """
        if key_points is None:
            key_points = []

        if output_filename is None:
            safe_title = self._sanitize_filename(video_info['title'])
            output_filename = f"{safe_title}.md"

        output_path = self.output_dir / output_filename

        # 格式化时长
        duration_mins = video_info['duration'] // 60
        duration_secs = video_info['duration'] % 60

        # 生成 Markdown 内容
        content = f"""# {video_info['title']}

## 元信息

| 项目 | 内容 |
|------|------|
| **视频链接** | [{video_info['url']}]({video_info['url']}) |
| **频道** | {video_info['author']} |
| **处理日期** | {datetime.now().strftime('%Y-%m-%d %H:%M')} |
| **视频时长** | {duration_mins}:{duration_secs:02d} |

---

## 中文摘要

<!-- Claude: 请在此处填写中文摘要 -->
{summary if summary else "（待填写）"}

---

## 关键要点

<!-- Claude: 请在此处填写关键要点 -->
"""

        if key_points:
            for point in key_points:
                content += f"- {point}\n"
        else:
            content += "- （待填写）\n"

        content += f"""
---

## 完整转录

<details>
<summary>点击展开完整转录</summary>

<!-- 转录文件位置: {transcript_path} -->

"""

        # 读取转录内容
        transcript_file = Path(transcript_path)
        if transcript_file.exists():
            with open(transcript_file, "r", encoding="utf-8") as f:
                content += f.read()
        else:
            content += "（转录文件未找到）"

        content += "\n</details>\n"

        # 保存文件
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"Markdown 文件已生成: {output_path}")
        return str(output_path)

    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名中的非法字符"""
        import re
        # 移除或替换非法字符
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # 限制长度
        if len(filename) > 100:
            filename = filename[:100]
        return filename.strip()

    def _format_duration(self, seconds: int) -> str:
        """Format duration in seconds to human readable string.

        Args:
            seconds: Duration in seconds

        Returns:
            Formatted string (H:MM:SS or M:SS)
        """
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"
