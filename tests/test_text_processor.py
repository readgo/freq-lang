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
