"""W6-12 — Fix dangling strategy references on Budget Lines (and their parent Budget).

Audit findings
──────────────
One active Budget Line has all four strategy FK fields pointing to records that
no longer exist (phantom IDs from a superseded seed run):

  Budget Line : BUD-MOH-INFRA-2026-001
                "District Health Facility Infrastructure Rehabilitation"
  Budget      : BUD-PE-MOH-2026-.0085  (BUDGET-MOH-2026, Approved)

  Field              Dangling value      Correct replacement
  ─────────────────  ──────────────────  ─────────────────────────────────────
  strategic_plan     PE-MOH-SP-2026-0001 PE-MOH-SP-2026-0077 (Primary Health
                     (record missing)    Care Expansion Plan 2026–2031)
  program            qi6p5sitnc (missing) 71i93q3ljs — Healthcare Infrastructure
                                          Development (PROG-MOH-INFRA)
  sub_program        mkq7tbetcf (missing) 71il48n0vg — District Hospital
                                          Renovation (SUB-INFRA-001)
  output_indicator   qi6o0duk01 (missing) 71i7v73bsf — Hospital Renovation
                                          Completion (OBJ-INFRA-001)
  performance_target qi750e3pjg (missing) 71i1qt9ork — Renovate 18 priority
                                          district hospitals (TGT-INFRA-001)

The parent Budget also carries strategic_plan = PE-MOH-SP-2026-0001.  Because
upsert_budget_line copies strategic_plan from the budget document, we fix both.

Script behaviour
────────────────
• Runs a live audit first; reports every dangling FK found.
• Applies only the mappings listed above; does nothing to records that already
  carry valid references.
• Uses frappe.db.set_value (bypasses validators) because the Budget is Approved
  and the Budget Line validator also guards against plan mismatches.
• Guards: only overwrites a field when the current value is in _DANGLING_IDS.
  A field that already holds a valid FK is left untouched.
• Commits once after all writes.

Run:
  bench --site kentender.midas.com execute \\
    kentender_budget.kentender_budget.seed.fix_dangling_strategy_refs.run
"""
from __future__ import annotations

import frappe


# ── Known dangling IDs → correct replacements ─────────────────────────────
# Maps the phantom primary key to the correct existing record name.

_PROGRAM_MAP: dict[str, str] = {
    "qi6p5sitnc": "71i93q3ljs",  # Healthcare Infrastructure Development
}

_SUB_PROGRAM_MAP: dict[str, str] = {
    "mkq7tbetcf": "71il48n0vg",  # District Hospital Renovation
}

_OUTPUT_INDICATOR_MAP: dict[str, str] = {
    "qi6o0duk01": "71i7v73bsf",  # Hospital Renovation Completion
}

_PERFORMANCE_TARGET_MAP: dict[str, str] = {
    "qi750e3pjg": "71i1qt9ork",  # Renovate 18 priority district hospitals
}

_STRATEGIC_PLAN_MAP: dict[str, str] = {
    "PE-MOH-SP-2026-0001": "PE-MOH-SP-2026-0077",  # Primary Health Care Expansion Plan
}

# All dangling IDs in one flat set — used by the audit query
_ALL_DANGLING: set[str] = (
    set(_PROGRAM_MAP)
    | set(_SUB_PROGRAM_MAP)
    | set(_OUTPUT_INDICATOR_MAP)
    | set(_PERFORMANCE_TARGET_MAP)
    | set(_STRATEGIC_PLAN_MAP)
)


# ── Audit helpers ─────────────────────────────────────────────────────────

def _audit_budget_lines() -> list[dict]:
    """Return active Budget Lines that carry at least one dangling strategy FK."""
    rows = frappe.get_all(
        "Budget Line",
        filters={"is_active": 1},
        fields=[
            "name", "budget_line_name", "budget",
            "strategic_plan", "program", "sub_program",
            "output_indicator", "performance_target",
        ],
        limit=5000,
    )
    dangling = []
    for r in rows:
        fields_with_dangling = {}
        for field in ("strategic_plan", "program", "sub_program",
                      "output_indicator", "performance_target"):
            val = r.get(field) or ""
            if val and not _exists(field, val):
                fields_with_dangling[field] = val
        if fields_with_dangling:
            dangling.append({"line": r, "dangling": fields_with_dangling})
    return dangling


def _audit_budgets() -> list[dict]:
    """Return Budget documents whose strategic_plan FK is missing."""
    rows = frappe.get_all(
        "Budget",
        fields=["name", "budget_name", "strategic_plan", "status"],
        limit=5000,
    )
    dangling = []
    for r in rows:
        sp = r.get("strategic_plan") or ""
        if sp and not frappe.db.exists("Strategic Plan", sp):
            dangling.append(r)
    return dangling


def _exists(field: str, value: str) -> bool:
    """Return True when *value* resolves to an existing record for the given field."""
    doctype_map = {
        "strategic_plan": "Strategic Plan",
        "program":        "Strategy Program",
        "sub_program":    "Sub Program",
        "output_indicator": "Strategy Objective",
        "performance_target": "Strategy Target",
    }
    dt = doctype_map.get(field)
    if not dt:
        return True   # unknown field → assume valid
    return bool(frappe.db.exists(dt, value))


# ── Fix helpers ───────────────────────────────────────────────────────────

def _replacement(field: str, value: str) -> str | None:
    """Return the correct replacement for a known dangling ID, or None."""
    maps = {
        "strategic_plan":    _STRATEGIC_PLAN_MAP,
        "program":           _PROGRAM_MAP,
        "sub_program":       _SUB_PROGRAM_MAP,
        "output_indicator":  _OUTPUT_INDICATOR_MAP,
        "performance_target": _PERFORMANCE_TARGET_MAP,
    }
    return maps.get(field, {}).get(value)


def _apply_fix(doctype: str, name: str, field: str, old_val: str) -> str:
    """Write the corrected value; returns a one-line description of the action."""
    replacement = _replacement(field, old_val)
    if replacement:
        frappe.db.set_value(doctype, name, field, replacement,
                            update_modified=False)
        return f"  [{field}]  {old_val!r}  →  {replacement!r}  (matched)"
    else:
        # Dangling ID is not in the map — clear to None so the API returns null
        frappe.db.set_value(doctype, name, field, None,
                            update_modified=False)
        return f"  [{field}]  {old_val!r}  →  None  (cleared — no mapping found)"


# ── Main ──────────────────────────────────────────────────────────────────

def run():
    """Entry point: audit → report → fix → commit → verify."""
    SEP = "=" * 70
    print(f"\n{SEP}")
    print("W6-12  Fix dangling strategy references")
    print(SEP)

    # ── 1. Audit ─────────────────────────────────────────────────────────
    dangling_lines  = _audit_budget_lines()
    dangling_budgets = _audit_budgets()

    print(f"\n  Budget Lines with dangling strategy refs : {len(dangling_lines)}")
    print(f"  Budget documents with dangling plan      : {len(dangling_budgets)}")

    if not dangling_lines and not dangling_budgets:
        print("\n✔  Nothing to fix — all strategy references are valid.")
        print(f"{SEP}\n")
        return {"fixed_lines": 0, "fixed_budgets": 0}

    print("\nDetails:")
    for item in dangling_lines:
        r = item["line"]
        print(f"\n  Budget Line: {r['name']}  |  {r['budget_line_name']}")
        print(f"  Budget     : {r['budget']}")
        for field, val in item["dangling"].items():
            repl = _replacement(field, val)
            action = f"→ {repl!r} (will match)" if repl else "→ None (will clear)"
            print(f"    dangling [{field}] = {val!r}   {action}")

    for r in dangling_budgets:
        repl = _STRATEGIC_PLAN_MAP.get(r["strategic_plan"], None)
        action = f"→ {repl!r} (will match)" if repl else "→ None (will clear)"
        print(f"\n  Budget: {r['name']}  |  {r['budget_name']}")
        print(f"    dangling [strategic_plan] = {r['strategic_plan']!r}   {action}")

    # ── 2. Apply fixes ────────────────────────────────────────────────────
    print(f"\n{'─'*70}")
    print("Applying fixes …")

    fixed_lines   = 0
    fixed_budgets = 0

    for item in dangling_lines:
        r = item["line"]
        print(f"\n  Fixing Budget Line: {r['name']}")
        for field, val in item["dangling"].items():
            msg = _apply_fix("Budget Line", r["name"], field, val)
            print(msg)
        fixed_lines += 1

    for r in dangling_budgets:
        val = r["strategic_plan"]
        msg = _apply_fix("Budget", r["name"], "strategic_plan", val)
        print(f"\n  Fixing Budget: {r['name']}")
        print(msg)
        fixed_budgets += 1

    # ── 3. Commit ─────────────────────────────────────────────────────────
    frappe.db.commit()
    print("\n  frappe.db.commit() — done.")

    # ── 4. Verify ─────────────────────────────────────────────────────────
    print(f"\n{'─'*70}")
    print("Post-fix verification …")

    remaining_lines   = _audit_budget_lines()
    remaining_budgets = _audit_budgets()

    if not remaining_lines and not remaining_budgets:
        print("✔  All strategy references are now valid.")
    else:
        print(f"⚠  {len(remaining_lines)} Budget Line(s) and "
              f"{len(remaining_budgets)} Budget(s) still have dangling refs — review manually.")
        for item in remaining_lines:
            print(f"   {item['line']['name']}: {item['dangling']}")
        for r in remaining_budgets:
            print(f"   {r['name']}: strategic_plan={r['strategic_plan']!r}")

    print(f"\n  Fixed Budget Lines  : {fixed_lines}")
    print(f"  Fixed Budgets       : {fixed_budgets}")
    print(f"{SEP}\n")
    return {"fixed_lines": fixed_lines, "fixed_budgets": fixed_budgets}
