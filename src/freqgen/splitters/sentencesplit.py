"""Sentence-boundary splitter — split at . ! ? into complete sentences."""

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
        candidates = self._find_split_positions(text)

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

    def _find_split_positions(self, text: str) -> list[int]:
        """Scan for split points: whitespace after sentence-ending punctuation.

        Closing quotes that directly follow the punctuation belong to the
        sentence being ended, so the split is placed after them — this keeps
        '"' from being orphaned into the next segment.
        """
        candidates = []
        i = 0
        while i < len(text):
            if text[i] not in '.!?':
                i += 1
                continue
            if self._is_abbrev(text, i):
                i += 1
                continue
            j = i + 1
            # Closing quote(s) directly attached to the sentence
            while j < len(text) and text[j] == '"':
                j += 1
            if j >= len(text) or not text[j].isspace():
                i += 1
                continue
            # New sentence must start with uppercase or an opening quote
            k = j
            while k < len(text) and text[k].isspace():
                k += 1
            if k < len(text) and (text[k].isupper() or text[k] == '"'):
                candidates.append(j)
            i = k
        return candidates

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
        Closing quote stays attached: 'said."Next' -> 'said." Next'
        """
        result = []
        i = 0
        while i < len(text):
            c = text[i]
            result.append(c)

            if c in '.!?' and i + 1 < len(text) and not self._is_abbrev(text, i):
                next_c = text[i + 1]
                if next_c.isupper():
                    result.append(' ')
                elif next_c == '"':
                    # Keep closing quote attached to the sentence;
                    # insert the space after the quote instead
                    result.append('"')
                    i += 1
                    if i + 1 < len(text) and not text[i + 1].isspace():
                        result.append(' ')
            i += 1
        return ''.join(result)
