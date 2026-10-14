"""The shared record picker's server side: one source registry and one search.

Wherever a reader chooses one person or one record from a list that can grow, the browser
asks this module for a page of matches instead of holding the whole list. This module owns the
mechanics — the registry, clamping, matching, ranking, the near/recent/rest order, the page —
and owns **no eligibility rule**: who may be listed, who may be chosen, and the reason a row is
unavailable belong to the module that owns the choice, which registers a *source* through the
`kt_record_picker_sources` hook (the same pattern as `kt_technical_reference_resolvers`):

	# hooks.py
	kt_record_picker_sources = ["<app>.<module>.picker_sources.sources"]

	# picker_sources.py
	def sources() -> list[dict]:
		return [{"key": "bid_opening.committee_member", "noun": "person", "match": "core",
			"provider": "<app>.<module>.picker_sources.committee_members"}]

	def committee_members(*, query: str, context: dict, actor: str, limit: int) -> list[dict]: ...

Optional wording a source may carry, returned with every search so a screen passes none of it:
`plural` (default the noun with an "s"), `near_title` ("Your department"), `rest_title` ("Everyone
else") and `hint` (one line shown when nothing matches, for example why only some people can be
named here).

`match` says who filters by the reader's text. `"core"`: the provider returns every row the actor
may see and this module matches and ranks them (a bounded set, up to about 2,000 rows).
`"provider"`: the provider filters in the database and returns `(rows, total)`; it must also
supply a `resolver(*, ids, context, actor)` so a saved choice can be shown by name.

A provider row has `id`, `label`, and optionally `detail` (one line beneath the name), `keywords`
(searchable, never shown), `near` (near the reader), `disabled_reason` (listed but not choosable)
and `extra` (a few short facts the screen wants back when the row is chosen, for example a
person's department: never shown by the picker, so a screen need not parse `detail`). Only `id`,
`label`, `detail`, `disabled_reason`, `section` and `extra` ever reach the browser.

The picker is never the authority. The command that saves the choice checks again; a provider
should call the same function the command calls, so the list and the command cannot drift."""

from __future__ import annotations

import json
import re
import unicodedata
from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr

HOOK = "kt_record_picker_sources"
DEFAULT_LIMIT = 20
LIMITS = (20, 50)
QUERY_MAX = 80
CONTEXT_MAX_BYTES = 2048
RECENT_READ = 10
RECENT_SHOWN = 5
RESOLVE_MAX = 50
ID_MAX = 140
EXTRA_KEYS = 8
EXTRA_TEXT = 200
MATCH_MODES = ("core", "provider")
KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_.]*$")


# -- registry ---------------------------------------------------------------------------------


def _source_paths() -> list[str]:
	return list(frappe.get_hooks(HOOK))


def _load() -> list[dict[str, Any]]:
	"""Every registered source, in hook order, duplicates included (`check_sources` reports them)."""
	out: list[dict[str, Any]] = []
	for path in _source_paths():
		out.extend(frappe.get_attr(path)() or [])
	return out


def _source(key: str) -> dict[str, Any]:
	for source in _load():
		if source.get("key") == key:
			return source
	raise frappe.DoesNotExistError("Not found")


def check_sources() -> list[str]:
	"""What is wrong with the registered sources, as readable lines; empty when all is well."""
	problems: list[str] = []
	seen: set[str] = set()
	for source in _load():
		key = cstr(source.get("key"))
		if not KEY_PATTERN.match(key):
			problems.append(f"{key or '(no key)'}: the key must read <module>.<what is chosen>, lower case")
		if key in seen:
			problems.append(f"{key}: registered more than once")
		seen.add(key)
		if not cstr(source.get("noun")).strip():
			problems.append(f"{key}: no noun")
		if source.get("match") not in MATCH_MODES:
			problems.append(f"{key}: match must be one of {MATCH_MODES}, not {source.get('match')!r}")
		for field in ("provider", "resolver"):
			path = source.get(field)
			if not path:
				if field == "resolver" and source.get("match") == "provider":
					problems.append(f"{key}: a source that filters in the database needs a resolver")
				continue
			try:
				if not callable(frappe.get_attr(path)):
					problems.append(f"{key}: {field} {path} is not callable")
			except Exception:
				problems.append(f"{key}: {field} {path} cannot be imported")
		if not source.get("provider"):
			problems.append(f"{key}: no provider")
	return problems


# -- argument hygiene ---------------------------------------------------------------------------


def _json(value: Any) -> Any:
	"""A whitelisted method receives lists and objects as text."""
	if isinstance(value, str):
		try:
			return json.loads(value)
		except ValueError:
			frappe.throw(_("The picker request was not understood."), frappe.ValidationError)
	return value


def _whole(value: Any, default: int) -> int:
	try:
		return int(value)
	except (TypeError, ValueError):
		return default


def _limit(value: Any) -> int:
	size = _whole(value, DEFAULT_LIMIT)
	return size if size in LIMITS else DEFAULT_LIMIT


def _query(value: Any) -> str:
	return cstr(value).strip()[:QUERY_MAX]


def _context(value: Any) -> dict[str, Any]:
	value = _json(value)
	if value in (None, ""):
		return {}
	if not isinstance(value, dict) or len(json.dumps(value)) > CONTEXT_MAX_BYTES:
		frappe.throw(_("The picker request was not understood."), frappe.ValidationError)
	return value


def _id_list(value: Any, most: int) -> list[str]:
	value = _json(value)
	if not isinstance(value, (list, tuple)):
		return []
	out: list[str] = []
	for item in value:
		text = cstr(item).strip()
		if text and len(text) <= ID_MAX and text not in out:
			out.append(text)
	return out[:most]


def _actor() -> str:
	user = frappe.session.user
	if not user or user == "Guest":
		raise frappe.DoesNotExistError("Not found")
	return user


# -- rows, matching and ranking -----------------------------------------------------------------


def _norm(text: Any) -> str:
	decomposed = unicodedata.normalize("NFD", cstr(text))
	return "".join(ch for ch in decomposed if not unicodedata.combining(ch)).casefold()


def words(text: Any) -> list[str]:
	"""The lower-case, accent-free words of a text: what a typed query is matched by."""
	return _words(text)


def _words(text: Any) -> list[str]:
	return re.findall(r"[^\W_]+", _norm(text))


def _extra(raw: Any) -> dict[str, str]:
	"""At most a few short text facts: anything nested, empty or oversized is not carried."""
	if not isinstance(raw, dict):
		return {}
	out: dict[str, str] = {}
	for key, value in raw.items():
		if len(out) >= EXTRA_KEYS:
			break
		if isinstance(value, (str, int, float)) and not isinstance(value, bool):
			out[cstr(key)] = cstr(value)[:EXTRA_TEXT]
	return out


def _row(raw: Any) -> dict[str, Any] | None:
	if not isinstance(raw, dict):
		return None
	row_id, label = cstr(raw.get("id")).strip(), cstr(raw.get("label")).strip()
	if not row_id or not label:
		return None
	keywords = raw.get("keywords") or ""
	if isinstance(keywords, (list, tuple)):
		keywords = " ".join(cstr(k) for k in keywords)
	return {
		"id": row_id,
		"label": label,
		"detail": cstr(raw.get("detail")).strip(),
		"keywords": cstr(keywords),
		"near": bool(raw.get("near")),
		"disabled_reason": cstr(raw.get("disabled_reason")).strip() or None,
		"extra": _extra(raw.get("extra")),
	}


def _rows(raw_rows: Any) -> list[dict[str, Any]]:
	seen: set[str] = set()
	out: list[dict[str, Any]] = []
	for raw in raw_rows or []:
		row = _row(raw)
		if row and row["id"] not in seen:
			seen.add(row["id"])
			out.append(row)
	return out


def _labels(definition: dict[str, Any]) -> dict[str, str]:
	noun = cstr(definition.get("noun")).strip()
	return {
		"noun": noun,
		"plural": cstr(definition.get("plural")).strip() or f"{noun}s",
		"near": cstr(definition.get("near_title")).strip() or "Your department",
		"rest": cstr(definition.get("rest_title")).strip() or "Everyone else",
		"hint": cstr(definition.get("hint")).strip(),
	}


def _out(row: dict[str, Any], section: str) -> dict[str, Any]:
	return {"id": row["id"], "label": row["label"], "detail": row["detail"], "disabled_reason": row["disabled_reason"], "section": section, "extra": row["extra"]}


def _by_name(row: dict[str, Any]) -> tuple[str, str]:
	return _norm(row["label"]), row["id"]


def _rank(row: dict[str, Any], tokens: list[str], typed: str = "") -> int | None:
	"""-1 what was typed is exactly one of the row's keywords (a whole login), 0 the name starts with it, 1 a word of
	the name starts with it, 2 the detail or keywords do; None no match."""
	name_words = _words(row["label"])
	other_words = _words(f"{row['detail']} {row['keywords']}")
	if not all(any(w.startswith(t) for w in name_words) or any(w.startswith(t) for w in other_words) for t in tokens):
		return None
	if typed and typed in {_norm(k) for k in row["keywords"].split()}:
		return -1
	if " ".join(name_words).startswith(" ".join(tokens)):
		return 0
	return 1 if any(w.startswith(tokens[0]) for w in name_words) else 2


def matches(row: dict[str, Any], query: str) -> bool:
	"""Whether a provider row matches what the reader typed, by the same word-start rule search applies in `match: "core"`.
	A source that filters in the database fetches generously on one word and keeps what this accepts."""
	normal = _row(row)
	tokens = _words(query)
	return bool(normal) and (not tokens or _rank(normal, tokens) is not None)


def _ranked(rows: list[dict[str, Any]], tokens: list[str], *, filter_rows: bool, typed: str = "") -> list[dict[str, Any]]:
	ranked: list[tuple[int, tuple[str, str], dict[str, Any]]] = []
	for row in rows:
		rank = _rank(row, tokens, typed)
		if rank is None:
			if filter_rows:
				continue
			rank = 3
		ranked.append((rank, _by_name(row), row))
	ranked.sort(key=lambda item: (item[0], item[1]))
	return [item[2] for item in ranked]


def _before_typing(rows: list[dict[str, Any]], recent_ids: list[str], limit: int) -> list[dict[str, Any]]:
	"""Near the reader, then the reader's recent picks, then everyone else; nobody twice; at most `limit`."""
	by_id = {r["id"]: r for r in rows}
	near = sorted((r for r in rows if r["near"]), key=_by_name)[:limit]
	used = {r["id"] for r in near}
	recent: list[dict[str, Any]] = []
	for rid in recent_ids:
		if rid in by_id and rid not in used and len(recent) < min(RECENT_SHOWN, limit - len(near)):
			recent.append(by_id[rid])
			used.add(rid)
	rest = sorted((r for r in rows if r["id"] not in used), key=_by_name)[: max(0, limit - len(near) - len(recent))]
	return [*(_out(r, "near") for r in near), *(_out(r, "recent") for r in recent), *(_out(r, "rest") for r in rest)]


# -- the two operations -------------------------------------------------------------------------


def _provider_result(result: Any) -> tuple[list[dict[str, Any]], int | None]:
	if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], int):
		return _rows(result[0]), result[1]
	return _rows(result), None


def search(source: str, query: str | None = None, context: Any = None, recent: Any = None, limit: Any = DEFAULT_LIMIT) -> dict[str, Any]:
	"""A page of matches. The actor is the session user; nothing the client sends can change it."""
	actor = _actor()
	definition = _source(cstr(source))
	text, ctx, size = _query(query), _context(context), _limit(limit)
	recent_ids = _id_list(recent, RECENT_READ)
	try:
		rows, provider_total = _provider_result(frappe.get_attr(definition["provider"])(query=text, context=ctx, actor=actor, limit=size))
	except frappe.PermissionError:
		raise frappe.DoesNotExistError("Not found") from None
	tokens = _words(text)
	if not tokens:
		shown = _before_typing(rows, recent_ids, size)
		total = provider_total if provider_total is not None else len(rows)
		return {"rows": shown, "total": max(total, len(shown)), "limit": size, "typed": False, "labels": _labels(definition)}
	filter_rows = definition["match"] == "core"
	ordered = _ranked(rows, tokens, filter_rows=filter_rows, typed=_norm(text))
	total = len(ordered) if filter_rows else (provider_total if provider_total is not None else len(ordered))
	return {"rows": [_out(r, "match") for r in ordered[:size]], "total": max(total, min(len(ordered), size)), "limit": size, "typed": True, "labels": _labels(definition)}


def resolve(source: str, ids: Any = None, context: Any = None) -> dict[str, Any]:
	"""The same rows for ids already chosen, so a saved choice shows its name (and, if it is no longer
	allowed, its reason). An id the actor may not see is dropped."""
	actor = _actor()
	definition = _source(cstr(source))
	wanted, ctx = _id_list(ids, RESOLVE_MAX), _context(context)
	if not wanted:
		return {"rows": []}
	try:
		if definition.get("resolver"):
			rows = _rows(frappe.get_attr(definition["resolver"])(ids=wanted, context=ctx, actor=actor))
		else:
			rows, _total = _provider_result(frappe.get_attr(definition["provider"])(query="", context=ctx, actor=actor, limit=max(LIMITS)))
	except frappe.PermissionError:
		raise frappe.DoesNotExistError("Not found") from None
	keep = {r["id"]: r for r in rows if r["id"] in wanted}
	return {"rows": [_out(keep[i], "match") for i in wanted if i in keep]}


# -- helpers for providers ----------------------------------------------------------------------


def people_near(actor: str, user_ids: list[str]) -> set[str]:
	"""Those of `user_ids` whose home organisation unit is the actor's.

	Core's own staff-home-unit read; the home unit is display information and never authority, so
	this orders suggestions and must never decide who may be chosen."""
	from kentender_core.services import staff_home_unit

	home = staff_home_unit.get_staff_home_organisation_unit(actor)
	unit = cstr(home.get("organisation_unit")) if home.get("state") == staff_home_unit.RECORDED else ""
	if not unit or not user_ids:
		return set()
	return set(frappe.get_all("User", filters={staff_home_unit.FIELD: unit, "name": ("in", list(user_ids))}, pluck="name"))


def person_row(user: str, detail: str = "", *, near: bool = False, disabled_reason: str | None = None, extra: dict[str, Any] | None = None) -> dict[str, Any]:
	"""A provider row for a person: their full name, the login as a hidden keyword."""
	return {"id": user, "label": cstr(frappe.db.get_value("User", user, "full_name")) or user, "detail": detail, "keywords": user, "near": near,
		"disabled_reason": disabled_reason, "extra": extra or {}}
