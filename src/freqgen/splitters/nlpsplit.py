"""NLP-based sentence segmenter using spaCy dependency parsing.

Splittes a sentence at grammatical clause boundaries rather than
character-count boundaries, producing linguistically meaningful chunks
for read-along practice.

Requires: spacy + en_core_web_sm (auto-downloaded on first use)
"""

import re
from pathlib import Path

from .base import SentenceSplitter

# Minimum segment length — shorter segments get merged with neighbors
_MIN_SEG_LEN = 18
# Maximum segment length — triggers re-splitting if exceeded
_MAX_SEG_LEN = 60

# Conjunction/transition words that make good split points
_CONJUNCTIONS = {
    "and", "but", "or", "nor", "yet", "so",
    "because", "although", "though", "while", "whereas",
    "when", "whenever", "if", "unless", "until", "once",
    "since", "as", "after", "before",
}

# Prepositions that often start long adverbial phrases
_PREPOSITIONS = {
    "in", "on", "at", "by", "for", "with", "without",
    "from", "to", "about", "through", "across", "during",
    "despite", "including", "according", "regarding",
}


class NlpSplitter(SentenceSplitter):
    """Split a sentence at grammatical clause boundaries using spaCy.

    Strategy:
      1. Parse sentence with spaCy dependency parser
      2. Find split points at clause boundaries (conj, advcl, relcl, ccomp)
      3. Cut at long prepositional phrase boundaries (>10 tokens)
      4. Merge segments <_MIN_SEG_LEN with neighbors
      5. If spaCy unavailable, fall back to rule-based splitting
    """

    def __init__(self):
        self._nlp = None

    def _ensure_nlp(self):
        """Lazy-load spaCy model, auto-downloading if needed."""
        if self._nlp is not None:
            return
        try:
            import spacy
            try:
                self._nlp = spacy.load("en_core_web_sm")
            except OSError:
                import subprocess
                import sys
                print("Downloading spaCy model en_core_web_sm...", file=sys.stderr)
                subprocess.check_call(
                    [sys.executable, "-m", "spacy", "download", "en_core_web_sm"]
                )
                self._nlp = spacy.load("en_core_web_sm")
        except ImportError:
            raise ImportError(
                "spacy not installed. Run: pip install spacy"
            )

    def split(self, sentence: str) -> list[str]:
        if not sentence or not sentence.strip():
            return [sentence]

        text = sentence.strip()

        # If short enough, keep as one segment
        if len(text) <= _MAX_SEG_LEN:
            return [text]

        # Try NLP-based split
        try:
            self._ensure_nlp()
            segments = self._split_by_deps(text)
        except ImportError:
            # Fallback to improved rule-based
            segments = self._split_by_rules(text)

        # Post-process: merge short segments
        segments = self._merge_short(segments)

        return segments if len(segments) > 1 else [text]

    def _split_by_deps(self, text: str) -> list[str]:
        """Split using spaCy dependency parse.

        Uses token.idx (character offset) for all string slicing,
        not token.i (sequential token index).
        """
        doc = self._nlp(text)
        # Collect character-offset split points
        split_chars: set[int] = set()

        for token in doc:
            # ── Coordinated clauses (and/but/or) ──
            if token.dep_ == "conj" and token.pos_ == "CCONJ":
                split_chars.add(token.idx)

            # ── Adverbial clauses (because/although/when/if) ──
            elif token.dep_ == "advcl":
                markers = [c for c in token.children if c.dep_ == "mark"]
                if markers:
                    split_chars.add(markers[0].idx)
                elif token.idx > 0:
                    split_chars.add(token.idx)

            # ── Complement clauses (that...) ──
            elif token.dep_ == "ccomp":
                markers = [c for c in token.children if c.dep_ == "mark"]
                if markers:
                    split_chars.add(markers[0].idx)

            # ── Relative clauses (who/which/that) ──
            elif token.dep_ == "relcl":
                # The relative pronoun is a child of the relcl verb, not its head
                rels = [c for c in token.children
                        if c.dep_ in ("nsubj", "nsubjpass", "relcl")
                        and c.text.lower() in ("who", "which", "that")
                        and c.idx > 0]
                if rels:
                    split_chars.add(rels[0].idx)

            # ── Long prepositional phrases ──
            elif token.dep_ == "prep" and token.idx > 0:
                subtree_len = max(t.idx + len(t.text) for t in token.subtree) - token.idx
                if subtree_len >= 50:  # ≥50 characters = long PP
                    split_chars.add(token.idx)

        # Apply splits in ascending character order
        splits = sorted(split_chars)
        spans = []
        prev = 0
        for pos in splits:
            if pos <= prev:
                continue
            span_text = text[prev:pos].strip()
            if span_text:
                spans.append(span_text)
            prev = pos
        remaining = text[prev:].strip()
        if remaining:
            spans.append(remaining)

        return spans if len(spans) > 1 else [text]

    def _split_by_rules(self, text: str) -> list[str]:
        """Rule-based split with grammar cues (fallback when spaCy unavailable)."""
        tokens = text.split()
        candidates = []

        for i, token in enumerate(tokens):
            clean = token.strip('",;:!?.()-—\u2013\u2014"\u201c\u201d\u2018\u2019').lower()

            # Clause-level conjunctions (and/but/or/because/although...)
            if clean in _CONJUNCTIONS:
                candidates.append(i)

            # Long prepositional phrases — cut before the preposition
            # Only if preceded by enough content (>15 chars before this point)
            if clean in _PREPOSITIONS and i > 0:
                prev_text_len = sum(len(t) + 1 for t in tokens[:i])
                if prev_text_len > 20:
                    candidates.append(i)

        # Build segments
        if not candidates:
            return [text]

        segments = []
        prev = 0
        for pos in candidates:
            segment = " ".join(tokens[prev:pos])
            if segment.strip():
                segments.append(segment.strip())
            prev = pos
        remaining = " ".join(tokens[prev:])
        if remaining.strip():
            segments.append(remaining.strip())

        return segments if len(segments) > 1 else [text]

    def _merge_short(self, segments: list[str]) -> list[str]:
        """Merge segments shorter than _MIN_SEG_LEN into neighbors."""
        if len(segments) <= 1:
            return segments

        result = []
        i = 0
        while i < len(segments):
            current = segments[i]

            # If current is too short and there's a next segment
            if len(current) < _MIN_SEG_LEN and i + 1 < len(segments):
                # Merge with next
                merged = current + " " + segments[i + 1]
                # Check if merging makes the whole thing too long
                if len(merged) <= _MAX_SEG_LEN + 10:
                    result.append(merged)
                    i += 2
                    continue
                else:
                    # Try merging with previous instead
                    if result:
                        prev_merged = result[-1] + " " + current
                        if len(prev_merged) <= _MAX_SEG_LEN + 10:
                            result[-1] = prev_merged
                            i += 1
                            continue
                    # Can't merge either way, keep as-is
                    result.append(current)
                    i += 1
                    continue

            # If current is too short and it's the last segment, merge with previous
            if len(current) < _MIN_SEG_LEN and result:
                result[-1] = result[-1] + " " + current
                i += 1
                continue

            result.append(current)
            i += 1

        return result
