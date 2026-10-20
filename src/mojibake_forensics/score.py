# -*- coding: utf-8 -*-
"""Three-layer scoring and the frozen ranking key.

Weights and character classes are defined once in ``data/README.md`` §4.4.
M2 implements readability/ranking; the constants and sort key are frozen now.
"""

from __future__ import absolute_import

W_READ = 1.0
W_DEPTH = 0.5
W_LANG = 0.3  # only when --freq is supplied; 0 by default

# data/README.md §4.4 readability table (kept here as named constants only;
# the scoring loop is M2). Do not add a second source of weights.
ASCII_VISIBLE = 0.2
CJK = 1.0
LATIN_EXT = 0.1
HALFWIDTH_KATAKANA = -0.5
CONTROL = -1.0
PUA = -1.0
REPLACEMENT = -1.5
OTHER = 0.0


def depth_score(depth):
    """1 / (1 + depth): shallow paths win ties (data/README.md §4.4)."""
    return 1.0 / (1.0 + float(depth))


def readability(text):
    """Normalized readability in [-1, 1] (M2)."""
    raise NotImplementedError("M2: readability scoring is not implemented yet")


def language_score(text, freq=None):
    """Optional frequency-table prior; disabled unless --freq is given."""
    if freq is None:
        return 0.0
    raise NotImplementedError("language prior is a phase-2 optional feature")


def rank(chains, freq=None):
    """Score, sort and return candidate entries (M2)."""
    raise NotImplementedError("M2: ranking is not implemented yet")


def sort_key(entry):
    """Frozen ranking key: (-score_total, depth, path_string)."""
    return (
        -float(entry["score_total"]),
        int(entry["depth"]),
        str(entry["path_string"]),
    )
