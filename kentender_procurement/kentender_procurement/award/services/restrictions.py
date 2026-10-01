# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Restrictions and issue outcomes (AWD-CHG-001 v0.4 §5.6, §5.10;
AWD-AC-016, AC-020, AC-030).

`RecordExternalAwardRestriction` (HOP's **Record restriction**) records a
received Board or court notice or order, or a reported challenge, with its
source, effective and received times, scope and evidence; **Basis for hold**
is Authoritative order or Reported challenge, and uncertainty uses Reported
challenge. `ReceiveAwardRestriction` does the same for a system-originated
event. Both apply the hold at once and reach Contracting as an update if the
award was already delivered.

`RecordAwardIssueDisposition` accepts only the fixed §5.10 outcomes
applicable to the selected issue and evidence — no free-text outcome, no
Override. It never lifts another owner's order, changes a decision or turns
a late acceptance into a timely one: a proposal to change the outcome goes
to the Accounting Officer's **Decide correction** (or the open Decide award)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_procurement.award.services import checks, clock, contracting, eligibility, guards, issues, notify, people, records, state
from kentender_procurement.award.services.errors import fail, invalid

BASES = ("Authoritative order", "Reported challenge")
NO_MATERIAL = "No material effect"
REQUEST_EVALUATION = "Request corrected evaluation"
REQUEST_REVIEW = "Request decision review"
ENDED = "Restriction ended"
NOT_SUBSTANTIATED = "Reported challenge not substantiated"
OWNER_CONFIRMED = "Owner correction confirmed"
FURTHER = "Further action required"
PROPOSALS = (REQUEST_EVALUATION, REQUEST_REVIEW)


def applicable(issue) -> tuple[str, ...]:
	"""The §5.10 outcomes the server offers for this issue."""
	if issue.issue_type == "Source correction":
		return (NO_MATERIAL, REQUEST_EVALUATION, REQUEST_REVIEW, FURTHER)
	if issue.issue_type == "Review/order":
		return (ENDED, FURTHER) if issue.basis == "Authoritative order" else (NOT_SUBSTANTIATED, FURTHER)
	if issue.issue_type == "Supplier response":
		return (REQUEST_REVIEW,)
	if issue.issue_type == "Validity":
		return (REQUEST_REVIEW, FURTHER)
	if issue.issue_type in ("Funding", "Rules and notice audience", "Delivery", "Service failure"):
		return (OWNER_CONFIRMED, FURTHER)
	return (FURTHER,)


def _later_update(doc, issue) -> None:
	"""A restriction after delivery reaches the existing Contracting case as a
	separate immutable update; the original package is never rewritten."""
	pkg = eligibility.current_package(doc)
	if not pkg or pkg.status != "Delivered":
		return
	update = {"reference": f"{pkg.name}:UPD:{issue.name}", "award_case": doc.name, "package": pkg.name, "kind": "Restriction", "issue": issue.name,
		"basis": issue.basis, "scope": issue.scope, "effective_at": str(issue.effective_at), "fixture_namespace": doc.fixture_namespace}
	try:
		receipt = contracting.deliver_update(update)["receipt"]
	except contracting.ReceiverUnavailable:
		receipt = ""
	records.append_json(pkg, "updates_json", {**update, "receipt": receipt, "at": str(clock.now())})
	records.save(pkg)


def _hold(doc, *, source_event: str, basis: str, source: str, received_at, effective_at, scope: str, evidence: str, reason: str, actor: str) -> Any:
	title = "This award is on hold."
	issue = issues.open_issue(doc, source_event=source_event, issue_type="Review/order", subtype="Restriction", title=title, basis=basis, scope=scope,
		source=source, evidence=evidence, reason=reason, effective_at=effective_at, received_at=received_at,
		detail={"precautionary": basis == "Reported challenge", "recorded_by": actor})
	_later_update(doc, issue)
	notify.tell(doc, [issues.hop_for(doc)], subject=f"Review restriction for {doc.tender_reference}", message=source, key=f"restriction:{issue.name}")
	return issue


def record_external(*, award: str, basis: str, source: str, received_at: str = "", effective_from: str = "", scope: str = "", evidence: str = "", reason: str = "",
		idempotency_key: str, user: str) -> dict[str, Any]:
	def body() -> dict[str, Any]:
		doc = records.lock(award)
		guards.require_hop(user)
		invalid({
			"basis": "Choose the basis for the hold." if basis not in BASES else "",
			"source": "Enter the source." if not cstr(source).strip() else "",
			"evidence": "Attach or describe the evidence." if basis == "Authoritative order" and not cstr(evidence).strip() else "",
			"reason": "Enter the reason." if not cstr(reason).strip() else "",
			"received_at": "Enter when it was received." if not cstr(received_at).strip() else "",
		})
		try:
			received = get_datetime(received_at)
			effective = get_datetime(effective_from) if cstr(effective_from).strip() else received
		except Exception:
			invalid({"received_at": "Enter a valid date and time."})
		issue = _hold(doc, source_event=f"restriction:{idempotency_key}", basis=basis, source=cstr(source).strip(), received_at=received, effective_at=effective,
			scope=cstr(scope).strip() or "This award", evidence=cstr(evidence).strip(), reason=cstr(reason).strip(), actor=user)
		records.bump(doc)
		records.audit(doc.name, "RecordExternalAwardRestriction", user, issue=issue.name, basis=basis)
		return records.summary(state.reload(doc), issue=issue.name)

	return records.command("RecordExternalAwardRestriction", case=award, idempotency_key=idempotency_key, actor=user,
		payload={"basis": basis, "source": source, "received": received_at, "effective": effective_from, "scope": scope, "evidence": evidence, "reason": reason},
		body=body)


def receive(*, tender: str, event_key: str, basis: str = "Authoritative order", authority: str = "", instruction: str = "", effective_at=None, scope: str = "",
		reason: str = "") -> dict[str, Any] | None:
	"""ReceiveAwardRestriction: an authoritative producer's event, once per key;
	a late receipt keeps its effective and received times apart."""
	name = frappe.db.get_value(records.CASE, {"tender": tender}, "name")
	if not name:
		return None

	def body() -> dict[str, Any]:
		doc = records.lock(name)
		issue = _hold(doc, source_event=f"tender-event:{event_key}", basis=basis if basis in BASES else "Reported challenge", source=cstr(authority or instruction),
			received_at=clock.now(), effective_at=get_datetime(effective_at) if effective_at else clock.now(), scope=scope or "This award",
			evidence=cstr(instruction), reason=cstr(reason), actor="system")
		records.bump(doc)
		return records.summary(state.reload(doc), issue=issue.name)

	return records.command("ReceiveAwardRestriction", case=name, idempotency_key=f"restriction-event:{event_key}", actor="system", payload={"key": event_key}, body=body)


def disposition(*, award: str, issue: str, outcome: str = "", reason: str = "", evidence: str = "", next_action: str = "", idempotency_key: str,
		user: str) -> dict[str, Any]:
	"""RecordAwardIssueDisposition. V06/V07 **Record next action** sends no
	outcome: it is always Request decision review, with the saved response or
	missed-deadline evidence attached by the server."""

	def body() -> dict[str, Any]:
		doc = records.lock(award)
		guards.require_hop(user)
		if not issue or not frappe.db.exists(state.ISSUE, {"name": issue, "award_case": doc.name}):
			raise frappe.DoesNotExistError("Not found")
		row = frappe.get_doc(state.ISSUE, issue)
		if row.state != "Open":
			fail("AWD_RECORD_CHANGED", {"reason": "issue_closed"})
		allowed = applicable(row)
		chosen = outcome or (REQUEST_REVIEW if row.issue_type == "Supplier response" else "")
		proof = cstr(evidence).strip()
		if row.issue_type == "Supplier response":
			detail = records.loads(row.detail_json)
			proof = proof or cstr(detail.get("response") or detail.get("late_response") or f"Reply deadline {detail.get('deadline', '')}")
		invalid({
			"outcome": "Choose an outcome." if chosen not in allowed else "",
			"reason": "Enter the reason." if not cstr(reason).strip() else "",
			"evidence": "Enter the evidence." if chosen in (NO_MATERIAL, ENDED, NOT_SUBSTANTIATED, OWNER_CONFIRMED, FURTHER, REQUEST_EVALUATION) and not proof else "",
			"next_action": "Enter the next action." if chosen in (REQUEST_REVIEW, REQUEST_EVALUATION, FURTHER) and not cstr(next_action).strip() else "",
		})
		if chosen == ENDED:
			others = [i for i in issues.open_issues(doc, issue_type="Review/order") if i.name != row.name and i.basis == "Authoritative order"]
			if others:
				fail("AWD_ON_HOLD", {"reason": "continuing_restriction", "issues": [i.name for i in others]})
		history = records.loads(row.detail_json)
		history.setdefault("dispositions", []).append({"outcome": chosen, "reason": cstr(reason).strip(), "evidence": proof, "next_action": cstr(next_action).strip(),
			"by": user, "at": str(clock.now())})
		if chosen in (NO_MATERIAL, ENDED, NOT_SUBSTANTIATED, OWNER_CONFIRMED):
			records.update(row, detail_json=records.dumps(history))
			issues.resolve(row, disposition=chosen, reason=reason, evidence=proof, next_action=next_action, user=user)
			if chosen == OWNER_CONFIRMED:
				checks.sync(state.reload(doc))
		elif chosen in PROPOSALS:
			history["proposal"] = {"outcome": chosen, "reason": cstr(reason).strip(), "next_action": cstr(next_action).strip(), "by": user, "at": str(clock.now()),
				"evidence": proof}
			records.update(row, detail_json=records.dumps(history), disposition=chosen, disposition_reason=cstr(reason).strip(), disposition_evidence=proof,
				next_action=cstr(next_action).strip())
			ao = issues.ao_for(doc)
			task = "Decide correction" if state.latest_committed(doc) else "Decide award"
			notify.tell(doc, [ao], subject=f"{task} for {doc.tender_reference}", message=cstr(reason).strip(), key=f"proposal:{row.name}:{len(history['dispositions'])}")
		else:
			records.update(row, detail_json=records.dumps(history), disposition=FURTHER, disposition_reason=cstr(reason).strip(), disposition_evidence=proof,
				next_action=cstr(next_action).strip())
		records.bump(doc)
		records.audit(doc.name, "RecordAwardIssueDisposition", user, issue=row.name, outcome=chosen)
		eligibility.refresh(state.reload(doc))
		return records.summary(state.reload(doc), issue=row.name, outcome=chosen)

	return records.command("RecordAwardIssueDisposition", case=award, idempotency_key=idempotency_key, actor=user,
		payload={"issue": issue, "outcome": outcome, "reason": reason, "evidence": evidence, "next_action": next_action}, body=body)


def proposals(doc) -> list:
	"""Open issues carrying HOP's proposal the AO has not yet decided (an
	authorised one stays open, holding, until its successor work is done)."""
	return [i for i in issues.open_issues(doc) if records.loads(i.detail_json).get("proposal") and not records.loads(i.detail_json).get("authorised")]


def owner_label(issue) -> str:
	return people.full_name(issue.owner_user) if issue.owner_user else cstr(issue.owner_role)
