"""Tests for text_processor: number-to-words conversion for TTS."""

from src.freqgen.text_processor import preprocess_for_tts, integer_to_words


# ── Decimals ─────────────────────────────────────────────────────────────

def test_standalone_decimal():
    """2.4 → two point four"""
    result = preprocess_for_tts("2.4")
    assert result == "two point four"


def test_decimal_in_sentence():
    """score is 2.4 → score is two point four"""
    result = preprocess_for_tts("score is 2.4")
    assert result == "score is two point four"


def test_decimal_zero_point_five():
    """0.5 → zero point five"""
    result = preprocess_for_tts("0.5")
    assert result == "zero point five"


def test_decimal_multi_digit():
    """3.14 → three point one four"""
    result = preprocess_for_tts("3.14")
    assert result == "three point one four"


def test_decimal_with_context():
    """The value is 2.4 seconds → The value is two point four seconds"""
    result = preprocess_for_tts("The value is 2.4 seconds")
    assert result == "The value is two point four seconds"


# ── Existing behavior (regression) ───────────────────────────────────────

def test_percentage():
    """6.5% → six point five percent"""
    result = preprocess_for_tts("6.5%")
    assert result == "six point five percent"


def test_comma_number():
    """2,000 households → two thousand households"""
    result = preprocess_for_tts("2,000 households")
    assert result == "two thousand households"


def test_dollar_amount():
    """Price: $2,000 → Price: two thousand dollars"""
    result = preprocess_for_tts("Price: $2,000")
    assert result == "Price: two thousand dollars"


# ── Display text preservation ──────────────────────────────────────────

def test_clean_display_preserves_decimals():
    """clean_display_text keeps 2.4 as-is"""
    from src.freqgen.text_processor import clean_display_text
    result = clean_display_text("2.4")
    assert result == "2.4"


def test_clean_display_preserves_commas():
    """clean_display_text keeps 2,000 as-is"""
    from src.freqgen.text_processor import clean_display_text
    result = clean_display_text("2,000")
    assert result == "2,000"


def test_clean_display_preserves_percentage():
    """clean_display_text keeps 6.5% as-is"""
    from src.freqgen.text_processor import clean_display_text
    result = clean_display_text("6.5%")
    assert result == "6.5%"


def test_clean_display_strips_prn_keeps_original():
    """clean_display_text: {{prn:2.4|two point four}} → 2.4"""
    from src.freqgen.text_processor import clean_display_text
    result = clean_display_text("{{prn:2.4|two point four}}")
    assert result == "2.4"


def test_segment_display_preserves_numbers():
    """Segment display (from display_sent split) keeps raw numbers, not TTS words."""
    from src.freqgen.text_processor import clean_display_text, preprocess_for_tts
    from src.freqgen.splitters import get_splitter
    
    seg_splitter = get_splitter('phrasplit')
    
    cases = [
        ("The temperature is 2.4 degrees.", "2.4"),
        ("About 6.5% of users", "6.5%"),
        ("Over 2,000 people attended.", "2,000"),
    ]
    
    for raw, expected_substring in cases:
        display = clean_display_text(raw)
        tts = preprocess_for_tts(raw)
        
        tts_parts = seg_splitter.split(tts)
        display_parts = seg_splitter.split(display)
        
        # Split counts should match
        assert len(tts_parts) == len(display_parts),             f"Split count mismatch for '{raw}': tts={len(tts_parts)}, display={len(display_parts)}"
        
        # Display parts should contain the original number
        combined = ' '.join(display_parts)
        assert expected_substring in combined,             f"Display parts missing '{expected_substring}' for '{raw}': {display_parts}"
        
        # TTS parts should NOT contain the raw number
        tts_combined = ' '.join(tts_parts)
        assert expected_substring not in tts_combined,             f"TTS parts still have '{expected_substring}' for '{raw}': {tts_parts}"
