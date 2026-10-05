# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Removing Tenders and everything that hangs off them — the one place that
knows the Tender family's tables.

The canonical seed's clear (`kentender_core.seeds.canonical`), this
module's own seed reset and full wipe, and the browser fixtures all delete
through here. The family rows go raw — the Tender controllers refuse
ordinary deletes by design — so each row's child-table rows and attached
files are removed explicitly. Until 26 Sep 2026 they were not: a removed
Tender left both behind, and a plain canonical reseed never removed a stray
Tender at all.

"Canonical" is the rule `validate_tenders_seed` checks: a Tender on a
Requisition of the canonical combined Plan Item. Every other Tender, and
every family row whose Tender is not canonical (including one whose Tender
an earlier, incomplete clean-up already removed), is disposable.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Any

import frappe

from kentender_core.utils.raw_delete import delete_rows

#: Every doctype that carries a `tender` link, dependants first; `Tender` last.
TENDER_DOCTYPES = (
	"Tender Event", "Tender Document", "Tender Submission Handoff", "Tender Channel Confirmation", "Tender Candidate Notice", "Tender Clarification",
	"Tender Bid Definition", "Tender Addendum", "Tender Cancellation", "Tender Publication", "Tender Decision", "Tender Task",
	"Tender Version", "Tender",
)

_CHUNK = 500


def _chunks(names: Iterable[str]) -> Iterator[list[str]]:
	names = list(names)
	for start in range(0, len(names), _CHUNK):
		yield names[start : start + _CHUNK]


def _count(deleted: dict[str, int], doctype: str, count: int) -> None:
	if count:
		deleted[doctype] = deleted.get(doctype, 0) + count


def notify_removal(tenders: list[str], deleted: dict[str, int] | None = None) -> None:
	"""Tell the modules holding rows about these Tenders (hook
	`kt_tender_removal_consumers`; Bid Submission's arrangements and bids)
	before the Tenders go: the family rows are removed raw, so no link check
	would stop an orphan."""
	if not tenders:
		return
	for path in frappe.get_hooks("kt_tender_removal_consumers") or []:
		for doctype, count in (frappe.get_attr(path)(tenders=list(tenders)) or {}).items():
			if deleted is not None:
				_count(deleted, doctype, count)


def _delete_family(removed: dict[str, list[str]]) -> dict[str, int]:
	"""`removed` is `{doctype: [names]}` within the Tender family. Their
	command-journal entries and attached files go with them; a File goes
	through its own document, which keeps the stored file while another
	File row still shares it."""
	deleted: dict[str, int] = {}
	notify_removal(removed.get("Tender", []), deleted)
	for doctype in TENDER_DOCTYPES:
		for chunk in _chunks(removed.get(doctype, [])):
			delete_rows(doctype, {"name": ("in", chunk)}, deleted=deleted)
	for chunk in _chunks(name for names in removed.values() for name in names):
		filters = {"document_name": ("in", chunk)}
		_count(deleted, "Tender Command Journal", frappe.db.count("Tender Command Journal", filters))
		frappe.db.delete("Tender Command Journal", filters)
	# notifications about a removed Tender, whoever received them: the browser
	# worlds use canonical people (Charles Mutiso as the Head of Procurement
	# Function; every Accounting Officer holder), whose bells otherwise fill with
	# tasks for Tenders that no longer exist
	for doctype, names in removed.items():
		for chunk in _chunks(names):
			filters = {"document_type": doctype, "document_name": ("in", chunk)}
			_count(deleted, "Notification Log", frappe.db.count("Notification Log", filters))
			frappe.db.delete("Notification Log", filters)
	for doctype, names in removed.items():
		for chunk in _chunks(names):
			for file in frappe.get_all("File", filters={"attached_to_doctype": doctype, "attached_to_name": ("in", chunk)}, pluck="name"):
				frappe.delete_doc("File", file, force=1, ignore_permissions=True)
				_count(deleted, "File", 1)
	return deleted


def canonical_tenders() -> list[str]:
	"""Every Tender on a canonical Requisition: the laptops' and the executed
	portfolio's (two-year seed world)."""
	from kentender_procurement.procurement_requisitions.seeds.kentender_mvp_v1 import canonical_plan_item_ids

	plan_items = canonical_plan_item_ids()
	requisitions = frappe.get_all("Procurement Requisition", filters={"plan_item_id": ("in", plan_items)}, pluck="name") if plan_items else []
	return frappe.get_all("Tender", filters={"requisition": ("in", requisitions)}, pluck="name") if requisitions else []


def non_canonical_tenders() -> list[str]:
	keep = set(canonical_tenders())
	return [name for name in frappe.get_all("Tender", pluck="name") if name not in keep]


def delete_tenders(tenders: Iterable[str]) -> dict[str, int]:
	"""These Tenders and every family row, child-table row, journal entry
	and attached file that hangs off them. No commit."""
	tenders = list(tenders)
	if not tenders:
		return {}
	removed: dict[str, list[str]] = {"Tender": tenders}
	for doctype in TENDER_DOCTYPES[:-1]:
		removed[doctype] = [name for chunk in _chunks(tenders) for name in frappe.get_all(doctype, filters={"tender": ("in", chunk)}, pluck="name")]
	return _delete_family(removed)


def tender_rows_to_clear() -> dict[str, list[str]]:
	"""What `clear_tender_fixture_rows` removes, as `{doctype: [names]}`:
	every Tender that is not canonical, and every family row whose Tender is
	not canonical. Read-only."""
	keep = set(canonical_tenders())
	removed: dict[str, list[str]] = {}
	for doctype in TENDER_DOCTYPES[:-1]:
		names = [row.name for row in frappe.get_all(doctype, fields=["name", "tender"]) if row.tender and row.tender not in keep]
		if names:
			removed[doctype] = names
	tenders = non_canonical_tenders()
	if tenders:
		removed["Tender"] = tenders
	return removed


def clear_tender_fixture_rows() -> dict[str, Any]:
	"""The canonical seed's `reset`. No commit."""
	return {"ok": True, "deleted": _delete_family(tender_rows_to_clear())}


def wipe_all_tender_rows() -> dict[str, int]:
	"""Every row of the family, whatever it references — only safe under a
	full site wipe. No commit."""
	deleted = _delete_family({doctype: frappe.get_all(doctype, pluck="name") for doctype in TENDER_DOCTYPES})
	_count(deleted, "Tender Command Journal", frappe.db.count("Tender Command Journal"))
	frappe.db.delete("Tender Command Journal")
	return deleted
