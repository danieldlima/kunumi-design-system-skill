"""Tests for how the skill is actually invoked.

This file exists because of a real defect. The docs first told the agent to call the engine with
`../kosmos-design-system/scripts/kunumi_critic.py`, which resolves relative to the *working
directory* — and in a real session that is the user's project, not the skill package. Every
command in the loop failed with "No such file or directory".

The engine was fine; the instructions were wrong. Instructions are part of the deliverable, so
they get tests.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CRITIC = REPO_ROOT / "skills" / "kosmos-design-system" / "scripts" / "kunumi_critic.py"
DOCS = (
    REPO_ROOT / "skills" / "kosmos-designer" / "SKILL.md",
    REPO_ROOT / "skills" / "kosmos-designer" / "references" / "design-loop.md",
    REPO_ROOT / "README.md",
)


@pytest.mark.parametrize("doc", DOCS, ids=lambda p: p.name)
def test_docs_never_teach_a_cwd_relative_engine_path(doc):
    """A path starting with `../` cannot find the sibling skill from a user's project."""
    text = doc.read_text(encoding="utf-8")
    assert "../kosmos-design-system/scripts" not in text


@pytest.mark.parametrize("doc", DOCS[:2], ids=lambda p: p.name)
def test_designer_docs_carry_the_resolver(doc):
    """Both designer-facing documents must show how to locate the engine."""
    text = doc.read_text(encoding="utf-8")
    assert "find -L" in text, "the resolver must use find -L or it misses a symlinked install"
    assert "kunumi_critic.py" in text


def test_resolver_uses_find_dash_l_because_installs_are_symlinks():
    """`find` without -L silently returns nothing for the documented local-dev install.

    Pinned as a test because the failure mode is an empty variable and a confusing error several
    steps later, not an obvious crash.
    """
    text = (REPO_ROOT / "skills" / "kosmos-designer" / "SKILL.md").read_text(encoding="utf-8")
    assert "find -L ~/.claude/skills" in text


def test_engine_runs_from_an_unrelated_working_directory(tmp_path):
    """The scripts resolve their own location, so the caller's CWD must not matter."""
    completed = subprocess.run(
        [sys.executable, str(CRITIC), "rules", "--scope", "web.new"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert "scope=web.new" in completed.stdout


def test_engine_lints_an_artifact_outside_the_repository(tmp_path):
    """The common real case: an artifact in the user's project, engine in the skill package."""
    artifact = tmp_path / "bad.html"
    artifact.write_text(
        """<!doctype html><html><head><meta charset="utf-8"><style>
             body { background: #000000; }
             .site-logo { filter: invert(1); }
           </style></head><body>
             <img class="site-logo" data-kunumi-role="logo" src="m.png" alt="Kunumi">
           </body></html>""",
        encoding="utf-8",
    )
    completed = subprocess.run(
        [sys.executable, str(CRITIC), "lint", str(artifact)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 2, completed.stdout + completed.stderr
    assert "color.prohibition.black" in completed.stdout
    assert "logo.no-effects" in completed.stdout


def test_decisions_resolve_through_a_symlinked_install(tmp_path):
    """`decisions/` is found relative to the script, not the CWD."""
    completed = subprocess.run(
        [sys.executable, str(CRITIC), "decisions", "--limit", "1"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert "next-id=" in completed.stdout


@pytest.mark.skipif(
    not (Path.home() / ".claude" / "skills" / "kosmos-designer").exists(),
    reason="kosmos-designer is not installed for local development",
)
def test_both_skills_are_installed_side_by_side():
    """The designer reaches the engine as a sibling, so a single symlink is not enough."""
    skills = Path.home() / ".claude" / "skills"
    assert (skills / "kosmos-designer" / "SKILL.md").is_file()
    assert (skills / "kosmos-design-system" / "scripts" / "kunumi_critic.py").is_file()


@pytest.mark.skipif(
    not (Path.home() / ".claude" / "skills" / "kosmos-design-system").exists(),
    reason="kosmos-design-system is not installed for local development",
)
def test_documented_resolver_finds_a_real_file():
    """Run the exact command the docs give, and assert it lands on an executable script."""
    command = (
        'find -L ~/.claude/skills ~/.claude/plugins/cache '
        "-maxdepth 7 -name kunumi_critic.py 2>/dev/null | head -1"
    )
    completed = subprocess.run(
        ["sh", "-c", command], capture_output=True, text=True, cwd=os.sep
    )
    resolved = completed.stdout.strip()
    assert resolved, "the documented resolver returned nothing"
    assert Path(resolved).is_file()
