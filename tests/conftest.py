"""Shared fixtures for the Kunumi design-engine tests.

The scripts directory is inserted on `sys.path` rather than installed, mirroring exactly how the
skill invokes them at runtime. Testing an import path the skill never uses would prove nothing.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT / "skills" / "kosmos-design-system"
SCRIPTS_DIR = SKILL_DIR / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


@pytest.fixture(scope="session")
def tokens() -> dict:
    """The real token tree."""
    from kunumi_design import rules

    return rules.load_tokens()


@pytest.fixture()
def mutable_tokens(tokens: dict) -> dict:
    """A deep copy of the token tree, safe to mutate in a derivation test."""
    return copy.deepcopy(tokens)


@pytest.fixture(scope="session")
def registry():
    """The assembled registry built from the real sources."""
    from kunumi_design import rules

    return rules.load_registry()


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    """Directory holding the deliberately non-compliant artifacts."""
    return Path(__file__).resolve().parent / "fixtures"


@pytest.fixture(scope="session")
def skill_dir() -> Path:
    """The skill package directory."""
    return SKILL_DIR


@pytest.fixture()
def lint():
    """Return a helper that reviews one fixture and yields the triggered rule ids."""
    from kunumi_design.checks import review

    def run(path: Path, reg, *, scope: str | None = None, min_severity: str | None = None):
        report = review([path], reg, scope_override=scope)[0]
        found = report.findings
        if min_severity:
            from kunumi_design.findings import severity_at_least

            found = tuple(f for f in found if severity_at_least(f.severity, min_severity))
        return report, {f.rule for f in found}

    return run
