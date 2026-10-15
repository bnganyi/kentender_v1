# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Obligations and History tabs: completion, close-out, remaining work and the contract's history (boards D22, D11, D10/D40; CM-CHG-001 v0.8 sections 5.9, 6.3, 19.5)."""

from __future__ import annotations

import frappe
from frappe.utils import cint, formatdate

from kentender_contracts.boards import changes, chrome, completion, kit, reports, statements, termination as termination_boards
from kentender_contracts.boards.context import Context, money, when
from kentender_contracts.services import change, clock, closeout, closure_correction, events, final_acceptance, issues, obligations as obligation_service, payment, people, records, reporting, security_actions, termination, warranty, work


def d22(ctx: Context) -> dict:
	"""Confirm contract completion (HOP): the completion certificate for non-complex goods."""
	review = closeout.review(ctx.case)
	accepted = sum(d["accepted"] for d in review["deliveries"])
	history = [f"{a['accepted']} on {formatdate(a['date'], 'd MMMM yyyy')}" for a in _acceptance_dates(ctx)]
	accepted_finally = final_acceptance.current(ctx.case) if final_acceptance.required(ctx.case) else None
	completed = formatdate(accepted_finally.signed_at if accepted_finally is not None and accepted_finally.signed_at else ctx.doc.operative_date or frappe.utils.today(), "d MMMM yyyy")
	statement = statements.COMPLETION.format(contract=f"{ctx.doc.contract_id} agreement {ctx.agreement.version_no}", date=completed)
	final = "Recorded" if review["final_acceptance"].startswith("Recorded") else review["final_acceptance"]
	b = chrome.base(ctx, "D22", d="D22", name="Completion certificate", title="Confirm contract completion", tab="Obligations", next=chrome.next_block(ctx), ev=["Final acceptance 1", "Financial reconciliation 1"] if accepted_finally is not None else ["Financial reconciliation 1"],
		regions=[kit.R("Certificate summary", kit.r(["Delivered and accepted", f"{accepted} {(ctx.terms.get('lines') or [{}])[0].get('description', '').lower()}"] if accepted else ["Delivered and accepted", "—"],
			["Acceptance", "; ".join(history) or "—"], ["Contracted services", "No contracted service line"], ["Unresolved defects", "None"], ["Final acceptance", final],
			["Obligations", "All fulfilled" if not review["remaining"] else f"{len(review['remaining'])} remaining"], ["Recipient", ctx.doc.supplier_name]), kit.x(statement), kit.r(["Surviving obligations", survivors_text(ctx, review)]))],
		p="Sign and issue certificate")
	b["actions"]["Sign and issue certificate"] = kit.command("IssueCompletionCertificate")
	return b


def survivors_text(ctx: Context, review: dict) -> str:
	"""What outlives the closure, in one line each: the item, who owns it and when it falls due."""
	listed = review.get("classified") or []
	return "None" if not listed else "; ".join(f"{c['kind']} — {ctx.name(c['owner']) or c['owner']}, {formatdate(c['due'], 'd MMM yyyy') if str(c['due'])[:2] == '20' else c['due']}" for c in listed)


def may_correct(ctx: Context) -> bool:
	"""The head of procurement asks for a correction of a close-out (the service checks the same)."""
	return people.holds(ctx.user, work.HOP)


def _acceptance_dates(ctx: Context) -> list[dict]:
	out = []
	for row in frappe.get_all("Contract Acceptance", filters={"contract_case": ctx.case, "state": "Effective"}, fields=["lines_json", "decision_at"], order_by="version_no asc"):
		out.append({"accepted": sum(cint(l["accepted"]) for l in records.loads(row.lines_json, [])), "date": row.decision_at})
	return out


def d11(ctx: Context, closeout_name: str) -> dict:
	"""Close contract (the Accounting Officer): the generated review and the exact-version proof."""
	row = frappe.get_doc("Contract Closeout", closeout_name)
	review = records.loads(row.review_json)
	cert = frappe.db.get_value("Contract Certificate", {"contract_case": ctx.case, "kind": "Completion", "state": "Signed"}, "name") or ""
	accepted = sum(d["accepted"] for d in review["deliveries"])
	decision = statements.CLOSEOUT
	running = next((c for c in review["classified"] if c["kind"] == "Warranty"), None)
	certificate_row = closeout.completion_certificate(ctx.case)
	warranty_text = f"Runs until {formatdate(running['due'], 'd MMM yyyy')}" if running else "Ended with no unresolved claim" if any(warranty.warranty_ends(ctx.case, u) for u in ctx.position["units"]) else "Not provided by the issued terms"
	b = chrome.base(ctx, "D11", d="D11", name="Close-out review", title="Close contract", tab="Obligations", next=chrome.next_block(ctx), ev=["Completion certificate 1", "Financial reconciliation 1"],
		regions=[kit.R("Completion review", kit.f(["Accepted", str(accepted)], ["Invoiced", money(review["claimed_total"], ctx.currency)], ["Cash confirmed", money(review["settled_total"], ctx.currency)],
			["Balance", money(review["claimed_total"] - review["settled_total"], ctx.currency)]), kit.r(["Warranty", warranty_text], ["Security", review["security"]], ["Required reporting", "Complete"], ["Completion certificate", f"Certificate {certificate_row.subject_version}" if certificate_row is not None else "Not signed"])),
			kit.R("Close-out decision", kit.x(decision), kit.r(["Surviving obligations", survivors_text(ctx, review) if not review["remaining"] else f"{len(review['remaining'])} remaining"]))],
		p="Sign close-out", s2=["Return for correction"])
	b["actions"]["Sign close-out"] = kit.command("SignContractCloseout", closeout=closeout_name)
	b["actions"]["Return for correction"] = kit.dialog("return")
	b["dialogs"]["return"] = kit.dlg("Return for correction", [kit.fl(kit.ta("Reason", "", "reason"))], "Return", command="ReturnContractCloseout", args={"stage": "close-out"})
	return b


def obligations(ctx: Context) -> dict:
	"""Remaining obligations (D10) and, for a reader with no personal work, the work register (D40)."""
	internal = ctx.sees("obligations")  # a supplier sees only their own remedies, never the internal work behind them
	closed = _closed(ctx) if ctx.doc.lifecycle == "Closed" and internal and not ctx.neutral else None  # a reader with no personal work keeps the register
	if closed is not None:
		return closed
	remaining = closeout.remaining_obligations(ctx.case) if ctx.doc.lifecycle == "Active" and internal else []
	regions = []
	if remaining:
		regions.append(kit.R("Remaining obligations", kit.t(["What", "Kind", "Held by"], [[r["what"], r["kind"], r["holder"]] for r in remaining])))
	elif ctx.doc.lifecycle == "Active" and internal:
		regions.append(kit.R("Remaining obligations", kit.xh("Nothing stands between this contract and completion.")))
	lead = ctx.lead
	others = [t for t in ctx.tasks if not (lead and t["task_id"] == lead["task_id"] and lead["holder"].lower() == ctx.user.lower())]
	shown = others if (ctx.neutral and internal) else [t for t in others if t["holder"].lower() == ctx.user.lower()]
	if shown:
		state = {"actionable": "Your turn", "blocked": "Blocked", "waiting": "Waiting", "scheduled": "Scheduled"}
		regions.append(kit.R("Work register" if ctx.neutral else "Other work", kit.t(["Task", "State", "Due", "Responsible person", "Action"],
			[[t["title"], state[t["state"]], when(t["due"]) if t["due"] and t["due_verified"] else "Not established", ctx.name(t["holder"]), "@Open"] for t in shown])))
	if not regions:
		regions.append(kit.R("Remaining obligations", kit.xh("There is no remaining work on this contract.")))
	if internal or ctx.doc.lifecycle == "Active":
		if frappe.db.exists("Contract Change", {"contract_case": ctx.case}):
			regions.append(changes.register(ctx))
	listed = issues_region(ctx)
	if listed is not None:
		regions.append(listed)
	filed = reports_region(ctx) if internal else None
	if filed is not None:
		regions.append(filed)
	if internal:
		held = [o for o in obligation_service.all_for(ctx.case) if o.state in ("Needs review", "Open") and o.kind != "Progress report"]
		if held:
			regions.append(kit.R("Duties", kit.t(["Duty", "Status", "Due", "Owner", ""], [[f"{o.kind}: {o.trigger_event}", o.state, o.due_basis if not o.due_at else when(o.due_at), ctx.name(o.owner_user), "@Review publication" if o.kind == "Publication" else ""] for o in held])))
	effective = change.latest_pending(ctx.case) if internal else None
	if effective is not None:  # the term is in force but the order or the funding update is not: spending that depends on it waits (D34-H)
		return changes.effective_pending(ctx, effective)
	ended = termination.live(ctx.case) if internal else None
	if ended is not None and ended.state in ("Approved", "Notice delivered", "Effective", "Settlement prepared"):
		return termination_boards.pending(ctx, ended)  # D20-P / D20-T: what the terminated contract is waiting on
	if ended is not None and ended.state == "Settled":
		return termination_boards.settled(ctx, ended)  # D39-C
	b = chrome.base(ctx, "D10", d="D10", name="Contract obligations", title="Remaining obligations", tab="Obligations", next=chrome.next_block(ctx), regions=regions, ev=["Agreement 1"], s2=[])
	if ctx.mine("PrepareContractCloseout"):  # a returned final acceptance or review: the head sends it back once the evidence is right
		b["p"] = "Send back for review"
		b["actions"]["Send back for review"] = kit.command("PrepareContractCloseout")
	_entries(ctx, b)
	return b


def _closed(ctx: Context):
	"""A closed contract's Obligations tab: the correction in progress where there is one (D38-P for the head, D38 for the Accounting Officer, D38-R after a reopening), else the closure (D11-C)."""
	live = closure_correction.live(ctx.case)
	if live is not None and live.state == "Submitted" and ctx.mine("ConfirmContractClosure"):
		return completion.correction_decision(ctx, live)
	if live is not None and live.state in ("Draft", "Returned") and ctx.mine("PrepareContractClosureCorrection"):
		return completion.correction_request(ctx, correcting=live)
	b = completion.closed(ctx)
	if may_correct(ctx) and live is None:
		b["s2"].append("Request close-out correction")
		b["actions"]["Request close-out correction"] = kit.route(ctx.case, "obligations", "request-correction")
	_entries(ctx, b)
	return b


def issues_region(ctx: Context):
	"""The contract's issues and warranty claims, each openable by its number."""
	rows = [issues.get(ctx.case, n) for n in frappe.get_all("Contract Issue", filters={"contract_case": ctx.case}, pluck="issue_no", order_by="issue_no asc")]
	if not rows:
		return None
	return kit.R("Issues", kit.t(["Issue", "Kind", "Status", "Reply by"], [[f"@Issue {r.issue_no}", r.kind, r.state, str(r.reply_by or "—")] for r in rows]))


def may_manage(ctx: Context) -> bool:
	"""The people who may record a warranty claim or report a matter: the contract's owner, its coordinator or a preparer (the service makes the same check)."""
	owner = (issues.owner_of(ctx.case) or "").lower()
	return bool(ctx.can_prepare or ctx.user.lower() == owner or people.holds(ctx.user, "Contract coordination", ctx.doc.managing_unit or ""))


def reports_region(ctx: Context):
	"""The period reports that cover this contract, each openable by its period: where the head finds what was submitted."""
	rows = reporting.for_case(ctx.case)
	if not rows:
		return None
	return kit.R("Reports", kit.t(["Report", "Period", "Status"], [[f"@{reporting.TYPES[r.report_type]['title']} {reporting.label_of(r.report_type, r.period_start.date() if hasattr(r.period_start, 'date') else r.period_start)}", reporting.label_of(r.report_type, r.period_start.date() if hasattr(r.period_start, 'date') else r.period_start), r.state] for r in rows]))


def _entries(ctx: Context, b: dict) -> None:
	"""What a person may start from the Obligations tab: a change, a warranty claim, a termination, a security claim or replacement. Each is offered only to who may do it, and only when it can be done."""
	offered: list[tuple[str, tuple[str, ...]]] = []
	active = ctx.doc.lifecycle == "Active"
	if active and change.can_request(ctx.case, ctx.user) and not change.open_change(ctx.case):
		offered += [("Request delivery extension", ("request-extension",)), ("Request quantity change", ("request-quantity",))]
	if may_manage(ctx) and ctx.doc.lifecycle in ("Active", "Closed") and ctx.position["units"]:
		offered.append(("Record a warranty claim", ("claim-warranty",)))
	if ctx.can_prepare and active and termination.live(ctx.case) is None:
		offered.append(("Request termination", ("request-termination",)))
	if ctx.can_prepare and ctx.doc.lifecycle in ("Active", "Terminated") and security_actions.operative(ctx.case):
		if security_actions.live_claim(ctx.case) is None:
			offered.append(("Request security claim", ("request-security-claim",)))
		offered.append(("Record replacement security", ("record-replacement",)))
	for label, route in offered:
		b["s2"].append(label)
		b["actions"][label] = kit.route(ctx.case, "obligations", *route)
	b["actions"]["Review publication"] = kit.route(ctx.case, "obligations", "publication")
	for r in reporting.for_case(ctx.case):
		start = r.period_start.date() if hasattr(r.period_start, "date") else r.period_start
		b["actions"][f"{reporting.TYPES[r.report_type]['title']} {reporting.label_of(r.report_type, start)}"] = kit.route(ctx.case, "obligations", "report", r.name)
	for n in frappe.get_all("Contract Issue", filters={"contract_case": ctx.case}, pluck="issue_no"):
		b["actions"][f"Issue {n}"] = kit.route(ctx.case, "obligations", "issue", str(n))


def operations(ctx: Context) -> dict:
	"""Pending operations for the technical operator who restores them (the original attempt is read first, never repeated with a fresh signature)."""
	from kentender_contracts.services import intents

	rows = [[op["kind"], op["subject"], f"!{op['state']}", op["recovery_owner"]] for op in intents.pending(ctx.case)]
	b = chrome.base(ctx, "D10-O", d="D10", name="Contract operations", title="Restore contract operation", tab="Obligations", next=chrome.next_block(ctx),
		regions=[kit.R("Operations that did not complete", kit.t(["Operation", "Subject", "State", "Recovery owner"], rows) if rows else kit.xh("Every operation has completed."))], p="Restore operation" if rows else "")
	if rows:
		b["actions"]["Restore operation"] = kit.command("RestoreContractOperation")
	return b


def history(ctx: Context) -> dict:
	rows = [[when(e["at"]), e["type"], ctx.name(e["actor"]) or e["actor"], e["summary"]] for e in events.history(ctx.case)]
	return chrome.base(ctx, "D41", d="D41", name="History", title="History", tab="History", next=chrome.next_block(ctx), regions=[kit.R("History", kit.t(["When", "Event", "By", "What happened"], rows) if rows else kit.xh("Nothing has been recorded yet."))], ev=[])
