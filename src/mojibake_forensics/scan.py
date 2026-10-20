# -*- coding: utf-8 -*-
"""M5 · scan — read-only CI gate with baseline accounting."""

from __future__ import absolute_import

from . import report

MILESTONE = "M5"


def run(args):
    return report.not_ready("scan", MILESTONE)


def scan_directory(directory, baseline, output_format="json"):
    """Return new / baselined / stale buckets and the exit code (M5)."""
    raise NotImplementedError("M5: scan is not implemented yet")
