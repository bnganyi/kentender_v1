# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Obligations and History tabs: completion, close-out, remaining work and the contract's history (boards D22, D11, D10/D40; CM-CHG-001 v0.8 sections 5.9, 6.3, 19.5)."""

from __future__ import annotations

import frappe
from frappe.utils import cint, formatdate

from kentender_contracts.boards import chrome, kit, statements
from kentender_contracts.boards.context import Context, money, when
from kentender_contracts.services import closeout, events, payment, records, work


def d22(ctx: Context) -> dict:
	"""Confirm contract completion (HOP): the completion certificate for non-complex goods."""
	review = closeout.review(ctx.case)
	accepted = sum(d["accepted"] for d in review["deliveries"])
	history = [f"{a['accepted']} on {formatdate(a['date'], 'd MMMM yyyy')}" for a in _acceptance_dates(ctx)]
	completed = formatdate(ctx.doc.operative_date or frappe.utils.today(), "d MMMM yyyy")
	statement = statements.COMPLETION.format(contract=f"{ctx.doc.contract_id} agreement {ctx.agreement.version_no}", date=completed)
	b = chrome.base(ctx, "D22", d="D22", name="Completion certificate", title="Confirm contract completion", tab="Obligations", next=chrome.next_block(ctx), ev=["Financial reconciliation 1"],
		regions=[kit.R("Certificate summary", kit.r(["Delivered and accepted", f"{accepted} {(ctx.terms.get('lines') or [{}])[0].get('description', '').lower()}"] if accepted else ["Delivered and accepted", "—"],
			["Acceptance", "; ".join(history) or "—"], ["Contracted services", "No contracted service line"], ["Unresolved defects", "None"], ["Final acceptance", "Not required by the issued terms"],
			["Obligations", "All fulfilled" if not review["remaining"] else f"{len(review['remaining'])} remaining"], ["Recipient", ctx.doc.supplier_name]), kit.x(statement), kit.r(["Surviving obligations", "None"]))],
		p="Sign and issue certificate")
	b["actions"]["Sign and issue certificate"] = kit.command("IssueCompletionCertificate")
	return b


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
	b = chrome.base(ctx, "D11", d="D11", name="Close-out review", title="Close contract", tab="Obligations", next=chrome.next_block(ctx), ev=["Completion certificate 1", "Financial reconciliation 1"],
		regions=[kit.R("Completion review", kit.f(["Accepted", str(accepted)], ["Invoiced", money(review["claimed_total"], ctx.currency)], ["Cash confirmed", money(review["settled_total"], ctx.currency)],
			["Balance", money(review["claimed_total"] - review["settled_total"], ctx.currency)]), kit.r(["Warranty", "Runs from each unit’s acceptance"], ["Security", review["security"]], ["Required reporting", "Complete"], ["Completion certificate", "Signed" if cert else "Not signed"])),
			kit.R("Close-out decision", kit.x(decision), kit.r(["Surviving obligations", "None" if not review["remaining"] else f"{len(review['remaining'])} listed"]))],
		p="Sign close-out")
	b["actions"]["Sign close-out"] = kit.command("SignContractCloseout", closeout=closeout_name)
	return b


def obligations(ctx: Context) -> dict:
	"""Remaining obligations (D10) and, for a reader with no personal work, the work register (D40)."""
	internal = ctx.sees("obligations")  # a supplier sees only their own remedies, never the internal work behind them
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
	b = chrome.base(ctx, "D10", d="D10", name="Contract obligations", title="Remaining obligations", tab="Obligations", next=chrome.next_block(ctx), regions=regions, ev=["Agreement 1"], s2=[])
	return b


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
