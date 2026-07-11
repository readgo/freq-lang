"""Sentence-boundary splitter — split at . ! ? into complete sentences."""

import re

from .base import SentenceSplitter


# Abbreviations ending with period that should NOT trigger sentence split
_ABBREVIATIONS = {
    "mr", "mrs", "ms", "dr", "prof", "sr", "jr", "st",
    "vs", "etc", "dept", "est", "govt", "inc", "corp", "ltd",
    "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "oct", "nov", "dec",
    "ave", "blvd", "rd", "ln",
}

# Compound abbreviations: "a.m.", "p.m.", "U.S."
_COMPOUND_ABBREVS = {"a.m.", "p.m.", "u.s.", "u.k.", "e.u."}


class SentenceBoundarySplitter(SentenceSplitter):
    """Split text into complete sentences at . ! ? boundaries.

    Unlike phrasplit (which groups by character length ~45),
    this splitter preserves each complete sentence as its own segment.

    Handles:
      - Normal:        "Hello world. Next sentence." -> ["Hello world.", "Next sentence."]
      - Missing space: "hello.World" -> ["hello.", "World"]
      - Abbreviations: "Dr. Smith is here." -> ["Dr. Smith is here."]
      - Compound:      "3 p.m. Please arrive." -> ["3 p.m.", "Please arrive."]
    """

    def split(self, text: str) -> list[str]:
        if not text or not text.strip():
            return [text]

        text = text.strip()

        # Step 1: Normalize missing spaces after sentence punctuation
        text = self._normalize(text)

        # Step 2: Find all candidate split positions
        candidates = []
        for m in re.finditer(r'(?<=[.!?])\s+(?=[A-Z"])', text):
            pos = m.start()
            period_pos = pos - 1
            if text[period_pos] in '.!?' and self._is_abbrev(text, period_pos):
                continue
            candidates.append(pos)

        if not candidates:
            return [text]

        parts = []
        prev = 0
        for pos in candidates:
            parts.append(text[prev:pos].strip())
            prev = pos
        parts.append(text[prev:].strip())

        parts = [p for p in parts if p]
        return parts if len(parts) > 1 else [text]

    def _is_abbrev(self, text: str, period_pos: int) -> bool:
        """Check if the period at period_pos is part of a known abbreviation."""
        word_end = period_pos
        word_start = word_end
        while word_start > 0 and text[word_start - 1].isalpha():
            word_start -= 1
        word = text[word_start:word_end]

        # Known word abbreviation (Mr., Dr., etc.)
        if word and word.lower() in _ABBREVIATIONS:
            return True

        # Check for X.X. pattern: "a.m.", "p.m.", "U.S."
        if (period_pos >= 2
                and text[period_pos - 1].isalpha()
                and text[period_pos - 2] == '.'
                and period_pos >= 3
                and text[period_pos - 3].isalpha()):
            compound = text[period_pos - 3:period_pos + 1].lower()
            if compound in _COMPOUND_ABBREVS:
                # a.m./p.m. CAN end a sentence if followed by uppercase
                if compound in ("a.m.", "p.m."):
                    # Check what follows the compound
                    if period_pos + 1 < len(text):
                        next_char = text[period_pos + 1]
                        if next_char.isspace() and period_pos + 2 < len(text):
                            after_space = text[period_pos + 2]
                            if after_space.isupper():
                                return False  # New sentence follows -> NOT an abbreviation
                return True

        # Single letter before period (initial, bullet point)
        if word and len(word) == 1 and word.isalpha():
            return True

        return False

    def _normalize(self, text: str) -> str:
        """Insert space after . ! ? when followed directly by uppercase letter.

        E.g. "market.The" -> "market. The"
        But "Dr.Smith" stays (abbreviation).
        "p.m.Please" stays (compound abbreviation).
        """
        result = []
        i = 0
        while i < len(text):
            c = text[i]
            result.append(c)

            if c in '.!?' and i + 1 < len(text):
                next_c = text[i + 1]
                if next_c.isupper() or next_c == '"':
                    if not self._is_abbrev(text, i):
                        result.append(' ')
            i += 1
        return ''.join(result)
