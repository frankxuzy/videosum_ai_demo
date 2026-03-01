"""语音转文字模块 - 使用本地 Whisper"""
import whisper
import os
from pathlib import Path
from tqdm import tqdm


class AudioTranscriber:
    """本地 Whisper 语音转文字"""

    def __init__(self, model_size: str = "base"):
        """
        初始化转录器

        Args:
            model_size: 模型大小 (tiny, base, small, medium, large)
                - tiny: 最快，准确率较低
                - base: 平衡速度和准确率（推荐）
                - small/medium/large: 更准但更慢
        """
        print(f"正在加载 Whisper 模型: {model_size} ...")
        self.model = whisper.load_model(model_size)
        print("✓ 模型加载完成")

    def transcribe(self, audio_path: str, output_dir: str = "./output") -> str:
        """
        转录音频文件

        Args:
            audio_path: 音频文件路径
            output_dir: 转录文本保存目录

        Returns:
            str: 转录的完整文本
        """
        print(f"\n开始转录: {Path(audio_path).name}")

        # 使用自定义进度回调
        result = self._transcribe_with_progress(audio_path)

        text = result["text"].strip()

        # 保存转录文本
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        audio_name = Path(audio_path).stem
        transcript_file = output_path / f"{audio_name}_transcript.txt"

        # 保存完整转录（带时间戳）
        with open(transcript_file, "w", encoding="utf-8") as f:
            f.write(f"# 转录文本\n\n")
            for segment in result["segments"]:
                start = self._format_time(segment["start"])
                end = self._format_time(segment["end"])
                f.write(f"[{start} - {end}] {segment['text']}\n")

        print(f"✓ 转录完成，已保存: {transcript_file}")
        print(f"  文本长度: {len(text)} 字符")
        print(f"  段落数: {len(result['segments'])}")
        return text

    def _transcribe_with_progress(self, audio_path: str):
        """使用进度条转录音频"""
        # 获取音频时长
        audio = whisper.load_audio(audio_path)
        duration = len(audio) / 16000  # Whisper 使用 16kHz

        # 创建进度条
        pbar = tqdm(total=100, unit='%', desc="转录进度", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]')

        # 自定义回调函数
        def progress_callback(seek, total):
            percent = int(seek / total * 100)
            pbar.n = percent
            pbar.refresh()

        try:
            result = self.model.transcribe(
                audio_path,
                verbose=False,
                language=None,  # 自动检测语言
                condition_on_previous_text=True,
            )

            # 手动更新进度条到 100%
            pbar.n = 100
            pbar.refresh()
            pbar.close()

            # 显示检测到的语言
            language = result.get('language', 'unknown')
            print(f"  检测到语言: {language}")

            return result

        except Exception as e:
            pbar.close()
            raise e

    def _format_time(self, seconds: float) -> str:
        """将秒数格式化为 MM:SS"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
