# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R3-014 / LV-R3-014-01 — **Current stage calculation** (cursor pack §9.4).

## Goal

``calculate_journey_current_stage(journey_code)`` derives the **current stage**,
**current status category**, and **next action** of a ``Procurement Journey`` from its
live step data, applying the four-tier priority algorithm defined in pack §9.4.

The companion ``update_journey_current_stage(journey_code)`` persists the computed
values back to the ``Procurement Journey`` DocType via ``frappe.db.set_value`` (only
touching the three PLC-owned fields — the source-module authority rule ADR-PLC-002 is
respected).

## Algorithm (pack §9.4 priority order)

1. **Critical blocker stage** — if any step has ``status_category == "Blocked"``,
   the current stage is the *first* (lowest ``step_order``) blocked step.

2. **Latest completed handoff with next incomplete step** — find the step with the
   highest ``step_order`` whose ``status_category`` is in
   ``{Completed, Handed Off, Ready for Handoff, In Progress, Needs Action, Returned}``.
   That step is the "current" step. ``current_stage`` = its ``label``;
   ``current_status`` = its ``status_category``.

3. **Next action derivation** — from the current step:
   a. Use the current step's own ``next_action`` text if non-empty.
   b. Otherwise fall back to the *following* step's ``next_action`` (the first
      ``Not Started`` step after the current one).
   c. Otherwise empty string.

4. **Fallback** — if all steps are ``Not Started``, return the first step (or a
   generic "Not Started" response if there are no steps at all).

## WORKS golden scenario (pack §9.4)

For the WORKS master seed at base checkpoint (``TENDER_PUBLISHED``):

| Step order | Step key | status_category |
|---|---|---|
| 1–4 | strategy → planning_inclusion | Completed |
| 5 | package_release | Handed Off |
| 6–7 | std_readiness → tender_publication | Completed |
| 8–12 | tender_closing → contract | Not Started |

→ Highest active step = 7 (tender_publication, Completed)

Expected:
```json
{
  "current_stage": "Tender Published",
  "current_stage_key": "tender_publication",
  "current_status": "Completed",
  "next_action": "Await tender closing"
}
```

(``next_action`` comes from step 7's stored ``next_action``; the journey-level stored
value may be longer — e.g. "Await tender closing / prepare bid opening readiness" — and
callers can supplement it from the Journey DocType when needed.)

## Return shape

```python
{
  "current_stage": str,        # label of the current step
  "current_stage_key": str,    # step_key of the current step
  "current_status": str,       # status_category of the current step
  "next_action": str,          # derived next action text (may be empty)
  "is_blocked": bool,          # True if any step is Blocked
  "blocked_step_key": str | None,  # step_key of the first blocked step
}
```

## Error codes

| Code | Condition |
|---|---|
| ``INVALID_JOURNEY_CODE`` | ``journey_code`` is blank or not a string. |
| ``JOURNEY_NOT_FOUND`` | No ``Procurement Journey`` with the given code. |
"""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.procurement_lifecycle.journey_step_aggregator import (
    aggregate_procurement_journey_steps,
)

# Status categories that mean "work has substantively started / progressed / completed"
# for this step — used to find the "latest active step".
_ACTIVE_STATUSES: frozenset[str] = frozenset(
    {
        "Completed",
        "Handed Off",
        "Ready for Handoff",
        "In Progress",
        "Needs Action",
        "Returned",
    }
)

_BLOCKED = "Blocked"
_NOT_STARTED = "Not Started"


def calculate_current_stage_from_steps(
    steps: list[dict[str, Any]],
) -> dict[str, Any]:
    """Pure function — derive current stage from an ordered step list.

    :param steps: Ordered step list (from ``aggregate_procurement_journey_steps``).
    :returns: Stage dict (see module docstring for shape).
    """
    if not steps:
        return {
            "current_stage": "",
            "current_stage_key": "",
            "current_status": _NOT_STARTED,
            "next_action": "",
            "is_blocked": False,
            "blocked_step_key": None,
        }

    # 1. Critical blocker check — first (lowest step_order) blocked step
    blocked_steps = [s for s in steps if s.get("status_category") == _BLOCKED]
    if blocked_steps:
        blocker = blocked_steps[0]
        return {
            "current_stage": blocker.get("label") or "",
            "current_stage_key": blocker.get("step_key") or "",
            "current_status": _BLOCKED,
            "next_action": blocker.get("next_action") or "",
            "is_blocked": True,
            "blocked_step_key": blocker.get("step_key") or None,
        }

    # 2. Latest active step (highest step_order in _ACTIVE_STATUSES)
    # Steps are already ordered by step_order ascending; iterate in reverse.
    active_step: dict[str, Any] | None = None
    active_index: int = -1
    for i, step in enumerate(reversed(steps)):
        if step.get("status_category") in _ACTIVE_STATUSES:
            # Convert reversed index to forward index
            active_step = step
            active_index = len(steps) - 1 - i
            break

    # 3. If no active step found → all Not Started → use first step
    if active_step is None:
        first = steps[0]
        return {
            "current_stage": first.get("label") or "",
            "current_stage_key": first.get("step_key") or "",
            "current_status": _NOT_STARTED,
            "next_action": first.get("next_action") or "",
            "is_blocked": False,
            "blocked_step_key": None,
        }

    # 4. Derive next_action:
    #    a. from active step's own next_action
    #    b. from the following (first Not Started) step's next_action
    next_action: str = str(active_step.get("next_action") or "").strip()
    if not next_action and active_index + 1 < len(steps):
        following_step = steps[active_index + 1]
        next_action = str(following_step.get("next_action") or "").strip()

    return {
        "current_stage": active_step.get("label") or "",
        "current_stage_key": active_step.get("step_key") or "",
        "current_status": str(active_step.get("status_category") or _NOT_STARTED),
        "next_action": next_action,
        "is_blocked": False,
        "blocked_step_key": None,
    }


def calculate_journey_current_stage(journey_code: str) -> dict[str, Any]:
    """Compute current stage + next_action from the live step data of a journey.

    :param journey_code: Procurement Journey identifier.
    :returns: Stage dict (see module docstring for shape).
    :raises ValueError: If ``journey_code`` is blank (``INVALID_JOURNEY_CODE``).
    :raises frappe.DoesNotExistError: If the journey does not exist (``JOURNEY_NOT_FOUND``).
    """
    if not journey_code or not isinstance(journey_code, str) or not journey_code.strip():
        raise ValueError(
            "INVALID_JOURNEY_CODE: journey_code must be a non-empty string"
        )

    code = journey_code.strip()

    # Load steps — raises DoesNotExistError / ValueError on invalid journey
    steps = aggregate_procurement_journey_steps(code)

    return calculate_current_stage_from_steps(steps)


def update_journey_current_stage(journey_code: str) -> dict[str, Any]:
    """Compute and persist the current stage fields on the ``Procurement Journey`` DocType.

    Only touches three PLC-owned fields (``current_stage_label``,
    ``current_status_category``, ``next_action``). Source-module fields on the Journey
    (ref fields, fiscal_year, etc.) are never touched. ADR-PLC-002 compliant.

    :param journey_code: Procurement Journey identifier.
    :returns: Computed stage dict (same as ``calculate_journey_current_stage``).
    :raises ValueError: If ``journey_code`` is blank (``INVALID_JOURNEY_CODE``).
    :raises frappe.DoesNotExistError: If the journey does not exist (``JOURNEY_NOT_FOUND``).
    """
    result = calculate_journey_current_stage(journey_code)

    frappe.db.set_value(
        "Procurement Journey",
        journey_code.strip(),
        {
            "current_stage_label": result["current_stage"],
            "current_stage_key": result["current_stage_key"],
            "current_status_category": result["current_status"],
            "next_action": result["next_action"],
        },
        update_modified=False,
    )
    frappe.db.commit()

    return result
