# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The seventeen mandatory release gates (STD-TPL-001 v0.10 §14.2) and the
plain verification rows the STD Templates surface shows (§11.3).

Owner decision OD5 (26 Sep 2026): gate results and open review items are
recorded evidence only. They never decide whether a site may use a release;
the site's On/Off switch does. There is therefore no owner-approval row and
no approve-the-manifest item.

A gate passes only when every mapped machine check passed and, where the gate
needs a named review, a `Passed` review with evidence is recorded. A missing
review is `Pending`; there is no implicit pass, warning-only or override.
Pure Python: no Frappe import.
"""

from __future__ import annotations

from typing import Any

RESULTS: tuple[str, ...] = ("Passed", "Failed", "Pending")

#: gate_id -> (label, required proof, machine checks, needs a named review)
GATES: dict[str, tuple[str, str, tuple[str, ...], bool]] = {
	"GATE-SOURCE": ("Source", "Exact official source, record, pages and digest", ("C02", "C19"), True),
	"GATE-APPLICABILITY": ("Applicability", "Supported and rejected uses are deterministic", ("C02", "C13"), False),
	"GATE-RESERVATION": ("Reservation", "Every supported reservation category and the County-residents overlay has exact wording, responses, evidence, eligibility mapping, award/reporting disposition and isolated fixture coverage; no designation treated as entitlement", ("C13",), True),
	"GATE-COVERAGE": ("Coverage", "Every source row and form has an approved treatment", ("C03",), True),
	"GATE-DOCUMENTS": ("Documents", "Invitation and issued Tender render completely and reconcile", ("C04", "C05", "C11", "C16"), True),
	"GATE-DATA-OWNERSHIP": ("Data ownership", "Inherited facts cannot be re-entered; officer decisions are finite", ("C03", "C12"), True),
	"GATE-RESPONSES": ("Responses", "Every bidder-editable field has identity, purpose, type and validation", ("C06", "C11"), True),
	"GATE-EVALUATION": ("Evaluation", "Every evaluated response maps to one published group; no hidden criterion", ("C08", "C09"), True),
	"GATE-CONTRACT": ("Contract", "Every applicable accepted response maps to an obligation or explicit N/A", ("C08", "C10"), True),
	"GATE-ADDENDA": ("Addenda", "Identity migration is deterministic and safe", ("C14",), False),
	"GATE-RENDERER": ("Renderer", "Every control, composition and rule is supported by the exact renderer profile", ("C07", "C16"), False),
	"GATE-FIXTURE": ("Fixture", "Document and structured MoH outputs reproduce and reconcile", ("C12", "C15"), False),
	"GATE-USABILITY": ("Usability", "Officer and supplier journeys pass representative-user review", (), True),
	"GATE-INSPECTION": ("Inspection", "Administrator, System Manager, Procurement Officer and Head of Procurement Function can see installed content, coverage, changes, mappings, evidence and blockers through STD Templates", (), True),
	"GATE-COMPILER-PARITY": ("Compiler parity", "Fixture and production paths invoke one deterministic compiler and reproduce the canonical vectors exactly", ("C20",), True),
	"GATE-CHANGE-CONTROL": ("Change control", "Generated preceding-release comparison is complete and its compatibility result is reviewed", ("C21",), True),
	"GATE-CONTENT": ("Content quality", "Labels carry the official wording, every official table has a recorded treatment, every evaluated field has an evaluation rule and each Yes/No answer is read the right way round", ("C22",), False),
	"GATE-INTEGRITY": ("Integrity", "Source, assets, outputs and bundle have immutable digests", ("C01", "C18"), False),
}

GATE_ROW_KEYS: tuple[str, ...] = ("gate_id", "result", "evidence_refs", "checked_by", "checked_at", "message")

#: §11.3 Verification rows -> contributing gates.
VERIFICATION_ROWS: tuple[tuple[str, tuple[str, ...]], ...] = (
	("Official source", ("GATE-SOURCE",)),
	("Tender documents", ("GATE-DOCUMENTS", "GATE-COVERAGE", "GATE-DATA-OWNERSHIP")),
	("Supplier responses", ("GATE-RESPONSES", "GATE-RENDERER", "GATE-USABILITY")),
	("Evaluation and contract mappings", ("GATE-EVALUATION", "GATE-CONTRACT")),
	("Reservation variants", ("GATE-RESERVATION",)),
	("Addendum identity rules", ("GATE-ADDENDA",)),
	("MoH fixture", ("GATE-FIXTURE", "GATE-COMPILER-PARITY")),
)


def evaluate(check_results: dict[str, str], reviews: dict[str, dict[str, Any]], *, machine_checked_by: str, machine_checked_at: str) -> list[dict[str, Any]]:
	"""One row per gate, in §14.2 order."""
	rows = []
	for gate_id, (label, proof, checks, needs_review) in GATES.items():
		failed = [c for c in checks if check_results.get(c) == "Failed"]
		missing = [c for c in checks if check_results.get(c) not in ("Passed", "Failed")]
		review = reviews.get(gate_id)
		evidence = [f"05_review/validation_report.json#{c}" for c in checks]
		checked_by, checked_at = machine_checked_by, machine_checked_at
		if failed:
			result, message = "Failed", f"Machine check(s) {', '.join(failed)} failed."
		elif missing:
			result, message = "Pending", f"Machine check(s) {', '.join(missing)} have no result."
		elif needs_review and not review:
			result, message = "Pending", f"{label}: machine checks passed; the named review is not recorded."
		elif needs_review and review["result"] != "Passed":
			result, message = review["result"], review["message"]
			checked_by, checked_at = review["checked_by"], review["checked_at"]
			evidence += list(review["evidence_refs"])
		elif needs_review:
			result, message = "Passed", review["message"]
			checked_by, checked_at = review["checked_by"], review["checked_at"]
			evidence += list(review["evidence_refs"])
		else:
			result, message = "Passed", f"{label}: every mapped machine check passed."
		if result == "Passed" and not evidence:
			result, message = "Pending", f"{label}: no evidence reference recorded."
		rows.append(
			{
				"gate_id": gate_id,
				"label": label,
				"required_proof": proof,
				"result": result,
				"evidence_refs": evidence,
				"checked_by": checked_by,
				"checked_at": checked_at,
				"message": message,
			}
		)
	return rows


def all_passed(gate_rows: list[dict[str, Any]]) -> bool:
	by_id = {row["gate_id"]: row for row in gate_rows}
	return set(by_id) == set(GATES) and all(row["result"] == "Passed" for row in by_id.values())


#: The named review each gate still needs, in plain words (§11.3: one plain
#: explanation per row; blockers name the next action and its owner).
REVIEW_NAMES: dict[str, str] = {
	"GATE-SOURCE": "official-source confirmation",
	"GATE-APPLICABILITY": "supported-use check",
	"GATE-RESERVATION": "procurement/legal review of the reservation wording, evidence and eligibility treatment",
	"GATE-COVERAGE": "review of the source rows and forms still marked Draft checked",
	"GATE-DOCUMENTS": "procurement/legal review of the rendered Invitation and issued Tender",
	"GATE-DATA-OWNERSHIP": "review of which values are inherited, entered and generated",
	"GATE-RESPONSES": "supplier-experience review of every response field",
	"GATE-EVALUATION": "procurement/legal review of the evaluation groups",
	"GATE-CONTRACT": "procurement/legal review of the contract destinations",
	"GATE-ADDENDA": "addendum identity check",
	"GATE-RENDERER": "renderer support check",
	"GATE-FIXTURE": "fixture reproduction",
	"GATE-USABILITY": "walk-through of the officer and supplier journeys with representative users",
	"GATE-INSPECTION": "confirmation that the four inspecting roles can see this release in STD Templates",
	"GATE-COMPILER-PARITY": "recorded production compiler parity test",
	"GATE-CHANGE-CONTROL": "release owner's review of the comparison with the preceding release",
	"GATE-INTEGRITY": "digest check",
}


def plain_status(row: dict[str, Any]) -> str:
	if row["result"] == "Passed":
		return f"{row['label']} passed."
	if row["result"] == "Failed":
		return f"{row['label']} failed: {row['message']}"
	if "named review" in row["message"]:
		return f"Automated checks passed; awaiting the {REVIEW_NAMES[row['gate_id']]}."
	return f"{row['label']} is not yet checked."


def verification_results(gate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
	by_id = {row["gate_id"]: row for row in gate_rows}
	out = []
	for label, gate_ids in VERIFICATION_ROWS:
		results = [by_id[g]["result"] for g in gate_ids]
		if "Failed" in results:
			result = "Failed"
		elif all(r == "Passed" for r in results):
			result = "Passed"
		elif "Passed" in results:
			result = "Incomplete"
		else:
			result = "Pending"
		open_rows = [by_id[g] for g in gate_ids if by_id[g]["result"] != "Passed"]
		failed = [r for r in open_rows if r["result"] == "Failed"]
		if failed:
			explanation = " ".join(plain_status(r) for r in failed)
		elif open_rows:
			pending_reviews = [REVIEW_NAMES[r["gate_id"]] for r in open_rows]
			explanation = "Automated checks passed; awaiting the " + "; the ".join(pending_reviews) + "."
		else:
			explanation = "Every check for this area passed."
		out.append({"check": label, "result": result, "explanation": explanation, "gate_ids": list(gate_ids)})
	return out


RELEASE_OWNER = "Controlled template-release owner (bnganyi)"
#: Who resolves a gate that is not yet Passed (owner ruling R5: the named
#: release owner; reviews are responsibilities, not system roles).
GATE_OWNERS: dict[str, str] = {
	"GATE-SOURCE": "Procurement/legal reviewer",
	"GATE-APPLICABILITY": RELEASE_OWNER,
	"GATE-RESERVATION": "Procurement/legal reviewer",
	"GATE-COVERAGE": "Procurement/legal reviewer",
	"GATE-DOCUMENTS": "Procurement/legal reviewer",
	"GATE-DATA-OWNERSHIP": "Procurement/legal reviewer",
	"GATE-RESPONSES": "Supplier-experience reviewer",
	"GATE-EVALUATION": "Procurement/legal reviewer",
	"GATE-CONTRACT": "Procurement/legal reviewer",
	"GATE-ADDENDA": RELEASE_OWNER,
	"GATE-RENDERER": RELEASE_OWNER,
	"GATE-FIXTURE": RELEASE_OWNER,
	"GATE-USABILITY": "Supplier-experience reviewer",
	"GATE-INSPECTION": RELEASE_OWNER,
	"GATE-COMPILER-PARITY": RELEASE_OWNER,
	"GATE-CHANGE-CONTROL": RELEASE_OWNER,
	"GATE-INTEGRITY": RELEASE_OWNER,
}


def blockers(gate_rows: list[dict[str, Any]], decisions: list[dict[str, str]], incomplete_variants: list[dict[str, str]]) -> list[dict[str, Any]]:
	"""Every open review item with its owner, recorded as evidence (OD5).
	Failed gates first (§11.4), then Pending gates, open decisions and
	incomplete variants."""
	out: list[dict[str, Any]] = []
	for wanted in ("Failed", "Pending"):
		for row in gate_rows:
			if row["result"] != wanted:
				continue
			if wanted == "Failed":
				summary = plain_status(row)
			elif "named review" in row["message"]:
				review = REVIEW_NAMES[row["gate_id"]]
				summary = review[0].upper() + review[1:] + "."
			else:
				summary = plain_status(row)
			out.append({"summary": summary, "owner": GATE_OWNERS[row["gate_id"]], "gate_id": row["gate_id"], "severity": wanted})
	for item in decisions:
		out.append({"summary": f"Decide: {item['title']} (open issue {item['item']}).", "owner": item["owner"], "gate_id": item["gate_id"], "severity": "Pending"})
	for variant in incomplete_variants:
		name = variant["variant"].replace("_", " ")
		out.append({"summary": f"Complete the {name} reservation variant. {variant['reason']}", "owner": "Procurement/legal reviewer", "gate_id": "GATE-RESERVATION", "severity": "Pending"})
	for index, row in enumerate(out, start=1):
		row["blocker_id"] = f"BLK-{index:02d}"
	return out
