# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Combining results (EVL-CHG-001 v0.4 §4.2–§4.3; plan D7; tracker EVL4-506).

A requirement combines its automatic checks, any required evidence
assessment and the human record:

- an automatic **Does not meet** stands: the committee cannot waive a failed
  mandatory condition (§4.3); a suspected rule defect goes to the technical
  route and is recalculated;
- an automatic **Needs review** (free text, an unavailable rule, a disclosed
  matter) is resolved by a member's evidence finding or a committee
  conclusion for that bid and requirement;
- a required evidence assessment keeps an otherwise Meets comparison at
  **Needs review** until a member's evidence finding or a committee
  conclusion records it (a presence check never verifies authenticity);
- an automatic **Needs review** caused by a price-arithmetic discrepancy or a
  missing or unavailable rule has no human resolution (§4.4, "a committee
  explanation cannot substitute for a missing legal or published basis"; §4.2,
  "no automatic default may fill a missing rule"): it stays Needs review until
  the discrepancy or rule is repaired through the owner route and the checks
  are rerun, or the committee records it for a qualified report;
- a member finding saved as Needs review, and an open concern, keep the
  requirement at Needs review until the committee concludes.

A committee conclusion is the latest word on its bid and requirement; a
member's evidence finding is next; the automatic result is never
overwritten. Group: any mandatory failure is Does not meet, otherwise any
unresolved requirement is Needs review, otherwise Meets; unresolved items
are still shown when another check has failed. A bid is Responsive only
when eligibility and technical compliance meet; Not responsive on a
supported mandatory failure; otherwise Needs review."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_evaluation.services import rules

MEETS, FAILS, REVIEW, NA = rules.MEETS, rules.FAILS, rules.REVIEW, rules.NOT_APPLICABLE
ELIGIBILITY, TECHNICAL, FINANCIAL = "EVG-ELIGIBILITY", "EVG-TECHNICAL-COMPLIANCE", "EVG-FINANCIAL"
EXPERIENCE = "RR-EXPERIENCE"
#: Check kinds whose Needs review only the owner route can clear: an arithmetic discrepancy (calculation) or a missing rule (unavailable).
UNSUPPORTED_KINDS = ("calculation", "unavailable")
RULE_LABELS = {
	"RR-DECL-FORM-OF-TENDER": "Form of Tender", "RR-DECL-CITD": "Certificate of independent tender determination", "RR-DECL-SD1": "Not debarred (SD1)",
	"RR-DECL-SD2": "No corrupt or fraudulent practice (SD2)", "RR-DECL-CODE-OF-ETHICS": "Code of ethics", "RR-DECL-CBQ": "Conflict of interest questionnaire",
	"RR-RESERVATION": "Youth reservation", "RR-TENDER-SECURITY": "Tender security", "RR-GOODS-OFFER": "Quantity and delivery",
	"RR-EXPERIENCE": "Comparable experience", "RR-ACCEPTANCE": "Acceptance requirement", "RR-SUBMISSION": "Tender signed by an authorised person",
	"RR-EVIDENCE-MANUFACTURER-AUTHORISATION": "Manufacturer authorisation", "RR-EVIDENCE-DATASHEET": "Product datasheet",
	"RR-EVIDENCE-AFTER-SALES": "Kenya service-centre details", "RR-EVIDENCE-ELIGIBILITY-DOCUMENTS": "Eligibility and registration documents",
}


def requirement_label(rule_id: str, facts: dict[str, Any], group_key: str = "") -> str:
	if rule_id in ("RR-TECHNICAL", "RR-WARRANTY-SUPPORT") and facts.get("label"):
		return cstr(facts["label"])
	if rule_id == "RR-ACCEPTANCE" and facts.get("check_type"):
		return f"Acceptance: {facts['check_type']}"
	return RULE_LABELS.get(rule_id) or cstr(facts.get("label")) or group_key


def _combine(values: list[str]) -> str:
	if FAILS in values:
		return FAILS
	if REVIEW in values:
		return REVIEW
	return MEETS if values else NA


def human_record(case: str) -> dict[tuple[str, str], dict[str, Any]]:
	"""(bid, requirement) → the latest committee conclusion, member evidence
	finding, and whether an open concern or discussion item remains."""
	out: dict[tuple[str, str], dict[str, Any]] = {}
	for c in frappe.get_all("Evaluation Conclusion", filters={"evaluation_case": case, "kind": ("in", ("Resolved finding", "Reply disposition", "Verification outcome"))},
			fields=["evaluation_bid", "requirement_key", "result", "reason", "recorded_at", "kind", "name"], order_by="recorded_at asc, creation asc"):
		if c.evaluation_bid and c.requirement_key and c.result:
			out.setdefault((c.evaluation_bid, c.requirement_key), {})["conclusion"] = c
	for c in frappe.get_all("Evaluation Conclusion", filters={"evaluation_case": case, "kind": "Qualified report"},
			fields=["evaluation_bid", "requirement_key", "reason", "name"]):
		if c.evaluation_bid and c.requirement_key:
			out.setdefault((c.evaluation_bid, c.requirement_key), {})["qualified"] = c
	for f in frappe.get_all("Evaluation Finding", filters={"evaluation_case": case, "status": "Current", "kind": "Evidence finding"},
			fields=["evaluation_bid", "requirement_key", "result", "reason", "author", "recorded_at", "name"], order_by="recorded_at asc, creation asc"):
		out.setdefault((f.evaluation_bid, f.requirement_key), {})["finding"] = f
	for i in frappe.get_all("Evaluation Discussion Item", filters={"evaluation_case": case, "status": "Open"}, fields=["evaluation_bid", "requirement_key", "name"]):
		out.setdefault((i.evaluation_bid, i.requirement_key), {})["open_item"] = i
	return out


def requirement(results: list[dict[str, Any]], human: dict[str, Any]) -> dict[str, Any]:
	"""One requirement's combined result from its automatic results and human record."""
	applicable = [r for r in results if r["applicable"]]
	automatic = _combine([r["result"] for r in applicable]) if applicable else NA
	pending_evidence = any(r["evidence_assessment_required"] and r["result"] == MEETS for r in applicable)
	conclusion, finding = human.get("conclusion"), human.get("finding")
	unsupported = automatic == REVIEW and any(r["check_kind"] in UNSUPPORTED_KINDS and r["result"] == REVIEW for r in applicable)
	basis, reason = "Automatic check", "; ".join(dict.fromkeys(r["reason"] for r in applicable if r["result"] != MEETS)) or \
		(applicable[0]["reason"] if len(applicable) == 1 else "")
	if automatic == FAILS:
		result = FAILS  # never waived by a finding or conclusion (§4.3)
	elif unsupported:
		result = REVIEW  # no member finding or committee conclusion can resolve it (§4.4)
	elif conclusion is not None:
		result, basis, reason = conclusion.result, "Committee conclusion", cstr(conclusion.reason)
	elif finding is not None and finding.result in (MEETS, FAILS):
		result, basis, reason = finding.result, "Member evidence finding", cstr(finding.reason)
	elif finding is not None:
		result, basis, reason = REVIEW, "Member evidence finding", cstr(finding.reason)
	elif automatic == REVIEW:
		result = REVIEW
	elif pending_evidence:
		result, reason = REVIEW, "The offered values have been checked. Supporting evidence needs review."
	else:
		result = automatic
	if human.get("open_item") and result != FAILS and basis != "Committee conclusion":
		result = REVIEW
	return {"result": result, "automatic": automatic, "basis": basis, "reason": reason, "evidence_pending": pending_evidence and finding is None and conclusion is None,
		"qualified": bool(human.get("qualified")), "open_item": bool(human.get("open_item")), "unsupported_basis": unsupported}


def bid_results(case: str, run: str, bid: str, human: dict | None = None) -> dict[str, Any]:
	"""Requirement, group and responsiveness results for one bid in one run."""
	human = human if human is not None else human_record(case)
	rows = frappe.get_all("Evaluation Check Result", filters={"check_run": run, "evaluation_bid": bid}, fields=["name", "group_id", "mapping_id", "requirement_key",
		"requirement_label", "response_id", "field_key", "check_kind", "applicable", "result", "reason", "basis", "evidence_assessment_required", "required_display",
		"offered_display", "calculation_json"], order_by="name asc")
	by_requirement: dict[str, list[dict[str, Any]]] = {}
	for r in rows:
		by_requirement.setdefault(r.requirement_key, []).append(r)
	requirements = []
	for key, results in by_requirement.items():
		combined = requirement(results, human.get((bid, key), {}))
		requirements.append({"requirement_key": key, "label": results[0].requirement_label, "group_id": results[0].group_id, "mapping_id": results[0].mapping_id,
			"checks": results, **combined})
	experience = [r for r in requirements if r["requirement_key"].startswith(EXPERIENCE + "/")]
	if experience:
		requirements = [r for r in requirements if r not in experience] + [_experience(experience, human.get((bid, EXPERIENCE), {}))]
	groups = {}
	for group in (ELIGIBILITY, TECHNICAL, FINANCIAL):
		members = [r for r in requirements if r["group_id"] == group]
		groups[group] = _combine([r["result"] for r in members if r["result"] != NA]) if members else NA
	if groups[ELIGIBILITY] == FAILS or groups[TECHNICAL] == FAILS:
		responsiveness = "Not responsive"
	elif groups[ELIGIBILITY] == MEETS and groups[TECHNICAL] == MEETS:
		responsiveness = "Responsive"
	else:
		responsiveness = REVIEW
	return {"requirements": requirements, "groups": groups, "responsiveness": responsiveness}


def _experience(entries: list[dict[str, Any]], human: dict[str, Any] | None = None) -> dict[str, Any]:
	"""Comparable experience: the published number of qualifying contracts.
	The compiled definition publishes exactly `required_count` entry groups
	(EXPERIENCE-01 … -nn; `reconciliation/rule_reconciliation.md`), so every
	published entry must meet."""
	required = len(entries)
	met = [r for r in entries if r["result"] == MEETS]
	if len(met) >= required:
		result = MEETS
	elif any(r["result"] == FAILS for r in entries):
		result = FAILS
	else:
		result = REVIEW
	combined = {"requirement_key": EXPERIENCE, "label": RULE_LABELS[EXPERIENCE], "group_id": ELIGIBILITY, "mapping_id": "DM-EXPERIENCE",
		"checks": [c for r in entries for c in r["checks"]], "entries": entries, "result": result, "automatic": _combine([r["automatic"] for r in entries]),
		"basis": "Published count", "reason": f"{len(met)} of {required} comparable contracts meet the published conditions.",
		"evidence_pending": any(r["evidence_pending"] for r in entries), "qualified": any(r["qualified"] for r in entries), "open_item": any(r["open_item"] for r in entries),
		"unsupported_basis": any(r["unsupported_basis"] for r in entries)}
	# The committee and members record findings on the combined requirement.
	human = human or {}
	if combined["automatic"] == FAILS or combined["unsupported_basis"]:
		combined["qualified"] = combined["qualified"] or bool(human.get("qualified"))
		return combined
	if human.get("conclusion") is not None:
		c = human["conclusion"]
		combined.update(result=c.result, basis="Committee conclusion", reason=cstr(c.reason), evidence_pending=False)
	elif human.get("finding") is not None:
		f = human["finding"]
		combined.update(result=f.result if f.result in (MEETS, FAILS) else REVIEW, basis="Member evidence finding", reason=cstr(f.reason), evidence_pending=False)
	if human.get("open_item"):
		combined.update(result=REVIEW if combined["result"] != FAILS and combined["basis"] != "Committee conclusion" else combined["result"], open_item=True)
	combined["qualified"] = combined["qualified"] or bool(human.get("qualified"))
	return combined
