# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Final acceptance, certificate delivery, the blocked close-out and the close-out correction screens (boards D32, D32-H, D22-P, D11-B, D11-C, D38-P, D38, D38-R, D38-T; CM-CHG-001 v0.8 sections 5.9, 5.21, 10.4, 19.5).

The Accounting Officer's final acceptance is its own screen with its own statement and its own proof; the completion certificate is the head of procurement's, and its delivery to the contractor is a further fact the
head confirms with evidence. A closed contract is corrected only by a reasoned request and a successor decision: the original closure stays, a termination is never reopened here. Everything is read from the records;
nothing is composed on the screen."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import formatdate, getdate

from kentender_contracts.boards import chrome, kit, statements
from kentender_contracts.boards.context import Context, money, when
from kentender_contracts.services import clock, closeout, closure_correction, final_acceptance, issues, picker_sources, records, warranty

CERTIFICATE = "Contract Certificate"


def _long(value: Any) -> str:
	return formatdate(value, "d MMMM yyyy") if value else "—"


def _day(value: Any) -> str:
	return formatdate(value, "d MMM yyyy") if value else "—"


def _today():
	return getdate(clock.now())


def _item(ctx: Context) -> str:
	line = next((l for l in ctx.terms.get("lines", []) if l.get("kind") != "service"), {})
	return (line.get("description") or line.get("item") or "unit").lower()


def _groups(ctx: Context) -> list[list[str]]:
	"""One row for the units first delivered and one for the replacements: how many, and the day their warranty ends (or ended)."""
	groups: dict[bool, list[str]] = {False: [], True: []}
	for unit, row in ctx.position["units"].items():
		if row["status"] == "Accepted":
			groups[bool(row["replaces"])].append(unit)
	out = []
	for replacement, units in groups.items():
		ends = [e for e in (warranty.warranty_ends(ctx.case, u) for u in units) if e]
		if not units or not ends:
			continue
		last = max(ends)
		out.append([f"{'Replacements' if replacement else 'Initial'} {len(units)} — warranty {'ended' if last <= _today() else 'ends'}", _long(last)])
	return out


def _reports(ctx: Context) -> list[str]:
	return [f"Acceptance report {n}" for n in frappe.get_all("Contract Acceptance", filters={"contract_case": ctx.case, "state": "Effective"}, pluck="version_no", order_by="version_no asc")]


def acceptance(ctx: Context) -> dict[str, Any]:
	"""D32: the Accounting Officer reviews the completion facts and signs the final acceptance; D32-H when a completion defect is unresolved (nothing to sign)."""
	found = final_acceptance.evidence(ctx.case)
	if found["defects"]:
		return _blocked_acceptance(ctx, found)
	statement = statements.FINAL_ACCEPTANCE.format(date=_long(clock.now()), clause_and_evidence=f"{found['treatment']} and the evidence listed")
	reports = _reports(ctx)
	b = chrome.base(ctx, "D32", d="D32", name="Final acceptance", title="Record final acceptance", tab="Obligations", next=chrome.next_block(ctx), subj="Final acceptance 1",
		regions=[kit.R("Completion facts", kit.r(["Units accepted", str(found["accepted"])], *_groups(ctx), ["Unresolved completion defects", "None"], ["Final-acceptance treatment", found["treatment"]])),
			kit.R("Final acceptance record", kit.x(statement), kit.r(["Scope", f"Whole contract — {found['accepted']} {_item(ctx)}{'' if found['accepted'] == 1 else 's'}"], ["Remaining obligations", "None"])),
			kit.R("Evidence", kit.lk(*reports, "Warranty history"))],
		p="Sign final acceptance", s2=["Return for correction"], ev=[*reports, "Warranty history"])
	b["actions"]["Sign final acceptance"] = kit.command("SignFinalContractAcceptance")
	b["actions"]["Return for correction"] = kit.dialog("return")
	b["dialogs"]["return"] = kit.dlg("Return for correction", [kit.fl(kit.ta("Reason", "", "reason"))], "Return", command="ReturnContractCloseout", args={"stage": "final acceptance"})
	return b


def _blocked_acceptance(ctx: Context, found: dict[str, Any]) -> dict[str, Any]:
	claim = next(iter(warranty.open_claims(ctx.case)), None)
	if claim is not None:
		facts = warranty.facts(claim)
		ended = getdate(facts["warranty_ends"]) < _today()
		rows = [["Warranty", "Warranty expired; timely claim remains open" if ended else "Warranty running; claim open"], ["Remedy", "Supplier remedy pending"],
			["Defect", f"{facts['fault']} — notified {_day(facts['notice_date'])}"]]
		evidence = [f"Claim {claim.issue_no}", *(["Defect notice"] if issues.thread(claim) else [])]
		subject = f"Agreement {ctx.agreement.version_no} · claim {claim.issue_no}"
	else:
		rows, evidence, subject = [[d["ref"].capitalize(), d["what"]] for d in found["defects"]], [d["ref"].capitalize() for d in found["defects"]], "Final acceptance 1"
	b = chrome.base(ctx, "D32-H", d="D32", name="Final acceptance", title="Record final acceptance", tab="Obligations", next=chrome.next_block(ctx), subj=subject,
		regions=[kit.R("Completion facts", kit.r(*rows)), kit.R("Evidence", kit.lk(*evidence))], p="", s2=[], ev=evidence)
	if claim is not None:
		b["actions"]["View claim"] = kit.route(ctx.case, "obligations", "issue", str(claim.issue_no))
	return b


def delivery(ctx: Context, certificate) -> dict[str, Any]:
	"""D22-P: the certificate is signed and its delivery to the contractor is not yet evidenced. The head of procurement confirms it here with the evidence (an authored form); everyone else sees who the case waits on."""
	mine = bool(ctx.mine("ConfirmCertificateDelivery"))
	fields = [kit.dt("Delivered on", "", "delivered_on"), kit.tx("How it was delivered", "", "method"), kit.tx("Delivery reference", "", "reference"), kit.file("Proof of delivery", "", "evidence")]
	b = chrome.base(ctx, "D22-P", d="D22", name="Completion certificate", title="Confirm contract completion", tab="Obligations", next=chrome.next_block(ctx), subj=f"Completion certificate {certificate.subject_version}",
		regions=[kit.R("Certificate summary", kit.r(["Certificate", f"Certificate {certificate.subject_version}"], ["Signed", when(certificate.signed_at)], ["Delivery to the contractor", "Not yet evidenced"], ["Recipient", ctx.doc.supplier_name]), *([kit.fl(*fields)] if mine else []))],
		p="Confirm delivery" if mine else "", s2=["View delivery status", "View certificate"], ev=["Completion certificate"])
	if mine:
		b["actions"]["Confirm delivery"] = kit.command("ConfirmCertificateDelivery", certificate=certificate.name)
	b["actions"]["View delivery status"] = b["actions"]["View certificate"] = kit.tab("History")
	return b


def blocked_closeout(ctx: Context) -> dict[str, Any]:
	"""D11-B: a timely warranty claim is still open, so the close-out cannot be signed; the claim and the contract's remaining work are one step away."""
	first = warranty.open_claims(ctx.case)[0]
	facts = warranty.facts(first)
	ended = getdate(facts["warranty_ends"]) < _today()
	b = chrome.base(ctx, "D11-B", d="D11", name="Close-out review", title="Close contract", tab="Obligations", next=chrome.next_block(ctx), subj=f"Claim {first.issue_no}",
		regions=[kit.R("Completion review", kit.r(["Warranty", "Warranty expired; timely claim remains open" if ended else "Warranty running; claim open"], ["Open claim", f"Unit {facts['unit']}"], ["Close-out", "Not available while the claim is open"]))],
		p="", s2=[], ev=[f"Claim {first.issue_no}"])
	b["actions"]["View claim"] = kit.route(ctx.case, "obligations", "issue", str(first.issue_no))
	b["actions"]["View remaining obligations"] = kit.tab("Obligations")
	return b


def closed(ctx: Context) -> dict[str, Any]:
	"""D11-C: the closed review as it was signed, with who closed the contract and when; the commitment's closure by the funding owner is its own row (closed, or still pending)."""
	from kentender_contracts.boards import obligations

	row = closure_correction.last_closure(ctx.case)
	b = obligations.d11(ctx, row.name)
	who = ctx.name(row.signer) if row.signer else ""
	b.update(id="D11-C", p="", s2=["View close-out record", "View history"], next=kit.done(f"{who} closed the contract on {when(row.closed_at)}."), subj=f"Closure {row.version_no}")
	b["actions"].pop("Sign close-out", None)
	b["actions"].pop("Return for correction", None)
	b["dialogs"].pop("return", None)
	for block in b["regions"][0]["b"]:
		if block["k"] == "rows":
			block["items"].append(["Funding", closeout.funding_state(ctx.case)])
	b["actions"]["View close-out record"] = b["actions"]["View history"] = kit.tab("History")
	return b


# -- close-out correction -----------------------------------------------------------------------------------------------------------------
def correction_request(ctx: Context, *, correcting=None) -> dict[str, Any]:
	"""D38-P: the head of procurement explains the completion error. Save draft makes no Accounting Officer task; Submit correction makes the exact one."""
	closure = closure_correction.last_closure(ctx.case)
	certificate = frappe.db.get_value(CERTIFICATE, {"contract_case": ctx.case, "kind": "Completion", "state": "Signed"}, "subject_version") or 1
	fields = [kit.sel("Completion fact that was wrong", closure_correction.fact_of(correcting) if correcting else closure_correction.FACTS[0], list(closure_correction.FACTS), "fact"),
		kit.ta("Reason", correcting.reason if correcting else "", "reason"), kit.file("Evidence", "", "evidence"), kit.ro("Proposed disposition", "Reopen for completion")]
	b = chrome.base(ctx, "D38-P", d="D38", name="Close-out correction", title="Request close-out correction", tab="Obligations", next=chrome.form_turn(ctx, "PrepareContractClosureCorrection", "Explain the completion error."),
		subj=f"Closure {closure.version_no}, {_day(closure.closed_at)}", regions=[kit.R("Original closure", kit.r(["Closure", f"Closure {closure.version_no}, {_day(closure.closed_at)}"], ["Affected output", f"Completion certificate {certificate}"])), kit.R("Correction", kit.fl(*fields))],
		p="Submit correction", s2=["Save draft", "Cancel"], ev=[f"Closure {closure.version_no}", f"Completion certificate {certificate}"])
	args = {"correcting": correcting.correction_no} if correcting else {}
	b["actions"]["Submit correction"] = kit.command("PrepareContractClosureCorrection", submit=True, **args)
	b["actions"]["Save draft"] = kit.command("PrepareContractClosureCorrection", submit=False, **args)
	b["actions"]["Cancel"] = kit.tab("Obligations")
	return b


def correction_decision(ctx: Context, row) -> dict[str, Any]:
	"""D38: the Accounting Officer reopens, returns, or (where the bound rule allows) keeps the closure with named surviving work."""
	fact = closure_correction.fact_of(row)
	closure = frappe.get_doc("Contract Closeout", row.closeout)
	blocked = fact in closure_correction.REQUIRED_FACTS
	evidence = [e["label"] for e in closure_correction.evidence(row)]
	review = records.loads(closure.review_json)
	block = [kit.r(["Finding", row.reason], ["Financial total", f"{money(review['claimed_total'], ctx.currency)}, unchanged"]), *([kit.xh("Keep closed with surviving work is unavailable: the bound completion rule requires this evidence.")] if blocked else []),
		kit.lk(f"Closure {closure.version_no}", *evidence, "HOP review")]
	b = chrome.base(ctx, "D38", d="D38", name="Close-out correction", title="Review close-out correction", tab="Obligations", next=chrome.next_block(ctx), subj=f"HOP correction {row.correction_no}", regions=[kit.R("Correction", *block)],
		p="Reopen contract", s2=[kit.disabled("Keep closed with surviving work") if blocked else "Keep closed with surviving work", "Return for correction", "View closure"], ev=[f"Closure {closure.version_no}", *evidence, "HOP review"])
	args = {"correction": row.correction_no}
	b["actions"]["Reopen contract"] = kit.dialog("reopen")
	b["actions"]["Return for correction"] = kit.dialog("return")
	b["actions"]["View closure"] = kit.tab("History")
	b["dialogs"]["reopen"] = kit.dlg("Reopen contract", [kit.fl(kit.ta("Reason", "", "reason"))], "Confirm reopening", command="ReopenContractCloseout", args=args)
	b["dialogs"]["return"] = kit.dlg("Return for correction", [kit.fl(kit.ta("Reason", "", "reason"))], "Return", command="ReturnContractCloseout", args=args)
	if not blocked:
		b["actions"]["Keep closed with surviving work"] = kit.dialog("keep")
		b["dialogs"]["keep"] = kit.dlg("Keep closed with surviving work", [kit.fl(kit.ta("Reason", "", "reason"), kit.tx("Surviving item", "", "survivor_kind"), kit.tx("Reference", "", "survivor_ref"), kit.pick("Owner", "", picker_sources.PERSON, "survivor_owner", context={"role": picker_sources.OWNER}, noun="person"),
			kit.tx("Due event", "", "survivor_due"), kit.ta("Term that lets it survive", "", "survivor_basis"))], "Keep closed", command="ConfirmContractClosure", args=args)
	return b


def reopened(ctx: Context, row, certificate=None) -> dict[str, Any]:
	"""D38-R: the contract is Active again; the closure and the reopening are both kept, and nothing about spending, stock or legal dates was restored. For the head of procurement, whose next step is to confirm the
	certificate's delivery, the delivery form is drawn under the history (the board draws the step but no way to take it)."""
	closure = frappe.get_doc("Contract Closeout", row.closeout)
	regions = [kit.R("History", kit.r([f"Closure {closure.version_no}", "Retained"], [f"Reopening {row.correction_no}", f"Recorded {_day(row.decided_at)}"], ["Spending, stock and legal dates", "Unchanged"]))]
	mine = certificate is not None and bool(ctx.mine("ConfirmCertificateDelivery"))
	if mine:
		regions.append(kit.R("Certificate delivery", kit.fl(kit.dt("Delivered on", "", "delivered_on"), kit.tx("How it was delivered", "", "method"), kit.tx("Delivery reference", "", "reference"), kit.file("Proof of delivery", "", "evidence"))))
	b = chrome.base(ctx, "D38-R", d="D38", name="Close-out correction", title="Review close-out correction", tab="Obligations", next=chrome.next_block(ctx), subj=f"HOP correction {row.correction_no}",
		regions=regions, p="Confirm delivery" if mine else "", s2=["View history"], ev=[])
	if mine:
		b["actions"]["Confirm delivery"] = kit.command("ConfirmCertificateDelivery", certificate=certificate.name)
	b["actions"]["View history"] = kit.tab("History")
	return b


def terminated_source(ctx: Context) -> dict[str, Any]:
	"""D38-T: a terminated contract is not reopened through a close-out correction; correcting a termination is a legal referral."""
	b = chrome.base(ctx, "D38-T", d="D38", name="Close-out correction", title="Review close-out correction", tab="Obligations", next=None,
		regions=[kit.R("Correction", kit.xh("A terminated contract cannot be reopened through close-out correction; this needs a legal referral."))], p="", s2=["View termination", "View settlement"], ev=[])
	b["actions"]["View termination"] = b["actions"]["View settlement"] = kit.tab("History")
	return b
