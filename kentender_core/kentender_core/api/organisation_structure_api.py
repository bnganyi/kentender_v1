"""AUTH-ADR-001 v1.6 §9.2/§14.1 — whitelisted Organisation structure endpoints.

Thin wrappers over :mod:`kentender_core.services.organisation_structure`, with
explicit signatures (no ``**kwargs``) so Frappe filters the transport fields
(``cmd``/``csrf_token``) out of the call itself rather than forwarding them
into a keyword-only service.

Every guard — administrator, root existence, parent, sibling uniqueness and
concurrency — is applied inside the service on every call. Nothing here trusts
a client-supplied action list, code or version. There is no Procuring Entity
parameter anywhere: one site is one PE.
"""

from __future__ import annotations

from typing import Any

import frappe

from kentender_core.services import organisation_structure as structure


@frappe.whitelist()
def get_organisation_structure(selected: str | None = None) -> dict[str, Any]:
	"""Tree projection, selected-node details and the actions the server allows."""
	return structure.get_organisation_structure(selected=selected or "")


@frappe.whitelist()
def tree_children(
	parent: str | None = None,
	is_root: int | str | bool = False,
	doctype: str | None = None,
	label: str | None = None,
) -> list[dict[str, Any]]:
	"""Child nodes for the Frappe tree control (§14.1: the tree is
	`frappe.ui.Tree`, never a Vue reimplementation). Returns name, stable code
	and status only — never a nested-set internal (AUTH-AC-025)."""
	structure.require_structure_administrator()
	rows = frappe.get_all(
		"Organisation Unit",
		filters={"parent_organisation_unit": parent} if parent else {"parent_organisation_unit": ("is", "not set")},
		fields=["name", "unit_code", "unit_name", "status", "rgt", "lft"],
		order_by="lft asc, unit_name asc",
		limit_page_length=0,
	)
	return [
		{
			"value": row["name"],
			"label": row["unit_name"],
			"unit_code": row["unit_code"],
			"status": row["status"],
			"expandable": (row["rgt"] or 0) - (row["lft"] or 0) > 1,
		}
		for row in rows
	]


@frappe.whitelist()
def get_unit_detail(unit_id: str) -> dict[str, Any]:
	structure.require_structure_administrator()
	return structure.get_unit_detail(unit_id)


@frappe.whitelist()
def add_organisation_unit(
	name: str,
	parent_id: str | None = None,
	idempotency_key: str | None = None,
) -> dict[str, Any]:
	return structure.add_organisation_unit(
		parent_id=parent_id or "",
		name=name,
		idempotency_key=idempotency_key or "",
	)


@frappe.whitelist()
def rename_organisation_unit(
	unit_id: str, name: str, expected_version: str | None = None
) -> dict[str, Any]:
	return structure.rename_organisation_unit(
		unit_id=unit_id, name=name, expected_version=expected_version or ""
	)


@frappe.whitelist()
def set_organisation_unit_active(
	unit_id: str, active: int | str | bool, expected_version: str | None = None
) -> dict[str, Any]:
	# Frappe delivers a boolean over HTTP as the string "0"/"1"/"true"/"false";
	# normalize before the service sees it so a string "0" cannot read truthy.
	if isinstance(active, str):
		active = active.strip().lower() not in ("", "0", "false", "no")
	return structure.set_organisation_unit_active(
		unit_id=unit_id, active=bool(active), expected_version=expected_version or ""
	)
