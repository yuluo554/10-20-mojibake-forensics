# -*- coding: utf-8 -*-
"""Shared payload shape for the five irreversible recover fixtures (M1).

Data only: standard library, no tool imports.
"""

from __future__ import print_function

import os
import sys

FIXTURES_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if FIXTURES_DIR not in sys.path:
    sys.path.insert(0, FIXTURES_DIR)

import genlib  # noqa: E402


CRITERIA = {
    "encoders": [
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
    ],
    "decoders": [
        "utf-8",
        "gb18030",
        "big5",
        "shift_jis",
        "euc-kr",
        "cp1252",
        "latin-1",
    ],
    "max_depth": 3,
}


def payload(input_block, expected_block, note):
    return {
        "input": input_block,
        "expected": expected_block,
        "criteria": CRITERIA,
        "note": note,
    }


def run(build, fixture_dir, description):
    return genlib.run(build, fixture_dir, description=description)
