# -*- coding: utf-8 -*-
"""Allow ``python -m mojibake_forensics``."""

from __future__ import absolute_import

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
