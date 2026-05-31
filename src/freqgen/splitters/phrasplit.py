"""Phrasplit sentence splitter — rule-based, no LLM required."""

from phrasplit import split_long_lines

from .base import SentenceSplitter

# 跟读场景：每段目标45字符，在句子/逗号/词边界三级拆分
_MAX_LENGTH = 45


class PhrasplitSplitter(SentenceSplitter):
    """Split a sentence into short chunks using phrasplit split_long_lines.

    Strategy (split_long_lines 内置):
      1. 先在句子边界 (.!?) 拆分
      2. 若仍超长，在逗号/分号处拆分
      3. 若仍超长，在词边界强制截断

    max_length=45：跟读节奏清晰，意群完整。
    """

    def split(self, sentence: str) -> list[str]:
        """Split at natural pause points. Returns list of short chunks."""
        if not sentence or not sentence.strip():
            return [sentence]

        text = sentence.strip()
        parts = split_long_lines(text, max_length=_MAX_LENGTH, use_spacy=False)
        parts = [p.strip() for p in parts if p.strip()]

        if len(parts) <= 1:
            return [sentence]
        return parts
