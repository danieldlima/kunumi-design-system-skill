#!/usr/bin/env python3
"""Read the design decision log.

The log is the only part of this engine that accumulates judgment rather than deriving it. A rule
set encodes what is always true; `decisions/` encodes what was decided once, for a reason, in a
case the rules could not settle. Reading it before proposing is step 0 of the loop.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DECISIONS_DIR = Path(__file__).resolve().parents[2] / "decisions"
_ID_RE = re.compile(r"^(\d{4})-")
NON_ENTRIES = frozenset({"README.md", "template.md"})


@dataclass(frozen=True, slots=True)
class Decision:
    """One recorded decision.

    Attributes:
        id: Four-digit identifier.
        status: `proposed`, `accepted`, or `superseded-by-NNNN`.
        date: ISO date the decision was taken.
        scope: Rule scope the decision applies under.
        artifact: What the decision was about.
        rules: Rule ids the decision interprets. The join key for `--rule`.
        tags: Free-form tags.
        title: The decision stated as a claim.
        path: Path to the entry.
        body: Full markdown body after the frontmatter.
    """

    id: str
    status: str
    date: str
    scope: str
    artifact: str
    rules: tuple[str, ...]
    tags: tuple[str, ...]
    title: str
    path: Path
    body: str

    def to_dict(self) -> dict[str, Any]:
        """Render the decision as a JSON-ready mapping."""
        return {
            "id": self.id,
            "status": self.status,
            "date": self.date,
            "scope": self.scope,
            "artifact": self.artifact,
            "rules": list(self.rules),
            "tags": list(self.tags),
            "title": self.title,
            "path": str(self.path),
        }


def _split_list(raw: str) -> tuple[str, ...]:
    """Read a comma-separated frontmatter list, dropping the `none` placeholder."""
    items = tuple(item.strip() for item in raw.split(",") if item.strip())
    return () if items == ("none",) else items


def parse(path: Path) -> Decision | None:
    """Parse one decision file.

    Reuses the same frontmatter shape `validate-skills.py` already parses, deliberately: a second
    frontmatter dialect in one repository is a maintenance tax with no benefit.

    Args:
        path: Path to the markdown entry.

    Returns:
        The parsed decision, or None when the file is not an entry. `README.md` and `template.md`
        live in the same directory, and the template deliberately carries placeholder frontmatter
        so it can be copied — so name and id shape are both checked, not just frontmatter
        presence.
    """
    if path.name in NON_ENTRIES:
        return None

    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end == -1:
        return None

    fields: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip().strip('"').strip("'")

    body = text[end + 5 :]
    title = next(
        (line[2:].strip() for line in body.splitlines() if line.startswith("# ")),
        path.stem,
    )
    match = _ID_RE.match(path.name)
    identifier = fields.get("id", "")
    if not (len(identifier) == 4 and identifier.isdigit()):
        identifier = match.group(1) if match else ""
    if not identifier:
        return None

    return Decision(
        id=identifier,
        status=fields.get("status", "proposed"),
        date=fields.get("date", ""),
        scope=fields.get("scope", ""),
        artifact=fields.get("artifact", ""),
        rules=_split_list(fields.get("rules", "")),
        tags=_split_list(fields.get("tags", "")),
        title=title,
        path=path,
        body=body,
    )


def load_all(directory: Path | None = None) -> tuple[Decision, ...]:
    """Read every decision, newest id first.

    Args:
        directory: Override for the decisions directory, for tests.

    Returns:
        The parsed entries, ordered by descending id so recent precedent is read first.
    """
    directory = directory or DECISIONS_DIR
    if not directory.is_dir():
        return ()
    found = [parse(path) for path in sorted(directory.glob("*.md"))]
    return tuple(sorted((item for item in found if item), key=lambda d: d.id, reverse=True))


def select(
    decisions: tuple[Decision, ...],
    *,
    search: str | None = None,
    rule: str | None = None,
    status: str | None = None,
    scope: str | None = None,
) -> tuple[Decision, ...]:
    """Filter decisions.

    Args:
        decisions: Entries to filter.
        search: Case-insensitive substring matched against title, body, artifact and tags.
        rule: Keep only entries interpreting this rule id.
        status: Keep only entries with this status.
        scope: Keep only entries taken under this scope.

    Returns:
        The matching entries, in input order.
    """
    result = decisions
    if rule:
        result = tuple(item for item in result if rule in item.rules)
    if status:
        result = tuple(item for item in result if item.status == status)
    if scope:
        result = tuple(item for item in result if item.scope == scope)
    if search:
        needle = search.lower()
        result = tuple(
            item
            for item in result
            if needle in item.title.lower()
            or needle in item.body.lower()
            or needle in item.artifact.lower()
            or any(needle in tag.lower() for tag in item.tags)
        )
    return result


def next_id(decisions: tuple[Decision, ...]) -> str:
    """Compute the next free decision id.

    Args:
        decisions: Existing entries.

    Returns:
        A zero-padded four-digit id.
    """
    numbers = [int(item.id) for item in decisions if item.id.isdigit()]
    return f"{(max(numbers) + 1) if numbers else 1:04d}"
