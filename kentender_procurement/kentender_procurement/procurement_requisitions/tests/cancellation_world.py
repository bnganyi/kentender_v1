# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The worlds of the whole-Tender cancellation recovery integration tests (REQ-CHG-001 v1.20 §16.6, fixtures CR-F01 and CR-F02) —
built through the real Planning, Requisitions, Tenders and Budget commands, never beside them.

CR-F01: one source of 100 units / KES 10m; an authorised Requisition draws 60 units / KES 6m; the Tender is published.
CR-F02: two sources (40 units / KES 4m and 60 units / KES 6m), each drawn in full into the one Tender, with separate reservations on the
same KES 10m Budget Line.

A world is built once per test class (the shared-world rule); a test that changes it does so inside a savepoint it rolls back."""

from __future__ import annotations

import frappe
from frappe.utils import cstr

from kentender_core.seeds.calendar import world as W
from kentender_procurement.procurement_planning.services import plan_requisition
from kentender_procurement.procurement_requisitions.tests import fixtures as req_fx
from kentender_procurement.tenders.services import cancellation, draft_commands as cmd, lifecycle, publication
from kentender_procurement.tenders.tests import fixtures as tnd_fx
from kentender_procurement.tenders.tests import sample

CHANNELS = ("STATE_PORTAL", "MINISTRY_WEBSITE", "NOTICE_BOARD", "NATIONAL_NEWSPAPERS")
CLOCK_PUBLISH = "2027-05-15 07:55:00"
CLOCK_CANCEL = "2027-06-04 14:00:00"


def _authorise(requisition: str, item_id: str) -> dict:
	req_fx.apply_standard_package(requisition)
	req_fx.send(requisition)
	req_fx.submit_as_hod(requisition)
	authorised = req_fx.authorise(requisition)
	frappe.set_user("Administrator")
	return {**authorised, "item_id": item_id, "requisition": requisition}


def single_source_requisition(*, quantity: int = 100, amount: int = 10_000_000, draw_quantity: int = 60, draw_value: str = "6000000.00", item: tuple[dict, str] | None = None) -> dict:
	"""CR-F01: an authorised Requisition that draws part of one source's allowance."""
	_, item_id = item or req_fx.active_item(indicative_amount=amount, quantity=quantity)
	requisition = req_fx.prepare(item_id)["requisition"]
	req_fx.fill_request_information(requisition)
	line = req_fx.editor(requisition)["equipment"]["add_rows"][0]["drawdown_line_id"]
	req_fx.add_laptops(requisition, quantities={line: draw_quantity})
	req_fx.enter_estimates(requisition, values={line: draw_value})
	return _authorise(requisition, item_id)


def combined_requisition(*, alpha: tuple[int, int] = (60, 6_000_000), beta: tuple[int, int] = (40, 4_000_000)) -> dict:
	"""CR-F02: two departments' sources on one Plan Item, each drawn in full; both sources sit on the same Budget Line. The larger value leads, so Alpha (the fixture's usual lead) leads."""
	_, item_id = req_fx.active_combined_item(alpha_amount=alpha[1], beta_amount=beta[1], alpha_quantity=alpha[0], beta_quantity=beta[0])
	requisition = req_fx.prepare(item_id)["requisition"]
	req_fx.fill_request_information(requisition)
	req_fx.add_laptops(requisition)  # the lead department's author can add items for every source
	req_fx.enter_estimates(requisition)
	req_fx.enter_estimates(requisition, req_fx.CONTRIBUTOR)
	return _authorise(requisition, item_id)


def publish_tender(builder, authorised: dict) -> str:
	"""Start the Tender from the authorised handoff and carry it to Published — open, as `OpenPeriodCase._published` does. `builder` is an
	`OpenPeriodCase` instance (it owns the channel-confirmation helper)."""
	frappe.flags.kt_tenders_clock = W(CLOCK_PUBLISH)
	started = cmd.start_tender(handoff=authorised["handoff"], idempotency_key=tnd_fx.key(), user=tnd_fx.OFFICER)
	root = frappe.get_doc("Tender", started["tender"])
	cmd.save_tender_draft(
		tender=root.name, values=sample.officer_values(inspection_location=tnd_fx.LOCATION, contact_office=tnd_fx.CONTACT_OFFICE),
		expected_record_version=root.record_version, idempotency_key=tnd_fx.key(), user=tnd_fx.OFFICER,
	)
	root.reload()
	submitted = lifecycle.submit_tender_for_approval(tender=root.name, expected_record_version=root.record_version, idempotency_key=tnd_fx.key(), user=tnd_fx.OFFICER)
	root.reload()
	approved = lifecycle.approve_tender_package(tender=root.name, expected_record_version=root.record_version, idempotency_key=tnd_fx.key(), user=tnd_fx.HOPF, task=submitted["task"])
	root.reload()
	publication.authorise_tender_publication(tender=root.name, expected_record_version=root.record_version, idempotency_key=tnd_fx.key(), user=tnd_fx.AO, task=approved["task"])
	builder.name = root.name
	for channel in CHANNELS:
		builder._confirm("publication", channel)
	assert frappe.db.get_value("Tender", root.name, "overall_status") == "Published — open"
	return root.name


def cancel_tender(tender: str) -> dict:
	frappe.flags.kt_tenders_clock = W(CLOCK_CANCEL)
	root = frappe.get_doc("Tender", tender)
	return cancellation.cancel_tender(
		tender=tender, ground="INADEQUATE_BUDGET", reason="The confirmed budget available for this procurement is insufficient to proceed.",
		expected_record_version=root.record_version, idempotency_key=tnd_fx.key(), user=tnd_fx.AO,
	)


# --------------------------------------------------------------------------
# What a test compares before and after
# --------------------------------------------------------------------------


def planning_remaining(item_id: str) -> tuple[str, str]:
	"""The item's remaining quantity and value as Planning reports them to Requisitions."""
	frappe.set_user(req_fx.PLANNER)
	read = plan_requisition.get_requisition_eligible_plan_item(plan_item_id=item_id)
	frappe.set_user("Administrator")
	return str(read["remaining_quantity"]), str(read["remaining_value"])


def budget_position(budget_line: str) -> dict[str, str]:
	"""Approved, reserved, committed and available for one Budget Line, exactly."""
	from kentender_budget.services.budget_cancellation_release import _current_line_version
	from kentender_budget.services.budget_contracts import _line_position_exact

	exact = _line_position_exact(budget_line, _current_line_version(budget_line))
	return {key: f"{value:f}" for key, value in exact.items()}


def reservations_of(requisition: str) -> list[str]:
	version = frappe.db.get_value("Procurement Requisition", requisition, "authorised_version")
	return [cstr(l.reservation_id) for l in frappe.get_doc("Requisition Version", version).drawdown_lines]


def budget_line_of(reservation: str) -> str:
	return cstr(frappe.db.get_value("Funding Reservation", reservation, "budget_line"))
