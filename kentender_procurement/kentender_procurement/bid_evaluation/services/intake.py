# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ReceiveOpeningPackage and ReceiveEmptyOpeningOutcome (EVL-CHG-001 v0.4
§5.1, §7.1, §7.2, §8 EVL_SOURCE_INCOMPLETE; tracker EVL4-501…503, EVL4-510;
boards D08-SOURCE, S-CHECKS, S-SOURCE-OPEN, D02-NO-BIDS, D02-INTAKE-FIRST).

Evaluation accepts one verified nonempty opening completion: the unchanged
packages, the issued definition, the register, the opening record and the
opening exceptions, with their exact source versions. Receipt is recorded
automatically: there is no receipt approval or "Start evaluation" click, and
this recorded intake is Bid Opening's take-up. A missing preparation is
created first (intake is a recovery path, not permission to skip
appointment). Checks run as soon as the source is valid, and the case enters
Reviewing whether or not a committee exists yet; bids stay hidden until
appointment and personal eligibility.

A failed intake automatically records one support issue for the named
support holder; every retry reuses the same intake identity and the same
issue, and waiting clears only when the intake succeeds. It is never shown
as "no bids". A verified final no-bids outcome closes an existing
preparation as No evaluation required (history kept, tasks cleared) and
creates no case where none exists. An incomplete opening never triggers
either."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cint, cstr

from kentender_procurement.bid_evaluation.services import checks, clock, people, prc, preparation, records, review_tasks, sources
from kentender_procurement.bid_evaluation.services.errors import EvaluationError

INTAKE = "Evaluation Source Intake"
BID = "Evaluation Bid"
SUPPORT_SUBJECT = "Resolve evaluation issue for {ref}"
SAFE_DETAIL = "The completed opening package could not be loaded."


def _issue(doc, intake_row, detail: str) -> dict[str, Any]:
	from kentender_core.services import support_issues

	return support_issues.open_issue(module="Bid Evaluation", operation="ReceiveOpeningPackage", operation_correlation=intake_row.operation_key,
		subject=SUPPORT_SUBJECT.format(ref=doc.tender_reference), reference_doctype=records.CASE, reference_name=doc.name, safe_detail=detail,
		holder_role=people.EVALUATION_SUPPORT, fixture_namespace=records.namespace())


def receive_opening_package(*, tender: str) -> dict[str, Any]:
	"""The system's intake of a completed nonempty opening. Safe to repeat."""
	from kentender_procurement.bid_opening.services import evaluation_seam as opening

	outcome = opening.final_outcome(tender) or {}
	if outcome.get("outcome") != "Bids opened":
		return {"ok": False, "received": False, "reason": "no_completed_opening", "opening": outcome.get("outcome")}
	completion = opening.completion(tender)
	if not completion:
		return {"ok": False, "received": False, "reason": "no_completion"}
	if not records.case_for(tender):
		prepared = preparation.ensure_preparation(tender=tender, source="Opening intake")
		if not prepared.get("evaluation"):
			return {"ok": False, "received": False, "reason": prepared.get("reason"), "preparation": prepared}
	key = f"intake:{tender}:{completion['handoff_id']}"

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		if doc.state in records.TERMINAL:
			return records.summary(doc, received=False, reason="closed")
		row = _intake_row(doc, key, completion)
		if row.status == "Received":
			return records.summary(doc, received=True, replayed=True, intake=row.name)
		row.attempts = cint(row.attempts) + 1
		failure = None
		loaded: list[tuple[dict[str, Any], dict[str, Any]]] = []
		if not completion.get("verified"):
			failure = "The opening completion does not match its digest."
		else:
			for package in completion["payload"].get("packages") or []:
				source = sources.release(tender=tender, package=package, completion_reference=completion["handoff_id"], correlation_id=f"{key}:{package['entry']}")
				if source.get("outcome") != sources.VERIFIED:
					failure = SAFE_DETAIL
					break
				loaded.append((package, source))
		if failure or not loaded:
			row.status, row.last_error_code = "Failed", "EVL_SOURCE_INCOMPLETE"
			issue = _issue(doc, row, failure or SAFE_DETAIL)
			row.support_issue = issue["issue_id"]
			records.save(row)
			records.bump(doc)
			return {"ok": False, "code": "EVL_SOURCE_INCOMPLETE", "received": False, "intake": row.name, "issue": issue["issue_id"], "evaluation": doc.name,
				"message": "Some opened bid information could not be loaded."}
		payload = completion["payload"]
		first_definition = loaded[0][1]["definition"]
		for package, source in loaded:
			body_ = source["body"]
			price = body_.get("price") or {}
			records.insert(frappe.get_doc({
				"doctype": BID, "evaluation_bid_id": f"{doc.name}-BID-{cint(package.get('number')):02d}", "evaluation_case": doc.name, "intake": row.name,
				"entry_reference": package["entry"], "entry_number": cint(package.get("number")), "envelope_id": package["envelope_id"],
				"receipt_reference": package.get("receipt_reference"), "submission_version": package["submission_version"], "package_digest": package["package_digest"],
				"bid_reference": cstr((body_.get("bid") or {}).get("bid_reference")), "tenderer_name": cstr((body_.get("bid") or {}).get("tenderer_name")),
				"organisation_id": cstr((body_.get("organisation_snapshot") or {}).get("facts", {}).get("organisation", {}).get("organisation_id")),
				"submitted_total": cstr(price.get("total")), "currency": cstr(price.get("currency")),
			}))
		row.update({"status": "Received", "received_at": clock.now(), "last_error_code": "", "package_count": len(loaded),
			"definition_id": first_definition["bid_definition_id"], "definition_version": cint(first_definition["definition_version"]),
			"definition_digest": first_definition["definition_digest"], "register_reference": cstr(payload.get("register", {}).get("register_id")),
			"register_digest": cstr(payload.get("register", {}).get("digest")), "opening_record_reference": cstr((payload.get("opening_record") or {}).get("minutes_version")),
			"opening_record_digest": cstr((payload.get("opening_record") or {}).get("digest"))})
		records.save(row)
		from kentender_core.services import support_issues

		support_issues.resolve_on_success(module="Bid Evaluation", operation_correlation=key, note="The opening package was received.")
		opening.acknowledge(completion["handoff_id"])
		records.bump(doc, source_intake=row.name, opening_handoff=completion["handoff_id"], opening_completed_at=outcome.get("completed_at"),
			definition_id=first_definition["bid_definition_id"], definition_version=cint(first_definition["definition_version"]),
			definition_digest=first_definition["definition_digest"])
		event = prc.owner_event(doc, "OpeningPackageReceived", f"intake:{row.name}", {"handoff": completion["handoff_id"], "digest": completion["digest"],
			"packages": [p["package_digest"] for p, _s in loaded]}, idempotency_key=key)
		ran = checks.run(doc, reason="Initial", idempotency_key=key)
		records.bump(doc, state="Reviewing", last_committed_event=event)
		review_tasks.intake_ready(doc)
		return records.summary(doc, received=True, intake=row.name, run=ran["run"], counts=ran["counts"])

	return records.command("ReceiveOpeningPackage", tender=tender, idempotency_key=f"{key}:attempt-{_attempt_number(key)}", actor="system",
		payload={"handoff": completion["handoff_id"]}, body=body)


def _attempt_number(key: str) -> int:
	return cint(frappe.db.get_value(INTAKE, {"operation_key": key}, "attempts")) + 1


def _intake_row(doc, key: str, completion: dict[str, Any]):
	name = frappe.db.get_value(INTAKE, {"operation_key": key}, "name")
	if name:
		return frappe.get_doc(INTAKE, name)
	return records.insert(frappe.get_doc({
		"doctype": INTAKE, "intake_id": f"{doc.name}-IN-01", "evaluation_case": doc.name, "operation_key": key, "source_kind": "Opening package",
		"opening_reference": cstr((completion.get("payload") or {}).get("opening")), "opening_handoff": completion["handoff_id"], "handoff_digest": completion["digest"],
		"status": "Pending", "attempts": 0, "first_attempt_at": clock.now(),
	}))


def retry(*, tender: str, user: str) -> dict[str, Any]:
	"""Try again (§8 EVL_SOURCE_INCOMPLETE): the secretary's retry of the same
	intake identity. Only the appointed secretary, or the Accounting Officer
	and Head of Procurement while there is no secretary, may ask."""
	from kentender_procurement.bid_evaluation.services import roster

	name = records.case_for(tender)
	if not name:
		raise frappe.DoesNotExistError("Not found")
	secretary = roster.secretary(name)
	allowed = user == secretary if secretary else (people.holds(user, people.ACCOUNTING_OFFICER) or people.holds(user, people.HEAD_OF_PROCUREMENT))
	if not allowed:
		raise frappe.DoesNotExistError("Not found")
	return receive_opening_package(tender=tender)


def receive_empty_outcome(*, tender: str) -> dict[str, Any]:
	"""A verified final no-bids opening closes an existing preparation."""
	from kentender_procurement.bid_opening.services import evaluation_seam as opening

	outcome = opening.final_outcome(tender) or {}
	if outcome.get("outcome") != "No bids":
		return {"ok": False, "closed": False, "reason": "not_a_final_empty_opening", "opening": outcome.get("outcome")}
	if not records.case_for(tender):
		return {"ok": True, "closed": False, "reason": "no_preparation"}  # the Bid Opening outcome stands; no case is created
	key = f"empty:{tender}:{outcome['opening']}"

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		if doc.state in records.TERMINAL:
			return records.summary(doc, closed=False, replayed=True)
		if doc.source_intake:
			return records.summary(doc, closed=False, reason="already_received")
		row = records.insert(frappe.get_doc({
			"doctype": INTAKE, "intake_id": f"{doc.name}-IN-00", "evaluation_case": doc.name, "operation_key": key, "source_kind": "Empty opening outcome",
			"opening_reference": outcome["opening"], "status": "Received", "attempts": 1, "first_attempt_at": clock.now(), "received_at": clock.now(),
		}))
		event = prc.owner_event(doc, "EmptyOpeningOutcomeReceived", f"empty:{row.name}", {"opening": outcome["opening"]}, idempotency_key=key)
		records.bump(doc, state="No evaluation required", source_intake=row.name, closed_reason="No bids were received. No evaluation is required.",
			opening_completed_at=outcome.get("completed_at"), last_committed_event=event)
		return records.summary(doc, closed=True)

	return records.command("ReceiveEmptyOpeningOutcome", tender=tender, idempotency_key=key, actor="system", payload={"opening": outcome["opening"]}, body=body)
