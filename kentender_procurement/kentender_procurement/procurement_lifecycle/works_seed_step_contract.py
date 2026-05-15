# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS master seed — **§15 Procurement Journey Step** contract (LV-R1-004-02).

**Rationale (LV-R1-004-01):** ``Procurement Journey Step`` is a **first-class child table** on
``Procurement Journey`` so seed loaders and R3 aggregators can **materialize** step rows while
the Journey View can still compute steps from source modules later (cursor pack §6.2 allows
child **or** computed rows).

**Dual vocabulary:** ``JOURNEY_STEP_CONFIG`` (R1-002) follows rectification pack **§6.2** (14 spine
rows, keys such as ``demand_captured`` / ``package_released``). The WORKS master seed
specification **§15** uses a **compressed 12-row** base checkpoint table with different
``step_key`` tokens (e.g. ``demand``, ``planning_inclusion``, ``package_release``,
``tender_publication``) so golden seed JSON stays stable. Child rows therefore accept **any**
non-empty ``step_key`` string; **header** ``current_stage_key`` remains validated against
``JOURNEY_STEP_KEYS_IN_ORDER`` (R1-003). R3 services must map between representations when
hydrating from seed vs live aggregates.

**Base checkpoint** ``TENDER_PUBLISHED`` — canonical ``step_key`` sequence (spec table rows
1–12, column *Step Key*):
"""

from __future__ import annotations

from typing import Final

# WORKS master seed data specification §15 — base checkpoint; order is contract-tested (LV-R1-004-02).
WORKS_SEED_TENDER_PUBLISHED_STEP_KEYS_IN_ORDER: Final[tuple[str, ...]] = (
	"strategy",
	"budget",
	"demand",
	"planning_inclusion",
	"package_release",
	"std_readiness",
	"tender_publication",
	"tender_closing",
	"opening_readiness",
	"bid_opening",
	"evaluation_award",
	"contract",
)
