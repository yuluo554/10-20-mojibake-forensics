# -*- coding: utf-8 -*-
"""Chain representation, enumeration and lossless filtering.

The engine is deliberately small and strict: every edge is a standard-library
``encode``/``decode`` call with the default (strict) error handler. There is no
``errors='replace'`` or ``errors='ignore'`` anywhere on the decision path.

Semantics (``data/README.md`` §4.2–§4.3):

* a chain starts with ``encode`` and ends with ``decode``;
* ``depth`` counts the ``decode`` steps;
* a chain is a candidate only if replaying it **backwards** reproduces every
  intermediate byte string exactly.
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

    @property
    def result(self):
        """Final text produced by the chain, or ``None`` for an empty chain."""
        if not self.steps:
            return None
        return self.steps[-1].output_text

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


def _apply(state, op, codec):
    """Apply one strict codec operation.

    ``UnicodeEncodeError`` / ``UnicodeDecodeError`` are intentionally allowed to
    propagate to the caller, which drops the edge.
    """
    if op == "encode":
        return state.encode(codec)
    if op == "decode":
        return state.decode(codec)
    raise ValueError("unknown chain op: %r" % (op,))


def replay(text, chain):
    """Apply the chain forward; return the final state or ``None`` on failure."""
    state = text
    try:
        for step in chain.steps:
            state = _apply(state, step.op, step.codec)
    except (UnicodeEncodeError, UnicodeDecodeError):
        return None
    return state


def verify_lossless(text, chain):
    """Replay a chain backwards and return True iff every byte matches.

    This is the strongest form of the §4.3 criterion: the forward run records
    every intermediate state, then the reverse run re-encodes/re-decodes each
    step and compares the result with the recorded state.
    """
    states = [text]
    state = text
    try:
        for step in chain.steps:
            state = _apply(state, step.op, step.codec)
            states.append(state)
    except (UnicodeEncodeError, UnicodeDecodeError):
        return False

    state = states[-1]
    for index in range(len(chain.steps) - 1, -1, -1):
        step = chain.steps[index]
        inverse = "decode" if step.op == "encode" else "encode"
        try:
            state = _apply(state, inverse, step.codec)
        except (UnicodeEncodeError, UnicodeDecodeError):
            return False
        if state != states[index]:
            return False

    return state == text


def _normalize_set(names, default):
    if names is None:
        return tuple(default)
    return tuple(names)


def enumerate_chains(text, encoders=None, decoders=None, max_depth=None):
    """Enumerate lossless candidate chains up to ``max_depth`` decode steps.

    The search is breadth-first. Only lossless, non-identity prefixes are
    extended: an invalid prefix can never become a valid full chain, and an
    identity prefix would only insert a no-op round trip. This keeps the search
    bounded without ever dropping a candidate that could reach a new result.

    Results are sorted by ``(depth, path_string)`` so callers are deterministic.
    """
    encoders = _normalize_set(encoders, codecs_table.ENCODERS)
    decoders = _normalize_set(decoders, codecs_table.DECODERS)
    depth_limit = validate_depth(max_depth)

    results = []
    frontier = [(text, ())]  # (current text, step tuple)
    for _level in range(1, depth_limit + 1):
        next_frontier = []
        for current, steps in frontier:
            for encoder in encoders:
                try:
                    raw = current.encode(encoder)
                except UnicodeEncodeError:
                    continue
                for decoder in decoders:
                    if decoder == encoder:
                        # encode:X>decode:X is a no-op for any valid text.
                        continue
                    try:
                        output = raw.decode(decoder)
                    except UnicodeDecodeError:
                        continue
                    new_steps = steps + (
                        Step(
                            index=len(steps) + 1,
                            op="encode",
                            codec=encoder,
                            input_text=current,
                            output_hex=hexdump(raw),
                        ),
                        Step(
                            index=len(steps) + 2,
                            op="decode",
                            codec=decoder,
                            input_hex=hexdump(raw),
                            output_text=output,
                        ),
                    )
                    chain = Chain(steps=new_steps)
                    if not verify_lossless(text, chain):
                        continue
                    if output == text:
                        # Identity round trip: not a recovery candidate.
                        continue
                    results.append(chain)
                    next_frontier.append((output, new_steps))
        frontier = next_frontier

    results.sort(key=lambda chain: (chain.depth, chain.path_string))
    return results


def collapse_by_result(chains):
    """Keep one representative chain per distinct recovered text.

    The representative is the shallowest chain, then the lexicographically
    smallest ``path_string``. This is a presentation choice only: the lossless
    filter itself is unchanged.
    """
    best = {}
    for chain in chains:
        result = chain.result
        if result is None:
            continue
        key = (chain.depth, chain.path_string)
        current = best.get(result)
        if current is None or key < (current.depth, current.path_string):
            best[result] = chain
    return [best[text] for text in sorted(best)]


def validate_depth(max_depth=None):
    depth = codecs_table.MAX_DEPTH if max_depth is None else int(max_depth)
    if depth < 1:
        raise ValueError("max_depth must be >= 1")
    return depth
