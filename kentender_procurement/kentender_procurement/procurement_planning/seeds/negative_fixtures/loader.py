# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Load NEG-PP2 negative fixtures (setup-only)."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.procurement_planning.seeds.negative_fixtures.clear import run_clear
from kentender_procurement.procurement_planning.seeds.negative_fixtures.registry import get_negative_fixture_spec

SEED_ACTOR = "Administrator"


def run_load(*, fixture_code: str) -> dict[str, Any]:
	frappe.set_user(SEED_ACTOR)
	code = (fixture_code or "").strip()
	spec = get_negative_fixture_spec(code)
	if not spec:
		return {
			"ok": False,
			"error_code": "UNKNOWN_FIXTURE",
			"fixture_code": code,
			"message": f"Unknown negative fixture: {code}",
		}

	run_clear(fixture_code=code, skip_guard=True)
	setup_out = spec.setup_fn()
	frappe.db.commit()

	return {
		"ok": True,
		"fixture_code": spec.fixture_code,
		"setup": spec.setup,
		"attempted_action": spec.attempted_action,
		"expected_result": spec.expected_result,
		"blocker_code": spec.blocker_code,
		"message": spec.message,
		"records": setup_out.get("records") or {},
		"context": setup_out.get("context") or {},
	}
