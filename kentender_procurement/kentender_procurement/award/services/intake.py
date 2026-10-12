# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ReceiveEvaluationReport (AWD-CHG-001 v0.4 §3 entry contract, §5.1, §5.3,
§5.7; AWD-AC-001, AC-002, AC-006).

Evaluation's successful delivery creates one Award case with decision cycle 1
and the Head of Procurement's "Prepare professional opinion" task against the
exact report — no acknowledgement, approval or manual start. Evaluation's own
"Review evaluation report" task becomes that same work item. A retry returns
the same case; a missing, mismatched or unverifiable artifact opens a source
issue automatically. A successor report (after a return, or after an
authorised correction) attaches to the cycle waiting for it and leaves every
earlier report, opinion and signature in place. A failed receipt leaves a
durable retry with the delivery's own identity and a named technical owner."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, cstr

from kentender_procurement.award.services import checks, clock, issues, notify, records, sources, state
from kentender_procurement.services import sequence


def receive(*, delivery: str, source_kind: str = sources.EVALUATION) -> dict[str, Any]:
	key = f"receive:{source_kind}:{delivery}"

	def body() -> dict[str, Any]:
		provider = sources.provider(source_kind)
		snap = provider.delivered_report(delivery)
		if not snap:
			raise frappe.DoesNotExistError("Not found")
		existing = frappe.db.get_value(state.REPORT, {"source_delivery": delivery}, ["name", "award_case"], as_dict=True)
		if existing:
			doc = frappe.get_doc(records.CASE, existing.award_case)
			return records.summary(doc, report=existing.name, created=False)
		case_name = records.case_id(snap["tender_reference"], "")
		namespace = cstr(snap.get("fixture_namespace")) or records.namespace()
		if frappe.db.exists(records.CASE, case_name):
			doc = records.lock(case_name)
			rep = _attach_successor(doc, snap, delivery)
		else:
			doc, rep = _create(case_name, snap, delivery, namespace, source_kind)
		provider.take_up(delivery)
		doc = state.reload(doc)
		checks.sync(doc)
		doc = state.reload(doc)
		hop = issues.hop_for(doc)
		c = state.cycle(doc)
		label = "Prepare the professional opinion on the corrected report" if cint(c.number) > 1 or cint(rep.version_number) > 1 else "Prepare professional opinion"
		notify.tell(doc, [hop], subject=f"{label} for {doc.tender_reference}", message=f"Evaluation report {rep.version_number} was received.", key=f"receive:{rep.name}")
		records.audit(doc.name, "ReceiveEvaluationReport", "system", report=rep.name, delivery=delivery)
		return records.summary(doc, report=rep.name, created=True)

	return records.command("ReceiveEvaluationReport", case="", idempotency_key=key, actor="system", payload={"delivery": delivery, "source": source_kind}, body=body)


def _new_report(doc, snap: dict[str, Any], delivery: str, cycle_number: int) -> Any:
	number = sequence.next_count(state.REPORT, {"award_case": doc.name})
	return records.new(state.REPORT, report_id=f"{doc.name}-RPT-{number:02d}", award_case=doc.name, cycle=cycle_number, source_delivery=delivery,
		source_version=snap.get("report"), version_number=cint(snap.get("version")) or number, content_digest=snap.get("content_digest"),
		signature_digest=records.digest(snap.get("signatures") or {}), snapshot_json=records.dumps(snap), received_at=_received_at(snap), state="Current",
		source_complete=0 if checks.source_problem(snap) else 1, source_problem=checks.source_problem(snap), fixture_namespace=doc.fixture_namespace)


def _received_at(snap: dict[str, Any]):
	"""Receipt follows delivery: never earlier than the delivery it receives."""
	from frappe.utils import get_datetime

	now = clock.now()
	delivered = get_datetime(snap.get("delivered_at")) if snap.get("delivered_at") else None
	return max(now, delivered) if delivered else now


def _create(case_name: str, snap: dict[str, Any], delivery: str, namespace: str, source_kind: str):
	now = _received_at(snap)
	doc = records.new(records.CASE, award_id=case_name, tender=snap["tender"], tender_reference=snap["tender_reference"], tender_title=snap.get("tender_title") or "",
		lot=snap.get("lot") or "1", procuring_entity=snap.get("procuring_entity") or "", source_kind=source_kind, source_case=snap.get("source_case") or "",
		current_cycle=1, stage="Opinion", outcome="", decision_status="No decision recorded", notification_status="Not issued", received_at=now,
		record_version=1, fixture_namespace=namespace)
	cycle = records.new(state.CYCLE, cycle_id=f"{doc.name}-C1", award_case=doc.name, number=1, stage="Opinion", outcome="", started_at=now,
		fixture_namespace=namespace)
	rep = _new_report(doc, snap, delivery, 1)
	records.update(cycle, source_report=rep.name)
	records.bump(doc, current_report=rep.name)
	return doc, rep


def _attach_successor(doc, snap: dict[str, Any], delivery: str):
	"""A later report version: before a committed decision it replaces the
	current one for this cycle (drafts go out of date, a signed opinion is
	superseded); after one, it is accepted only by a cycle authorised to wait
	for it. Otherwise it becomes a review item (§5.7)."""
	c = state.cycle(doc)
	committed = state.committed_decision(doc, c.number)
	if doc.stage == "Closed" or (committed and not c.awaiting_report):
		rep = _new_report(doc, snap, delivery, c.number)
		records.update(rep, state="Superseded")
		issues.open_issue(doc, source_event=f"successor:{delivery}", issue_type="Source correction", subtype="Report correction",
			title="Review the report correction before this award proceeds.", reason=f"Evaluation delivered report {rep.version_number}.")
		return rep
	previous = state.report(c.source_report)
	if previous and previous.state == "Current":
		records.update(previous, state="Superseded")
	rep = _new_report(doc, snap, delivery, c.number)
	for o in state.opinions(doc, c.number):
		if o.state == "Signed":
			records.update(o, state="Superseded")
		elif o.state in ("Draft", "Signing"):
			records.update(o, state="Out of date")
	records.update(c, source_report=rep.name, awaiting_report=0, stage="Opinion")
	for i in issues.open_issues(doc, issue_type="Source correction"):
		if i.subtype == checks.SOURCE_INCOMPLETE:
			issues.resolve(i, disposition="Owner correction confirmed", reason=f"Evaluation delivered report {rep.version_number}.", evidence=rep.name)
	records.bump(doc, stage="Opinion", current_report=rep.name)
	return rep


# -- hooks -------------------------------------------------------------------------
def on_report_delivered(delivery: str) -> None:
	"""`kt_evaluation_report_consumers`: Evaluation delivered a signed report."""
	receive(delivery=delivery, source_kind=sources.EVALUATION)


def on_report_delivery_failed(delivery: str) -> None:
	"""`kt_evaluation_report_consumers_failed`: the receipt failed; the
	delivery stays open for the sweep's retry and a technical owner is named."""
	from kentender_core.services import support_issues

	support_issues.open_issue(module="Award", operation="ReceiveEvaluationReport", operation_correlation=f"receive:{delivery}",
		subject="Restore evaluation report receipt", reference_doctype="Evaluation Report Delivery", reference_name=delivery,
		safe_detail="An evaluation report could not be received by Award. It will be received again automatically.")


def retry_pending() -> int:
	"""The sweep: receive any delivered report Award has not yet taken up."""
	count = 0
	provider = sources.providers().get(sources.EVALUATION)
	if not provider:
		return 0
	from kentender_core.services import support_issues

	for delivery in provider.pending_deliveries():
		try:
			receive(delivery=delivery, source_kind=sources.EVALUATION)
			support_issues.resolve_on_success(module="Award", operation_correlation=f"receive:{delivery}", note="The report was received.")
			count += 1
		except Exception:
			frappe.log_error(title=f"Award receipt retry failed for {delivery}")
	return count
