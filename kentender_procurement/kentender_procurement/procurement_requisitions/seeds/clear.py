# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 — clear Requisitions fixture rows. Wired into
`kentender_core.seeds.kentender_mvp_v1.clear.purge_kentender_playwright_data`
(imported lazily there, per its own note) with the exact signature that
caller expects.

Requisitions rows carry no `fixture_namespace` column (D5 predates that
column on this module's doctypes); "canonical" ownership here means rows
tied to the two named MOH Plan Items (§16.1), and "playwright" ownership
means rows tied to the Playwright fixture's own reserved plan items, once
`playwright_ui_fixtures.py` exists. Until then the playwright branch is a
visible no-op rather than a silent one.
"""

from __future__ import annotations

from typing import Any

import frappe

from kentender_core.utils.raw_delete import delete_rows
from kentender_procurement.procurement_requisitions.seeds.kentender_mvp_v1 import (
	COMBINED_ITEM_TITLE,
	SINGLE_ITEM_TITLE,
	_plan_item_id,
)

_DOCTYPES = (
	"Requisition Event", "Requisition Decision", "Requisition Task", "Authorised Requisition Handoff",
	"Requisition Version", "IT Equipment Requirement Package Version", "IT Equipment Requirement Package",
	"Procurement Requisition", "Requisition Command Journal",
)


def _consumed_by_a_removed_tender(root_name: str) -> bool:
	handoff = frappe.db.get_value("Authorised Requisition Handoff", {"requisition": root_name, "consumed_at": ("is", "set")}, ["tender"], as_dict=True)
	return bool(handoff) and not (handoff.tender and frappe.db.exists("Tender", handoff.tender))


def _delete_for_plan_items(plan_item_ids: list[str], *, cross_module_rebuild: bool = False) -> dict[str, int]:
	"""`cross_module_rebuild`: only `canonical.clear_canonical_modules` passes
	it — the one caller that clears Planning and Budget in the same
	transaction straight after. There, a root whose handoff was consumed by a
	Tender the Tenders stage has already removed may go even though its
	reservation is still Active: REQ-CHG-001 v1.11 has no command to release
	a consumed handoff, and the Budget and Planning clears remove the
	reservation and drawdown rows next. Everywhere else the guard holds."""
	plan_item_ids = [p for p in plan_item_ids if p]
	roots = frappe.get_all("Procurement Requisition", filters={"plan_item_id": ("in", plan_item_ids or ("",))}, pluck="name")
	for root_name in roots:
		root = frappe.db.get_value("Procurement Requisition", root_name, ["current_state", "requisition_reference"], as_dict=True)
		if root.current_state != "Authorised":
			continue
		# The label alone is not the ground truth this build learned to
		# distrust (the "wipe after authorise" hazard): check the real
		# cross-app position. A reservation still Active means real Budget/
		# Planning state would be orphaned by deleting the local rows now.
		if frappe.db.exists("Funding Reservation", {"calling_module": "Procurement Requisitions", "caller_reference": root.requisition_reference, "status": "Active"}):
			if cross_module_rebuild and _consumed_by_a_removed_tender(root_name):
				continue
			frappe.throw(
				f"{root_name} is Authorised with an Active Budget reservation — clearing it directly would "
				"orphan Planning's drawdown and Budget's reservation. Revoke it first through "
				"authorise.revoke_unconsumed_authorisation()."
			)
	return _delete_roots(roots)


def _delete_roots(roots: list[str]) -> dict[str, int]:
	"""These Requisitions and every row of this module that hangs off them.
	No guard: callers decide which roots may go."""
	deleted: dict[str, int] = {}
	packages = frappe.get_all("IT Equipment Requirement Package", filters={"requisition": ("in", roots or ("",))}, pluck="name")
	package_versions = frappe.get_all("IT Equipment Requirement Package Version", filters={"package": ("in", packages or ("",))}, pluck="name")
	versions = frappe.get_all("Requisition Version", filters={"requisition": ("in", roots or ("",))}, pluck="name")
	tasks = frappe.get_all("Requisition Task", filters={"requisition": ("in", roots or ("",))}, pluck="name")

	def delete(doctype: str, names: list[str]) -> None:
		if names:
			delete_rows(doctype, {"name": ("in", names)})
		deleted[doctype] = deleted.get(doctype, 0) + len(names)

	handoffs = frappe.get_all("Authorised Requisition Handoff", filters={"requisition": ("in", roots or ("",))}, pluck="name")
	# Journal entries for documents deleted here (e.g. a Tender's
	# RecordHandoffConsumption on the handoff) would otherwise replay a stale
	# result into the next run that reuses the same idempotency key.
	delete("Requisition Command Journal", frappe.get_all("Requisition Command Journal", filters={"document_name": ("in", (roots + handoffs + versions) or ("",))}, pluck="name"))
	delete("Requisition Decision", frappe.get_all("Requisition Decision", filters={"task": ("in", tasks or ("",))}, pluck="name"))
	delete("Requisition Task", tasks)
	delete("Authorised Requisition Handoff", handoffs)
	delete("Requisition Version", versions)
	delete("IT Equipment Requirement Package Version", package_versions)
	delete("IT Equipment Requirement Package", packages)
	delete("Requisition Event", frappe.get_all("Requisition Event", filters={"requisition": ("in", roots or ("",))}, pluck="name"))
	delete("Procurement Requisition", roots)
	return deleted


def requisition_rows_to_clear() -> dict[str, list[str]]:
	"""Every Requisition that is not on one of the canonical MOH Plan Items
	(the same "tied to the canonical item" rule the rest of this module
	uses). Found 26 Sep 2026: a test world's Authorised Requisition whose
	plan had gone survived every reseed. Read-only."""
	from kentender_procurement.procurement_requisitions.seeds.kentender_mvp_v1 import canonical_plan_item_ids

	keep = set(canonical_plan_item_ids())
	roots = [row.name for row in frappe.get_all("Procurement Requisition", fields=["name", "plan_item_id"]) if row.plan_item_id not in keep]
	return {"Procurement Requisition": roots} if roots else {}


def clear_stray_requisitions() -> dict[str, Any]:
	"""The canonical seed's `reset`: remove `requisition_rows_to_clear()`.
	Their Budget reservations are Budget's strays (the canonical clear
	removes any reservation not stamped for the canonical Requisition)."""
	return {"ok": True, "deleted": _delete_roots(requisition_rows_to_clear().get("Procurement Requisition", []))}


def clear_requisition_fixture_rows(
	*, include_canonical: bool = False, include_playwright: bool = True
) -> dict[str, Any]:
	deleted: dict[str, int] = {}
	if include_canonical:
		from kentender_procurement.procurement_requisitions.seeds.kentender_mvp_v1 import canonical_plan_item_ids

		plan_items = canonical_plan_item_ids()
		for doctype, count in _delete_for_plan_items(plan_items).items():
			deleted[doctype] = deleted.get(doctype, 0) + count
	if include_playwright:
		from kentender_procurement.procurement_requisitions.seeds import playwright_ui_fixtures as pw

		pw.reset_all(commit=False)
		pw.restore_site(commit=False)
		deleted["playwright_namespace"] = pw.NS_PW
	journal = frappe.get_all("Requisition Command Journal", filters={"idempotency_key": ("like", "req-seed:%")}, pluck="name") if include_canonical else []
	if journal:
		frappe.db.delete("Requisition Command Journal", {"name": ("in", journal)})
	deleted["Requisition Command Journal"] = len(journal)
	return {"ok": True, "deleted": deleted}


def wipe_all_requisitions() -> dict[str, int]:
	"""Unconditional: every row this module owns, regardless of which Plan
	Item it references or whether it is Authorised with an Active Budget
	reservation. `clear_requisition_fixture_rows` deliberately refuses that
	case (it would orphan Planning/Budget state that is still live) — but a
	full site `wipe` clears Planning and Budget in the same pass, so there
	is nothing left to orphan. This is also the only path that reaches a
	Requisition whose Plan Item was itself already deleted by an earlier,
	incomplete clear (title lookup finds nothing for it, so the selective
	clear above can never see it — the orphan otherwise survives every wipe
	forever)."""
	deleted: dict[str, int] = {}
	for doctype in _DOCTYPES:
		deleted[doctype] = delete_rows(doctype)
	reservations = frappe.get_all("Funding Reservation", filters={"calling_module": "Procurement Requisitions"}, pluck="name")
	if reservations:
		frappe.db.delete("Funding Reservation", {"name": ("in", reservations)})
	deleted["Funding Reservation"] = len(reservations)
	return deleted
