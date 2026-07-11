"""Sentence splitters — rule-based text segmentation."""

from .base import SentenceSplitter

def get_splitter(provider: str = "sentence") -> SentenceSplitter:
    """Factory: return a SentenceSplitter by name."""
    if provider == "sentence":
        from .sentencesplit import SentenceBoundarySplitter
        return SentenceBoundarySplitter()
    if provider == "phrasplit":
        from .phrasplit import PhrasplitSplitter
        return PhrasplitSplitter()
    raise ValueError(f"Unknown splitter provider: {provider}")

__all__ = ["SentenceSplitter", "get_splitter"]
