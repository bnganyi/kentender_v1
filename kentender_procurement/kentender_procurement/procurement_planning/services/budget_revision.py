# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.27 §4.7, §7.2, §7.3, §7.7 — RequestBudgetRevision.

When a Draft plan's planned total on a Budget Line exceeds its approved
amount, the Planner may hand the fix to the Budget Officer inside the
product instead of phoning them (KT-STD-001 v1.8 §3B.4). This creates one
Plan Budget Revision Request and, in the same transaction, Budget's own
request (BUD-CHG-001 v1.11 §8.5); the Planner's next step becomes Waiting on
the Budget Officer. It changes no Budget amount, reservation or Plan state.

Budget reports each outcome (Revised, Declined, Withdrawn) through its
outbox to `receive_budget_revision_outcome`; Planning updates the request
idempotently and recomputes readiness — no Planning decision is inferred.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, flt, now_datetime

from kentender_procurement.procurement_planning.errors import fail
from kentender_procurement.procurement_planning.services import budget_gateway, envelope, money, plan_finance
from kentender_procurement.procurement_planning.services import planning_authorization as authz
from kentender_procurement.procurement_planning.services.planning_roles import ROLE_PROCUREMENT_PLANNER
from kentender_procurement.procurement_planning.write_family import planning_command

DOCTYPE = "Plan Budget Revision Request"
OPEN = "Open"


def _site_instant(value):
	"""An ISO-8601 UTC instant from Budget's outcome (BUD v1.11 §6: instants
	cross the contract in UTC) as the site-timezone datetime Planning stores
	(owner decision 26 Sep 2026: stored in site time, UTC only on the wire)."""
	from kentender_core.utils.instants import from_utc_iso

	return from_utc_iso(value) or now_datetime()


def _new_reference() -> str:
	return f"PBR-{frappe.generate_hash(length=10).upper()}"


def _line_statement(plan, version, budget_line: str) -> dict[str, Any] | None:
	statement = plan_finance.affordability_statement(plan, version)
	return next((line for line in statement.get("lines") or [] if line["budget_line"] == budget_line), None)


def open_request(plan_version: str, budget_line: str) -> str:
	return cstr(frappe.db.get_value(DOCTYPE, {"plan_version": plan_version, "budget_line": budget_line, "status": OPEN}, "name"))


@planning_command
def request_budget_revision(*, plan_version: str, budget_line: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""§7.2 `RequestBudgetRevision` — the line, approved, planned and over
	amounts are server-derived, never supplied by the client."""
	actor = authz.actor(user)
	payload = {"plan_version": plan_version, "budget_line": budget_line}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	version = envelope.locked("Annual Plan Version", plan_version)
	plan = frappe.get_doc("Annual Plan", version.annual_plan)
	assignment = authz.require_site_role(ROLE_PROCUREMENT_PLANNER, actor)
	envelope.check_record_version(version, expected_record_version)
	if version.version_status != "Draft":
		fail("PLN_BASELINE_LOCKED")

	line = _line_statement(plan, version, budget_line)
	if not line or not money.exceeds(line.get("planned"), line.get("approved")):
		fail("PLN_BUDGET_REVISION_NOT_REQUIRED")
	if open_request(version.name, budget_line):
		fail("PLN_BUDGET_REVISION_ALREADY_REQUESTED")
	# Owner decision 26 Sep 2026: after Budget declines, a fresh request needs
	# a new basis — the line's approved or planned amount has changed since.
	last = frappe.db.get_value(
		DOCTYPE, {"plan_version": version.name, "budget_line": budget_line, "status": ("in", ("Revised", "Declined", "Withdrawn"))},
		["status", "approved_amount", "planned_amount"], as_dict=True, order_by="outcome_at desc, requested_at desc",
	)
	if (
		last and last.status == "Declined"
		and money.same_amount(last.approved_amount, line.get("approved"))
		and money.same_amount(last.planned_amount, line.get("planned"))
	):
		fail("PLN_BUDGET_REVISION_ALREADY_DECLINED")

	approved, planned = flt(line["approved"]), flt(line["planned"])
	over = float(money.as_decimal(line["planned"]) - money.as_decimal(line["approved"]))  # exact, then stored
	request = frappe.get_doc({
		"doctype": DOCTYPE,
		"request_reference": _new_reference(),
		"plan_version": version.name,
		"budget_line": budget_line,
		"budget_line_reference": cstr(line.get("reference")),
		"budget_line_title": cstr(line.get("title")),
		"approved_amount": approved,
		"planned_amount": planned,
		"over_amount": over,
		"status": OPEN,
		"requested_by": actor,
		"authority_snapshot": authz.authority_snapshot(assignment),
		"requested_at": now_datetime(),
		"idempotency_key": idempotency_key,
		"fixture_namespace": cstr(version.fixture_namespace),
	}).insert(ignore_permissions=True)

	# BUD v1.11 §8.5 item 1 — Budget records its side in this transaction; a
	# refusal there refuses the whole command (nothing commits).
	received = budget_gateway.receive_budget_revision_request({
		"planning_request_id": request.name,
		"idempotency_key": idempotency_key,
		"fiscal_year": plan.fiscal_year,
		"budget_line": budget_line,
		"planned_amount": planned,
		"over_amount": over,
		"plan_version_reference": version.name,
		"plan_label": f"{plan.plan_reference}, Version {version.version_number}",
		"requested_by": actor,
		"fixture_namespace": cstr(version.fixture_namespace),
	})
	if not received.get("ok"):
		code = cstr(received.get("code"))
		if code == "BUDGET_REVISION_NOT_REQUIRED":
			fail("PLN_BUDGET_REVISION_NOT_REQUIRED")
		if code == "BUDGET_DECISION_BASIS_STALE":
			fail("PLN_FINANCE_STALE")
		fail("PLN_REFERENCE_UNAVAILABLE", next(iter((received.get("errors") or {}).values()), "") or None)
	request.db_set("bud_request_reference", cstr(received.get("budget_revision_request_id")), update_modified=False)
	result = {
		"ok": True,
		"action": "requested",
		"request": request.name,
		"bud_request_reference": cstr(received.get("budget_revision_request_id")),
		"plan_reference": plan.plan_reference,
		"idempotent": False,
	}
	envelope.record_command(
		idempotency_key=idempotency_key, command="RequestBudgetRevision", payload=payload, result=result,
		document_type=DOCTYPE, document_name=request.name, actor=actor, fixture_namespace=cstr(version.fixture_namespace),
	)
	return result


def withdraw_budget_revision_request(*, request: str, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""§7.2 — the Planner withdraws an Open request once the line fits
	because they reduced the plan; Budget records Withdrawn and reports it
	back through its outbox."""
	actor = authz.actor(user)
	if not request or not frappe.db.exists(DOCTYPE, request):
		authz.not_found()
	doc = frappe.get_doc(DOCTYPE, request)
	authz.require_site_role(ROLE_PROCUREMENT_PLANNER, actor)
	if doc.status != OPEN:
		return {"ok": True, "action": "unchanged", "status": doc.status}
	version = frappe.get_doc("Annual Plan Version", doc.plan_version)
	plan = frappe.get_doc("Annual Plan", version.annual_plan)
	# A cancelled plan update needs nothing from Budget, whatever its lines say.
	if version.version_status != "Cancelled":
		line = _line_statement(plan, version, doc.budget_line)
		if line and money.exceeds(line.get("planned"), line.get("approved")):
			fail("PLN_BUDGET_REVISION_ALREADY_REQUESTED", "The line is still over its approved amount; the request stays open.")
	withdrawn = budget_gateway.withdraw_budget_revision_request({
		"planning_request_id": doc.name, "idempotency_key": idempotency_key, "requested_by": actor,
	})
	if not withdrawn.get("ok") and cstr(withdrawn.get("code")) != "BUDGET_REVISION_REQUEST_CLOSED":
		fail("PLN_REFERENCE_UNAVAILABLE")
	doc.reload()
	return {"ok": True, "action": "withdrawn", "status": doc.status}


def withdraw_fitting_requests(version, *, actor: str) -> list[str]:
	"""A Planner who reduced the plan and now sends it to Finance no longer
	needs an Open request on a line that fits: withdraw it as part of that
	decision, so the Budget Officer is not left holding moot work."""
	withdrawn = []
	for name in frappe.get_all(DOCTYPE, filters={"plan_version": version.name, "status": OPEN}, pluck="name"):
		result = withdraw_budget_revision_request(request=name, idempotency_key=f"auto-withdraw-{name}", user=actor)
		if result.get("action") == "withdrawn":
			withdrawn.append(name)
	return withdrawn


def receive_budget_revision_outcome(event: dict[str, Any]) -> None:
	"""`kt_budget_revision_outcome_consumers` — BudgetRevisionRequestOutcome.v1
	(§7.3). Idempotent and ordered: an event whose sequence is not newer than
	the last applied one changes nothing."""
	name = cstr(event.get("planning_request_id"))
	if not name or not frappe.db.exists(DOCTYPE, name):
		return
	frappe.db.sql(f"select name from `tab{DOCTYPE}` where name=%s for update", (name,))
	doc = frappe.get_doc(DOCTYPE, name)
	sequence = int(event.get("sequence") or 0)
	if sequence <= int(doc.outcome_sequence or 0):
		return
	outcome = cstr(event.get("outcome"))
	if outcome not in ("Revised", "Declined", "Withdrawn"):
		return
	doc.status = outcome
	doc.outcome_sequence = sequence
	doc.outcome_at = _site_instant(event.get("decided_at"))
	doc.outcome_by = cstr(event.get("decided_by_name") or event.get("decided_by"))
	doc.outcome_reason = cstr(event.get("reason"))
	doc.resulting_line_version = cstr(event.get("resulting_line_version"))
	if event.get("resulting_approved_amount") is not None:
		doc.resulting_approved_amount = flt(event.get("resulting_approved_amount"))
	doc.save(ignore_permissions=True)
