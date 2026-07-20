"""Sentence splitters — NLP-enhanced text segmentation.

Provider selection (auto mode):
  1. nlp       — spaCy dependency parse (best quality, requires spacy)
  2. rules     — improved rule-based with grammar cues (no dependencies)
  3. phrasplit — original char-count splitter (fallback)

The CLI's --splitter option can select these explicitly or use 'auto'.
"""

from .base import SentenceSplitter


def get_splitter(provider: str = "auto") -> SentenceSplitter:
    """Factory: return a SentenceSplitter by name.

    Args:
        provider: one of "auto", "nlp", "rules", "sentence", "phrasplit"
    """
    if provider == "sentence":
        from .sentencesplit import SentenceBoundarySplitter
        return SentenceBoundarySplitter()

    if provider == "phrasplit":
        from .phrasplit import PhrasplitSplitter
        return PhrasplitSplitter()

    if provider == "nlp":
        from .nlpsplit import NlpSplitter
        return NlpSplitter()

    if provider == "rules":
        from .phrasplit import PhrasplitSplitter
        return PhrasplitSplitter()

    if provider == "auto":
        return _auto_select()

    raise ValueError(f"Unknown splitter provider: {provider}")


def _auto_select() -> SentenceSplitter:
    """Auto-select best available splitter.

    Priority: nlp > rules > phrasplit
    """
    # Try NLP (spaCy)
    try:
        from .nlpsplit import NlpSplitter
        # Quick probe — try to import spacy
        import spacy  # noqa: F401
        return NlpSplitter()
    except ImportError:
        pass

    # Fallback to improved rules
    from .phrasplit import PhrasplitSplitter
    return PhrasplitSplitter()


__all__ = ["SentenceSplitter", "get_splitter"]
