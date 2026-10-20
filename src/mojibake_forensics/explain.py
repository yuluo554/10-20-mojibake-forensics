# -*- coding: utf-8 -*-
"""M3 · explain — replayable byte-level proof for each candidate path."""

from __future__ import absolute_import

from . import report

MILESTONE = "M3"


def run(args):
    return report.not_ready("explain", MILESTONE)


def explain(text, pick, versus=None, all_candidates=False):
    """Render steps, verify flags and divergence (M3)."""
    raise NotImplementedError("M3: explain is not implemented yet")
