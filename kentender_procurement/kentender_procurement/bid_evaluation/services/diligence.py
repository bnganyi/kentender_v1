# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Due diligence (EVL-CHG-001 v0.4 §5.4, §7.2, §7.3 rows 10–12; tracker
EVL4-801…805; acceptance EVL-A08; boards D08-VERIFY-PLAN, D08-DD,
D08-DD-FREEZE, D08-DD-SIGN, D08-VERIFY-OUTCOME, D08-VERIFY-NEG).

During a collective discussion the chair records the committee's
verification plan in one operation: scope, the legal or published basis,
the participants chosen from the current eligible committee and one of them
as lead. This allocates work inside the appointed committee; it is not a new
appointment or approval, and no adviser or outside user is appointed. A
change of scope or participants uses the same command with a reason, keeps
the history and supersedes any frozen verification report. Each participant
records their own observations; the lead freezes the report once every
participant has done so; each participant proves their own page and
signature targets. A finding that affects the recommendation returns to the
committee, and a negative one never silently substitutes the next bidder:
the next eligible ranked bid is only proposed, with the checks it needs."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_evaluation.services import (
	clock, comparison, conclusion, discussion, findings, guards, notify, people, prc, prc_owner, records, roster,
)
from kentender_procurement.bid_evaluation.services.errors import Guards, fail, invalid
from kentender_procurement.services import sequence

PLAN = "Evaluation Verification Plan"
OBSERVATION = "Evaluation Verification Observation"


def current_plan(case: str):
	name = frappe.db.get_value(PLAN, {"evaluation_case": case, "status": ("in", ("Current", "Completed"))}, "name", order_by="version_number desc")
	return frappe.get_doc(PLAN, name) if name else None


def participants(plan) -> list[str]:
	return json.loads(plan.participants_json or "[]")


def record_plan(*, tender: str, scope: str, basis: str, participants_: list[str], lead: str, change_reason: str = "", idempotency_key: str,
		user: str) -> dict[str, Any]:
	payload = {"scope": scope, "basis": basis, "participants": sorted(participants_), "lead": lead, "change_reason": change_reason}
	discussion.recheck_presence(tender)

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		if roster.chair(doc.name) != user:
			raise frappe.DoesNotExistError("Not found")
		members = conclusion.collective(doc, idempotency_key)
		prior = current_plan(doc.name)
		eligible = set(roster.eligible_members(doc.name))
		fields = {f: "Required." for f, v in (("scope", scope), ("basis", basis)) if not cstr(v).strip()}
		chosen = list(dict.fromkeys(participants_))
		if not chosen or not set(chosen) <= eligible:
			fields["participants"] = "Choose participants from the current eligible committee."
		if lead not in chosen:
			fields["lead"] = "Choose the lead from the participants."
		if prior and not cstr(change_reason).strip():
			fields["change_reason"] = "Give the reason for changing the verification plan."
		invalid(fields)
		if prior:
			_supersede(doc, prior, reason=change_reason, idempotency_key=idempotency_key, actor=user)
		out = conclusion.committed(doc, event_type="VerificationPlanRecorded", owner_event_id=f"plan:{doc.name}:{idempotency_key}", members=members,
			payload={"participants": chosen, "lead": lead}, note=cstr(scope).strip(), idempotency_key=idempotency_key)
		decided = conclusion.insert(doc, kind="Verification plan", session=out["session_id"], reason=cstr(basis).strip(), recorded_by=user,
			participants=out["participants"], event=out["event_id"], next_action="Verification")
		number = sequence.next_count(PLAN, {"evaluation_case": doc.name})
		plan = records.insert(frappe.get_doc({
			"doctype": PLAN, "plan_id": f"{doc.name}-VP-{number:02d}", "evaluation_case": doc.name, "version_number": number, "scope": cstr(scope).strip(),
			"basis": cstr(basis).strip(), "participants_json": json.dumps(chosen), "lead_user": lead, "change_reason": cstr(change_reason).strip(),
			"session": out["session_id"], "conclusion": decided.name, "recorded_by": user, "recorded_at": clock.now(), "status": "Current", "report_state": "Draft",
		}))
		notify.tell(doc, chosen, subject=f"Record verification findings for {doc.tender_reference}", message=cstr(scope).strip(), key=f"verify-{plan.name}")
		records.bump(doc, last_committed_event=out["event_id"])
		return records.summary(doc, plan=plan.name, conclusion=decided.name)

	return records.command("RecordVerificationPlan", tender=tender, idempotency_key=idempotency_key, actor=user, payload=payload, body=body)


def _supersede(doc, prior, *, reason: str, idempotency_key: str, actor: str) -> None:
	from kentender_procurement.proceedings.services import record_versions

	if prior.report_state == "Frozen" and prior.report_version:
		with prc_owner.acting(doc.name):
			record_versions.supersede_record(**prc.ref(doc), record_version=prior.report_version, reason=cstr(reason), idempotency_key=prc.key(idempotency_key,
				f"supersede-{prior.name}"), actor=actor)
	prior.status, prior.report_state = "Superseded", "Superseded" if prior.report_state in ("Frozen", "Signed") else prior.report_state
	records.save(prior)
	for name in frappe.get_all(OBSERVATION, filters={"verification_plan": prior.name, "status": "Current"}, pluck="name"):
		records.save(frappe.get_doc(OBSERVATION, name).update({"status": "Superseded"}))


def record_observation(*, tender: str, findings_: str, evidence: list | None = None, idempotency_key: str, user: str) -> dict[str, Any]:
	payload = {"findings": findings_, "evidence": evidence or []}

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		plan = current_plan(doc.name)
		if not plan or plan.status != "Current" or user not in participants(plan):
			raise frappe.DoesNotExistError("Not found")
		findings.require_member(doc, user)
		guards.open_case(doc).raise_if_any()
		if plan.report_state != "Draft":
			fail("EVL_VERSION_CONFLICT", {"reason": "report_frozen"})
		invalid({"findings": "Record your observations."} if not cstr(findings_).strip() else {})
		for name in frappe.get_all(OBSERVATION, filters={"verification_plan": plan.name, "participant_user": user, "status": "Current"}, pluck="name"):
			records.save(frappe.get_doc(OBSERVATION, name).update({"status": "Superseded"}))
		number = sequence.next_count(OBSERVATION, {"verification_plan": plan.name})
		row = records.insert(frappe.get_doc({
			"doctype": OBSERVATION, "observation_id": f"{plan.name}-OBS-{number:02d}", "verification_plan": plan.name, "evaluation_case": doc.name,
			"participant_user": user, "findings": cstr(findings_).strip(), "evidence_json": json.dumps(evidence or []), "recorded_at": clock.now(), "status": "Current",
		}))
		event = prc.owner_event(doc, "VerificationObservation", f"observation:{row.name}", {"plan": plan.name}, idempotency_key=idempotency_key,
			note=cstr(findings_).strip())
		records.bump(doc, last_committed_event=event)
		return records.summary(doc, observation=row.name)

	return records.command("RecordDueDiligence", tender=tender, idempotency_key=idempotency_key, actor=user, payload=payload, body=body)


def observations(plan) -> list[dict[str, Any]]:
	return frappe.get_all(OBSERVATION, filters={"verification_plan": plan.name, "status": "Current"}, fields=["name", "participant_user", "findings",
		"evidence_json", "recorded_at"], order_by="recorded_at asc")


def report_content(doc, plan) -> str:
	lines = [f"Verification report — {doc.tender_reference}", f"Scope: {plan.scope}", f"Basis: {plan.basis}",
		"Participants: " + ", ".join(people.full_name(u) for u in participants(plan)), f"Lead: {people.full_name(plan.lead_user)}"]
	for row in observations(plan):
		lines.append(f"{people.full_name(row.participant_user)} ({row.recorded_at}): {row.findings}")
	return "\n".join(lines)


def send_for_signing(*, tender: str, idempotency_key: str, user: str) -> dict[str, Any]:
	"""SendDueDiligenceForSigning: the lead freezes the completed findings."""
	from kentender_procurement.proceedings.services import record_versions

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		plan = current_plan(doc.name)
		if not plan or plan.status != "Current" or plan.lead_user != user:
			raise frappe.DoesNotExistError("Not found")
		findings.require_member(doc, user)  # due diligence is by eligible members only (§5.4)
		guards.open_case(doc).raise_if_any()
		if plan.report_state != "Draft":
			fail("EVL_VERSION_CONFLICT", {"reason": "already_frozen"})
		missing = [u for u in participants(plan) if u not in {o.participant_user for o in observations(plan)}]
		if missing:
			fail("EVL_REPORT_INCOMPLETE", {"missing_observations": [{"user": u, "name": people.full_name(u)} for u in missing]})
		content = report_content(doc, plan)
		digest = records.digest(content)
		targets = []
		for u in participants(plan):
			slug = u.split("@")[0]
			targets.append({"target_id": f"{plan.name}-P1-{slug}", "target_type": "Verification report page", "target_reference": plan.name, "page_number": 1,
				"target_digest": digest, "required_member": u})
			targets.append({"target_id": f"{plan.name}-SIG-{slug}", "target_type": "Verification report signature", "target_reference": plan.name,
				"target_digest": digest, "required_member": u})
		with prc_owner.acting(doc.name):
			frozen = record_versions.freeze_record(**prc.ref(doc), record_kind="Verification report", owner_reference=plan.name, content=content, targets=targets,
				idempotency_key=prc.key(idempotency_key, "freeze"), actor=user)
		records.save(plan.update({"report_state": "Frozen", "report_version": frozen["record_version"], "report_digest": digest, "frozen_at": clock.now()}))
		notify.tell(doc, participants(plan), subject=f"Review and sign verification report for {doc.tender_reference}", message=plan.scope,
			key=f"verify-sign-{frozen['record_version']}")
		records.bump(doc, last_committed_event=frozen["event_id"])
		return records.summary(doc, plan=plan.name, record_version=frozen["record_version"])

	return records.command("SendDueDiligenceForSigning", tender=tender, idempotency_key=idempotency_key, actor=user, payload={}, body=body)


def my_targets(doc, plan, user: str) -> list[dict[str, Any]]:
	from kentender_procurement.proceedings.services import record_versions

	if not plan or not plan.report_version:
		return []
	missing = {m["target_id"] for m in record_versions.missing_proofs(plan.report_version) if m["required_member"] == user}
	version = frappe.get_doc("Proceeding Minutes Version", plan.report_version)
	return [{"target_id": t.target_id, "target_type": t.target_type, "target_digest": t.target_digest} for t in version.targets
		if t.required_member == user and t.target_id in missing]


def sign(*, tender: str, idempotency_key: str, user: str) -> dict[str, Any]:
	"""SignDueDiligenceReport: the participant's own page and signature targets."""
	from kentender_procurement.proceedings.services import record_versions

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		plan = current_plan(doc.name)
		if not plan or user not in participants(plan):
			raise frappe.DoesNotExistError("Not found")
		findings.require_member(doc, user)  # a conflicted, unavailable or replaced participant cannot sign (§5.4)
		guards.open_case(doc).raise_if_any()
		if plan.report_state != "Frozen":
			fail("EVL_TARGET_CHANGED", {"reason": "not_frozen"})
		results = []
		for target in my_targets(doc, plan, user):
			with prc_owner.acting(doc.name):
				out = record_versions.record_proof(**prc.ref(doc), record_version=plan.report_version, target_id=target["target_id"],
					target_digest=target["target_digest"], action="Initial" if target["target_type"] == "Verification report page" else "Sign",
					idempotency_key=prc.key(idempotency_key, target["target_id"]), actor=user)
			results.append(out)
			if not out.get("ok"):
				fail("EVL_SIGNATURE_UNCONFIRMED", {"target": target["target_id"], "verification_result": out.get("verification_result")})
		if not record_versions.missing_proofs(plan.report_version):
			with prc_owner.acting(doc.name):
				record_versions.complete_record(**prc.ref(doc), record_version=plan.report_version, idempotency_key=prc.key(idempotency_key, "complete"),
					actor=prc.SYSTEM)
			records.save(plan.update({"report_state": "Signed"}))
			chair = roster.chair(doc.name)
			notify.tell(doc, [chair] if chair else [], subject=f"Review verification outcome for {doc.tender_reference}", message=plan.scope,
				key=f"verify-outcome-{plan.name}")
		records.bump(doc)
		return records.summary(doc, plan=plan.name, report_state=plan.report_state)

	return records.command("SignDueDiligenceReport", tender=tender, idempotency_key=idempotency_key, actor=user, payload={}, body=body)


def record_outcome(*, tender: str, bid: str, requirement_key: str, result: str, reason: str, idempotency_key: str, user: str) -> dict[str, Any]:
	"""The committee's conclusion on how verification affects the evaluation;
	a negative result proposes (never substitutes) the next eligible bid."""
	payload = {"bid": bid, "requirement_key": requirement_key, "result": result, "reason": reason}
	discussion.recheck_presence(tender)

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		conclusion.require_recorder(doc, user)
		members = conclusion.collective(doc, idempotency_key)
		plan = current_plan(doc.name)
		if not plan or plan.report_state != "Signed":
			fail("EVL_REPORT_INCOMPLETE", {"reason": "verification_not_signed"})
		findings._requirement(doc, bid, requirement_key)
		fields = {}
		if result not in ("Meets", "Does not meet"):
			fields["result"] = "Record whether the verified requirement is met."
		if not cstr(reason).strip():
			fields["reason"] = "Give the committee's reason."
		invalid(fields)
		out = conclusion.committed(doc, event_type="VerificationOutcome", owner_event_id=f"verification-outcome:{plan.name}", members=members,
			payload={"bid": bid, "requirement": requirement_key, "result": result}, note=cstr(reason).strip(), idempotency_key=idempotency_key)
		decided = conclusion.insert(doc, kind="Verification outcome", session=out["session_id"], reason=reason, recorded_by=user, participants=out["participants"],
			event=out["event_id"], bid=bid, requirement_key=requirement_key, result=result, evidence=[plan.name])
		records.save(plan.update({"status": "Completed"}))
		records.bump(doc, last_committed_event=out["event_id"])
		proposal = None
		if result == "Does not meet":
			table = comparison.compare(doc.name, with_funding=False)
			ranked = sorted([r for r in table["rows"] if isinstance(r["position"], int) and r["bid"] != bid], key=lambda r: r["position"])
			if ranked:
				proposal = {"bid": ranked[0]["bid"], "bidder": ranked[0]["bidder"], "required_checks": "The same verification scope for this bidder."}
		return records.summary(doc, conclusion=decided.name, next_ranked=proposal)

	return records.command("RecordVerificationOutcome", tender=tender, idempotency_key=idempotency_key, actor=user, payload=payload, body=body)
