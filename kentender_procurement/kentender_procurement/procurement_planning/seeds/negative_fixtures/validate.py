# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Validate NEG-PP2 negative fixtures by proving attempted_action blockers (P3-017)."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.procurement_planning.seeds.negative_fixtures.attempted_actions import (
	fixture_loaded,
	prove_fixture_blocker,
)
from kentender_procurement.procurement_planning.seeds.negative_fixtures.registry import (
	get_negative_fixture_spec,
)

SEED_ACTOR = "Administrator"


def run_validate(*, fixture_code: str) -> dict[str, Any]:
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

	if not fixture_loaded(code):
		return {
			"ok": False,
			"error_code": "FIXTURE_NOT_LOADED",
			"fixture_code": code,
			"message": (
				"Negative fixture precondition is not loaded. "
				"Call load_procurement_planning_negative_fixture first."
			),
		}

	proof_out = prove_fixture_blocker(code, spec)
	observed_result = (proof_out.get("observed_result") or "").strip()
	observed_blocker = (proof_out.get("observed_blocker_code") or "").strip()
	expected_result = spec.expected_result
	expected_blocker = spec.blocker_code

	if observed_result != "FAIL" or observed_blocker != expected_blocker:
		return {
			"ok": False,
			"error_code": "NEG_FIXTURE_VALIDATION_FAILED",
			"fixture_code": code,
			"attempted_action": spec.attempted_action,
			"expected_result": expected_result,
			"expected_blocker_code": expected_blocker,
			"observed_result": observed_result or None,
			"observed_blocker_code": observed_blocker or None,
			"message": spec.message,
			"proof": proof_out.get("proof") or {},
		}

	return {
		"ok": True,
		"fixture_code": code,
		"attempted_action": spec.attempted_action,
		"expected_result": expected_result,
		"expected_blocker_code": expected_blocker,
		"observed_result": observed_result,
		"observed_blocker_code": observed_blocker,
		"message": spec.message,
		"proof": proof_out.get("proof") or {},
	}
