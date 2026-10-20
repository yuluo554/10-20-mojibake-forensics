# -*- coding: utf-8 -*-
"""M4 · recover — deterministic recovery or an explicit LOST verdict."""

from __future__ import absolute_import

from . import report

MILESTONE = "M4"


def run(args):
    return report.not_ready("recover", MILESTONE)


def recover(text, pick, out=None):
    """RECOVERED / LOST / NOT_MOJIBAKE with loss-point evidence (M4)."""
    raise NotImplementedError("M4: recover is not implemented yet")
