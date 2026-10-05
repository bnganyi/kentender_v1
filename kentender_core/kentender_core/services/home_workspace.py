"""HOME-CHG-001 v0.6 §7 — `GetHomeWorkspace`: Home's one read.

Core cannot import an owner module, so owners register a provider on the
`kt_home_providers` hook (dotted path to ``fn(user=, region=)``). For each
region a provider returns:

* ``None``  the region does not apply to this actor (an owner with no
  oversight responsibility for them);
* a list    the actor's entries from `kentender_core.services.home_entries`,
  possibly empty (applicable, nothing to show);
* or it raises, which is a failed read.

Core merges the lists, then decides everything the page shows: coverage,
complete counts, order, the 14-day Coming up window, de-duplication, paging
and every phrase (`home_time`). A failed provider is never a zero: the region
reads *partial* (rows kept, no total) or *unavailable* (HOME §8). Nothing here
creates, clears or marks read any work (HOME-AC-03); a provider must not either.

Counts are the size of the full, de-duplicated, authorised set the providers
returned, never the number of rows on a page, so they do not change with page
size (HOME-AC-05). Core hands out `PAGE_SIZE` rows at a time behind an opaque
cursor holding the sort position of the last row, so a list that changes
between pages neither repeats nor skips rows.
"""

from __future__ import annotations

import base64
import json
from datetime import date, datetime
from typing import Any, Callable

import frappe
from frappe import _
from frappe.core.doctype.page.page import get_custom_allowed_roles
from frappe.utils import cstr

from kentender_core.services import analytics_workspace
from kentender_core.services import home_entries as he
from kentender_core.services import home_support
from kentender_core.services import home_time as ht
from kentender_core.services import home_viewer as hv

HOOK = "kt_home_providers"
#: Providers a technical reader is read through (a Technical Operator's support issues): technical work, never a business action.
TECHNICAL_HOOK = "kt_home_technical_providers"
PAGE_SIZE = 5

COMPLETE = "complete"
PARTIAL = "partial"
UNAVAILABLE = "unavailable"
NOT_APPLICABLE = "not_applicable"

_LOG = "kentender.home"


# --------------------------------------------------------------------------
# Providers
# --------------------------------------------------------------------------


def _hook_paths(hook: str = HOOK) -> list[str]:
	return list(frappe.get_hooks(hook) or [])


def _load(path: str) -> Callable[..., Any]:
	return frappe.get_attr(path)


def _providers(providers: list[Callable[..., Any]] | None, hook: str = HOOK) -> list[tuple[str, Any]]:
	"""(name, callable or the Exception that stopped it loading). A module that
	is not installed has no hook and so no row at all; one that is configured
	but cannot load is a failure, not an absent module."""
	if providers is not None:
		return [(getattr(fn, "__name__", f"provider-{i}") + f"#{i}", fn) for i, fn in enumerate(providers)]
	resolved: list[tuple[str, Any]] = []
	for path in _hook_paths(hook):
		try:
			resolved.append((path, _load(path)))
		except Exception as error:
			frappe.logger(_LOG).error("home provider could not load | provider=%s", path, exc_info=True)
			resolved.append((path, error))
	return resolved


def _read(user: str, region: str, resolved: list[tuple[str, Any]]) -> list[tuple[str, str, Any]]:
	"""(provider, "ok"|"failed", rows or None) for every provider, one region."""
	outcomes: list[tuple[str, str, Any]] = []
	for name, fn in resolved:
		if isinstance(fn, Exception):
			outcomes.append((name, "failed", None))
			continue
		try:
			rows = fn(user=user, region=region)
			if rows is not None and not isinstance(rows, (list, tuple)):
				raise TypeError(f"{name} returned {type(rows).__name__} for {region}")
			outcomes.append((name, "ok", rows))
		except Exception:
			frappe.logger(_LOG).error("home provider failed | provider=%s region=%s", name, region, exc_info=True)
			outcomes.append((name, "failed", None))
	return outcomes


# --------------------------------------------------------------------------
# Ordering and cursors
# --------------------------------------------------------------------------


def _ts(value: Any) -> float:
	moment = datetime(value.year, value.month, value.day) if isinstance(value, date) and not isinstance(value, datetime) else value
	return (moment - datetime(1970, 1, 1)).total_seconds()


def _sort_key(entry: dict[str, Any], at: datetime) -> list[Any]:
	"""HOME §5. [group, time, identity]: JSON-safe, so it doubles as the cursor."""
	region, ident = entry["region"], "|".join(entry["identity"])
	if region == he.MY_WORK:
		if entry["due"] and ht.is_overdue(entry["due"], at):
			return [0, _ts(entry["due"]), ident]
		if entry["due"]:
			return [1, _ts(entry["due"]), ident]
		return [2, _ts(entry["entered_at"]), ident]
	if region == he.WAITING:
		return [0, _ts(entry["since"]), ident]
	if region == he.OVERSIGHT:
		# Outstanding matters first by oldest recorded since; other disclosed
		# updates newest first.
		return [0, _ts(entry["since"]), ident] if entry["outstanding"] else [1, -_ts(entry["since"]), ident]
	if region == he.COMING_UP:
		return [0, _ts(entry["scheduled_at"]), ident]
	return [0, -_ts(entry["completed_at"]), ident]


def _encode(key: list[Any]) -> str:
	return base64.urlsafe_b64encode(json.dumps(key).encode()).decode()


def _decode(cursor: str) -> list[Any]:
	try:
		key = json.loads(base64.urlsafe_b64decode(cursor.encode()))
		if isinstance(key, list) and len(key) == 3 and isinstance(key[0], int) and isinstance(key[1], (int, float)) and isinstance(key[2], str):
			return key
	except Exception:
		pass
	frappe.throw(_("This page of results is no longer valid. Reload the page."), frappe.ValidationError)


# --------------------------------------------------------------------------
# Destinations
# --------------------------------------------------------------------------


def _page_permitted(root: str, user: str) -> bool:
	"""The destination's first segment is a real Desk Page the viewer's roles
	may open. The owner's record read still rechecks authority and state when
	the page loads (HOME §5, §7)."""
	if not frappe.db.exists("Page", root):
		return False
	allowed = set(frappe.get_all("Has Role", filters={"parent": root, "parenttype": "Page"}, pluck="role"))
	allowed.update(get_custom_allowed_roles("page", root))
	return not allowed or bool(allowed & set(frappe.get_roles(user)))


def _destination_permitted(route: list[str], user: str, memo: dict[str, bool]) -> bool:
	"""A Page route is checked once per root. A Form route (a record that has no Page of its own, such as a Support Issue)
	is allowed when the doctype exists and the viewer may read that record."""
	if route[0] == "Form":
		if len(route) < 3 or not frappe.db.exists("DocType", route[1]):
			return False
		return bool(frappe.has_permission(route[1], "read", doc=route[2], user=user))
	if route[0] not in memo:
		memo[route[0]] = _page_permitted(route[0], user)
	return memo[route[0]]


# --------------------------------------------------------------------------
# One region
# --------------------------------------------------------------------------


def _coverage(outcomes: list[tuple[str, str, Any]]) -> str:
	failed = sum(1 for _name, status, _rows in outcomes if status == "failed")
	answered = sum(1 for _name, status, rows in outcomes if status == "ok" and rows is not None)
	if not failed:
		return COMPLETE if answered else NOT_APPLICABLE
	return PARTIAL if answered else UNAVAILABLE


def _gather(region: str, outcomes: list[tuple[str, str, Any]], user: str, at: datetime, permitted: dict[str, bool]) -> tuple[list[dict[str, Any]], str]:
	"""The region's valid, windowed, de-duplicated, ordered entries and its
	coverage. An entry the owner got wrong is dropped and the region reads
	partial: the page never shows something it cannot stand behind, and never
	claims a total it cannot vouch for."""
	coverage = _coverage(outcomes)
	kept: list[dict[str, Any]] = []
	for name, status, rows in outcomes:
		if status != "ok" or not rows:
			continue
		for raw in rows:
			try:
				he.validate(raw)
				if raw["region"] != region:
					raise ValueError(f"{name} returned a {raw['region']} entry for {region}")
				link = raw.get("link")
				for target in (raw["destination"], link["destination"] if link else None):
					if target and not _destination_permitted(target["route"], user, permitted):
						raise ValueError(f"destination {target['route'][:2]!r} is not something this viewer may open")
			except (ValueError, KeyError, TypeError):
				frappe.logger(_LOG).error("home entry dropped | provider=%s region=%s", name, region, exc_info=True)
				if coverage == COMPLETE:
					coverage = PARTIAL
				continue
			if region == he.COMING_UP and not ht.in_coming_up_window(raw["scheduled_at"], at):
				continue
			if region == he.COMPLETED and not ht.in_completed_window(raw["completed_at"], at):
				continue
			kept.append(raw)
	kept.sort(key=lambda entry: _sort_key(entry, at))
	unique: dict[tuple[str, str, str], dict[str, Any]] = {}
	for entry in kept:
		unique.setdefault(entry["identity"], entry)
	return list(unique.values()), coverage


def _present(entry: dict[str, Any], at: datetime, *, primary: bool) -> dict[str, Any]:
	"""One row exactly as the page draws it. Every phrase is made here."""
	region = entry["region"]
	row = {
		"key": "|".join(entry["identity"]),
		"owner": entry["owner"],
		"module": he.module_label(entry["owner"]),
		"title": entry["title"],
		"reference": entry["reference"],
		"action": entry["action"],
		"reason": entry["reason"],
		"blocked": entry["blocked"],
		"holder": entry["holder"],
		"fact": ht.stated(entry["fact"], entry["fact_at"], at) if entry["fact"] else "",
		"link": entry.get("link"),
		"sentence": entry["sentence"],
		"destination": entry["destination"],
		"primary": primary,
		"timing": "",
		"due": ht.due(entry["due"], at) if entry["due"] else "",
		"badge": "",
		"exact": "",
	}
	if region == he.MY_WORK:
		row["timing"] = ht.entered(entry["entered_verb"], entry["entered_at"], at)
	elif region == he.WAITING:
		row["timing"] = ht.waiting(entry["since"], at)
	elif region == he.OVERSIGHT:
		row["timing"] = ht.outstanding(entry["since"], at) if entry["outstanding"] else ht.entered(_("Updated"), entry["since"], at)
	elif region == he.COMING_UP:
		row["badge"], row["exact"] = ht.coming_up(entry["scheduled_at"], at)
	return row


def _label(region: str, count: int | None) -> str:
	"""The summary column's label beside its figure (HOME §5.1 item 2; boards 21 and 24). Singular for exactly one,
	plural for zero, many and unknown ("Count unavailable" still sits beside "items you're waiting on")."""
	one = count == 1
	if region == he.MY_WORK:
		return _("action for you") if one else _("actions for you")
	if region == he.WAITING:
		return _("item you're waiting on") if one else _("items you're waiting on")
	if region == he.OVERSIGHT:
		return _("record with outstanding matters") if one else _("records with outstanding matters")
	return ""


def _page(region: str, entries: list[dict[str, Any]], coverage: str, cursor: str | None, at: datetime) -> dict[str, Any]:
	keys = [_sort_key(entry, at) for entry in entries]
	start = 0
	if cursor:
		after = _decode(cursor)
		start = sum(1 for key in keys if key <= after)
	page = entries[start : start + PAGE_SIZE]
	shown = start + len(page)
	remaining = len(entries) - shown
	# The summary column's figure: the complete authorised count, or unknown
	# (HOME-AC-05, AC-09). Records you oversee counts records with an
	# outstanding matter only; its other rows are updates, not outstanding.
	count = (sum(1 for entry in entries if entry["outstanding"]) if region == he.OVERSIGHT else len(entries)) if coverage == COMPLETE else None
	return {
		"applicable": coverage != NOT_APPLICABLE,
		"coverage": coverage,
		"count": count,
		"label": _label(region, count),
		# Every row the region can show, for "Showing n of {total}".
		"total": len(entries) if coverage == COMPLETE else None,
		"entries": [_present(entry, at, primary=region == he.MY_WORK and not cursor and index == 0) for index, entry in enumerate(page)],
		"shown": shown,
		"remaining": remaining,
		# More than one page: the footer reads "Showing n of {total}", with Show more while rows remain.
		"paged": start > 0 or remaining > 0,
		# "Show {next_count} more": one left reads "Show 1 more", more than five left reads "Show 5 more".
		"next_count": min(remaining, PAGE_SIZE),
		"next_cursor": _encode(keys[start + len(page) - 1]) if remaining > 0 and page else None,
	}


# --------------------------------------------------------------------------
# The read
# --------------------------------------------------------------------------


def _regions(regions: Any) -> list[str]:
	if regions in (None, "", []):
		return list(he.REGIONS)
	if not isinstance(regions, (list, tuple)) or any(region not in he.REGIONS for region in regions):
		frappe.throw(_("Unknown Home section."), frappe.ValidationError)
	return [region for region in he.REGIONS if region in regions]


def _analytics_link(user: str, at: datetime) -> dict[str, Any]:
	"""The "Procurement Analytics" link (HOME §9): shown only when the viewer's Analytics verdict permits it
	(ANL-CHG-001 v0.8 plan D14). A cheap role check; a failed check hides the link rather than failing Home."""
	try:
		allowed = bool(analytics_workspace.get_access(user, at=at)["allowed"])
	except Exception:
		frappe.logger(_LOG).error("analytics verdict failed", exc_info=True)
		allowed = False
	return {"allowed": allowed, "label": _("Procurement Analytics"), "see_all": _("See all in Procurement Analytics"), "route": ["analytics"]}


def _empty_region(applicable: bool = False) -> dict[str, Any]:
	return {"applicable": applicable, "coverage": NOT_APPLICABLE, "count": None, "label": "", "total": None, "next_count": 0, "entries": [], "shown": 0, "remaining": 0, "paged": False, "next_cursor": None}


def _technical_workspace(user, viewer, updated, wanted, cursors, technical_providers, at) -> dict[str, Any]:
	"""A technical reader has no business entries and no counts (HOME §6). The one exception is technical work given to them
	by name (a Technical Operator's support issues, `kt_home_technical_providers`): My work rows, read through those
	providers only, so no business provider is ever called for them."""
	resolved = _providers(technical_providers, TECHNICAL_HOOK)
	out = {region: _empty_region() for region in wanted}
	base = {
		"state": "ready", "viewer": viewer, "updated": updated, "empty": True, "summary_visible": False,
		"analytics": _analytics_link(user, at), "providers": {"configured": len(resolved), "failed": 0}, "regions": out,
	}
	if not resolved or he.MY_WORK not in wanted:
		return base
	outcomes = _read(user, he.MY_WORK, resolved)
	entries, coverage = _gather(he.MY_WORK, outcomes, user, at, {})
	out[he.MY_WORK] = _page(he.MY_WORK, entries, coverage, cursors.get(he.MY_WORK), at)
	base["providers"] = {"configured": len(resolved), "failed": sum(1 for _n, status, _r in outcomes if status == "failed")}
	base["empty"] = not (out[he.MY_WORK]["entries"] or out[he.MY_WORK]["remaining"])
	return base


def get_workspace(
	user: str,
	*,
	regions: Any = None,
	cursors: dict[str, str] | None = None,
	providers: list[Callable[..., Any]] | None = None,
	technical_providers: list[Callable[..., Any]] | None = None,
	at: datetime | None = None,
) -> dict[str, Any]:
	"""The whole Home read for `user`. `regions` limits it (a retry, or Show
	more with a cursor in `cursors`); `providers` and `technical_providers` replace their hooks, for tests."""
	home_support.reset()
	at = at or ht.now()
	if not hv.is_internal(user):
		return {"state": "denied"}
	wanted = _regions(regions)
	cursors = {region: cursor for region, cursor in (cursors or {}).items() if region in wanted and cursor}
	technical = hv.is_technical_reader(user, at)
	viewer = {
		"greeting": ht.greeting(at),
		"first_name": hv.first_name(user),
		"responsibilities": hv.responsibilities(user, at),
		"technical": technical,
	}
	updated = ht.long_instant(at)

	if technical:
		return _technical_workspace(user, viewer, updated, wanted, cursors, technical_providers, at)

	resolved = _providers(providers)
	# Coming up and Records you oversee drop what My work already shows, so a
	# retry of either still reads My work, without returning it.
	reading = [region for region in he.REGIONS if region in wanted or (region == he.MY_WORK and {he.COMING_UP, he.OVERSIGHT} & set(wanted))]
	permitted: dict[str, bool] = {}
	gathered: dict[str, tuple[list[dict[str, Any]], str]] = {}
	failed_providers: set[str] = set()
	calls = failures = 0
	for region in reading:
		outcomes = _read(user, region, resolved)
		calls += len(outcomes)
		failures += sum(1 for _n, status, _r in outcomes if status == "failed")
		failed_providers.update(name for name, status, _r in outcomes if status == "failed")
		gathered[region] = _gather(region, outcomes, user, at, permitted)

	work_identities = {entry["identity"] for entry in gathered.get(he.MY_WORK, ([], ""))[0]}
	out: dict[str, dict[str, Any]] = {}
	for region in wanted:
		entries, coverage = gathered[region]
		if region in (he.COMING_UP, he.OVERSIGHT):
			entries = [entry for entry in entries if entry["identity"] not in work_identities]
		out[region] = _page(region, entries, coverage, cursors.get(region), at)

	state = "failed" if calls and failures == calls else "ready"
	clean = all(r["coverage"] in (COMPLETE, NOT_APPLICABLE) for r in out.values())
	empty = clean and not any(r["entries"] or r["remaining"] for r in out.values())
	counted_applicable = any(out[region]["applicable"] for region in he.COUNTED if region in out)
	return {
		"state": state,
		"viewer": viewer,
		"updated": updated,
		"empty": empty,
		"summary_visible": counted_applicable and not empty,
		"analytics": _analytics_link(user, at),
		"providers": {"configured": len(resolved), "failed": len(failed_providers)},
		"regions": out,
	}
