# -*- coding: utf-8 -*-
"""M2 · attr — bounded candidate attribution.

The command contract is implemented in ``cli.py``; this module will own the
enumeration → lossless filter → ranking pipeline in M2.
"""

from __future__ import absolute_import

from . import report

MILESTONE = "M2"


def run(args):
    return report.not_ready("attr", MILESTONE)


def attribute(text, source_enc=None, target_enc=None, top=5, freq=None):
    """Return the bounded candidate envelope (M2)."""
    raise NotImplementedError("M2: attr is not implemented yet")
