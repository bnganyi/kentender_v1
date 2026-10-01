# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Send for signing, personal signatures, concerns, revision and delivery
(EVL-CHG-001 v0.4 §5.5, §7.2, §7.3 rows 13–15, §8 EVL_REPORT_INCOMPLETE,
EVL_TARGET_CHANGED, EVL_SIGNATURE_UNCONFIRMED, EVL_REPORT_DELIVERY_FAILED;
tracker EVL4-903…907, EVL4-912; acceptance EVL-A10; boards D07-*).

**Send for signing** freezes the report and its annexes as one exact version,
only when every required result is resolved or explicitly qualified, every
sent clarification is disposed of or withdrawn, no meeting is active, any
verification exercise is complete, the outcome is not provisional, the
current eligible roster is complete and nothing is paused. Every applicable
reason is listed together, with who holds it. Before freezing and before
delivery the source, roster, cancellation or suspension and validity are
rechecked. Every member of the current eligible roster signs that version
personally; a stale or unconfirmed proof counts for nothing. A member may
instead **Raise a concern**, and the secretary or chair may **Revise
report**: either ends signature collection for that version, keeping old
signatures as history. The last valid signature completes the record and
delivers it once to the Head of Procurement; a delivery failure keeps the
signatures and Signing, and is retried under the same delivery identity.
There is no chair Complete, Release or recipient receipt approval."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_evaluation.services import (
	clock, comparison, discussion, findings, guards, lifecycle, notify, people, prc, prc_owner, records, report, roster, simulation, timers,
)
from kentender_procurement.bid_evaluation.services.errors import Guards, fail, invalid

REPORT = report.REPORT
DELIVERY = "Evaluation Report Delivery"


def signing_version(doc):
	name = lifecycle.signing_report(doc)
	return frappe.get_doc(REPORT, name) if name else None


def readiness(doc) -> Guards:
	"""Every reason the report cannot be frozen yet (EVL_REPORT_INCOMPLETE and friends)."""
	from kentender_procurement.bid_evaluation.services import diligence

	checks_ = guards.open_case(doc)
	if checks_:
		return checks_
	issues = []
	chair = roster.chair(doc.name)
	built = report.build(doc)
	for bid in built["bid_findings"]:
		for row in bid["eligibility"] + bid["technical"]:
			if row["finding"] == "Needs review" and not row["qualified"]:
				issues.append({"item": f"{row['requirement']} — Needs review; no committee disposition", "bidder": bid["bidder"], "holder": chair,
					"holder_name": people.full_name(chair) if chair else ""})
	for c in built["clarifications_and_record"]["clarifications"]:
		if c["status"] in ("Authorised", "Sent"):
			issues.append({"item": "A clarification has no final disposition", "holder": chair, "holder_name": people.full_name(chair) if chair else ""})
	if discussion.active_session(doc):
		issues.append({"item": "A committee discussion is still active", "holder": chair, "holder_name": people.full_name(chair) if chair else ""})
	plan = diligence.current_plan(doc.name)
	if plan and plan.status == "Current":
		issues.append({"item": "The verification exercise is not complete", "holder": plan.lead_user, "holder_name": people.full_name(plan.lead_user)})
	if built["recommendation"]["provisional"]:
		issues.append({"item": "The comparison is provisional", "holder": chair, "holder_name": people.full_name(chair) if chair else ""})
	complete = roster.complete(doc.name)
	if not complete["complete"]:
		for p in complete["pending"]:
			issues.append({"item": f"{people.full_name(p['user'])} is not an eligible member", "reasons": p["reasons"], "holder": p["user"],
				"holder_name": people.full_name(p["user"])})
	if issues:
		checks_.add("EVL_REPORT_INCOMPLETE", issues=issues)
	return checks_


def send_for_signing(*, tender: str, expected_version: int, idempotency_key: str, user: str) -> dict[str, Any]:
	from kentender_procurement.proceedings.services import record_versions

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		if roster.secretary(doc.name) != user:
			raise frappe.DoesNotExistError("Not found")
		if doc.state != "Reviewing":
			fail("EVL_VERSION_CONFLICT", {"reason": "not_reviewing", "state": doc.state})
		readiness(doc).raise_if_any()
		draft = report.draft(doc)
		records.check_version(draft, expected_version)
		built = report.build(doc)
		content = json.dumps({**built, "narrative": cstr(draft.narrative)}, sort_keys=True, default=str)
		digest = records.digest(content)
		members = roster.member_users(doc.name)
		targets = [{"target_id": f"{draft.name}-SIG-{u.split('@')[0]}", "target_type": "Report signature", "target_reference": draft.name, "target_digest": digest,
			"required_member": u} for u in members]
		with prc_owner.acting(doc.name):
			frozen = record_versions.freeze_record(**prc.ref(doc), record_kind="Evaluation report", owner_reference=draft.name, content=content, targets=targets,
				idempotency_key=prc.key(idempotency_key, "freeze"), actor=user)
		rec = built["recommendation"]
		draft.update({"state": "Signing", "content_json": content, "content_digest": digest, "outcome": cstr(rec["outcome"]),
			"recommended_bid": cstr((rec.get("recommended") or {}).get("bid")), "recommended_total": cstr((rec.get("recommended") or {}).get("evaluated_total")),
			"qualifications_json": json.dumps(rec["qualifications"]), "source_versions_json": json.dumps({"run": doc.current_run, "definition": doc.definition_digest,
			"intake": doc.source_intake}), "frozen_by": user, "frozen_at": clock.now(), "record_version_reference": frozen["record_version"]})
		records.bump(draft)
		records.bump(doc, state="Signing", current_report=draft.name, last_committed_event=frozen["event_id"])
		notify.tell(doc, members, subject=f"Review and sign report for {doc.tender_reference}", message=f"Evaluation report {draft.version_number} is ready to sign.",
			key=f"sign-{draft.name}")
		return records.summary(doc, report=draft.name, version_number=draft.version_number, digest=digest)

	return records.command("SendReportForSigning", tender=tender, idempotency_key=idempotency_key, actor=user, payload={"expected_version": expected_version},
		body=body)


def my_target(doc, version, user: str) -> dict[str, Any] | None:
	from kentender_procurement.proceedings.services import record_versions

	if not version or not version.record_version_reference:
		return None
	missing = {m["target_id"] for m in record_versions.missing_proofs(version.record_version_reference) if m["required_member"] == user}
	row = frappe.get_doc("Proceeding Minutes Version", version.record_version_reference)
	return next(({"target_id": t.target_id, "target_digest": t.target_digest} for t in row.targets if t.required_member == user and t.target_id in missing), None)


def sign(*, tender: str, report_version: str, idempotency_key: str, user: str) -> dict[str, Any]:
	"""SignEvaluationReport: the member's own proof on the exact current version."""
	from kentender_procurement.proceedings.services import record_versions

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		findings.require_member(doc, user)
		checks_ = guards.open_case(doc)
		version = signing_version(doc)
		if version is None or version.name != report_version:
			checks_.add("EVL_TARGET_CHANGED", current=version.name if version else "")
		checks_.raise_if_any()
		target = my_target(doc, version, user)
		if target is None:
			return records.summary(doc, report=version.name, signed=True, replayed=True)
		with prc_owner.acting(doc.name):
			out = record_versions.record_proof(**prc.ref(doc), record_version=version.record_version_reference, target_id=target["target_id"],
				target_digest=target["target_digest"], action="Sign", idempotency_key=prc.key(idempotency_key, "proof"), actor=user)
		if not out.get("ok"):
			records.bump(doc)
			return {"ok": False, "code": "EVL_SIGNATURE_UNCONFIRMED", "message": "Your signature has not been confirmed. Check its status before trying again.",
				"evaluation": doc.name, "report": version.name, "verification_result": out.get("verification_result")}
		records.bump(doc, last_committed_event=out["event_id"])
		delivered = None
		if not record_versions.missing_proofs(version.record_version_reference):
			delivered = _complete_and_deliver(doc, version, idempotency_key, user)
		return records.summary(doc, report=version.name, signed=True, delivery=delivered)

	return records.command("SignEvaluationReport", tender=tender, idempotency_key=idempotency_key, actor=user, payload={"report_version": report_version}, body=body)


def _recipient(doc) -> str | None:
	assigned_by = frappe.db.get_value("Evaluation Secretary Appointment", {"evaluation_case": doc.name, "status": "Current"}, "assigned_by")
	if assigned_by and people.holds(assigned_by, people.HEAD_OF_PROCUREMENT):
		return assigned_by
	holders = people.holders(people.HEAD_OF_PROCUREMENT)
	return holders[0] if holders else None


def recheck(doc) -> Guards:
	"""Before delivery: roster, cancellation, suspension and validity (§5.5)."""
	checks_ = guards.open_case(doc)
	if not roster.complete(doc.name)["complete"]:
		checks_.add("EVL_REPORT_INCOMPLETE", issues=[{"item": "The committee changed while the report was being signed."}])
	return checks_


def _complete_and_deliver(doc, version, key: str, actor: str) -> dict[str, Any]:
	from kentender_procurement.proceedings.services import record_versions

	if recheck(doc):
		return {"status": "Paused"}
	dated = timers.dated(doc)
	if dated["validity_expired"] and version.outcome == "Recommendation":
		lifecycle.withdraw_signing(doc, kind="Validity", reason="Tender validity expired while the report was being signed.", idempotency_key=key, actor=actor)
		return {"status": "Returned for validity"}
	with prc_owner.acting(doc.name):
		record_versions.complete_record(**prc.ref(doc), record_version=version.record_version_reference, idempotency_key=prc.key(key, "complete"), actor=prc.SYSTEM)
	return deliver(doc, version, key)


def deliver(doc, version, key: str) -> dict[str, Any]:
	"""DeliverEvaluationReport: one recipient record and task per version."""
	delivery_key = f"{doc.name}:{version.name}"
	name = frappe.db.get_value(DELIVERY, {"delivery_key": delivery_key}, "name")
	row = frappe.get_doc(DELIVERY, name) if name else records.insert(frappe.get_doc({"doctype": DELIVERY,
		"delivery_id": f"{version.name}-DLV", "evaluation_case": doc.name, "report_version": version.name, "delivery_key": delivery_key, "status": "Pending",
		"attempts": 0}))
	if row.status == "Delivered":
		return {"status": "Delivered", "delivery": row.name}
	row.attempts = (row.attempts or 0) + 1
	recipient = _recipient(doc)
	if simulation.controls().get("delivery_outcome") == "Failed" or not recipient:
		row.status, row.last_error = "Failed", "The signed report could not be delivered."
		records.save(row)
		return {"status": "Failed", "delivery": row.name, "code": "EVL_REPORT_DELIVERY_FAILED", "message": "The signed report could not be delivered."}
	row.update({"status": "Delivered", "recipient_user": recipient, "delivered_at": clock.now(), "review_state": "Open", "last_error": ""})
	records.save(row)
	records.save(version.update({"state": "Delivered"}))
	event = prc.owner_event(doc, "ReportDelivered", f"delivered:{row.name}", {"report": version.name, "recipient": recipient}, idempotency_key=key)
	records.bump(doc, state="Report sent", last_committed_event=event)
	notify.tell(doc, [recipient], subject=f"Review evaluation report for {doc.tender_reference}", message=f"Evaluation report {version.version_number} was sent to you.",
		key=f"review-{version.name}")
	# AWD-CHG-001 v0.4 §3 entry contract (AWD-IF-01): the delivered report
	# reaches Award, which takes this recipient's review task up as its own.
	from kentender_procurement.bid_evaluation.services.award_seam import notify_consumers

	notify_consumers("kt_evaluation_report_consumers", delivery=row.name)
	return {"status": "Delivered", "delivery": row.name, "recipient": recipient}


def retry_delivery(*, tender: str, idempotency_key: str, user: str) -> dict[str, Any]:
	"""RetryEvaluationOperation for delivery: the same delivery identity."""

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		if roster.secretary(doc.name) != user:
			raise frappe.DoesNotExistError("Not found")
		version = signing_version(doc)
		if version is None:
			fail("EVL_VERSION_CONFLICT", {"reason": "nothing_to_deliver"})
		from kentender_procurement.proceedings.services import record_versions

		if record_versions.missing_proofs(version.record_version_reference):
			fail("EVL_VERSION_CONFLICT", {"reason": "signatures_outstanding"})
		out = deliver(doc, version, idempotency_key)
		return records.summary(frappe.get_doc(records.CASE, doc.name), **out) if out["status"] == "Delivered" else {**records.summary(doc), **out, "ok": False}

	return records.command("RetryEvaluationOperation", tender=tender, idempotency_key=idempotency_key, actor=user, payload={"operation": "DeliverEvaluationReport"},
		body=body)


def raise_report_concern(*, tender: str, reason: str, idempotency_key: str, user: str) -> dict[str, Any]:
	"""RaiseReportConcern: a member returns the version being signed to review."""

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		findings.require_member(doc, user)
		guards.closed(doc, Guards()).raise_if_any()
		invalid({"reason": "Say what needs correction."} if not cstr(reason).strip() else {})
		version = signing_version(doc)
		if version is None:
			fail("EVL_VERSION_CONFLICT", {"reason": "not_signing"})
		lifecycle.withdraw_signing(doc, kind="Concern", reason=cstr(reason).strip(), idempotency_key=idempotency_key, actor=user)
		event = prc.owner_event(doc, "ReportConcern", f"report-concern:{version.name}:{idempotency_key}", {"report": version.name, "member": user},
			idempotency_key=idempotency_key, note=cstr(reason).strip())
		notify.tell(doc, [u for u in (roster.chair(doc.name), roster.secretary(doc.name)) if u], subject=f"Resolve report concern for {doc.tender_reference}",
			message=cstr(reason).strip(), key=f"report-concern-{version.name}")
		records.bump(frappe.get_doc(records.CASE, doc.name), last_committed_event=event)
		return records.summary(frappe.get_doc(records.CASE, doc.name), report=version.name)

	return records.command("RaiseReportConcern", tender=tender, idempotency_key=idempotency_key, actor=user, payload={"reason": reason}, body=body)


def revise(*, tender: str, reason: str, idempotency_key: str, user: str) -> dict[str, Any]:
	"""ReviseEvaluationReport: the secretary or chair returns it for a new version."""

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		if user not in (roster.chair(doc.name), roster.secretary(doc.name)):
			raise frappe.DoesNotExistError("Not found")
		guards.closed(doc, Guards()).raise_if_any()
		invalid({"reason": "Give the reason."} if not cstr(reason).strip() else {})
		version = signing_version(doc)
		if version is None:
			fail("EVL_VERSION_CONFLICT", {"reason": "not_signing"})
		lifecycle.withdraw_signing(doc, kind="Revision", reason=cstr(reason).strip(), idempotency_key=idempotency_key, actor=user)
		return records.summary(frappe.get_doc(records.CASE, doc.name), report=version.name)

	return records.command("ReviseEvaluationReport", tender=tender, idempotency_key=idempotency_key, actor=user, payload={"reason": reason}, body=body)


def signatures(version) -> list[dict[str, Any]]:
	"""Each target's member and the time of their valid proof, if any."""
	if not version or not version.record_version_reference:
		return []
	row = frappe.get_doc("Proceeding Minutes Version", version.record_version_reference)
	proofs = {(p.target_id, p.member_user): p for p in frappe.get_all("Proceeding Attestation", filters={"minutes_version": row.name,
		"verification_result": "Accepted/Verified"}, fields=["target_id", "member_user", "recorded_at", "method"])}
	return [{"member": t.required_member, "name": people.full_name(t.required_member), "signed_at": proofs[(t.target_id, t.required_member)].recorded_at
		if (t.target_id, t.required_member) in proofs else None} for t in row.targets]
