"""YouTube 字幕获取模块 - 使用 youtube-transcript-api"""
from typing import Optional, List, Dict, Any
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

from src.translator import ContentTranslator


def extract_video_id(url: str) -> Optional[str]:
    """从 URL 提取视频 ID

    Args:
        url: YouTube URL

    Returns:
        视频 ID 或 None
    """
    import re
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    # 假设直接传入的是 video_id
    if len(url) == 11 and url.replace('-', '').replace('_', '').isalnum():
        return url
    return None


class YouTubeTranscriptFetcher:
    """获取 YouTube 视频字幕并翻译"""

    def __init__(self):
        self.translator = None  # 延迟初始化，只在需要翻译时创建

    def fetch_transcript(self, video_id: str, translate_to_chinese: bool = True,
                         language: Optional[str] = None) -> Optional[Dict]:
        """
        获取 YouTube 视频字幕

        Args:
            video_id: YouTube 视频 ID
            translate_to_chinese: 是否翻译成中文（如果是中文视频则自动跳过）
            language: 指定语言代码（如 'en', 'zh', 'ja'），None 则自动检测

        Returns:
            dict: 包含原文和翻译的字幕数据，如果没有字幕返回 None
        """
        try:
            # 获取可用字幕列表 - 新版 API 需要先创建实例
            api = YouTubeTranscriptApi()
            transcript_list = api.list(video_id)

            # 获取最佳字幕（指定语言或自动检测）
            transcript, language_code, language_name = self._get_best_transcript(
                video_id, transcript_list, preferred_lang=language
            )

            if not transcript:
                print(f"⚠️  视频 {video_id} 没有可用的字幕")
                return None

            # 检测是否为中文
            is_chinese = self._is_chinese_language(language_code)

            print(f"✓ 成功获取字幕")
            print(f"  语言: {language_name} ({language_code}){' [中文视频]' if is_chinese else ''}")
            print(f"  段落数: {len(transcript)}")

            # 合并文本
            full_text = self._merge_transcript(transcript)
            print(f"  文本长度: {len(full_text)} 字符")

            result = {
                "video_id": video_id,
                "language_code": language_code,
                "language_name": language_name,
                "language": f"{language_name} ({language_code})",  # 保持向后兼容
                "is_chinese": is_chinese,
                "full_text": full_text,
                "segments": transcript,
            }

            # 翻译成中文（如果原文不是中文且需要翻译）
            if translate_to_chinese:
                if is_chinese:
                    print("\n检测到中文视频，跳过翻译")
                    result["chinese_text"] = full_text
                else:
                    # 尝试翻译，如果没有 API Key 则跳过
                    chinese_text = self._translate_text(full_text)
                    if chinese_text:
                        result["chinese_text"] = chinese_text
                        print(f"✓ 翻译完成")
                    else:
                        print(f"⚠️  跳过翻译（无 API Key，保存原文）")
                        result["chinese_text"] = full_text

            return result

        except TranscriptsDisabled:
            print(f"⚠️  视频 {video_id} 已禁用字幕")
            return None
        except NoTranscriptFound:
            print(f"⚠️  视频 {video_id} 没有字幕")
            return None
        except Exception as e:
            print(f"❌ 获取字幕失败: {str(e)}")
            return None

    def _is_chinese_language(self, lang_code: str) -> bool:
        """检查语言代码是否为中文

        Args:
            lang_code: ISO 语言代码

        Returns:
            bool: 是否为中文
        """
        if not lang_code:
            return False
        lang_lower = lang_code.lower()
        # 支持 zh, zh-CN, zh-TW, zh-Hans, zh-Hant, cmn 等中文变体
        return lang_lower.startswith('zh') or lang_lower == 'cmn'

    def _get_best_transcript(self, video_id: str, transcript_list,
                              preferred_lang: Optional[str] = None) -> tuple:
        """获取最佳字幕（优先自动生成的字幕，通常是视频原语言）

        Args:
            video_id: YouTube 视频 ID
            transcript_list: 可用字幕列表
            preferred_lang: 优先语言代码（如 'en', 'zh'），None 则自动检测

        Returns:
            tuple: (transcript_data, language_code, language_name)
        """
        # 收集所有字幕
        auto_generated = []  # 自动生成的字幕
        manual = []  # 手动字幕

        for transcript in transcript_list:
            lang_code = transcript.language_code
            is_generated = transcript.is_generated

            info = {
                'transcript': transcript,
                'lang_code': lang_code,
                'lang_name': transcript.language,
                'is_generated': is_generated
            }

            if is_generated:
                auto_generated.append(info)
            else:
                manual.append(info)

        chosen = None

        # 1. 如果指定了语言，优先找该语言
        if preferred_lang:
            preferred_lower = preferred_lang.lower()
            # 先找手动字幕
            for info in manual:
                if info['lang_code'].lower().startswith(preferred_lower):
                    chosen = info
                    break
            # 再找自动生成
            if not chosen:
                for info in auto_generated:
                    if info['lang_code'].lower().startswith(preferred_lower):
                        chosen = info
                        break

        # 2. 未指定语言或没找到，优先找非英语的自动生成字幕（通常是原语言）
        if not chosen and auto_generated:
            # 优先非英语的自动生成字幕
            for info in auto_generated:
                if not info['lang_code'].lower().startswith('en'):
                    chosen = info
                    break
            # 如果没有非英语的，使用第一个自动生成的
            if not chosen:
                chosen = auto_generated[0]

        # 3. 使用第一个手动字幕
        if not chosen and manual:
            chosen = manual[0]

        # 打印可用字幕
        print("可用的字幕语言:")
        all_transcripts = manual + auto_generated
        for info in all_transcripts:
            lang_type = "自动生成" if info['is_generated'] else "手动"
            marker = " [将使用]" if info == chosen else ""
            print(f"  - {info['lang_name']} ({info['lang_code']}) [{lang_type}]{marker}")

        if not chosen:
            print(f"\n⚠️  没有找到可用的字幕")
            return None, None, None

        # 获取字幕数据
        try:
            transcript_data = chosen['transcript'].fetch()
            return transcript_data, chosen['lang_code'], chosen['lang_name']
        except Exception as e:
            print(f"获取字幕数据失败: {e}")
            return None, None, None

    def _merge_transcript(self, transcript_data) -> str:
        """将字幕段落合并成完整文本"""
        texts = []
        for segment in transcript_data:
            # 新版 API 返回的是对象，需要访问属性
            if hasattr(segment, 'text'):
                text = segment.text.strip()
            else:
                text = str(segment).strip()
            if text:
                texts.append(text)
        return ' '.join(texts)

    def _translate_text(self, text: str) -> str:
        """翻译文本为中文

        注意：此方法需要 OPENAI_API_KEY 环境变量。
        如果没有设置 API Key，将返回原文并提示用户使用 Claude AI 手动翻译。
        """
        import os

        # 检查是否有 API Key
        if not os.getenv('OPENAI_API_KEY'):
            print("  ⚠️  未设置 OPENAI_API_KEY，跳过自动翻译")
            print("  💡 提示：你可以使用 Claude AI 手动翻译博客中的原文")
            return text  # 返回原文，用户可以用 Claude AI 手动翻译

        # 有 API Key，使用 OpenAI 翻译
        if not self.translator:
            self.translator = ContentTranslator()

        # 分段翻译（避免超过 API 限制）
        max_chunk = 4000
        if len(text) <= max_chunk:
            return self.translator._translate_text(text)

        # 长文本分段翻译
        chunks = self._split_text(text, max_chunk)
        translated_chunks = []

        print(f"  文本较长，分 {len(chunks)} 段翻译...")
        for i, chunk in enumerate(chunks, 1):
            print(f"  翻译第 {i}/{len(chunks)} 段...")
            translated = self.translator._translate_text(chunk)
            translated_chunks.append(translated)

        return '\n\n'.join(translated_chunks)

    def _split_text(self, text: str, max_length: int) -> List[str]:
        """将长文本分段"""
        chunks = []
        sentences = text.replace('. ', '.|').split('|')
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk) + len(sentence) > max_length:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
            else:
                current_chunk += sentence + " "

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks if chunks else [text]

    def fetch_video_metadata(self, video_id_or_url: str) -> Optional[Dict[str, Any]]:
        """获取 YouTube 视频元数据（标题、作者、发布时间等）

        Args:
            video_id_or_url: YouTube 视频 ID 或 URL

        Returns:
            包含视频元数据的字典，失败返回 None
        """
        try:
            import yt_dlp
        except ImportError:
            print("⚠️  yt-dlp 未安装，无法获取视频元数据")
            return None

        # 提取视频 ID
        video_id = extract_video_id(video_id_or_url)
        if not video_id:
            video_id = video_id_or_url  # 假设传入的是 ID

        url = f"https://www.youtube.com/watch?v={video_id}"

        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                return {
                    "video_id": video_id,
                    "title": info.get("title", "Unknown Title"),
                    "description": info.get("description", ""),
                    "author": info.get("uploader", "Unknown Channel"),
                    "channel_url": info.get("uploader_url", ""),
                    "publish_date": info.get("upload_date"),  # YYYYMMDD format
                    "duration": info.get("duration"),  # seconds
                    "view_count": info.get("view_count"),
                    "thumbnail": info.get("thumbnail"),
                    "url": url
                }

        except Exception as e:
            print(f"⚠️  获取视频元数据失败: {e}")
            return None
