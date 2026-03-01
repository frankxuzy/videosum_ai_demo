"""Content translation module using OpenAI GPT."""

import os
from typing import Dict, Optional
from openai import OpenAI


class ContentTranslator:
    """Translate content to Chinese using OpenAI GPT models."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """Initialize translator.

        Args:
            api_key: OpenAI API key (optional, defaults to env var)
            model: Model to use (defaults to env var or gpt-4o)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")

        self.model = model or os.getenv("TRANSLATOR_MODEL", "gpt-4o")
        self.client = OpenAI(api_key=self.api_key)

    def translate_to_chinese(self, content: Dict[str, any]) -> Dict[str, any]:
        """Translate content to Chinese.

        Args:
            content: Dictionary with summary, key_points, and topics

        Returns:
            Dictionary with translated content
        """
        # Translate summary
        translated_summary = self._translate_text(content.get('summary', ''))

        # Translate key points
        translated_key_points = []
        for point in content.get('key_points', []):
            translated = self._translate_text(point)
            translated_key_points.append(translated)

        # Translate topics
        translated_topics = []
        for topic in content.get('topics', []):
            translated = self._translate_text(topic)
            translated_topics.append(translated)

        return {
            "summary": translated_summary,
            "key_points": translated_key_points,
            "topics": translated_topics
        }

    def _translate_text(self, text: str) -> str:
        """Translate a single text to Chinese.

        Args:
            text: Text to translate

        Returns:
            Translated text
        """
        if not text or not text.strip():
            return ""

        prompt = f"""Translate the following text to natural, fluent Chinese (简体中文). Maintain the meaning and tone:

{text}

Translation:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional translator. Translate the given text to natural, fluent Chinese (简体中文) while preserving the original meaning and tone."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            raise Exception(f"Translation failed: {str(e)}")
