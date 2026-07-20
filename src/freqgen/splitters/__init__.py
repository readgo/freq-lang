"""Sentence splitters — rule-based text segmentation.

Provider selection (auto mode):
  1. rules     — improved rule-based with grammar cues (no dependencies)
  2. phrasplit — original char-count splitter (fallback)

The CLI's --splitter option can select these explicitly or use 'auto'.
"""

from .base import SentenceSplitter


def get_splitter(provider: str = "auto") -> SentenceSplitter:
    """Factory: return a SentenceSplitter by name.

    Args:
        provider: one of "auto", "rules", "sentence", "phrasplit"
    """
    if provider == "sentence":
        from .sentencesplit import SentenceBoundarySplitter
        return SentenceBoundarySplitter()

    if provider == "phrasplit":
        from .phrasplit import PhrasplitSplitter
        return PhrasplitSplitter()

    if provider == "rules":
        from .phrasplit import PhrasplitSplitter
        return PhrasplitSplitter()

    if provider in ("auto", "nlp"):
        # nlp provider is no longer available; rules is the default
        from .phrasplit import PhrasplitSplitter
        return PhrasplitSplitter()

    raise ValueError(f"Unknown splitter provider: {provider}")


__all__ = ["SentenceSplitter", "get_splitter"]
