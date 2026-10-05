"""HOME-CHG-001 v0.6 §4 — the transient entry an owner hands to Home.

Not a DocType and not stored: an entry is one response value (HOME §4 "These
are transient response values, not new DocTypes or saved business fields").
An owner builds one with `make()` from facts it already holds; Home never
recomputes a guard, a holder or a deadline (HOME §3).

Identity is owner + root + exact action (§4 "Entry identity"), so the same
work is shown once while two genuinely different actions on one record stay
two entries.

The module label comes from `MODULES`, not from the owner, because the
owners' own labels disagree ("Procurement Planning", "Bid Opening",
"Budget & Funding") and the page needs one name and one icon per module
(HOME-AC-11, KT-STD-001 v1.22 §2.6.11).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from frappe.utils import cstr, get_datetime, getdate

MY_WORK = "my_work"
COMING_UP = "coming_up"
WAITING = "waiting"
OVERSIGHT = "oversight"
COMPLETED = "completed"

REGIONS = (MY_WORK, COMING_UP, WAITING, OVERSIGHT, COMPLETED)
# Regions with a summary column (HOME §5.1 item 2). Coming up and Recently
# completed actions have no count.
COUNTED = (MY_WORK, WAITING, OVERSIGHT)

# Owner key -> the module label the page shows. A module that joins Home later
# (Contract Management) is one more row here.
MODULES = {
	"strategy": "Strategy",
	"budget": "Budget & Funding",
	"needs": "Needs",
	"planning": "Planning",
	"requisitions": "Requisitions",
	"tenders": "Tenders",
	"bid_opening": "Bid opening",
	"evaluation": "Evaluation",
	"award": "Award",
	# Work that has no business module of its own but the Home page must still carry (it was on My Work): a Technical
	# Operator's support issues, and a Supplier Account support officer's suspended accounts.
	"support": "Support issues",
	"suppliers": "Supplier accounts",
}


_SCRIPT_SCHEMES = ("javascript:", "data:", "vbscript:")


def module_label(owner: str) -> str:
	return MODULES[owner]


def _instant(value: Any) -> datetime | date | None:
	"""A datetime stays a datetime, a date stays a date (a date-only deadline
	means the end of that day), a string is read as site time."""
	if value in (None, ""):
		return None
	if isinstance(value, datetime):
		return value
	if isinstance(value, date):
		return value
	text = cstr(value).strip()
	return getdate(text) if len(text) <= 10 else get_datetime(text)


def _destination(value: Any) -> dict[str, Any]:
	options: dict[str, Any] = {}
	if isinstance(value, dict):
		options = dict(value.get("route_options") or {})
		route = value.get("route")
	else:
		route = value
	if not isinstance(route, (list, tuple)) or not route:
		raise ValueError("a Home entry needs a destination route")
	parts = [cstr(part).strip() for part in route]
	for part in parts:
		if not part or "://" in part or part.startswith("/") or part.lower().startswith(_SCRIPT_SCHEMES):
			raise ValueError(f"a Home destination is a Desk route, not {part!r}")
	return {"route": parts, "route_options": options}


def _link(value: Any) -> dict[str, Any] | None:
	"""An owner's one named link beside the record (HOME §9 "Delivered report"): a label and a Desk route of its own."""
	if value in (None, {}):
		return None
	if not isinstance(value, dict) or not cstr(value.get("label")).strip():
		raise ValueError("a Home link needs a label")
	return {"label": cstr(value["label"]).strip(), "destination": _destination(value.get("destination"))}


def _holder(value: Any) -> str:
	if isinstance(value, dict):
		return cstr(value.get("display") or "").strip()
	return cstr(value or "").strip()


def make(
	*,
	region: str,
	owner: str,
	root: str,
	action_id: str,
	title: str,
	action: str,
	destination: Any,
	reference: str = "",
	reason: str = "",
	blocked: bool = False,
	holder: Any = None,
	entered_at: Any = None,
	entered_verb: str = "Received",
	since: Any = None,
	outstanding: bool = False,
	due: Any = None,
	scheduled_at: Any = None,
	completed_at: Any = None,
	sentence: str = "",
	fact: str = "",
	fact_at: Any = None,
	link: dict[str, Any] | None = None,
	source_revision: str = "",
) -> dict[str, Any]:
	"""One validated entry. Raises ValueError when the owner's facts cannot be
	shown honestly, so a defect surfaces in the owner's own test."""
	entry = {
		"region": cstr(region),
		"owner": cstr(owner),
		"root": cstr(root).strip(),
		"action_id": cstr(action_id).strip(),
		"title": cstr(title).strip(),
		"reference": cstr(reference).strip(),
		"action": cstr(action).strip(),
		"reason": cstr(reason).strip(),
		"blocked": bool(blocked),
		"holder": _holder(holder),
		"entered_at": _instant(entered_at),
		"entered_verb": cstr(entered_verb) or "Received",
		"since": _instant(since),
		"outstanding": bool(outstanding),
		"due": _instant(due),
		"scheduled_at": _instant(scheduled_at),
		"completed_at": _instant(completed_at),
		"sentence": cstr(sentence).strip(),
		"fact": cstr(fact).strip(),
		"fact_at": _instant(fact_at),
		"link": _link(link),
		"source_revision": cstr(source_revision),
		"destination": _destination(destination),
	}
	entry["identity"] = (entry["owner"], entry["root"], entry["action_id"])
	validate(entry)
	return entry


def validate(entry: dict[str, Any]) -> None:
	"""Refuse an entry that cannot be shown honestly. Run by `make()` and again
	by Home on everything a provider returns, so a hand-built dict gets no
	shortcut."""
	if not isinstance(entry, dict):
		raise ValueError("a Home entry is a dict")
	region = entry.get("region")
	if region not in REGIONS:
		raise ValueError(f"unknown Home region {region!r}")
	if entry.get("owner") not in MODULES:
		raise ValueError(f"unknown Home owner {entry.get('owner')!r}")
	for field in ("root", "action_id", "title", "action"):
		if not cstr(entry.get(field)).strip():
			raise ValueError(f"a Home entry needs {field}")
	if not isinstance(entry.get("destination"), dict) or not entry["destination"].get("route"):
		raise ValueError("a Home entry needs a destination route")
	if cstr(entry.get("fact")).strip() and not entry.get("fact_at"):
		raise ValueError("a fact needs the instant it happened")
	link = entry.get("link")
	if link and (not cstr(link.get("label")).strip() or not isinstance(link.get("destination"), dict) or not link["destination"].get("route")):
		raise ValueError("a Home link needs a label and a destination route")
	if entry.get("blocked") and not cstr(entry.get("reason")).strip():
		raise ValueError("blocked work must say why")
	needs = {
		MY_WORK: ("entered_at",),
		WAITING: ("since", "holder"),
		OVERSIGHT: ("since",),
		COMING_UP: ("scheduled_at",),
		COMPLETED: ("completed_at", "sentence"),
	}[region]
	for field in needs:
		if not entry.get(field):
			raise ValueError(f"a {region} entry needs {field}")
