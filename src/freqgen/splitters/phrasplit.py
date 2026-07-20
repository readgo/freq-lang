"""Phrasplit sentence segmenter — rule-based, no NLP model required.

Three-level split strategy:
  1. Sentence boundaries (.!?)
  2. Comma/semicolon boundaries
  3. Grammar-aware word-level split (conjunctions, prepositions)
  4. Fallback: only if > 65 chars, split at last space before 50

Post-merge: segments < 18 chars are absorbed into neighbors.
"""

from phrasplit import split_long_lines

from .base import SentenceSplitter

_MAX_LENGTH = 45
_MIN_SEG_LEN = 18
_HARD_MAX = 65

# Conjunction words marking clause boundaries
_CLAUSE_CONJUNCTIONS = {
    "and", "but", "or", "nor", "yet", "so",
    "because", "although", "though", "while", "whereas",
    "when", "whenever", "if", "unless", "until", "once",
    "since", "as", "after", "before",
}

# Prepositions that often start long adverbial phrases
_LONG_PREPOSITIONS = {
    "in", "on", "at", "by", "for", "with", "without",
    "from", "to", "about", "through", "across", "during",
    "despite", "including", "according",
}

# Transition words at sentence start — should not be left orphaned
_TRANSITIONS = {"however", "meanwhile", "nevertheless", "therefore",
                "moreover", "furthermore", "consequently", "additionally"}

# Words that should NOT end a segment (push to next segment instead)
_BAD_SEGMENT_END = {"a", "an", "the", "to", "in", "on", "at", "for",
                    "with", "by", "of", "and", "or", "but", "nor", "yet"}
# Words that should NOT start a segment (merge backward)
_BAD_SEGMENT_START = {"a", "an", "the", "to", "of"}


class PhrasplitSplitter(SentenceSplitter):
    """Split a sentence into short chunks using phrasplit + post-processing.

    Strategy:
      1. phrasplit split_long_lines (existing, good for .!? and comma splits)
      2. Post-merge: absorb < 18-char orphan segments into neighbors
      3. If a segment still exceeds _HARD_MAX, re-split using grammar cues
    """

    def split(self, sentence: str) -> list[str]:
        if not sentence or not sentence.strip():
            return [sentence]

        text = sentence.strip()

        # If already short enough, keep as one
        if len(text) <= _HARD_MAX:
            return [text]

        # Step 1: phrasplit base split
        parts = split_long_lines(text, max_length=_MAX_LENGTH, use_spacy=False)
        parts = [p.strip() for p in parts if p.strip()]

        if len(parts) <= 1:
            return [text]

        # Step 2: Post-merge short segments
        parts = self._merge_short(parts)

        # Step 2b: Fix segments ending/starting with bad tokens
        parts = self._fix_ragged_edges(parts)

        # Step 3: If any segment still exceeds _HARD_MAX, re-split it with grammar cues
        final = []
        for part in parts:
            if len(part) > _HARD_MAX:
                sub = self._grammar_split(part)
                final.extend(sub)
            else:
                final.append(part)

        # Step 3b: Fix ragged edges again (grammar_split may have undone it)
        final = self._fix_ragged_edges(final)

        return final if len(final) > 1 else [text]

    def _grammar_split(self, text: str) -> list[str]:
        """Split a long segment at grammar-aware boundaries.

        Looks for clause-level conjunctions and long prepositional phrases,
        preferring split points that produce balanced segments.
        """
        tokens = text.split()
        if len(tokens) <= 3:
            return [text]

        # Check if first token is a transition (don't leave it orphaned)
        first_word = tokens[0].strip('",;:!?.').lower()
        start_offset = 0
        if first_word in _TRANSITIONS and len(tokens) > 3:
            # Treat first two tokens as a unit
            start_offset = 0

        candidates = []
        for i in range(1, len(tokens) - 1):
            clean = tokens[i].strip('",;:!?.()-—').lower()

            # Clause conjunctions
            if clean in _CLAUSE_CONJUNCTIONS:
                # Only if there's enough text on both sides
                left_len = sum(len(t) + 1 for t in tokens[:i])
                right_len = sum(len(t) + 1 for t in tokens[i:])
                if left_len > 15 and right_len > 15:
                    candidates.append(i)

            # Long prepositions (only if preceded by substantial text)
            if clean in _LONG_PREPOSITIONS:
                left_len = sum(len(t) + 1 for t in tokens[:i])
                if left_len > 25:
                    candidates.append(i)

        if not candidates:
            # Fallback: split at last space before position 50
            char_count = 0
            for i, token in enumerate(tokens):
                char_count += len(token) + 1
                if char_count > 50 and i > 1:
                    return [" ".join(tokens[:i]), " ".join(tokens[i:])]
            return [text]

        # Pick the candidate closest to the middle of the text
        mid = len(tokens) // 2
        best = min(candidates, key=lambda i: abs(i - mid))
        left = " ".join(tokens[:best])
        right = " ".join(tokens[best:])

        result = [left, right]

        # Recursively split if still too long
        final = []
        for seg in result:
            if len(seg) > _HARD_MAX:
                final.extend(self._grammar_split(seg))
            else:
                final.append(seg)
        return final

    def _fix_ragged_edges(self, segments: list[str]) -> list[str]:
        """Fix segments ending with articles/prepositions or starting with orphans.

        Pass 1: Recursively push bad-ending tokens to next segment.
        Pass 2: Merge segments that start with articles backward.
        """
        if len(segments) <= 1:
            return segments

        # Pass 1: fix bad segment endings (recursive — keep pushing until clean)
        result = []
        i = 0
        while i < len(segments):
            cur = segments[i]
            if i + 1 >= len(segments):
                result.append(cur)
                break

            words = cur.split()
            if not words:
                result.append(cur)
                i += 1
                continue

            # Keep checking last word and pushing until clean
            while words:
                last_word = words[-1].strip('",;:!?.-—\u2013\u2014"\'')
                if last_word.lower() in _BAD_SEGMENT_END:
                    segments[i + 1] = words[-1] + " " + segments[i + 1]
                    words = words[:-1]
                else:
                    break

            if words:
                result.append(" ".join(words))
            # If all words were pushed, don't add anything — the next segment absorbed it
            i += 1

        # Pass 2: fix bad segment starts
        segments = result
        result = []
        i = 0
        while i < len(segments):
            cur = segments[i]
            if not cur.strip():
                i += 1
                continue

            first_word = cur.split()[0].strip('",;:!?.-—"\'')
            if first_word.lower() in _BAD_SEGMENT_START and result:
                # Merge with previous segment
                result[-1] = result[-1] + " " + cur
            else:
                result.append(cur)
            i += 1

        return result

    def _merge_short(self, segments: list[str]) -> list[str]:
        """Merge segments shorter than _MIN_SEG_LEN into neighbors."""
        if len(segments) <= 1:
            return segments

        result = []
        i = 0
        while i < len(segments):
            cur = segments[i]

            # Short segment with a successor → merge forward
            if len(cur) < _MIN_SEG_LEN and i + 1 < len(segments):
                merged = cur + " " + segments[i + 1]
                if len(merged) <= _HARD_MAX + 10:
                    result.append(merged)
                    i += 2
                    continue

                # Try merge backward instead
                if result:
                    prev = result[-1] + " " + cur
                    if len(prev) <= _HARD_MAX + 10:
                        result[-1] = prev
                        i += 1
                        continue

                result.append(cur)
                i += 1
                continue

            # Last segment too short → merge backward
            if len(cur) < _MIN_SEG_LEN and result:
                result[-1] = result[-1] + " " + cur
                i += 1
                continue

            result.append(cur)
            i += 1

        return result
