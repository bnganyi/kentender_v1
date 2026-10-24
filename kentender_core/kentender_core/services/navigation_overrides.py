# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The shared-rail seam: how an installed app takes over a Planned placeholder in a shared sidebar (CM-CHG-001 v0.8 FU-CM-58).

KenTender pages share one rail (the Procurement sidebar, whose file belongs to Procurement). Its owner reserves a slot, marked Planned, for a module that is not
built yet. An optional app, upstream of nobody, must not edit that file: a row naming a Page that does not exist on a site without the app would fail
`bench migrate` there. Instead the app declares the hook `kt_navigation_overrides`, a callable returning

    {"<sidebar name>": {"items": {"<existing label>": {"link_to": ..., "link_type": ..., "route_options": ..., "url": ..., "icon": ...}},
                        "routes": ["<desk route>", ...]}}

The rail's owner applies `apply_to_items` when it builds the sidebar at boot, and publishes each of `routes` as a boot alias of that sidebar, so a route of the app shows
the shared rail. Only the link fields of a label that already exists can be replaced: never the label, the type or the availability badge (a replaced item is live, so
its Planned badge goes). With no installed app contributing, nothing changes; a contributor that fails is logged and skipped, never breaking the boot."""

from __future__ import annotations

from typing import Any

import frappe

HOOK = "kt_navigation_overrides"
LINK_FIELDS = ("link_to", "link_type", "route_options", "url", "icon")


def _collected() -> dict[str, dict[str, Any]]:
	merged: dict[str, dict[str, Any]] = {}
	for path in frappe.get_hooks(HOOK) or []:
		try:
			payload = frappe.get_attr(path)() or {}
		except Exception:
			frappe.log_error(title=f"Navigation override failed: {path}")
			continue
		for sidebar, spec in payload.items():
			target = merged.setdefault(sidebar, {"items": {}, "routes": []})
			for label, fields in (spec.get("items") or {}).items():
				target["items"].setdefault(label, {}).update({k: v for k, v in fields.items() if k in LINK_FIELDS})
			target["routes"] += [r for r in (spec.get("routes") or ()) if r not in target["routes"]]
	return merged


def for_sidebar(name: str) -> dict[str, Any]:
	return _collected().get(name, {"items": {}, "routes": []})


def apply_to_items(name: str, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
	"""The rail's items with every contributed replacement applied. A replaced item is live: its availability badge is dropped."""
	replacements = for_sidebar(name)["items"]
	if not replacements:
		return items
	out = []
	for item in items:
		fields = replacements.get((item.get("label") or "").strip())
		if fields:
			item = {**item, **fields}
			item.pop("suffix", None)
		out.append(item)
	return out
