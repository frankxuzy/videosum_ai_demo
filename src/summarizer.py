"""Content summarization module using OpenAI GPT."""

import os
from typing import Dict, Optional, List
from openai import OpenAI


class ContentSummarizer:
    """Summarize content using OpenAI GPT models."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """Initialize summarizer.

        Args:
            api_key: OpenAI API key (optional, defaults to env var)
            model: Model to use (defaults to env var or gpt-4o)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")

        self.model = model or os.getenv("SUMMARIZER_MODEL", "gpt-4o")
        self.client = OpenAI(api_key=self.api_key)

    def _split_text(self, text: str, max_length: int = 4000) -> List[str]:
        """Split text into chunks for processing.

        Args:
            text: Input text
            max_length: Maximum chunk length

        Returns:
            List of text chunks
        """
        chunks = []
        current_chunk = ""

        sentences = text.replace('\n', ' ').split('. ')

        for sentence in sentences:
            if len(current_chunk) + len(sentence) > max_length:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
            else:
                current_chunk += sentence + ". "

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks if chunks else [text]

    def summarize(self, text: str, video_info: Optional[Dict] = None) -> Dict[str, any]:
        """Summarize the given text.

        Args:
            text: Text to summarize
            video_info: Optional video metadata

        Returns:
            Dictionary with summary, key_points, and topics
        """
        title = video_info.get('title', 'Unknown') if video_info else 'Unknown'

        chunks = self._split_text(text)

        if len(chunks) == 1:
            return self._summarize_chunk(chunks[0], title)

        # For long texts, summarize each chunk and then combine
        chunk_summaries = []
        for chunk in chunks:
            result = self._summarize_chunk(chunk, title)
            chunk_summaries.append(result['summary'])

        # Combine chunk summaries
        combined_text = "\n\n".join(chunk_summaries)
        return self._summarize_chunk(combined_text, title, is_final=True)

    def _summarize_chunk(self, text: str, title: str, is_final: bool = False) -> Dict[str, any]:
        """Summarize a single chunk of text.

        Args:
            text: Text chunk to summarize
            title: Video title
            is_final: Whether this is the final summary

        Returns:
            Dictionary with summary, key_points, and topics
        """
        if is_final:
            prompt = f"""Based on the following summaries of a video titled "{title}", provide a final comprehensive summary.

Summaries:
{text}

Please provide a structured response in the following format:

SUMMARY:
[2-3 paragraph comprehensive summary]

KEY_POINTS:
- [Key point 1]
- [Key point 2]
- [Key point 3]
- [Key point 4]
- [Key point 5]

TOPICS:
- [Topic 1]
- [Topic 2]
- [Topic 3]
"""
        else:
            prompt = f"""Please summarize the following transcript from a video titled "{title}".

Transcript:
{text}

Please provide a structured response in the following format:

SUMMARY:
[1-2 paragraph summary]

KEY_POINTS:
- [Key point 1]
- [Key point 2]
- [Key point 3]

TOPICS:
- [Topic 1]
- [Topic 2]
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that summarizes video transcripts accurately and extracts key information."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
            )

            content = response.choices[0].message.content
            return self._parse_summary_response(content)

        except Exception as e:
            raise Exception(f"Summarization failed: {str(e)}")

    def _parse_summary_response(self, content: str) -> Dict[str, any]:
        """Parse the structured summary response.

        Args:
            content: Raw response content

        Returns:
            Dictionary with summary, key_points, and topics
        """
        result = {
            "summary": "",
            "key_points": [],
            "topics": []
        }

        lines = content.split('\n')
        current_section = None

        for line in lines:
            line = line.strip()

            if line.startswith('SUMMARY:'):
                current_section = 'summary'
                continue
            elif line.startswith('KEY_POINTS:'):
                current_section = 'key_points'
                continue
            elif line.startswith('TOPICS:'):
                current_section = 'topics'
                continue

            if not line:
                continue

            if current_section == 'summary':
                result['summary'] += line + ' '
            elif current_section == 'key_points' and line.startswith('-'):
                result['key_points'].append(line[1:].strip())
            elif current_section == 'topics' and line.startswith('-'):
                result['topics'].append(line[1:].strip())

        result['summary'] = result['summary'].strip()

        return result
