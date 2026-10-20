# -*- coding: utf-8 -*-
"""Frozen encoder/decoder sets and availability probes.

This module is the **code-side freeze point**. The authoritative definition is
``data/README.md`` §4.1/§4.2; both must change in the same commit.
"""

from __future__ import absolute_import

import codecs

# data/README.md §4.1 — do not edit without updating the document and bench.
ENCODERS = (
    "utf-8",
    "gb18030",
    "gbk",
    "big5",
    "shift_jis",
    "euc-jp",
    "euc-kr",
    "cp1252",
    "latin-1",
    "cp437",
)

DECODERS = (
    "utf-8",
    "gb18030",
    "big5",
    "shift_jis",
    "euc-kr",
    "cp1252",
    "latin-1",
)

# data/README.md §4.2
MAX_DEPTH = 3


class CodecUnavailable(RuntimeError):
    """Raised when a frozen codec is missing from the current interpreter."""

    def __init__(self, names):
        self.names = tuple(names)
        super(CodecUnavailable, self).__init__(
            "codec_unavailable: " + ", ".join(self.names)
        )


def missing_codecs(encoders=ENCODERS, decoders=DECODERS):
    """Return codec names that cannot be looked up in this interpreter."""
    missing = []
    for name in tuple(encoders) + tuple(decoders):
        try:
            codecs.lookup(name)
        except LookupError:
            missing.append(name)
    return tuple(sorted(set(missing)))


def ensure_codecs():
    """Fail loudly instead of silently shrinking the search space."""
    missing = missing_codecs()
    if missing:
        raise CodecUnavailable(missing)


def criteria():
    """Stable criteria block included in every report."""
    return {
        "encoders": list(ENCODERS),
        "decoders": list(DECODERS),
        "max_depth": MAX_DEPTH,
    }
