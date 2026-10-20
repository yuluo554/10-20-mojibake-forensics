# -*- coding: utf-8 -*-
"""Canonical JSON, exit codes and report envelopes.

Single serialization point for the whole project. Subcommands must not call
``json.dump`` directly (K4 in plan/HANDOFF-M1.md).
"""

from __future__ import absolute_import, print_function

import json
import platform
import sys

from . import SCHEMA, __version__
from . import codecs_table


EXIT_OK = 0
EXIT_ATTENTION = 1
EXIT_USAGE = 2
EXIT_ENV = 3
# Skeleton-only code; retired in M5/M6 (constant, CLI, tests, docs — four places).
EXIT_NOT_READY = 4


def base_envelope(status):
    return {
        "schema": SCHEMA,
        "tool_version": __version__,
        "python_version": platform.python_version(),
        "status": status,
        "notes": [],
        "criteria": codecs_table.criteria(),
    }


def not_ready(command, milestone):
    envelope = base_envelope("not_ready")
    envelope["command"] = command
    envelope["milestone"] = milestone
    envelope["notes"] = ["not_implemented_in_skeleton"]
    return envelope


def error(code, message, command=None):
    envelope = base_envelope("error")
    envelope["code"] = code
    envelope["message"] = message
    if command:
        envelope["command"] = command
    return envelope


def dumps(payload):
    """Canonical JSON text: sorted keys, UTF-8 literals, LF, trailing newline."""
    return (
        json.dumps(payload, sort_keys=True, ensure_ascii=False, indent=2) + "\n"
    )


def write_json(payload, stream=None):
    stream = stream if stream is not None else sys.stdout
    stream.write(dumps(payload))


def human_not_ready(command, milestone):
    return (
        "%s: not implemented yet (skeleton, milestone %s)\n"
        "  This build exposes the interface and exit-code contract only.\n"
        "  See plan/03-模块详设.md and plan/HANDOFF-M1.md for the next milestone.\n"
        % (command, milestone)
    )


def emit(payload, as_json=False, command=None, milestone=None, stream=None):
    stream = stream if stream is not None else sys.stdout
    if as_json or payload.get("status") == "error":
        write_json(payload, stream=stream)
    elif payload.get("status") == "not_ready":
        stream.write(human_not_ready(command or payload.get("command", "?"), milestone or payload.get("milestone", "?")))
    else:
        write_json(payload, stream=stream)
