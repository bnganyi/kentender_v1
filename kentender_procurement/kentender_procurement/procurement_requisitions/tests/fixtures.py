# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 test world (D13) — extends Procurement Planning's own
`KENTENDER_TEST` world rather than building a second one: an eligible Plan
Item can only come from Planning's own commands, and Planning's fixture
actors (`AUTHOR`/`HOD`/`HOPF`/`PLANNER`/`AUDITOR`/`OUTSIDER`) already hold
exactly the responsibilities Requisitions tests need for `OU_ALPHA`.

`confirmed_single_source_item()`/`active_single_source_item()` are Planning's
own proven `test_plan_requisition.RequisitionCase.confirmed_item()`/
`.activate()`/`.active_item()` sequence, copied verbatim (not re-derived)
precisely to avoid a second, subtly-different copy of a multi-step
governed-plan-activation flow already exercised by 22 passing Planning
tests.
"""

from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

import frappe

from kentender_procurement.procurement_planning.services import (
	dpp_lifecycle,
	dpp_validation,
	needs_intake,
	plan_finance,
	plan_governance,
	plan_read,
	plan_workbench,
)
from kentender_procurement.procurement_planning.tests import fixtures as pln_fx

NS = pln_fx.NS
AUTHOR = pln_fx.AUTHOR
HOD = pln_fx.HOD
HOPF = pln_fx.HOPF
PLANNER = pln_fx.PLANNER
AUDITOR = pln_fx.AUDITOR
OUTSIDER = pln_fx.OUTSIDER
FINANCE_OFFICER = pln_fx.FINANCE_OFFICER
ACCOUNTING_OFFICER = pln_fx.ACCOUNTING_OFFICER
STATUTORY = pln_fx.STATUTORY


def _ou_alpha() -> str:
	"""`pln_fx.OU_ALPHA` is only filled in by `ensure_world()` (a `global`
	rebinding inside Planning's own module) — a static alias captured at
	import time would freeze the pre-`ensure_world()` empty string, which is
	exactly the bug this function exists to avoid."""
	return pln_fx.OU_ALPHA


def key() -> str:
	return uuid4().hex


def ensure_world() -> None:
	pln_fx.ensure_world()
	# §9.1A's segregation-of-duties test needs one actor who legitimately
	# holds both a submit-eligible responsibility (Head of User Department
	# both prepares AND submits — §7.3) and Head of Procurement Function,
	# so the block under test is the *action* pairing (drafted, submitted
	# and would-authorise the same Requisition), not a role Planning's own
	# fixture roster never grants HOPF in the first place.
	from kentender_core.services import responsibility_administration as administration

	administration.grant(user=pln_fx.HOPF, business_role="Head of User Department", organisation_unit=_ou_alpha(), fixture_namespace=NS, actor="Administrator")


def restore_site() -> None:
	pln_fx.restore_site()


def wipe_planning_rows() -> None:
	"""Delegates to Planning's own per-test DPP/Plan isolation — required
	before every test that calls `confirmed_item`/`active_item`, or the next
	test reuses the prior one's already-progressed DPP (PLN_DPP_STALE)."""
	pln_fx.wipe_planning_rows()


def wipe_requisition_rows() -> None:
	frappe.set_user("Administrator")
	for doctype in (
		"Requisition Event", "Requisition Decision", "Requisition Task", "Authorised Requisition Handoff",
		"Requisition Version", "IT Equipment Requirement Package Version", "IT Equipment Requirement Package",
		"Procurement Requisition", "Requisition Command Journal",
	):
		frappe.db.delete(doctype)
	# authorise_requisition() reserves funding in Budget (D1) under
	# `calling_module="Procurement Requisitions"`; those rows live outside
	# this app and are never touched by `wipe_planning_rows()`, so a prior
	# test's still-Active reservation on the same (deterministically
	# re-issued) plan_source_allocation blocks the next test's reserve call
	# with BUDGET_RESERVATION_CONFLICT unless wiped here too.
	frappe.db.delete("Funding Reservation", {"calling_module": "Procurement Requisitions"})
	frappe.db.commit()


def complete_and_confirm(item_id: str, **value_overrides) -> None:
	frappe.set_user(PLANNER)
	item = plan_read.get_plan_item(plan_item_id=item_id)
	plan_workbench.save_plan_item(
		plan_item=item_id, values=pln_fx.item_values(**value_overrides),
		expected_record_version=item["record_version"], idempotency_key=key(),
	)
	plan = plan_read.get_annual_plan(plan_reference=item["plan_reference"])
	requested = plan_finance.request_plan_funding_confirmation(
		plan_version=plan["version_reference"], expected_record_version=plan["record_version"], idempotency_key=key(),
	)
	task = frappe.get_doc("Plan Finance Task", requested["task"])
	frappe.set_user(FINANCE_OFFICER)
	plan_finance.confirm_plan_funding(task=task.name, task_token=task.task_token, idempotency_key=key())
	frappe.set_user(PLANNER)


def confirmed_item(*, indicative_amount: float = 50_000_000) -> tuple[dict, str]:
	# This is Planning's own `RequisitionCase.confirmed_item()`, copied
	# verbatim per this module's docstring — including the one thing that
	# copy silently dropped: Planning's own `setUp()` mocks
	# `needs_intake.current_accepted_sources` to `[]`, because
	# `refresh_draft_entries` (called from both `open_departmental_plan` and
	# `submit_departmental_plan`) would otherwise auto-include a real
	# accepted Need's entry alongside the direct one this fixture explicitly
	# funds below. Without the mock, an accepted Need for `OU_ALPHA`/
	# `FY_OPEN` elsewhere on the shared site — not created by this fixture,
	# and invisible to `wipe_planning_rows()`, which only wipes Planning's
	# own DPP/Plan rows — surfaces here as an unfunded, unrelated entry that
	# fails `submit_departmental_plan` with `PLN_ENTRY_INCOMPLETE` (found
	# 2026-09-12, all nine Requisitions test modules sharing this fixture
	# were failing on it). The mock must stay active through submission,
	# not just the open call, or the second `refresh_draft_entries` inside
	# `submit_departmental_plan` reintroduces the exact same entry right
	# before its own coverage check.
	with patch.object(needs_intake, "current_accepted_sources", return_value=[]):
		frappe.set_user(AUTHOR)
		opened = dpp_lifecycle.open_departmental_plan(
			organisation_unit=_ou_alpha(), fiscal_year=pln_fx.FY_OPEN, idempotency_key=key(), fixture_namespace=NS,
		)
		added = dpp_lifecycle.save_direct_requirement(
			dpp_version=opened["current_version"], values=pln_fx.direct_values(indicative_amount=indicative_amount),
			expected_record_version=opened["record_version"], idempotency_key=key(),
		)
		frappe.set_user(HOD)
		submitted = dpp_lifecycle.submit_departmental_plan(
			dpp_version=opened["current_version"], certification_confirmed=True,
			expected_record_version=added["record_version"], idempotency_key=key(),
		)
	dpp_task = frappe.get_doc("Departmental Plan Validation Task", {"task_reference": submitted["task"]})
	frappe.set_user(PLANNER)
	accepted = dpp_validation.accept_departmental_plan(
		task=dpp_task.name, classifications={added["entry_id"]: "Goods"}, task_token=dpp_task.task_token, idempotency_key=key(),
	)
	plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
	formed = plan_workbench.form_plan_items(
		plan_version=accepted["annual_plan_version"], dpp_entries=[plan["unallocated_sources"][0]["dpp_entry"]],
		mode="each", expected_record_version=plan["record_version"], idempotency_key=key(),
	)
	item_id = formed["created_items"][0]
	complete_and_confirm(item_id)
	return accepted, item_id


def activate(plan_reference: str) -> dict:
	frappe.set_user(PLANNER)
	plan = plan_read.get_annual_plan(plan_reference=plan_reference)
	submitted = plan_governance.submit_consolidated_plan(
		plan_version=plan["version_reference"], expected_record_version=plan["record_version"], idempotency_key=key(),
	)
	ao_task = frappe.get_doc("Plan Governance Task", submitted["task"])
	frappe.set_user(ACCOUNTING_OFFICER)
	adopted = plan_governance.adopt_and_submit_plan(task=ao_task.name, task_token=ao_task.task_token, idempotency_key=key())
	statutory_task = frappe.get_doc("Plan Governance Task", adopted["statutory_task"])
	frappe.set_user(STATUTORY)
	result = plan_governance.approve_annual_plan(task=statutory_task.name, task_token=statutory_task.task_token, idempotency_key=key())
	frappe.set_user(PLANNER)
	return result


def active_item(*, indicative_amount: float = 50_000_000) -> tuple[dict, str]:
	accepted, item_id = confirmed_item(indicative_amount=indicative_amount)
	activate(accepted["annual_plan"])
	return accepted, item_id


# A baseline rule that proposes no default (Memory, Storage capacity) needs
# a value supplied before it can be confirmed — every test building a Draft
# through Step 3 hits this, so it lives here once rather than as six
# separately-drifting inline loops.
_VALUE_LESS_BASELINE_DEFAULTS = {"memory": 16, "storage_capacity": 512}


def confirm_all_proposed_requirements(requisition: str, package_version) -> None:
	from kentender_procurement.procurement_requisitions.services import draft_commands as cmd

	package_version.reload()
	for row in package_version.technical_requirements:
		if row.row_status != "Proposed":
			continue
		extra = {}
		if not row.required_value_json:
			extra["value"] = _VALUE_LESS_BASELINE_DEFAULTS[row.characteristic_key]
		cmd.confirm_proposed_requirement(
			requisition=requisition, technical_requirement_id=row.technical_requirement_id,
			expected_record_version=package_version.record_version, idempotency_key=key(), **extra,
		)
		package_version.reload()
