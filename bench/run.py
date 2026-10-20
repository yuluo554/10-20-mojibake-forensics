#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""57-case probe benchmark (skeleton).

M1/M2 implements the programmatic generator and replay. This skeleton only
freezes the probe *shape* so nobody invents a second set of numbers.

Probe shape (data/README.md §1.3): 10 encoders x 6 decoders, chain depth 2,
10 synthetic CJK samples x 8 incident scenarios = 57 usable cases.
"""

from __future__ import print_function

import argparse
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

PROBE = {
    "encoders": 10,
    "decoders": 6,
    "depth": 2,
    "samples": 10,
    "scenarios": 8,
    "cases": 57,
    "note": "small-sample feasibility probe, not a product metric",
}


def main(argv=None):
    parser = argparse.ArgumentParser(description="57-case mojibake attribution probe")
    parser.add_argument("--out", default=os.path.join(ROOT, "bench", "out", "attr.json"))
    parser.add_argument("--check", action="store_true", help="recompute and compare with frozen output")
    args = parser.parse_args(argv)

    print("bench: 57-case probe is not implemented yet (M1/M2)")
    print("shape: %(encoders)d encoders x %(decoders)d decoders, depth %(depth)d, "
          "%(samples)d samples x %(scenarios)d scenarios = %(cases)d cases" % PROBE)
    print("note: %s" % PROBE["note"])
    return 4


if __name__ == "__main__":
    sys.exit(main())
