"""中文摘要生成器 - 使用 OpenAI 或 Anthropic API 自动生成视频摘要."""

import os
from typing import Optional

# Try to import OpenAI
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

# Try to import Anthropic
try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


class SummaryGenerator:
    """自动生成中文摘要."""

    def __init__(self, provider: Optional[str] = None):
        """初始化摘要生成器.

        Args:
            provider: "openai" 或 "anthropic"，默认自动检测
        """
        self.provider = provider or self._detect_provider()
        self.client = self._init_client()
        self.model = self._get_model()

    def _detect_provider(self) -> str:
        """检测可用的 API provider."""
        # Check for Anthropic (support both standard and custom config)
        if (os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN")) and HAS_ANTHROPIC:
            return "anthropic"
        elif os.getenv("OPENAI_API_KEY") and HAS_OPENAI:
            return "openai"
        else:
            return None

    def _get_model(self) -> str:
        """获取模型名称."""
        if self.provider == "anthropic":
            return os.getenv("ANTHROPIC_MODEL") or os.getenv("ANTHROPIC_DEFAULT_SONNET_MODEL") or "claude-sonnet-4-20250514"
        elif self.provider == "openai":
            return os.getenv("SUMMARIZER_MODEL", "gpt-4o")
        return ""

    def _init_client(self):
        """初始化 API client."""
        if self.provider == "anthropic":
            # Support both standard and custom Anthropic config
            api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN")
            base_url = os.getenv("ANTHROPIC_BASE_URL")

            if base_url:
                # Custom endpoint (e.g., DashScope)
                return Anthropic(api_key=api_key, base_url=base_url)
            else:
                return Anthropic(api_key=api_key)
        elif self.provider == "openai":
            return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        return None

    def is_available(self) -> bool:
        """检查是否有可用的 API."""
        return self.client is not None

    def generate_brief_summary(self, text: str, title: str = "") -> str:
        """生成 Brief 模式的简短摘要（3-5 个要点）.

        Args:
            text: 视频字幕文本
            title: 视频标题

        Returns:
            中文摘要文本
        """
        if not self.is_available():
            return None

        prompt = f"""请总结以下视频内容的核心要点，生成 3-5 条中文摘要。

视频标题: {title}

字幕内容:
{text}

要求:
1. 用中文总结核心要点，每条要点用一句话概括
2. 每条要点以序号开头，加粗标题，然后用冒号分隔详细说明
3. 格式示例:
   1. **标题**: 详细说明内容...

请直接输出摘要内容，不要其他废话:"""

        return self._call_api(prompt)

    def generate_detailed_notes(self, text: str, title: str = "") -> str:
        """生成 Detailed 模式的详细学习笔记.

        Args:
            text: 视频字幕文本
            title: 视频标题

        Returns:
            中文学习笔记
        """
        if not self.is_available():
            return None

        prompt = f"""请将以下视频内容整理成学习笔记格式，分章节总结要点。

视频标题: {title}

字幕内容:
{text}

要求:
1. 用中文整理，不要直接拷贝原文，要用自己的话总结
2. 分章节组织，每个章节用 #### 标题
3. 每个章节下用列表形式列出关键要点
4. 保留重要的技术术语和概念
5. 格式清晰，便于阅读

请直接输出学习笔记内容:"""

        return self._call_api(prompt)

    def _call_api(self, prompt: str) -> str:
        """调用 API 生成内容."""
        try:
            if self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    messages=[{"role": "user", "content": prompt}]
                )
                # Handle different content block types (GLM uses ThinkingBlock)
                result_parts = []
                for block in response.content:
                    if hasattr(block, 'text'):
                        result_parts.append(block.text)
                    elif hasattr(block, 'type') and block.type == 'text':
                        result_parts.append(block.text if hasattr(block, 'text') else str(block))
                return "\n".join(result_parts).strip() if result_parts else None

            elif self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "你是一个专业的视频内容总结助手，擅长用中文整理视频要点。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                )
                return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"  ⚠️ API 调用失败: {e}")
            return None

        return None