"""Deterministic engine behind the Kunumi designer loop.

The package is deliberately import-safe and stdlib-only except for `render`, which declares its
own optional dependency. Every public entry point takes JSON-serializable input and returns a
dataclass carrying `to_dict()`, so the same functions can later be exposed as MCP tools without
restructuring: `kunumi_critic.py` is only an argparse shell over this package.
"""

from __future__ import annotations

__all__ = ["findings", "rules", "scan"]
