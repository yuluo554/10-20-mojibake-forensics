# -*- coding: utf-8 -*-
"""Chain representation, enumeration and lossless filtering.

M2 implements ``enumerate_chains`` and ``verify_lossless``. The data classes
and the canonical ``path_string`` are already frozen so that ``attr``,
``explain`` and ``recover`` share one intermediate representation.
"""

from __future__ import absolute_import

from dataclasses import dataclass
from typing import Optional, Tuple

from . import codecs_table


@dataclass(frozen=True)
class Step:
    index: int
    op: str  # "encode" | "decode"
    codec: str
    input_text: Optional[str] = None
    output_text: Optional[str] = None
    input_hex: Optional[str] = None
    output_hex: Optional[str] = None

    def as_dict(self):
        payload = {"index": self.index, "op": self.op, "codec": self.codec}
        if self.input_text is not None:
            payload["input"] = self.input_text
        if self.output_text is not None:
            payload["output"] = self.output_text
        if self.input_hex is not None:
            payload["input_hex"] = self.input_hex
        if self.output_hex is not None:
            payload["output_hex"] = self.output_hex
        return payload


@dataclass(frozen=True)
class Chain:
    steps: Tuple[Step, ...]

    @property
    def depth(self):
        return sum(1 for step in self.steps if step.op == "decode")

    @property
    def path(self):
        return [{"op": step.op, "codec": step.codec} for step in self.steps]

    @property
    def path_string(self):
        return ">".join("%s:%s" % (step.op, step.codec) for step in self.steps)

    def as_dict(self):
        return {
            "path": self.path,
            "path_string": self.path_string,
            "depth": self.depth,
            "steps": [step.as_dict() for step in self.steps],
        }


def hexdump(data):
    """Uppercase hex, single spaces between bytes (report contract)."""
    return " ".join("%02X" % byte for byte in data)


def enumerate_chains(text, encoders=None, decoders=None, max_depth=None):
    """Enumerate lossless candidate chains (M2).

    Contract: start with ``encode``, end with ``decode``; ``depth`` counts
    decode steps; edges raising UnicodeEncodeError/UnicodeDecodeError are
    dropped. Never uses ``errors='replace'``.
    """
    raise NotImplementedError("M2: chain enumeration is not implemented yet")


def verify_lossless(text, chain):
    """Replay a chain backwards and return True iff every byte matches (M2)."""
    raise NotImplementedError("M2: lossless verification is not implemented yet")


def validate_depth(max_depth=None):
    depth = codecs_table.MAX_DEPTH if max_depth is None else int(max_depth)
    if depth < 1:
        raise ValueError("max_depth must be >= 1")
    return depth
