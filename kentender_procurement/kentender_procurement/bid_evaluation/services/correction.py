# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Return, correction and later evidence (EVL-CHG-001 v0.4 §5.6, §7.2, §7.3 rows
16–19, §8 EVL_DECISION_STATUS_UNKNOWN; tracker EVL4-908…910; acceptance
EVL-A11, EVL-A12; boards D07-HOP, D07-HOP-RETURN, D07-RETURNED,
D07-DECISION-UNKNOWN, D08-CORRECTION, D08-SUPPLEMENT, D08-SUPPLEMENT-SENT).

Before a downstream decision the Head of Procurement may **Return for
correction** with a specific reason: the delivered report is kept, the case
returns to Reviewing, and a new numbered report with fresh signatures
follows. The Head cannot change results or ranking. After an authoritative
downstream award decision nothing reopens: the chair records a linked
**correction notice** for the Head's own review. An unavailable downstream
status is never read as "no award". Opening supplements are new source
evidence: before delivery an eligible member records their impact on the
chair's shared item (a material effect reopens the affected work and ends
signature collection); after delivery the chair and the Head each have their
own item, cleared only by their own recorded action. Each item is keyed by
its evaluation, source event and holder, so concurrent supplements and
corrections never clear one another."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_evaluation.services import (
	clock, findings, guards, lifecycle, notify, people, prc, prc_owner, records, roster, simulation,
)
from kentender_procurement.bid_evaluation.services.errors import Guards, fail, invalid

DELIVERY = "Evaluation Report Delivery"
NOTICE = "Evaluation Correction Notice"
EVENT = "Evaluation Source Event"
IMPACTS = ("No effect on findings", "Findings need review")


def decision_status(doc) -> dict[str, Any]:
	"""The authoritative downstream status; a test environment may force it."""
	from kentender_procurement.tenders.services import evaluation_seam as tenders

	forced = simulation.controls().get("downstream_status")
	if forced:
		return {"status": forced, "checked_at": clock.now(), "source": "Simulation"}
	recorded = frappe.db.get_value(EVENT, {"evaluation_case": doc.name, "kind": "Award decision"}, ["effective_at", "source_reference"], as_dict=True)
	if recorded:
		return {"status": "Award decision recorded", "checked_at": clock.now(), "decided_at": recorded.effective_at, "source": recorded.source_reference}
	return tenders.award_decision_status(doc.tender)


def _delivered(doc):
	name = frappe.db.get_value(DELIVERY, {"evaluation_case": doc.name, "status": "Delivered"}, "name", order_by="delivered_at desc")
	return frappe.get_doc(DELIVERY, name) if name else None


def _status_known(doc) -> None:
	"""The decision status was read: any open issue about reading it is resolved."""
	from kentender_core.services import support_issues

	support_issues.resolve_on_success(module="Bid Evaluation", operation_correlation=f"decision-status:{doc.name}",
		note="The later decision status could be read again.")


def report_status_issue(*, tender: str, description: str, idempotency_key: str, user: str) -> dict[str, Any]:
	"""Board D07-DECISION-UNKNOWN(-CHAIR) "Report issue": the delivered report's
	recipient or the chair tells technical support the later decision status
	cannot be read. One issue per evaluation; no bid content in it."""
	from kentender_core.services import support_issues

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		delivery = _delivered(doc)
		if not delivery or user not in (delivery.recipient_user, roster.chair(doc.name)):
			raise frappe.DoesNotExistError("Not found")
		invalid({"description": "Describe the problem."} if not cstr(description).strip() else {})
		issue = support_issues.open_issue(module="Bid Evaluation", operation="CheckDecisionStatus", operation_correlation=f"decision-status:{doc.name}",
			subject=f"Resolve evaluation issue for {doc.tender_reference}", reference_doctype=records.CASE, reference_name=doc.name,
			safe_detail=f"The later decision status could not be checked: {cstr(description).strip()}", reported_by=user, fixture_namespace=records.namespace())
		records.bump(doc)
		return records.summary(doc, issue=issue["issue_id"], created=issue["created"])

	return records.command("ReportDecisionStatusIssue", tender=tender, idempotency_key=idempotency_key, actor=user, payload={"description": description}, body=body)


def return_report(*, tender: str, comment: str, idempotency_key: str, user: str) -> dict[str, Any]:
	"""ReturnEvaluationReport: the Head of Procurement, before any downstream decision."""

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		delivery = _delivered(doc)
		if not delivery or delivery.recipient_user != user:
			raise frappe.DoesNotExistError("Not found")
		guards.closed(doc, Guards()).raise_if_any()
		invalid({"comment": "Say what needs correction."} if not cstr(comment).strip() else {})
		status = decision_status(doc)
		if status["status"] == "Unknown":
			fail("EVL_DECISION_STATUS_UNKNOWN", {"checked_at": str(status["checked_at"]), "report": delivery.report_version})
		_status_known(doc)
		if status["status"] != "No award decision recorded":
			fail("EVL_VERSION_CONFLICT", {"reason": "decision_recorded"})
		return _apply_return(doc, delivery, comment, user, idempotency_key, status)

	return records.command("ReturnEvaluationReport", tender=tender, idempotency_key=idempotency_key, actor=user, payload={"comment": comment}, body=body)


def _apply_return(doc, delivery, comment: str, user: str, idempotency_key: str, status: dict[str, Any]) -> dict[str, Any]:
	"""The report goes back to the committee: the delivered version is kept as
	returned and the chair and secretary are told what needs correction."""
	delivery.update({"review_state": "Returned", "returned_by": user, "return_comment": cstr(comment).strip(), "returned_at": clock.now(),
		"downstream_status": status["status"], "downstream_checked_at": status["checked_at"]})
	records.save(delivery)
	version = frappe.get_doc("Evaluation Report Version", delivery.report_version)
	records.save(version.update({"state": "Returned", "supersession_kind": "Return", "supersession_reason": cstr(comment).strip(), "superseded_at": clock.now()}))
	event = prc.owner_event(doc, "ReportReturned", f"returned:{delivery.name}", {"report": version.name}, idempotency_key=idempotency_key, note=cstr(comment).strip())
	records.bump(doc, state="Reviewing", last_committed_event=event)
	notify.tell(doc, [u for u in (roster.chair(doc.name), roster.secretary(doc.name)) if u],
		subject=f"Correct evaluation report for {doc.tender_reference}: {cstr(comment).strip()}", message=cstr(comment).strip(), key=f"correct-{version.name}")
	return records.summary(doc, report=version.name)


def return_for_authorised_correction(*, tender: str, comment: str, instruction: str, authorised_by: str, idempotency_key: str) -> dict[str, Any]:
	"""The controlled post-decision correction route (EVL v0.4 §5.6; AWD-CHG-001
	v0.4 §5.7, AWD-IF-01): after a committed award decision the ordinary return
	is refused, but the Accounting Officer's recorded correction instruction
	(checked against Award's authority status) sends the delivered report back
	to the same committee for a corrected, freshly signed successor."""

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		delivery = _delivered(doc)
		if not delivery:
			fail("EVL_VERSION_CONFLICT", {"reason": "not_delivered"})
		status = decision_status(doc)
		if status["status"] == "Unknown":
			fail("EVL_DECISION_STATUS_UNKNOWN", {"checked_at": str(status["checked_at"]), "report": delivery.report_version})
		if cstr(status.get("correction_instruction")) != cstr(instruction):
			fail("EVL_VERSION_CONFLICT", {"reason": "no_authorised_correction"})
		_status_known(doc)
		return _apply_return(doc, delivery, comment, authorised_by, idempotency_key, status)

	return records.command("ReturnEvaluationReport", tender=tender, idempotency_key=idempotency_key, actor=authorised_by,
		payload={"comment": comment, "instruction": instruction}, body=body)


def record_correction_notice(*, tender: str, reason: str, correction: str, idempotency_key: str, user: str) -> dict[str, Any]:
	"""RecordCorrectionNotice: after delivery, a linked notice; the report is never reopened."""
	from kentender_procurement.proceedings.services import record_versions

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		if roster.chair(doc.name) != user:
			raise frappe.DoesNotExistError("Not found")
		delivery = _delivered(doc)
		if not delivery:
			fail("EVL_VERSION_CONFLICT", {"reason": "not_delivered"})
		invalid({f: "Required." for f, v in (("reason", reason), ("correction", correction)) if not cstr(v).strip()})
		status = decision_status(doc)
		if status["status"] != "Unknown":
			_status_known(doc)
		number = frappe.db.count(NOTICE, {"evaluation_case": doc.name}) + 1
		notice = records.insert(frappe.get_doc({
			"doctype": NOTICE, "notice_id": f"{doc.name}-CN-{number:02d}", "evaluation_case": doc.name, "report_version": delivery.report_version,
			"reason": cstr(reason).strip(), "correction": cstr(correction).strip(), "recorded_by": user, "recorded_at": clock.now(),
			"downstream_status": status["status"], "head_review_state": "Open",
		}))
		version_ref = frappe.db.get_value("Evaluation Report Version", delivery.report_version, "record_version_reference")
		with prc_owner.acting(doc.name):
			record_versions.append_correction(**prc.ref(doc), record_version=version_ref, kind="Correction notice", correct_information=cstr(correction).strip(),
				reason=cstr(reason).strip(), idempotency_key=prc.key(idempotency_key, "correction"), actor=user)
		notify.tell(doc, [delivery.recipient_user], subject=f"Review report correction for {doc.tender_reference}", message=cstr(correction).strip(),
			key=f"correction-{notice.name}")
		records.bump(doc)
		_tell_award(doc.tender)
		return records.summary(doc, notice=notice.name, downstream_status=status["status"])

	return records.command("RecordCorrectionNotice", tender=tender, idempotency_key=idempotency_key, actor=user, payload={"reason": reason, "correction": correction},
		body=body)


def _tell_award(tender: str) -> None:
	"""A post-delivery correction or opening update reaches Award
	(`kt_evaluation_correction_consumers`, AWD-IF-01). Award takes it up as its
	own review item; a failure there never undoes Evaluation's record."""
	from kentender_procurement.bid_evaluation.services.award_seam import notify_consumers

	notify_consumers("kt_evaluation_correction_consumers", tender=tender)


def consume_supplements(tender: str) -> int:
	"""Bid Opening's completed-record corrections, recorded once each (ReceiveOpeningSupplement)."""
	from kentender_procurement.bid_opening.services import evaluation_seam as opening

	name = records.case_for(tender)
	if not name:
		return 0
	doc = frappe.get_doc(records.CASE, name)
	if not doc.source_intake or doc.state in records.TERMINAL:
		return 0
	count = 0
	for supplement in opening.supplements(tender):
		key = f"BOP-SUPP:{supplement.supplement_id}"
		if frappe.db.exists(EVENT, {"event_key": key}):
			continue
		count += 1
		_receive_supplement(tender, key, supplement)
	return count


def _receive_supplement(tender: str, key: str, supplement) -> dict[str, Any]:

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		after = doc.state == "Report sent"
		number = frappe.db.count(EVENT, {"evaluation_case": doc.name}) + 1
		row = records.insert(frappe.get_doc({
			"doctype": EVENT, "source_event_id": f"{doc.name}-SE-{number:02d}", "evaluation_case": doc.name, "event_key": key, "source": "Bid Opening",
			"kind": "Opening supplement", "source_reference": supplement.supplement_id, "authority": cstr(supplement.author), "reason": cstr(supplement.reason),
			"effective_at": supplement.recorded_at, "received_at": clock.now(), "detail_json": json.dumps({"kind": supplement.kind,
			"text": supplement.correct_information}, default=str), "delivered_context": "After delivery" if after else "Before delivery", "impact": "Pending",
			"head_review_state": "Open" if after else "",
		}))
		event = prc.owner_event(doc, "OpeningSupplementReceived", f"supplement:{row.name}", {"supplement": supplement.supplement_id}, idempotency_key=key)
		records.bump(doc, last_committed_event=event)
		chair = roster.chair(doc.name)
		recipients = [chair] if chair else []
		if after:
			recipients += [frappe.db.get_value(DELIVERY, {"evaluation_case": doc.name, "status": "Delivered"}, "recipient_user")]
		notify.tell(doc, [u for u in recipients if u], subject=f"Review opening update for {doc.tender_reference}", message=cstr(supplement.correct_information),
			key=f"supplement-{row.name}")
		if after:
			_tell_award(doc.tender)
		return records.summary(doc, source_event=row.name)

	return records.command("ReceiveOpeningSupplement", tender=tender, idempotency_key=key, actor="system", payload={"key": key}, body=body)


def assess_supplement(*, tender: str, source_event: str, impact: str, reason: str, idempotency_key: str, user: str) -> dict[str, Any]:
	"""AssessOpeningSupplement: an eligible member before delivery; the chair after."""

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		row = frappe.db.get_value(EVENT, {"name": source_event, "evaluation_case": doc.name, "kind": "Opening supplement"}, "name")
		if not row:
			raise frappe.DoesNotExistError("Not found")
		row = frappe.get_doc(EVENT, row)
		findings.require_member(doc, user)
		if row.delivered_context == "After delivery" and roster.chair(doc.name) != user:
			raise frappe.DoesNotExistError("Not found")
		guards.closed(doc, Guards()).raise_if_any()
		invalid({**({"impact": "Choose the effect on findings."} if impact not in IMPACTS else {}), **({"reason": "Give the reason."} if not cstr(reason).strip() else {})})
		if row.impact not in ("", "Pending"):
			fail("EVL_VERSION_CONFLICT", {"reason": "already_assessed"})
		records.save(row.update({"impact": impact, "impact_reason": cstr(reason).strip(), "impact_by": user, "impact_at": clock.now()}))
		event = prc.owner_event(doc, "OpeningSupplementAssessed", f"impact:{row.name}", {"impact": impact}, idempotency_key=idempotency_key, note=cstr(reason).strip())
		if impact == "Findings need review" and doc.state != "Report sent":
			lifecycle.withdraw_signing(doc, kind="Source change", reason=cstr(reason).strip(), idempotency_key=idempotency_key, actor=user)
		records.bump(frappe.get_doc(records.CASE, doc.name), last_committed_event=event)
		return records.summary(frappe.get_doc(records.CASE, doc.name), source_event=row.name, impact=impact)

	return records.command("AssessOpeningSupplement", tender=tender, idempotency_key=idempotency_key, actor=user, payload={"source_event": source_event, "impact": impact,
		"reason": reason}, body=body)


def head_review(*, tender: str, item: str, idempotency_key: str, user: str) -> dict[str, Any]:
	"""The Head of Procurement's recorded review of one supplement or correction notice."""

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		delivery = _delivered(doc)
		if not delivery or delivery.recipient_user != user:
			raise frappe.DoesNotExistError("Not found")
		for doctype in (EVENT, NOTICE):
			if frappe.db.exists(doctype, {"name": item, "evaluation_case": doc.name}):
				row = frappe.get_doc(doctype, item)
				if row.head_review_state != "Open":
					fail("EVL_VERSION_CONFLICT", {"reason": "already_reviewed"})
				records.save(row.update({"head_review_state": "Reviewed", "head_reviewed_at": clock.now()}))
				return records.summary(doc, item=item)
		raise frappe.DoesNotExistError("Not found")

	return records.command("RecordHeadReview", tender=tender, idempotency_key=idempotency_key, actor=user, payload={"item": item}, body=body)
