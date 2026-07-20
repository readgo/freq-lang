"""Text preprocessing for TTS: number-to-words, pronunciation hints, display cleanup."""

import re
from typing import Tuple

# ── {{prn:...}} markers ──────────────────────────────────────────────────
# Forms:
#   {{prn:original|pronunciation}}  → display "original", TTS says "pronunciation"
#   {{prn:pronunciation}}           → display "pronunciation", TTS says "pronunciation"

PRN_RE = re.compile(r'\{\{prn:([^}]+)\}\}')

def parse_prn(text: str) -> Tuple[str, str]:
    """
    Given text with {{prn:...|...}} markers, return:
      (display_text, tts_text)

    - display_text strips markers, keeping original (or inner if no pipe)
    - tts_text uses pronunciation hint (or inner if no pipe)
    """
    def _display_repl(m):
        inner = m.group(1)
        if '|' in inner:
            return inner.split('|', 1)[0]
        return inner

    def _tts_repl(m):
        inner = m.group(1)
        if '|' in inner:
            return inner.split('|', 1)[1]
        return inner

    display = PRN_RE.sub(_display_repl, text)
    tts = PRN_RE.sub(_tts_repl, text)
    return display, tts


# ── Number-to-words ──────────────────────────────────────────────────────

ONES = ["zero", "one", "two", "three", "four", "five", "six", "seven",
        "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen",
        "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy",
        "eighty", "ninety"]
SCALES = ["", "thousand", "million", "billion", "trillion"]


def _hundreds_words(n: int) -> str:
    """Convert 0..999 to words."""
    if n == 0:
        return ""
    parts = []
    if n >= 100:
        parts.append(ONES[n // 100])
        parts.append("hundred")
        n %= 100
    if n >= 20:
        parts.append(TENS[n // 10])
        n %= 10
        if n:
            parts[-1] += "-" + ONES[n]
    elif n > 0:
        parts.append(ONES[n])
    return " ".join(parts)


def integer_to_words(num_str: str) -> str:
    """Convert an integer string (possibly with commas) to English words.
    
    Examples:
        "2,000" → "two thousand"
        "145"   → "one hundred forty-five"
        "0.1"   → "zero point one"
        "6.5"   → "six point five"
    """
    # Handle decimal
    if '.' in num_str:
        parts = num_str.split('.')
        int_part = parts[0].replace(',', '')
        dec_part = parts[1]
        try:
            n = int(int_part)
            int_words = _integer_to_words_positive(n) if n > 0 else "zero"
        except ValueError:
            return num_str
        dec_words = " ".join(ONES[int(d)] for d in dec_part if d.isdigit())
        return f"{int_words} point {dec_words}"
    
    num_str = num_str.replace(',', '')
    try:
        n = int(num_str)
    except ValueError:
        return num_str
    
    if n == 0:
        return "zero"
    if n < 0:
        return "minus " + _integer_to_words_positive(-n)
    return _integer_to_words_positive(n)


def _integer_to_words_positive(n: int) -> str:
    """Convert positive integer to words."""
    if n < 20:
        return ONES[n]
    
    result = []
    scale_idx = 0
    while n > 0:
        chunk = n % 1000
        if chunk > 0:
            chunk_words = _hundreds_words(chunk)
            if scale_idx > 0:
                chunk_words += " " + SCALES[scale_idx]
            result.insert(0, chunk_words)
        n //= 1000
        scale_idx += 1
    return " ".join(result)


# ── Composite patterns ───────────────────────────────────────────────────

def preprocess_for_tts(text: str) -> str:
    """Main preprocessing: prn markers → pronunciation, then number conversion.
    
    Pipeline:
      1. Handle {{prn:...}} markers (extract pronunciation)
      2. Convert known number patterns to words for better TTS
    """
    # Step 1: Extract pronunciation from prn markers
    _, tts_text = parse_prn(text)
    
    # Step 2: Convert number patterns to words
    tts_text = _convert_numbers_to_words(tts_text)
    
    return tts_text


def clean_display_text(text: str) -> str:
    """Clean text for display: strip prn markers, keep original."""
    display, _ = parse_prn(text)
    return display


# ── Number pattern conversion ────────────────────────────────────────────

# Patterns to match that need number-to-word conversion
# We match various number patterns in English text

def _convert_numbers_to_words(text: str) -> str:
    """Convert standalone number patterns in text to English words.
    
    Handles:
      - Plain integers: "2,000" → "two thousand"  
      - Decimals: "6.5" → "six point five"
      - Percentages: "6.5%" → "six point five percent"
      - Dollar amounts: "$2,200" → "two thousand two hundred dollars"
      - Currency-like: "$150 billion" → "one hundred fifty billion dollars"
    
    NOTE: Years and small numbers (under 100) are left as-is since Kokoro
    handles those acceptably. The problem is specifically with comma-separated
    numbers and large/dollar amounts.
    """
    # Process in order from most specific to least
    
    # 1. Dollar amounts with multipliers: $150 billion, $40 million
    text = re.sub(
        r'\$(\d{1,3}(?:,\d{3})*)\s*(billion|million|trillion|thousand)\b',
        lambda m: f"{integer_to_words(m.group(1))} {m.group(2)} dollars",
        text
    )
    
    # 2. Dollar amounts plain: $2,200, $299, $3,499
    text = re.sub(
        r'\$(\d{1,3}(?:,\d{3})*)',
        lambda m: f"{integer_to_words(m.group(1))} dollars",
        text
    )
    
    # 3. Percentages: 6.5%, 60%, 19.5%
    text = re.sub(
        r'(\d+(?:\.\d+)?)\s*%',
        lambda m: f"{integer_to_words(m.group(1))} percent",
        text
    )
    
    # 4. Standalone decimals: 2.4, 0.5, 3.14
    # (must come after % pattern to avoid stealing 6.5 from 6.5%)
    text = re.sub(
        r'(?<!\w)(\d+\.\d+)(?!\w)',
        lambda m: integer_to_words(m.group(1)),
        text
    )

    # 5. Plain numbers with commas (e.g., "2,000", "5,400")
    # These are the main problem case for Kokoro
    text = re.sub(
        r'(?<!\w)(\d{1,3},\d{3}(?:,\d{3})*)(?!\w)',
        lambda m: integer_to_words(m.group(1)),
        text
    )
    
    # 5. Large plain numbers without commas: 500, 650, but NOT years
    # Years are 4 digits, typically 1900-2099
    # If a 4-digit number is not in the year range, treat as number
    # For now, just handle this conservatively
    text = re.sub(
        r'(?<!\w)(\d{5,})(?!\w)',  # 5+ digit numbers → words
        lambda m: integer_to_words(m.group(1)),
        text
    )
    
    return text


# ── Integration helpers ──────────────────────────────────────────────────

def preprocess_sentence_for_pack(sentence_text: str) -> dict:
    """Process a sentence for inclusion in a .freqpack.
    
    Returns:
        dict with:
          - display_text: text to show in course.json
          - tts_text: text to pass to TTS engine
    """
    display_text = clean_display_text(sentence_text)
    tts_text = preprocess_for_tts(sentence_text)
    return {
        "display_text": display_text,
        "tts_text": tts_text,
    }


# ── Verification ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Quick test
    tests = [
        ("{{prn:2026|twenty twenty-six}}", "twenty twenty-six", "2026"),
        ("{{prn:$2,200|two thousand two hundred dollars}}", 
         "two thousand two hundred dollars", "$2,200"),
        ("{{prn:2016|twenty sixteen}}", "twenty sixteen", "2016"),
        ("{{prn:$129|one hundred twenty-nine dollars}}",
         "one hundred twenty-nine dollars", "$129"),
        ("Price: $2,000", "Price: two thousand dollars", "Price: $2,000"),
        ("2,000 households", "two thousand households", "2,000 households"),
        ("6.5% of electricity", "six point five percent of electricity", "6.5% of electricity"),
        ("21% of Ireland's", "twenty-one percent of Ireland's", "21% of Ireland's"),
        ("Plain text no numbers.", "Plain text no numbers.", "Plain text no numbers."),
        ("$150 billion", "one hundred fifty billion dollars", "$150 billion"),
    ]
    
    for test_in, expected_tts, expected_display in tests:
        tts = preprocess_for_tts(test_in)
        display = clean_display_text(test_in)
        status_tts = "✓" if tts == expected_tts else "✗"
        status_disp = "✓" if display == expected_display else "✗"
        print(f"{status_tts} TTS: {test_in[:50]:<50s} → {tts}")
        print(f"{status_disp} DISP:{'':<48s} → {display}")
        print()
