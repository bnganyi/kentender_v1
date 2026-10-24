# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""HOME-CHG-001 v0.6 section 7 -- Contract Management's feed to Home (owner key `contracts`; CM-CHG-001 v0.8 section 5.10, FU-CM-68).

Registered on the `kt_home_providers` hook; core never imports this app. One function, `entries(*, user, region)`, answers for one actor (never the session user) and only reads: it reuses the stored tasks of
`services/work.py` and the authority filter of `services/audience.py`, so what Home shows is what the contract's own list and boards show, never a second opinion.

- **my_work** -- each live task of the actor on a contract they may read: their turn, or blocked with the hold's reason and holder.
- **waiting** -- the actor's own "waiting" items, naming who the work is with and since when.
- **coming_up** -- a scheduled task that has a verified date (a warranty's end, a security's return); one without a verified date is not shown, because no date is invented.
- **completed** -- the actor's own recorded acts of the recent past (a presentation window, not a period of any law).
- **oversight** -- not a Contract Management concept (None).

Returns None where the region does not apply to the actor, [] where it applies and there is nothing to show. A supplier's people have their own portal and no Home; a failed read raises."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_contracts.boards import chrome
from kentender_contracts.services import audience, clock, people, work
from kentender_core.services import home_entries as he

OWNER = "contracts"
RECENT = 30  # the days Home looks back over: a presentation window, not a legal period

#: The acts Home lists as "recently completed" and how each reads after "You": a recorded event's type -> (the action, what "You ..." says). An event not named here is not the actor's act (the system's and an integration's are not).
COMPLETED = {
	"Signed": ("Signed the agreement", "signed the agreement"),
	"Acceptance report signed": ("Signed an acceptance report", "signed the acceptance report"),
	"Technical certificate signed": ("Signed the technical certificate", "signed the technical certificate"),
	"Certification signed": ("Certified an invoice", "certified the invoice for payment"),
	"Final acceptance recorded": ("Recorded final acceptance", "recorded the final acceptance"),
	"Completion certified": ("Issued the completion certificate", "issued the completion certificate"),
	"Certificate delivered": ("Confirmed delivery of the certificate", "confirmed that the completion certificate reached the contractor"),
	"Contract closed": ("Closed the contract", "closed the contract"),
	"Arrival recorded": ("Recorded a delivery", "recorded a delivery"),
	"Inspection recorded": ("Recorded an inspection", "recorded the inspection"),
	"Interest declared": ("Declared interest", "declared your interest"),
	"Inspectors appointed": ("Appointed the inspectors", "appointed the inspectors"),
	"Payment approved": ("Approved a payment", "approved the payment"),
	"Settlement confirmed": ("Confirmed a settlement", "confirmed the settlement"),
	"Change decided": ("Decided a change", "decided the change"),
}


def _applies(user: str) -> bool:
	found = audience.workspace_audiences(user)
	return bool(found) and found != ["supplier"]


def _title(case: Any) -> str:
	return cstr(case.title or case.supplier_name or case.contract_id)


def _tasks(user: str) -> dict[str, list[dict[str, Any]]]:
	"""The actor's live tasks on the contracts they may read, by contract."""
	cases = sorted(set(frappe.get_all(work.TASK, filters={"holder": user, "state": ["in", list(work.LIVE)]}, pluck="contract_case")))
	found: dict[str, list[dict[str, Any]]] = {}
	for case in cases:
		if not audience.readable(user, case):
			continue
		found[case] = [t for t in work.live(case) if t["holder"].lower() == user.lower()]
	return found


def _route(case: str, command: str, subject: str, lifecycle: str) -> dict[str, Any]:
	return {"route": ["contracts", case, chrome.tab_of(command, subject, lifecycle).lower()]}


def _register(user: str) -> dict[str, list[dict[str, Any]]]:
	out: dict[str, list[dict[str, Any]]] = {he.MY_WORK: [], he.WAITING: [], he.COMING_UP: []}
	for case, tasks in _tasks(user).items():
		doc = frappe.get_doc("Contract Case", case)
		for t in tasks:
			base = dict(owner=OWNER, root=doc.contract_id, action_id=f"{t['command']}|{t['subject']}|{t['version']}", title=_title(doc), reference=doc.contract_id, destination=_route(case, t["command"], t["subject"], doc.lifecycle))
			if t["state"] in ("actionable", "blocked"):
				blocker = t.get("blocker") or {}
				out[he.MY_WORK].append(he.make(region=he.MY_WORK, action=t["title"], blocked=t["state"] == "blocked", reason=cstr(blocker.get("message")), holder=None, entered_at=t["assigned_at"],
					due=t["due"] if t.get("due_verified") else None, **base))
			elif t["state"] == "waiting":
				others = [x for x in work.live(case) if x["subject"] == t["subject"] and x["state"] in ("actionable", "blocked") and x["holder"].lower() != user.lower()]
				if not others:
					continue
				out[he.WAITING].append(he.make(region=he.WAITING, action=t["title"], holder=people.full_name(others[0]["holder"]) or others[0]["holder"], since=t["assigned_at"], **base))
			elif t["state"] == "scheduled" and t.get("due") and t.get("due_verified"):
				out[he.COMING_UP].append(he.make(region=he.COMING_UP, action=t["title"], scheduled_at=t["due"], **base))
	return out


def _completed(user: str) -> list[dict[str, Any]]:
	since = clock.now() - timedelta(days=RECENT)
	rows = frappe.get_all("Contract Event", filters={"actor": user, "event_type": ["in", list(COMPLETED)], "occurred_at": [">=", since]}, fields=["contract_case", "event_type", "occurred_at"], order_by="occurred_at desc", limit=40)
	out = []
	for row in rows:
		if not audience.readable(user, row.contract_case):
			continue
		doc = frappe.get_doc("Contract Case", row.contract_case)
		action, sentence = COMPLETED[row.event_type]
		out.append(he.make(region=he.COMPLETED, owner=OWNER, root=doc.contract_id, action_id=f"{row.event_type}|{row.occurred_at}", title=_title(doc), reference=doc.contract_id, action=action, sentence=sentence, completed_at=row.occurred_at,
			destination={"route": ["contracts", row.contract_case, "history"]}))
	return out


def entries(*, user: str, region: str) -> list[dict[str, Any]] | None:
	if region not in he.REGIONS:
		raise ValueError(f"unknown Home region {region!r}")
	if not user or user == "Guest" or region == he.OVERSIGHT or not _applies(user):
		return None
	if region == he.COMPLETED:
		return _completed(user)
	return _register(user)[region]
