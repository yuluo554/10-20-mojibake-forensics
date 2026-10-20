# -*- coding: utf-8 -*-
"""Mojibake Forensics — proof-carrying encoding attribution.

This package is local-only: standard-library codecs, no network, no models.
The public contract for schema and exit codes lives in ``report.py``; the
frozen encoder/decoder sets live in ``codecs_table.py``.
"""

__version__ = "0.1.0"

SCHEMA = "mojibake-forensics/1"

__all__ = ["SCHEMA", "__version__"]
