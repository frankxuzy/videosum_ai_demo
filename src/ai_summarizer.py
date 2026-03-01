"""AI Summarizer module for generating brief summaries using Claude API."""
import os
from typing import Optional


def generate_brief_summary(transcript_text: str, title: str = "") -> str:
    """Generate a 3-5 sentence summary of the video content using Claude API.

    Args:
        transcript_text: The video transcript text
        title: Video title for context

    Returns:
        A 3-5 sentence Chinese summary
    """
    try:
        import anthropic
    except ImportError:
        raise ImportError(
            "anthropic SDK is required for AI summarization. "
            "Install it with: pip install anthropic"
        )

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY environment variable is required for brief mode. "
            "Please set it in your .env file or environment."
        )

    client = anthropic.Anthropic(api_key=api_key)

    # Limit transcript length to avoid token limits (roughly 8000 chars ~ 2000 tokens)
    max_chars = 8000
    truncated_text = transcript_text[:max_chars]
    if len(transcript_text) > max_chars:
        truncated_text += "\n\n[内容已截断...]"

    prompt = f"""请阅读以下视频字幕，用 3-5 句话总结其核心内容。

要求：
1. 用中文回答
2. 简洁明了，突出要点
3. 不要照搬原文句子，用自己的话总结
4. 控制在 3-5 句话以内

视频标题: {title}

字幕内容:
{truncated_text}

请输出 3-5 句话的简述:"""

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            temperature=0.3,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        summary = response.content[0].text.strip()
        return summary

    except Exception as e:
        raise RuntimeError(f"Claude API call failed: {e}")


def generate_brief_summary_with_openai(transcript_text: str, title: str = "") -> str:
    """Fallback: Generate summary using OpenAI API if Claude is not available.

    Args:
        transcript_text: The video transcript text
        title: Video title for context

    Returns:
        A 3-5 sentence Chinese summary
    """
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError(
            "openai SDK is required for AI summarization. "
            "Install it with: pip install openai"
        )

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable is required. "
            "Please set it in your .env file or environment."
        )

    client = OpenAI(api_key=api_key)

    # Limit transcript length to avoid token limits
    max_chars = 8000
    truncated_text = transcript_text[:max_chars]
    if len(transcript_text) > max_chars:
        truncated_text += "\n\n[内容已截断...]"

    prompt = f"""请阅读以下视频字幕，用 3-5 句话总结其核心内容。

要求：
1. 用中文回答
2. 简洁明了，突出要点
3. 不要照搬原文句子，用自己的话总结
4. 控制在 3-5 句话以内

视频标题: {title}

字幕内容:
{truncated_text}

请输出 3-5 句话的简述:"""

    try:
        response = client.chat.completions.create(
            model=os.getenv("SUMMARIZER_MODEL", "gpt-4o"),
            max_tokens=500,
            temperature=0.3,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        summary = response.choices[0].message.content.strip()
        return summary

    except Exception as e:
        raise RuntimeError(f"OpenAI API call failed: {e}")
