# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The public supplier portal shell (BDS-CHG-001 v0.8 §10.1 "Supplier Website
shell"; plan owner decision OD-B, D3 of Phase 2C).

One Website page, `kentender_core/www/kt_portal`, serves every public and
supplier route. The route belongs to the app that registers it on the
`kt_portal_surfaces` hook; this module only resolves the path to that
surface, asks the surface's resolver for the verdict and first payload
(KT-STD-001 §3A.1), and projects the shared shell around it:

- the compact header — **KenTender** and **Tenders**, **My bids**,
  **Account**, with the section that owns the path marked current;
- the quiet footer from CFG `GetPublicPortalInformation` — only the links
  the active projection supplies, never a placeholder (BDS §10.7);
- environment notices from the `kt_portal_environment_notices` hook (the
  "Test environment" strip on a simulation site, OD-C).

A surface entry is a dict: `prefix` (for example "/tenders"), `resolver`
(dotted path of `resolve(*, path, query, user) -> dict`), `bundle` (the
surface's JS bundle), optional `css` (static stylesheet paths) and `key`.
A resolver returns `verdict` (`OK`, `NOT_FOUND`, `SIGN_IN`), optional
`redirect`, `title` and `payload` (JSON-serialisable; it becomes the
screen's first paint). Tests may set `frappe.flags.kt_portal_surfaces` to a
list of entries; nothing else sets that flag.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

import frappe
from frappe.utils import cstr

from kentender_core.services import public_portal

SURFACES_HOOK = "kt_portal_surfaces"
NOTICES_HOOK = "kt_portal_environment_notices"
VERDICTS = ("OK", "NOT_FOUND", "SIGN_IN")
#: (key, label, href, owned prefixes) — BDS §10.1 header order.
NAV: tuple[tuple[str, str, str, tuple[str, ...]], ...] = (
	("tenders", "Tenders", "/tenders", ("/tenders",)),
	("my-bids", "My bids", "/my-bids", ("/my-bids",)),
	("account", "Account", "/account", ("/account",)),
)


def normalise(path: str) -> str:
	text = "/" + cstr(path or "").strip().strip("/")
	return text if text != "/" else "/"


def _owns(prefix: str, path: str) -> bool:
	prefix = normalise(prefix)
	return path == prefix or path.startswith(prefix + "/")


def surfaces() -> list[dict[str, Any]]:
	override = frappe.flags.get("kt_portal_surfaces")
	if override is not None:
		return list(override)
	return [entry for entry in (frappe.get_hooks(SURFACES_HOOK) or []) if isinstance(entry, dict)]


def owners() -> list[dict[str, str]]:
	"""Every surface's prefix and key, for the page's in-app navigation to
	apply the same longest-prefix rule as `resolve_surface`."""
	return [{"prefix": normalise(entry["prefix"]), "key": cstr(entry.get("key") or entry["prefix"])} for entry in surfaces() if entry.get("prefix")]


def resolve_surface(path: str) -> dict[str, Any] | None:
	"""The registered surface with the longest prefix that owns `path`."""
	path = normalise(path)
	owners = [entry for entry in surfaces() if entry.get("prefix") and _owns(entry["prefix"], path)]
	return max(owners, key=lambda entry: len(normalise(entry["prefix"]))) if owners else None


def nav(path: str) -> list[dict[str, Any]]:
	path = normalise(path)
	return [{"key": key, "label": label, "href": href, "current": any(_owns(p, path) for p in prefixes)} for key, label, href, prefixes in NAV]


def footer() -> list[dict[str, str]]:
	"""The footer links the active CFG projection supplies, in board order."""
	info = public_portal.get_public_portal_information()
	out: list[dict[str, str]] = []
	support = info.get("support") or {}
	if support.get("email"):
		out.append({"key": "support", "label": cstr(support.get("label") or "Supplier support"), "href": f"mailto:{support['email']}"})
	for link in info.get("links") or []:
		out.append({"key": link["key"], "label": link["label"], "href": link["url"]})
	return out


def support_contact() -> dict[str, str]:
	"""The allowlisted support facts (email, phone, hours) for pages that
	name the support route; empty when CFG supplies none."""
	support = dict(public_portal.get_public_portal_information().get("support") or {})
	support.pop("label", None)
	return support


def environment_notices() -> list[dict[str, str]]:
	out = []
	for path in frappe.get_hooks(NOTICES_HOOK) or []:
		notice = frappe.get_attr(path)()
		if notice and notice.get("label"):
			out.append({"label": cstr(notice["label"]), "text": cstr(notice.get("text"))})
	return out


def sign_in_url(path: str, query: str = "") -> str:
	target = normalise(path) + (f"?{query}" if query else "")
	return f"/login?redirect-to={quote(target, safe='')}"


def resolve(path: str, *, query: dict[str, Any] | None = None, query_string: str = "", user: str | None = None) -> dict[str, Any]:
	"""The whole server-side answer for one portal request: the surface, the
	resolver's verdict and payload, and the shell. A path no surface owns is
	`NOT_FOUND` with no surface."""
	path = normalise(path)
	principal = user or frappe.session.user
	surface = resolve_surface(path)
	result: dict[str, Any] = {"verdict": "NOT_FOUND", "title": "Page not found", "payload": {}}
	if surface:
		answered = frappe.get_attr(surface["resolver"])(path=path, query=dict(query or {}), user=principal) or {}
		verdict = answered.get("verdict") or "OK"
		if verdict not in VERDICTS:
			raise ValueError(f"Portal resolver {surface['resolver']} returned an unknown verdict {verdict!r}.")
		result = {"verdict": verdict, "title": cstr(answered.get("title")), "payload": answered.get("payload") or {}}
		if answered.get("redirect"):
			result["redirect"] = cstr(answered["redirect"])
		elif verdict == "SIGN_IN":
			result["redirect"] = sign_in_url(path, query_string)
	return {
		**result,
		"path": path,
		"surface": {"key": cstr((surface or {}).get("key") or (surface or {}).get("prefix", "")), "bundle": cstr((surface or {}).get("bundle")), "css": list((surface or {}).get("css") or [])},
		"shell": {"nav": nav(path), "footer": footer(), "notices": environment_notices(), "signed_in": principal not in ("", "Guest")},
	}
