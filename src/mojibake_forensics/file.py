# -*- coding: utf-8 -*-
"""M5 · file — raw-byte pipeline diagnostics (BOM, UTF-16, zip names, CSV)."""

from __future__ import absolute_import

from . import report

MILESTONE = "M5"


def run(args):
    return report.not_ready("file", MILESTONE)


def inspect_path(path, preset=None):
    """Read-only byte inspection; never writes back (M5)."""
    raise NotImplementedError("M5: file pipeline is not implemented yet")
