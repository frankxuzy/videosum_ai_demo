"""YouTube 音频下载模块"""
import re
import subprocess
import sys
from typing import Optional
import yt_dlp
from pathlib import Path
from tqdm import tqdm


class YouTubeDownloader:
    """YouTube 视频音频下载器"""

    def __init__(self, temp_dir: str = "./temp"):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from various URL formats.

        Args:
            url: YouTube URL (standard, short, or embed)

        Returns:
            Video ID string or None if not found
        """
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def download_audio(self, url: str, progress_callback=None) -> dict:
        """
        下载 YouTube 视频音频

        Args:
            url: YouTube 视频 URL
            progress_callback: 可选的进度回调函数

        Returns:
            dict: 包含音频路径和视频信息
        """
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': str(self.temp_dir / '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            # Bypass 403 errors
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'referer': 'https://www.youtube.com/',
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
            },
            'cookiesfrombrowser': None,
            'nocheckcertificate': True,
            'age_limit': None,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # 获取视频信息
                info = ydl.extract_info(url, download=False)
                video_id = info['id']
                audio_path = self.temp_dir / f"{video_id}.mp3"

                # 如果已存在则跳过下载
                if audio_path.exists():
                    print(f"音频已存在: {audio_path}")
                    return self._build_result(info, audio_path, url)

                # 使用进度条下载
                print(f"正在下载: {info['title']}")
                self._download_with_progress(ydl, url, info)

                return self._build_result(info, audio_path, url)

        except Exception as e:
            error_msg = str(e)
            if '403' in error_msg or 'Forbidden' in error_msg:
                print("⚠️  YouTube API 返回 403 错误，尝试使用命令行方式下载...")
                return self._download_with_cli(url, progress_callback)
            raise

    def _download_with_progress(self, ydl, url: str, info: dict):
        """使用进度条显示下载进度"""
        duration = info.get('duration', 0)

        with tqdm(total=duration, unit='s', desc="下载进度") as pbar:
            last_progress = [0]

            def progress_hook(d):
                if d['status'] == 'downloading':
                    downloaded = d.get('downloaded_bytes', 0)
                    total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
                    if total > 0:
                        progress = int(downloaded * duration / total)
                        pbar.update(progress - last_progress[0])
                        last_progress[0] = progress
                elif d['status'] == 'finished':
                    pbar.update(duration - last_progress[0])

            ydl_opts = {
                'progress_hooks': [progress_hook],
                'quiet': True,
                'no_warnings': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl_progress:
                ydl_progress.download([url])

    def _download_with_cli(self, url: str, progress_callback=None) -> dict:
        """使用命令行 yt-dlp 下载（作为 403 错误的回退）"""
        video_id = self.extract_video_id(url)
        if not video_id:
            raise ValueError(f"无法从 URL 提取视频 ID: {url}")

        output_path = self.temp_dir / f"{video_id}.mp3"

        # 如果已存在则跳过
        if output_path.exists():
            print(f"音频已存在: {output_path}")
            # 获取视频信息
            cmd = [
                sys.executable, '-m', 'yt_dlp',
                '--dump-json',
                '--skip-download',
                url
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            info = {}
            if result.returncode == 0:
                import json
                info = json.loads(result.stdout.strip().split('\n')[0])
            return self._build_result(info, output_path, url)

        print(f"使用命令行下载视频: {video_id}")

        # 先获取视频信息以检查可用格式
        cmd_check = [
            sys.executable, '-m', 'yt_dlp',
            '--dump-json',
            '--skip-download',
            url
        ]
        result = subprocess.run(cmd_check, capture_output=True, text=True)
        has_audio_only = False
        info = {}
        if result.returncode == 0:
            import json
            info = json.loads(result.stdout.strip().split('\n')[0])
            # 检查是否有纯音频格式
            formats = info.get('formats', [])
            for fmt in formats:
                if fmt.get('vcodec') == 'none' and fmt.get('acodec') != 'none':
                    has_audio_only = True
                    break

        # 构建下载命令
        if has_audio_only:
            # 有纯音频格式
            cmd = [
                sys.executable, '-m', 'yt_dlp',
                '-f', 'bestaudio[ext=m4a]/bestaudio/best',
                '--extract-audio',
                '--audio-format', 'mp3',
                '--audio-quality', '192K',
                '-o', str(self.temp_dir / '%(id)s.%(ext)s'),
                '--newline',
                '--progress',
                url
            ]
        else:
            # 没有纯音频格式，下载视频后提取音频
            print("该视频没有纯音频格式，将下载视频后提取音频...")
            cmd = [
                sys.executable, '-m', 'yt_dlp',
                '-f', 'best[height<=720]/best',  # 限制分辨率以加快下载
                '--extract-audio',
                '--audio-format', 'mp3',
                '--audio-quality', '192K',
                '-o', str(self.temp_dir / '%(id)s.%(ext)s'),
                '--newline',
                '--progress',
                url
            ]

        # 执行下载并显示进度
        print("开始下载...")
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        # 解析进度输出
        for line in process.stdout:
            line = line.strip()
            if progress_callback:
                progress_callback(line)
            elif '[download]' in line and '%' in line:
                # 提取进度百分比
                try:
                    parts = line.split()
                    for part in parts:
                        if '%' in part and part.replace('%', '').replace('.', '').isdigit():
                            percent = float(part.replace('%', ''))
                            print(f"\r下载进度: {percent:.1f}%", end='', flush=True)
                            break
                except:
                    pass
            elif 'Destination:' in line or 'Extracting audio' in line:
                print(f"\n{line}")

        process.wait()
        print()  # 换行

        if process.returncode != 0:
            print("⚠️  命令行下载也失败了。这可能是 YouTube 的限制。")
            print("尝试方法：")
            print("1. 等待几分钟后重试")
            print("2. 使用 --download-only 模式，然后手动下载音频文件到 temp/ 目录")
            print(f"3. 手动下载音频文件并命名为: {output_path}")
            raise RuntimeError(f"YouTube 下载被阻止 (HTTP 403)。视频可能受到保护或限制。")

        # 获取视频信息
        cmd_info = [
            sys.executable, '-m', 'yt_dlp',
            '--dump-json',
            '--skip-download',
            url
        ]
        result = subprocess.run(cmd_info, capture_output=True, text=True)
        info = {}
        if result.returncode == 0:
            import json
            info = json.loads(result.stdout.strip().split('\n')[0])

        return self._build_result(info, output_path, url)

    def _build_result(self, info: dict, audio_path: Path, url: str) -> dict:
        """构建返回结果字典"""
        return {
            "audio_path": str(audio_path),
            "title": info.get('title', 'Unknown'),
            "author": info.get('uploader', 'Unknown'),
            "duration": info.get('duration', 0),
            "video_id": info.get('id', ''),
            "url": url,
            "thumbnail": info.get('thumbnail', ''),
            "description": info.get('description', ''),
        }

    def cleanup(self, audio_path: str):
        """清理临时音频文件"""
        path = Path(audio_path)
        if path.exists():
            path.unlink()
            print(f"已清理: {path}")
