# -*- coding: utf-8 -*-
"""Three-layer scoring and the frozen ranking key.

Weights and character classes are defined once in ``data/README.md`` §4.4.
The module is deterministic: no locale, no clock, no randomness.
"""

from __future__ import absolute_import

W_READ = 1.0
W_DEPTH = 0.5
W_LANG = 0.3  # only when --freq is supplied; 0 by default

# data/README.md §4.4 readability table (kept here as named constants only;
# the scoring loop is below). Do not add a second source of weights.
ASCII_VISIBLE = 0.2
CJK = 1.0
LATIN_EXT = 0.1
HALFWIDTH_KATAKANA = -0.5
CONTROL = -1.0
PUA = -1.0
REPLACEMENT = -1.5
OTHER = 0.0

REGULAR_WHITESPACE = ("\t", "\n", "\r")


def _is_noncharacter(code):
    if 0xFDD0 <= code <= 0xFDEF:
        return True
    return (code & 0xFFFE) == 0xFFFE


def char_score(char):
    """Per-character readability contribution from the §4.4 table."""
    code = ord(char)

    if code == 0xFFFD:
        return REPLACEMENT
    if char in REGULAR_WHITESPACE:
        return ASCII_VISIBLE
    if 0x20 <= code <= 0x7E:
        return ASCII_VISIBLE
    if 0x4E00 <= code <= 0x9FFF:
        return CJK
    if 0x3040 <= code <= 0x30FF:  # hiragana + katakana
        return CJK
    if 0xAC00 <= code <= 0xD7AF:  # hangul syllables
        return CJK
    if 0x00A0 <= code <= 0x024F:
        return LATIN_EXT
    if 0xFF61 <= code <= 0xFF9F:
        return HALFWIDTH_KATAKANA
    if code < 0x20 or code == 0x7F:
        return CONTROL
    if 0xE000 <= code <= 0xF8FF:
        return PUA
    if 0xD800 <= code <= 0xDFFF:
        return PUA
    if _is_noncharacter(code):
        return PUA
    return OTHER


def depth_score(depth):
    """1 / (1 + depth): shallow paths win ties (data/README.md §4.4)."""
    return 1.0 / (1.0 + float(depth))


def readability(text):
    """Normalized readability in [-1, 1] (data/README.md §4.4).

    The raw sum is divided by the character count and clamped so the documented
    output range holds even for the -1.5 replacement-character class.
    """
    if not text:
        return 0.0
    total = 0.0
    for char in text:
        total += char_score(char)
    normalized = total / float(len(text))
    if normalized < -1.0:
        return -1.0
    if normalized > 1.0:
        return 1.0
    return normalized


def language_score(text, freq=None):
    """Optional frequency-table prior; disabled unless --freq is given."""
    if freq is None:
        return 0.0
    raise NotImplementedError("language prior is a phase-2 optional feature")


def rank(chains, freq=None):
    """Score, sort and return candidate entries.

    Each entry carries the canonical path plus the three score components; the
    sort key is the frozen ``(-score_total, depth, path_string)``.
    """
    entries = []
    for chain in chains:
        result = chain.result or ""
        read = readability(result)
        depth = depth_score(chain.depth)
        language = language_score(result, freq)
        total = W_READ * read + W_DEPTH * depth + W_LANG * language
        entries.append(
            {
                "path": chain.path,
                "path_string": chain.path_string,
                "depth": chain.depth,
                "result": result,
                "score_total": total,
                "score": {
                    "readability": read,
                    "depth": depth,
                    "language": language,
                    "total": total,
                },
            }
        )
    entries.sort(key=sort_key)
    for position, entry in enumerate(entries, 1):
        entry["rank"] = position
    return entries


def sort_key(entry):
    """Frozen ranking key: (-score_total, depth, path_string)."""
    total = entry.get("score_total")
    if total is None:
        total = entry.get("score", {}).get("total", 0.0)
    return (
        -float(total),
        int(entry["depth"]),
        str(entry["path_string"]),
    )
