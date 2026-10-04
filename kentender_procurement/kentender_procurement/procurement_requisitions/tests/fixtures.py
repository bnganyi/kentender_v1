# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.11 test world (D13) — extends Procurement Planning's own
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

from kentender_core.utils.raw_delete import delete_rows

from kentender_procurement.procurement_planning.services import (
	dpp_lifecycle,
	dpp_validation,
	needs_intake,
	plan_finance,
	plan_governance,
	plan_read,
	plan_workbench,
	publication_pipeline,
	treasury,
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


#: REQ-CHG-001 v1.11 §2.1/§7.3A — a second contributing department for the
#: combined-item cases: a Departmental Author assigned only there (the
#: REQ-DES-03-CONTRIBUTOR actor) and that department's Head.
CONTRIBUTOR = "reqt.contributor@example.test"
HOD_BETA = "reqt.hodbeta@example.test"
COMBINATION_REASON = (
	"Both departments require the same laptop specification for one programme; combining secures better unit pricing "
	"and one delivery schedule."
)


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
	pln_fx._user(CONTRIBUTOR, "REQ Test Contributor")
	pln_fx._user(HOD_BETA, "REQ Test Head Beta")
	pln_fx._grant(CONTRIBUTOR, "Departmental Author", pln_fx.OU_BETA)
	pln_fx._grant(HOD_BETA, "Departmental Author", pln_fx.OU_BETA)
	pln_fx._grant(HOD_BETA, "Head of User Department", pln_fx.OU_BETA)
	# The combined-item Author holds both departments (REQ-DES-03's Grace).
	pln_fx._grant(pln_fx.AUTHOR, "Departmental Author", pln_fx.OU_BETA)
	if not frappe.db.exists("Delivery Location", {"status": "Active"}):
		frappe.get_doc({"doctype": "Delivery Location", "location_name": "REQ Test Delivery Point", "address": "Test Road, Nairobi", "status": "Active", "fixture_namespace": NS}).insert(ignore_permissions=True)


def restore_site() -> None:
	pln_fx.restore_site()


def wipe_planning_rows() -> None:
	"""Delegates to Planning's own per-test DPP/Plan isolation — required
	before every test that calls `confirmed_item`/`active_item`, or the next
	test reuses the prior one's already-progressed DPP (PLN_DPP_STALE)."""
	pln_fx.wipe_planning_rows()


#: Test worlds live in fiscal years that start in 2100 or later (Planning's
#: 2101-2102/2103-2104, the Playwright worlds' 2100-2101). A real site year
#: never does.
TEST_YEAR_FLOOR = 2100


def is_test_fiscal_year(fiscal_year: str) -> bool:
	head = (fiscal_year or "")[:4]
	return head.isdigit() and int(head) >= TEST_YEAR_FLOOR


def _real_plans() -> set[str]:
	return {
		row.name
		for row in frappe.get_all("Annual Plan", fields=["name", "fiscal_year"])
		if not is_test_fiscal_year(row.fiscal_year)
	}


def test_requisitions() -> list[str]:
	"""Requisitions that belong to a test world: their Annual Plan is in a
	test fiscal year, or no longer exists at all (a test world's plan wiped
	first). A requisition on a live plan in a real year is never included."""
	real = _real_plans()
	return [row.name for row in frappe.get_all("Procurement Requisition", fields=["name", "plan_id"]) if row.plan_id not in real]


def test_reservations() -> list[str]:
	"""Requisitions-owned Funding Reservations against a test-year (or
	missing) budget."""
	real_budgets = {
		row.name
		for row in frappe.get_all("Procurement Budget", fields=["name", "fiscal_year"])
		if not is_test_fiscal_year(row.fiscal_year)
	}
	return [
		row.name
		for row in frappe.get_all("Funding Reservation", filters={"calling_module": "Procurement Requisitions"}, fields=["name", "budget"])
		if row.budget not in real_budgets
	]


def wipe_requisition_rows() -> None:
	"""Removes test-world Requisitions only (TPR-CHG-001 v0.12 plan §5): until
	26 Sep 2026 this deleted every Requisition on the site, canonical data
	included."""
	frappe.set_user("Administrator")
	requisitions = test_requisitions() or [""]
	versions = frappe.get_all("Requisition Version", filters={"requisition": ("in", requisitions)}, pluck="name") or [""]
	packages = frappe.get_all("IT Equipment Requirement Package", filters={"requisition": ("in", requisitions)}, pluck="name") or [""]
	package_versions = frappe.get_all("IT Equipment Requirement Package Version", filters={"package": ("in", packages)}, pluck="name") or [""]
	names = set(requisitions) | set(versions) | set(packages) | set(package_versions)
	for doctype, field, values in (
		("Requisition Event", "requisition", requisitions),
		("Requisition Decision", "requisition_version", versions),
		("Requisition Task", "requisition", requisitions),
		("Authorised Requisition Handoff", "requisition", requisitions),
		("Requisition Correction Outcome", "requisition", requisitions),
	):
		names |= set(frappe.get_all(doctype, filters={field: ("in", values)}, pluck="name"))
		frappe.db.delete(doctype, {field: ("in", values)})
	frappe.db.delete("Requisition Command Journal", {"document_name": ("in", list(names - {""}) or [""])})
	delete_rows("Requisition Version", {"name": ("in", versions)})
	delete_rows("IT Equipment Requirement Package Version", {"name": ("in", package_versions)})
	delete_rows("IT Equipment Requirement Package", {"name": ("in", packages)})
	delete_rows("Procurement Requisition", {"name": ("in", requisitions)})
	# authorise_requisition() reserves funding in Budget (D1) under
	# `calling_module="Procurement Requisitions"`; those rows live outside
	# this app and are never touched by `wipe_planning_rows()`, so a prior
	# test's still-Active reservation on the same (deterministically
	# re-issued) plan_source_allocation blocks the next test's reserve call
	# with BUDGET_RESERVATION_CONFLICT unless wiped here too — test-year
	# budgets only.
	frappe.db.delete("Funding Reservation", {"name": ("in", test_reservations() or [""])})
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
	"""§5.5.2 (plan D8): approve only commits; Treasury evidence gates the
	worker; the worker runs inline here (no RQ worker on this bench)."""
	frappe.set_user(HOPF)  # v1.18 §6.2: the Head of Procurement Function signs and submits
	plan = plan_read.get_annual_plan(plan_reference=plan_reference)
	submitted = plan_governance.submit_consolidated_plan(
		plan_version=plan["version_reference"], expected_record_version=plan["record_version"], idempotency_key=key(),
	)
	ao_task = frappe.get_doc("Plan Governance Task", submitted["task"])
	frappe.set_user(ACCOUNTING_OFFICER)
	adopted = plan_governance.adopt_and_submit_plan(task=ao_task.name, task_token=ao_task.task_token, idempotency_key=key())
	statutory_task = frappe.get_doc("Plan Governance Task", adopted["statutory_task"])
	frappe.set_user(STATUTORY)
	approved = plan_governance.approve_annual_plan(task=statutory_task.name, task_token=statutory_task.task_token, idempotency_key=key())
	version_name = frappe.db.get_value("Plan Publication", approved["publication"], "plan_version")
	frappe.set_user(ACCOUNTING_OFFICER)
	treasury.record_treasury_submission(
		plan_version=version_name, submitted_at="2101-11-01 09:00:00", channel="Email", destination="treasury@example.test",
		dispatch_reference="MOH/APP/2101/001", exact_document_confirmed=True, idempotency_key=key(),
	)
	frappe.set_user("Administrator")
	published = publication_pipeline.publish_annual_plan(plan_version=version_name, idempotency_key=key())
	frappe.set_user(PLANNER)
	return published


def active_item(*, indicative_amount: float = 50_000_000) -> tuple[dict, str]:
	accepted, item_id = confirmed_item(indicative_amount=indicative_amount)
	activate(accepted["annual_plan"])
	return accepted, item_id


def ou_beta() -> str:
	return pln_fx.OU_BETA


def ou_alpha() -> str:
	return _ou_alpha()


def delivery_location() -> str:
	return frappe.db.get_value("Delivery Location", {"status": "Active"}, "name")


def _accepted_direct_entry(*, unit: str, author: str, hod: str, indicative_amount: float, quantity: int, title: str) -> tuple[dict, str, str]:
	with patch.object(needs_intake, "current_accepted_sources", return_value=[]):
		frappe.set_user(author)
		opened = dpp_lifecycle.open_departmental_plan(organisation_unit=unit, fiscal_year=pln_fx.FY_OPEN, idempotency_key=key(), fixture_namespace=NS)
		added = dpp_lifecycle.save_direct_requirement(
			dpp_version=opened["current_version"], values=pln_fx.direct_values(title=title, indicative_amount=indicative_amount, quantity=quantity),
			expected_record_version=opened["record_version"], idempotency_key=key(),
		)
		frappe.set_user(hod)
		submitted = dpp_lifecycle.submit_departmental_plan(
			dpp_version=opened["current_version"], certification_confirmed=True, expected_record_version=added["record_version"], idempotency_key=key(),
		)
	task = frappe.get_doc("Departmental Plan Validation Task", {"task_reference": submitted["task"]})
	frappe.set_user(PLANNER)
	accepted = dpp_validation.accept_departmental_plan(task=task.name, classifications={added["entry_id"]: "Goods"}, task_token=task.task_token, idempotency_key=key())
	entry = frappe.db.get_value("Departmental Plan Entry", {"dpp_version": opened["current_version"], "entry_id": added["entry_id"]}, "name")
	return accepted, entry, opened["current_version"]


def active_combined_item(*, alpha_amount: float = 30_000_000, beta_amount: float = 20_000_000, alpha_quantity: int = 150, beta_quantity: int = 100) -> tuple[dict, str]:
	"""§13.1 in miniature: one Plan Item formed by Planning from two
	departments' approved requirements (Alpha leads on value)."""
	accepted, alpha_entry, _ = _accepted_direct_entry(unit=_ou_alpha(), author=AUTHOR, hod=HOD, indicative_amount=alpha_amount, quantity=alpha_quantity, title="Business laptops")
	accepted, beta_entry, _ = _accepted_direct_entry(unit=pln_fx.OU_BETA, author=HOD_BETA, hod=HOD_BETA, indicative_amount=beta_amount, quantity=beta_quantity, title="Business laptops")
	frappe.set_user(PLANNER)
	plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
	formed = plan_workbench.form_plan_items(
		plan_version=accepted["annual_plan_version"], dpp_entries=[alpha_entry, beta_entry], mode="combined", combination_reason=COMBINATION_REASON,
		expected_record_version=plan["record_version"], idempotency_key=key(),
	)
	item_id = formed["created_items"][0]
	complete_and_confirm(item_id, aggregation_reason="Both laptop batches ship in a single combined tender lot.", aggregation_indicator="Aggregated into this package")
	activate(accepted["annual_plan"])
	return accepted, item_id


# --------------------------------------------------------------------------
# Driving a Draft through the real commands
# --------------------------------------------------------------------------


def editor(requisition: str, user: str = AUTHOR) -> dict:
	from kentender_procurement.procurement_requisitions.services import read

	frappe.set_user(user)
	return read.get_requisition_record(requisition=requisition)


def prepare(item_id: str, user: str = AUTHOR) -> dict:
	from kentender_procurement.procurement_requisitions.services import draft_commands as cmd

	frappe.set_user(user)
	return cmd.prepare_it_equipment_requisition(plan_item_id=item_id, idempotency_key=key())


def fill_request_information(requisition: str, user: str = AUTHOR, *, latest: str = "2102-04-30") -> None:
	from kentender_procurement.procurement_requisitions.services import draft_commands as cmd

	view = editor(requisition, user)
	cmd.save_requisition_summary(
		requisition=requisition, values={"delivery_location": delivery_location(), "latest_delivery_date": latest},
		expected_record_version=view["header"]["version_record_version"], idempotency_key=key(),
	)


def add_laptops(requisition: str, user: str = AUTHOR, *, item_name: str = "Business laptops") -> dict:
	from kentender_procurement.procurement_requisitions.services import draft_commands as cmd

	view = editor(requisition, user)
	rows = [
		{"drawdown_line_id": r["drawdown_line_id"], "quantity": r["quantity"], "intended_use": f"Field deployment for {r['department']} staff"}
		for r in view["equipment"]["add_rows"] if r["quantity"] > 0
	]
	return cmd.add_same_specification_items(
		requisition=requisition, shared={"equipment_category": "Laptop", "item_name": item_name},
		rows=rows, expected_record_version=view["package_record_version"], idempotency_key=key(),
	)


def visible_proposal(view: dict) -> tuple[list[dict], list[dict], dict]:
	"""Exactly what the Requirements workbench shows: every row selected."""
	technical = [
		{"technical_requirement_id": r["technical_requirement_id"], "characteristic_key": r["characteristic_key"], "value": _raw(r["value"]), "selected": True}
		for g in view["requirements"]["technical_groups"] for r in g["rows"]
	]
	acceptance = [
		{"acceptance_requirement_id": a["acceptance_requirement_id"], "check_type": a["check_type"], "pass_condition": a["pass_condition"], "evidence_type": a["evidence_type"], "applies_to_scope": a["applies_to_scope"], "applies_to_id": a["applies_to_id"], "selected": True}
		for a in view["requirements"]["acceptance"]
	]
	return technical, acceptance, dict(view["requirements"]["support"])


def _raw(value: dict):
	if "ports" in value:
		return value["ports"]
	if "values" in value:
		return value["values"]
	return value.get("value")


def apply_standard_package(requisition: str, user: str = AUTHOR) -> dict:
	from kentender_procurement.procurement_requisitions.services import draft_commands as cmd

	view = editor(requisition, user)
	technical, acceptance, support = visible_proposal(view)
	req = view["requirements"]
	return cmd.apply_selected_requirement_package(
		requisition=requisition, profile_key=req["profile_key"], profile_version=req["profile_version"], proposal_digest=req["proposal_digest"],
		technical=technical, acceptance=acceptance, support=support, expected_record_version=view["package_record_version"], idempotency_key=key(),
	)


def complete_draft(item_id: str, user: str = AUTHOR) -> str:
	"""Prepare and complete all three visible tasks; returns the root name."""
	prepared = prepare(item_id, user)
	requisition = prepared["requisition"]
	fill_request_information(requisition, user)
	add_laptops(requisition, user)
	apply_standard_package(requisition, user)
	return requisition


def root_version(requisition: str) -> int:
	return int(frappe.db.get_value("Procurement Requisition", requisition, "record_version"))


def open_task(requisition: str, role: str) -> str:
	return frappe.db.get_value("Requisition Task", {"requisition": requisition, "business_role": role, "status": "Open"}, "name")


def submit_as_hod(requisition: str, hod: str = HOD) -> dict:
	from kentender_procurement.procurement_requisitions.services import lifecycle

	frappe.set_user(hod)
	task = open_task(requisition, "Head of User Department")
	return lifecycle.submit_requisition_to_procurement(requisition=requisition, task=task, expected_record_version=root_version(requisition), idempotency_key=key())


def send(requisition: str, user: str = AUTHOR) -> dict:
	from kentender_procurement.procurement_requisitions.services import lifecycle

	frappe.set_user(user)
	return lifecycle.send_for_department_approval(requisition=requisition, expected_record_version=root_version(requisition), idempotency_key=key())


def submitted(item_id: str) -> str:
	requisition = complete_draft(item_id)
	send(requisition)
	submit_as_hod(requisition)
	return requisition


def authorise(requisition: str, user: str = HOPF) -> dict:
	from kentender_procurement.procurement_requisitions.services import authorise as authorise_service

	frappe.set_user(user)
	return authorise_service.authorise_requisition(
		requisition=requisition, task=open_task(requisition, "Head of Procurement Function"),
		expected_record_version=root_version(requisition), idempotency_key=key(),
	)


def confirm_funding(plan_reference: str) -> None:
	frappe.set_user(PLANNER)
	plan = plan_read.get_annual_plan(plan_reference=plan_reference)
	requested = plan_finance.request_plan_funding_confirmation(plan_version=plan["version_reference"], expected_record_version=plan["record_version"], idempotency_key=key())
	task = frappe.get_doc("Plan Finance Task", requested["task"])
	frappe.set_user(FINANCE_OFFICER)
	plan_finance.confirm_plan_funding(task=task.name, task_token=task.task_token, idempotency_key=key())
	frappe.set_user(PLANNER)


def correcting_active_version(plan_reference: str) -> str:
	"""Planning's own test helper: an ordinary successor carried to Active,
	standing in for the correcting Active Plan Version (same stable item)."""
	from kentender_procurement.procurement_planning.services import plan_publication

	frappe.set_user(PLANNER)
	plan_publication.begin_plan_update(plan_reference=plan_reference, idempotency_key=key())
	confirm_funding(plan_reference)
	activate(plan_reference)
	return frappe.db.get_value("Annual Plan", {"plan_reference": plan_reference}, "active_version")


def stop_for_planning_correction(item_id: str, reason: str = "The approved source allocation refers to the wrong Budget Line.") -> tuple[str, str]:
	from kentender_procurement.procurement_requisitions.services import lifecycle

	requisition = submitted(item_id)
	frappe.set_user(HOPF)
	result = lifecycle.request_upstream_plan_correction(requisition=requisition, reason=reason, expected_record_version=root_version(requisition), idempotency_key=key())
	return requisition, result["correction_request"]
