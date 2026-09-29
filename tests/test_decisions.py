"""Tests for the precedent log."""

from __future__ import annotations


def test_template_and_readme_are_not_entries():
    """The template carries placeholder frontmatter so it can be copied, not listed."""
    from kunumi_design import decisions

    names = {item.path.name for item in decisions.load_all()}
    assert "template.md" not in names
    assert "README.md" not in names


def test_entries_are_ordered_newest_first():
    from kunumi_design import decisions

    ids = [item.id for item in decisions.load_all()]
    assert ids == sorted(ids, reverse=True)


def test_rules_field_is_the_join_key():
    from kunumi_design import decisions

    all_entries = decisions.load_all()
    matched = decisions.select(all_entries, rule="typography.line-height.display")
    ids = [item.id for item in matched]

    # Both rulings on this rule must come back: 0002 recorded the tension, 0009 resolved it by
    # measurement. Asserting membership rather than a literal list keeps a new decision on the
    # same rule from breaking the suite.
    assert {"0002", "0009"} <= set(ids)
    assert ids[0] == "0009", "the join key returns the most recent ruling first"


def test_search_covers_body_and_tags():
    from kunumi_design import decisions

    all_entries = decisions.load_all()
    assert decisions.select(all_entries, search="chrome")
    assert decisions.select(all_entries, search="leading")
    assert not decisions.select(all_entries, search="nonexistent-topic-xyz")


def test_next_id_is_padded_and_sequential():
    """Asserted relative to what exists, not against a literal.

    Pinning the number would make every new decision break the suite, which trains people to
    stop writing decisions.
    """
    from kunumi_design import decisions

    entries = decisions.load_all()
    next_id = decisions.next_id(entries)
    assert len(next_id) == 4 and next_id.isdigit()
    assert int(next_id) == max(int(item.id) for item in entries) + 1


def test_ids_are_unique():
    from kunumi_design import decisions

    ids = [item.id for item in decisions.load_all()]
    assert len(ids) == len(set(ids))


def test_every_entry_has_a_title_and_status():
    from kunumi_design import decisions

    for item in decisions.load_all():
        assert item.title and not item.title.startswith("<")
        assert item.status in ("proposed", "accepted") or item.status.startswith("superseded-by-")
