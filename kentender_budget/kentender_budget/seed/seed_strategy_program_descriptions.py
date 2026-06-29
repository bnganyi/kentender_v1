"""W6-11 — One-shot idempotent seed: add descriptions to Strategy Program records.

Rules:
  • Only set description when the current value is null / empty string.
  • Never overwrite a non-empty description (guard clause per record).
  • Derive narrative from program_title + program_code where both are meaningful;
    fall back to a standard placeholder for auto-generated test fixtures.
  • Commit once at the end.

Run:
  bench --site kentender.midas.com execute \\
    kentender_budget.kentender_budget.seed.seed_strategy_program_descriptions.run
"""
from __future__ import annotations

import frappe


# ---------------------------------------------------------------------------
# Curated descriptions for "real" programmes (those with PROG-* codes or
# recognisable titles that have no auto-generated fingerprint in the title).
# Keys are the DocType `name` (primary key); fallback logic below handles
# everything else.
# ---------------------------------------------------------------------------
_CURATED: dict[str, str] = {
    # ── Ministry of Education ─────────────────────────────────────────────
    "dhrcavad23": (
        "Provision of capitation grants to public primary and secondary schools "
        "and equipping institutions with approved learning resources, textbooks, "
        "and instructional materials to support learner outcomes across the county."
    ),
    # ── MOH programmes (already have descriptions — listed for documentation) ──
    # "71ihnhi0c0": already set — Digital Health & ICT Infrastructure
    # "71i93q3ljs": already set — Healthcare Infrastructure Development
    # "71itvto016": already set — Medical Supply Chain Management
    # ── SDT programme (already set) ──────────────────────────────────────
    # "dhre1giubs": already set — Rural Access Roads Development
}

# Standard placeholder applied to auto-generated test fixtures
# (title pattern "Prog-XXXXXX", "AutoTest Programme …", "F5 Programme …").
_TEST_FIXTURE_PLACEHOLDER = (
    "Development programme record — awaiting formal description and "
    "strategic documentation review."
)


def _is_test_fixture(title: str) -> bool:
    """Return True for auto-generated test programme titles."""
    t = (title or "").strip()
    if t.startswith("Prog-") and len(t) == 11:   # e.g. "Prog-0a63ef"
        return True
    if t.startswith("AutoTest Programme") or t.startswith("AutoTest Program"):
        return True
    if t.startswith("F5 Programme") or t.startswith("F5 Program"):
        return True
    if t in ("Program 1", "Programme 1"):        # seed fixture, already has description
        return True
    return False


def _derive_description(name: str, title: str, code: str | None) -> str:
    """Return an appropriate description string for a programme record."""
    # Curated descriptions take absolute priority
    if name in _CURATED:
        return _CURATED[name]

    # Auto-generated / test fixture titles → placeholder
    if _is_test_fixture(title):
        return _TEST_FIXTURE_PLACEHOLDER

    # Fallback for any other un-described programme: generic but contextual
    code_part = f" ({code})" if code else ""
    return (
        f"{title}{code_part} — strategic programme supporting the procuring "
        "entity's mandate. Full description to be provided by the programme owner."
    )


def run():
    """Entry point called by bench execute."""
    records = frappe.get_all(
        "Strategy Program",
        fields=["name", "program_title", "program_code", "description"],
        limit=1000,
        order_by="program_code asc, name asc",
    )

    updated = []
    skipped_has_desc = []
    skipped_no_title = []

    for r in records:
        existing = (r.get("description") or "").strip()

        # Guard: never overwrite real data
        if existing:
            skipped_has_desc.append(r["name"])
            continue

        title = (r.get("program_title") or "").strip()
        if not title:
            skipped_no_title.append(r["name"])
            continue

        desc = _derive_description(r["name"], title, r.get("program_code"))
        frappe.db.set_value(
            "Strategy Program",
            r["name"],
            "description",
            desc,
            update_modified=False,
        )
        updated.append((r["name"], title, desc[:60] + "…" if len(desc) > 60 else desc))

    frappe.db.commit()

    # ── Report ────────────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Strategy Program description seed — W6-11")
    print(f"{'='*70}")
    print(f"  Updated  : {len(updated)}")
    print(f"  Skipped (already had description) : {len(skipped_has_desc)}")
    print(f"  Skipped (no program_title)        : {len(skipped_no_title)}")
    print()

    if updated:
        print("Updated records:")
        for name, title, preview in updated:
            print(f"  [{name}] {title!r}")
            print(f"    → {preview}")
    if skipped_no_title:
        print(f"\nSkipped (no title): {skipped_no_title}")

    # ── Verification ──────────────────────────────────────────────────────
    total   = frappe.db.count("Strategy Program")
    no_desc = frappe.db.count("Strategy Program", {"description": ["in", ["", None]]})
    print(f"\nVerification: {total} total records, {no_desc} still have no description.")
    if no_desc == 0:
        print("✔  All Strategy Program records now have a description.")
    else:
        print("⚠  Some records still lack a description — review manually.")
    print(f"{'='*70}\n")

    return {"updated": len(updated), "total": total, "remaining_empty": no_desc}
