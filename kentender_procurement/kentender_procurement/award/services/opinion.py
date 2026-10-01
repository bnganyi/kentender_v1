# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Head of Procurement's professional opinion (AWD-CHG-001 v0.4 §5.2,
§5.3; AWD-AC-003, AC-005, AC-006).

`SaveProfessionalOpinion` keeps a draft (inherited facts never change);
`SignProfessionalOpinion` freezes the exact opinion against the exact report
and obtains HOP's personal proof through the shared signing service. Success
makes the signed opinion immutable and creates the Accounting Officer's task
in the same transaction — "Decide award", or "Decide correction" after a
committed decision. Failed or uncertain signing keeps the draft, is never
shown as signed, and resolves through the same attempt. `ReturnEvaluationReport`
sends a disagreement requiring changed findings to Evaluation before any
committed decision; no opinion is signed merely to return."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, cstr

from kentender_procurement.award.services import checks, clock, guards, issues, notify, people, records, simulation, sources, state
from kentender_procurement.award.services.errors import fail, invalid

CONCLUSIONS = ("Recommend award", "No current recommendation")
SIGNING_LABEL = "Test attestation — not an electronic signature"


def _correction_cycle(doc) -> bool:
	"""After a committed decision (a successor cycle, or a post-decision
	review) the AO task is Decide correction (§5.2)."""
	c = state.cycle(doc)
	return cint(c.number) > 1 or bool(state.committed_decision(doc))


def save(*, award: str, conclusion: str = "", reason: str = "", addressed_issues: str = "", expected_version=None, idempotency_key: str, user: str) -> dict[str, Any]:
	def body() -> dict[str, Any]:
		doc = records.lock(award)
		guards.require_hop(user)
		guards.open_case(doc).raise_if_any()
		records.check_version(doc, expected_version)
		guards.stage(doc, "Opinion")
		guards.cycle_ready(doc)
		invalid({"conclusion": "Choose a conclusion." if conclusion and conclusion not in CONCLUSIONS else ""})
		rep = state.current_report(doc)
		working = state.working_opinion(doc)
		values = {"conclusion": conclusion or "", "reason": cstr(reason).strip(), "addressed_issues": cstr(addressed_issues).strip(), "saved_at": clock.now(),
			"source_report": rep.name, "report_digest": rep.content_digest, "state": "Draft", "signing_attempt": "", "signing_outcome": "", "author": user}
		if working:
			records.update(working, **values)
		else:
			version = records.next_number(state.OPINION, {"award_case": doc.name})
			working = records.new(state.OPINION, opinion_id=f"{doc.name}-OP-{version:02d}", award_case=doc.name, cycle=doc.current_cycle, version=version,
				fixture_namespace=doc.fixture_namespace, **values)
		records.bump(doc)
		return records.summary(state.reload(doc), opinion=working.name, version=working.version)

	return records.command("SaveProfessionalOpinion", case=award, idempotency_key=idempotency_key, actor=user,
		payload={"conclusion": conclusion, "reason": reason, "addressed": addressed_issues, "expected": cstr(expected_version)}, body=body)


def _frozen(opinion, rep) -> str:
	return records.digest({"opinion": opinion.name, "version": opinion.version, "report": rep.name, "report_digest": rep.content_digest,
		"conclusion": opinion.conclusion, "reason": opinion.reason, "addressed": opinion.addressed_issues})


def _attest(user: str, opinion, frozen: str, attempt: str) -> dict[str, Any]:
	forced = cstr(simulation.controls().get("signing_outcome"))
	if forced:
		return {"outcome": {"Unavailable": "Unavailable", "Indeterminate": "Indeterminate", "Rejected": "Rejected"}[forced], "proof_reference": "", "label": ""}
	from kentender_procurement.proceedings.services import signing

	return signing.attest(member=user, target_id=opinion.name, target_digest=frozen, minutes_version="", action="Sign", correlation_id=attempt)


def sign(*, award: str, expected_version=None, idempotency_key: str, user: str) -> dict[str, Any]:
	def body() -> dict[str, Any]:
		doc = records.lock(award)
		guards.require_hop(user)
		guards.open_case(doc).raise_if_any()
		guards.stage(doc, "Opinion")
		guards.cycle_ready(doc)
		opinion = state.working_opinion(doc)
		if not opinion:
			invalid({"conclusion": "Choose a conclusion.", "reason": "Enter the reason."})
		if opinion.state == "Out of date":
			fail("AWD_RECORD_CHANGED", {"reason": "report_changed", "opinion": opinion.name})
		records.check_version(doc, expected_version)
		invalid({"conclusion": "Choose a conclusion." if opinion.conclusion not in CONCLUSIONS else "", "reason": "Enter the reason." if not cstr(opinion.reason).strip() else ""})
		# A source that is incomplete or unverifiable, unconfirmed rules or an
		# unreadable status stop signing (§5.1, V02, V15); an expired validity
		# or a restriction on a positive award does not (§5.2: a factual
		# opinion is signed even when a positive award is blocked).
		blocking = [i for i in issues.holding(doc) if i.subtype in (checks.SOURCE_INCOMPLETE, checks.RULES_UNVERIFIED, checks.STATUS_UNAVAILABLE)]
		if blocking:
			g = guards.Guards()
			for i in blocking:
				code = {checks.SOURCE_INCOMPLETE: "AWD_SOURCE_INCOMPLETE", checks.RULES_UNVERIFIED: "AWD_RULE_UNVERIFIED"}.get(i.subtype, "AWD_STATUS_UNAVAILABLE")
				g.add(code, issue=i.name, reason=i.reason)
			g.raise_if_any()
		if opinion.conclusion == "Recommend award" and not checks.recommendation(doc)["supported"]:
			fail("AWD_NO_SUPPORTED_AWARD", {"reason": checks.recommendation(doc)["reason"]})
		rep = state.report(opinion.source_report)
		frozen = _frozen(opinion, rep)
		attempt = f"{opinion.name}:{frozen[:16]}"
		records.update(opinion, state="Signing", frozen_digest=frozen, signing_attempt=attempt)
		proof = _attest(user, opinion, frozen, attempt)
		if proof.get("outcome") != "Accepted/Verified":
			records.update(opinion, signing_outcome=cstr(proof.get("outcome")))
			checks.open_support_issue(doc, "SignProfessionalOpinion", f"signing:{attempt}", "Restore signing",
				"The professional opinion could not be signed. The draft is saved and the same signing attempt will be completed.")
			records.bump(doc)
			return {**records.summary(state.reload(doc), opinion=opinion.name), "ok": False, "code": "AWD_SIGNATURE_UNAVAILABLE",
				"message": "Signing is unavailable. Your draft has been saved.", "outcome": proof.get("outcome"), "attempt": attempt}
		now = clock.now()
		records.update(opinion, state="Signed", signing_outcome="Accepted/Verified", proof_reference=cstr(proof.get("proof_reference")),
			proof_label=cstr(proof.get("label") or SIGNING_LABEL), signed_at=now)
		checks.support_resolved(f"signing:{attempt}")
		c = state.cycle(doc)
		records.update(c, opinion=opinion.name)
		for i in issues.open_issues(doc, subtype="Returned decision"):
			issues.resolve(i, disposition="Owner correction confirmed", reason="A fresh opinion was signed.", evidence=opinion.name, user=user)
		state.set_stage(doc, "Decision")
		doc = state.reload(doc)
		task = "Decide correction" if _correction_cycle(doc) else "Decide award"
		notify.tell(doc, [issues.ao_for(doc)], subject=f"{task} for {doc.tender_reference}", message=f"Professional opinion {opinion.version} was signed.",
			key=f"signed:{opinion.name}")
		records.audit(doc.name, "SignProfessionalOpinion", user, opinion=opinion.name, digest=frozen, proof=opinion.proof_reference)
		return records.summary(doc, opinion=opinion.name, signed=True, task=task)

	return records.command("SignProfessionalOpinion", case=award, idempotency_key=idempotency_key, actor=user, payload={"expected": cstr(expected_version)}, body=body)


def return_report(*, award: str, reason: str, expected_version=None, idempotency_key: str, user: str) -> dict[str, Any]:
	"""ReturnEvaluationReport: before a committed decision only (§5.3, §5.7)."""

	def body() -> dict[str, Any]:
		doc = records.lock(award)
		guards.require_hop(user)
		guards.open_case(doc).raise_if_any()
		records.check_version(doc, expected_version)
		guards.stage(doc, "Opinion", "Decision")
		guards.cycle_ready(doc)
		invalid({"reason": "Enter the reason." if not cstr(reason).strip() else ""})
		if state.committed_decision(doc):
			fail("AWD_RECORD_CHANGED", {"reason": "decision_committed"})
		rep = state.current_report(doc)
		result = sources.for_case(doc).return_report(delivery=rep.source_delivery, comment=cstr(reason).strip(), idempotency_key=f"awd-return:{idempotency_key}",
			user=user)
		if result.get("ok") is False:
			return {**records.summary(doc), **result, "ok": False}
		records.update(rep, state="Returned")
		for o in state.opinions(doc):
			if o.state in ("Draft", "Signing"):
				records.update(o, state="Out of date")
			elif o.state == "Signed":
				records.update(o, state="Superseded")
		c = state.cycle(doc)
		records.update(c, awaiting_report=1, stage="Opinion")
		for i in issues.open_issues(doc, subtype="Returned decision"):
			issues.resolve(i, disposition="Owner correction confirmed", reason="The report was returned to Evaluation.", evidence=rep.name, user=user)
		state.set_stage(doc, "Opinion")
		records.audit(doc.name, "ReturnEvaluationReport", user, report=rep.name, reason=reason)
		return records.summary(state.reload(doc), returned=rep.name)

	return records.command("ReturnEvaluationReport", case=award, idempotency_key=idempotency_key, actor=user, payload={"reason": reason, "expected": cstr(expected_version)},
		body=body)


def hop_label(user: str) -> str:
	return people.full_name(user)
