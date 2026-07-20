"""Unit tests for NlpSplitter dependency-based splitting logic.

Since spaCy + en_core_web_sm (~500MB) isn't installed in the dev environment,
this test validates the _split_by_deps algorithm using mock token objects
with the same interface as spaCy Token objects.

Run:  python tests/test_nlpsplit.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from freqgen.splitters.nlpsplit import NlpSplitter


class MockToken:
    """Minimal mock of spaCy Token."""

    def __init__(self, text: str, idx: int, dep_: str, pos_: str,
                 head=None, children=None):
        self.text = text
        self.idx = idx
        self.dep_ = dep_
        self.pos_ = pos_
        self.head = head or self
        self._children = children or []
        self._subtree = None

    @property
    def children(self):
        return self._children

    @property
    def subtree(self):
        if self._subtree is not None:
            return self._subtree
        return [self]


def make_tokens(text: str, specs: list[tuple[str, str, str, list | None]]) -> list:
    """Build MockTokens with auto-calculated idx.

    specs: list of (text_str, dep_, pos_, children_or_None)
    """
    tokens = []
    pos = 0
    for raw_text, dep, pos_tag, children in specs:
        idx = text.find(raw_text, pos)
        if idx < 0:
            raise ValueError(f"Can't find {raw_text!r} in text at pos {pos}")
        children_tokens = []
        if children:
            for ct in children:
                ct_idx = text.find(ct.text)
                ct.idx = ct_idx
                children_tokens.append(ct)
        t = MockToken(raw_text, idx, dep, pos_tag,
                      children=children_tokens)
        tokens.append(t)
        pos = idx + len(raw_text)

    # Second pass: set head relationships for relcl detection
    for raw_text, dep, pos_tag, children in specs:
        if children:
            for ct in children:
                for t in tokens:
                    if t.text == ct.text and t.idx == ct.idx:
                        t.head = [tt for tt in tokens if tt.text == raw_text][0] if dep not in ('ROOT',) else t
                        break
    return tokens


class MockDoc:
    def __init__(self, tokens: list):
        self.tokens = tokens

    def __iter__(self):
        return iter(self.tokens)


def test_split_at_coordinating_conjunction():
    """Split before 'and' when it coordinates two clauses (conj + CCONJ)."""
    text = "I stayed home and they went out."
    specs = [
        ("I", "nsubj", "PRON", None),
        ("stayed", "ROOT", "VERB", None),
        ("home", "advmod", "ADV", None),
        ("and", "conj", "CCONJ", None),    # ← split here
        ("they", "nsubj", "PRON", None),
        ("went", "conj", "VERB", None),
        ("out", "advmod", "ADV", None),
        (".", "punct", "PUNCT", None),
    ]
    splitter = NlpSplitter()
    splitter._nlp = lambda x: MockDoc(make_tokens(text, specs))
    splitter._ensure_nlp = lambda: None

    result = splitter._split_by_deps(text)
    assert len(result) == 2, f"Expected 2 segments, got {len(result)}: {result}"
    # "and" should be at start of segment 2
    assert result[1].lstrip().startswith("and"), f"'and' should start seg 2: {result}"
    print(f"  ✓ conj: {result}")


def test_split_at_adverbial_clause():
    """Split before 'because' (marker of adverbial clause)."""
    text = "I stayed home because it was raining."
    because = MockToken("because", 0, "mark", "SCONJ")
    raining = MockToken("raining", 0, "advcl", "VERB", children=[because])

    # Build tokens manually due to children relationship
    raw_specs = [
        ("I", "nsubj", "PRON", None),
        ("stayed", "ROOT", "VERB", None),
        ("home", "advmod", "ADV", None),
    ]
    after_specs = [
        ("it", "nsubj", "PRON", None),
        ("was", "aux", "VERB", None),
        (".", "punct", "PUNCT", None),
    ]

    tokens = make_tokens(text, raw_specs + [
        ("because", "mark", "SCONJ", None),
    ] + after_specs)

    # Set correct idx for the extra tokens
    because.idx = text.find("because")
    raining.idx = text.find("raining")
    # Add them to tokens in the right order
    # rebuild properly
    all_tokens = []
    pos = 0
    for src, dep, pos_tag, children in [
        ("I", "nsubj", "PRON", None),
        ("stayed", "ROOT", "VERB", None),
        ("home", "advmod", "ADV", None),
        ("because", "mark", "SCONJ", None),
        ("it", "nsubj", "PRON", None),
        ("was", "aux", "VERB", None),
        ("raining", "advcl", "VERB", [because]),
        (".", "punct", "PUNCT", None),
    ]:
        idx = text.find(src, pos)
        t = MockToken(src, idx, dep, pos_tag, children=children)
        if children:
            for ch in children:
                ch.idx = text.find(ch.text)
        all_tokens.append(t)
        pos = idx + len(src)

    doc = MockDoc(all_tokens)
    splitter = NlpSplitter()
    splitter._nlp = lambda x: doc
    splitter._ensure_nlp = lambda: None

    result = splitter._split_by_deps(text)
    assert len(result) == 2, f"Expected 2 segments, got {len(result)}: {result}"
    assert result[1].lstrip().startswith("because"), f"Seg 2 should start 'because': {result}"
    print(f"  ✓ advcl: {result}")


def test_split_at_complement_clause():
    """Split before 'that' in complement clause."""
    text = "We believe that AI will transform work."
    that = MockToken("that", 0, "mark", "SCONJ")
    transform = MockToken("transform", 0, "ccomp", "VERB", children=[that])

    all_tokens = []
    pos = 0
    for src, dep, pos_tag, children in [
        ("We", "nsubj", "PRON", None),
        ("believe", "ROOT", "VERB", None),
        ("that", "mark", "SCONJ", None),
        ("AI", "nsubj", "PROPN", None),
        ("will", "aux", "VERB", None),
        ("transform", "ccomp", "VERB", [that]),
        ("work", "dobj", "NOUN", None),
        (".", "punct", "PUNCT", None),
    ]:
        idx = text.find(src, pos)
        t = MockToken(src, idx, dep, pos_tag, children=children)
        if children:
            for ch in children:
                ch.idx = text.find(ch.text)
        all_tokens.append(t)
        pos = idx + len(src)

    doc = MockDoc(all_tokens)
    splitter = NlpSplitter()
    splitter._nlp = lambda x: doc
    splitter._ensure_nlp = lambda: None

    result = splitter._split_by_deps(text)
    assert len(result) == 2, f"Expected 2 segments: {result}"
    assert result[1].lstrip().startswith("that"), f"Seg 2 should start 'that': {result}"
    print(f"  ✓ ccomp: {result}")


def test_short_sentence_kept():
    """Sentences under 60 chars should not be split."""
    splitter = NlpSplitter()
    result = splitter.split("Hello world.")
    assert len(result) == 1
    print(f"  ✓ short: {result}")


def test_fallback_rules():
    """When spacy not available, fall back to rules."""
    splitter = NlpSplitter()
    splitter._ensure_nlp = lambda: (_ for _ in ()).throw(ImportError("mock"))
    result = splitter.split("The fox jumps over the dog near the river bank every morning.")
    assert len(result) >= 1
    print(f"  ✓ fallback ({len(result)} segs)")


if __name__ == "__main__":
    test_short_sentence_kept()
    test_split_at_coordinating_conjunction()
    test_split_at_adverbial_clause()
    test_split_at_complement_clause()
    test_fallback_rules()
    print("\nAll NlpSplitter tests passed.")
