# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BOQ instance (header, bills, items) — PE quantities; supplier rates collected per DSM.

STDINST-0300.
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from kentender_procurement.tender_management.std_instance.audit import emit_std_instance_event
from kentender_procurement.tender_management.std_instance.events import (
	EVT_STDINST_BOQ_CHANGED,
	EVT_STDINST_OUTPUTS_STALED,
)
from kentender_procurement.tender_management.std_instance.parameter import (
	INSTANCE_STATUSES_BLOCKING_PARAMETER_MUTATION,
	OUTPUT_KEY_TO_PARENT_FIELD,
)
from kentender_procurement.tender_management.security.authorization.integration import (
	enforce_sec_authorization,
)

INSTANCE_STATUSES_BLOCKING_BOQ_MUTATION = INSTANCE_STATUSES_BLOCKING_PARAMETER_MUTATION

BOQ_HEADER_BLOCKS_STRUCTURE_STATUSES: frozenset[str] = frozenset({"Published", "Superseded", "Archived"})

BOQ_STALE_OUTPUT_KEYS: frozenset[str] = frozenset({"Bundle", "DSM", "DEM", "DCM"})


def get_boq_for_instance(instance_name: str) -> Document | None:
	"""Return the BOQ document for this STD Instance (one-to-one), if any."""
	names = frappe.get_all(
		"Tender STD Instance BOQ",
		filters={"tender_std_instance": instance_name},
		pluck="name",
		limit=2,
	)
	if not names:
		return None
	if len(names) > 1:
		frappe.throw(
			_("Multiple BOQ documents for STD Instance {0}: {1}").format(
				instance_name,
				", ".join(names),
			),
			title=_("STD Instance BOQ"),
		)
	return frappe.get_doc("Tender STD Instance BOQ", names[0])

ITEM_TYPES: frozenset[str] = frozenset(
	{"Normal", "Preliminary", "Daywork", "Provisional Sum", "Summary"}
)


def _strip(value: str | None) -> str:
	return (value or "").strip()


def published_boq_header_fingerprint(doc: Document) -> tuple[Any, ...]:
	return (
		_strip(doc.get("boq_definition_code")),
		_strip(doc.get("currency")),
		_strip(doc.get("pricing_model")),
		_strip(doc.get("quantity_owner")),
		_strip(doc.get("supplier_input_mode")),
		_strip(doc.get("amount_computation_rule")),
		_strip(doc.get("arithmetic_correction_stage")),
		int(doc.get("version_number") or 0),
	)


def published_bill_fingerprint(row: Any) -> tuple[Any, ...]:
	return (
		_strip(row.get("bill_number")),
		_strip(row.get("bill_title")),
		_strip(row.get("bill_type")),
		int(row.get("order_index") or 0),
	)


def published_item_fingerprint(row: Any) -> tuple[Any, ...]:
	return (
		_strip(row.get("bill_instance_code")),
		_strip(row.get("item_number")),
		_strip(row.get("description")),
		_strip(row.get("unit")),
		float(row.get("quantity") or 0),
		_strip(row.get("item_type")),
		_strip(row.get("supplier_input_mode")),
		int(row.get("rate_required_from_supplier") or 0),
		float(row.get("fixed_amount") or 0),
		float(row.get("provisional_sum_amount") or 0),
	)


def assert_no_duplicate_bill_codes(doc: Document) -> None:
	seen: set[str] = set()
	for row in doc.boq_bills or []:
		bc = _strip(row.bill_instance_code)
		if not bc:
			continue
		if bc in seen:
			frappe.throw(_("Duplicate bill_instance_code: {0}").format(bc), title=_("STD Instance BOQ"))
		seen.add(bc)


def assert_no_duplicate_item_codes(doc: Document) -> None:
	seen: set[str] = set()
	for row in doc.boq_items or []:
		ic = _strip(row.item_instance_code)
		if not ic:
			continue
		if ic in seen:
			frappe.throw(_("Duplicate item_instance_code: {0}").format(ic), title=_("STD Instance BOQ"))
		seen.add(ic)


def assert_boq_referential_integrity(doc: Document) -> None:
	bill_codes = {_strip(r.bill_instance_code) for r in (doc.boq_bills or []) if _strip(r.bill_instance_code)}
	for row in doc.boq_items or []:
		bref = _strip(row.bill_instance_code)
		if not bref:
			frappe.throw(_("BOQ item must reference bill_instance_code."), title=_("STD Instance BOQ"))
		if bref not in bill_codes:
			frappe.throw(
				_("BOQ item references unknown bill_instance_code {0}.").format(bref),
				title=_("STD Instance BOQ"),
			)


def assert_published_boq_rows_honored(prev_doc: Document, new_doc: Document) -> None:
	"""Published header and rows immutable except Published→Superseded with unchanged content fingerprint."""
	prev_st = (prev_doc.status or "").strip()
	if prev_st == "Published":
		fp_old = published_boq_header_fingerprint(prev_doc)
		fp_new = published_boq_header_fingerprint(new_doc)
		new_st = (new_doc.status or "").strip()
		if new_st == "Published":
			if fp_old != fp_new:
				frappe.throw(_("Published BOQ header cannot change."), title=_("STD Instance BOQ"))
		elif new_st == "Superseded":
			if fp_old != fp_new:
				frappe.throw(_("Published BOQ header cannot change when superseding."), title=_("STD Instance BOQ"))
		else:
			frappe.throw(_("Published BOQ cannot change to status {0}.").format(new_st), title=_("STD Instance BOQ"))

	prev_bills = {_strip(r.bill_instance_code): r for r in (prev_doc.boq_bills or []) if _strip(r.bill_instance_code)}
	new_bills = {_strip(r.bill_instance_code): r for r in (new_doc.boq_bills or []) if _strip(r.bill_instance_code)}
	for bic, pr in prev_bills.items():
		if (pr.status or "").strip() != "Published":
			continue
		cur = new_bills.get(bic)
		if cur is None:
			frappe.throw(_("Published bill {0} cannot be removed.").format(bic), title=_("STD Instance BOQ"))
		fpo = published_bill_fingerprint(pr)
		fpn = published_bill_fingerprint(cur)
		if fpo != fpn:
			frappe.throw(_("Published bill {0} cannot change.").format(bic), title=_("STD Instance BOQ"))
		st = (cur.status or "").strip()
		if st == "Published":
			continue
		if st == "Superseded":
			continue
		frappe.throw(_("Published bill {0} invalid status {1}.").format(bic, st), title=_("STD Instance BOQ"))

	prev_items = {_strip(r.item_instance_code): r for r in (prev_doc.boq_items or []) if _strip(r.item_instance_code)}
	new_items = {_strip(r.item_instance_code): r for r in (new_doc.boq_items or []) if _strip(r.item_instance_code)}
	for iic, pr in prev_items.items():
		if (pr.status or "").strip() != "Published":
			continue
		cur = new_items.get(iic)
		if cur is None:
			frappe.throw(_("Published item {0} cannot be removed.").format(iic), title=_("STD Instance BOQ"))
		fpo = published_item_fingerprint(pr)
		fpn = published_item_fingerprint(cur)
		if fpo != fpn:
			frappe.throw(_("Published item {0} cannot change PE-owned fields.").format(iic), title=_("STD Instance BOQ"))
		st = (cur.status or "").strip()
		if st in ("Published", "Superseded"):
			continue
		frappe.throw(_("Published item {0} invalid status {1}.").format(iic, st), title=_("STD Instance BOQ"))


def mark_outputs_stale_for_boq_change(instance_name: str) -> Document | None:
	if not instance_name:
		return None
	doc = frappe.get_doc("Tender STD Instance", instance_name)
	raw = (doc.outputs_stale_flags or "").strip()
	existing: list[str] = []
	if raw:
		try:
			parsed = json.loads(raw)
			if isinstance(parsed, list):
				existing = [str(x) for x in parsed]
		except Exception:
			existing = []

	merged = sorted(set(existing) | set(BOQ_STALE_OUTPUT_KEYS))
	doc.outputs_stale_flags = json.dumps(merged)

	for key in BOQ_STALE_OUTPUT_KEYS:
		field = OUTPUT_KEY_TO_PARENT_FIELD.get(key)
		if field:
			doc.set(field, None)

	doc.readiness_status = "Blocked"
	doc.save(ignore_permissions=True)
	emit_std_instance_event(
		EVT_STDINST_BOQ_CHANGED,
		instance_code=instance_name,
		details={"staled_outputs": sorted(BOQ_STALE_OUTPUT_KEYS)},
	)
	emit_std_instance_event(
		EVT_STDINST_OUTPUTS_STALED,
		instance_code=instance_name,
		document_name=instance_name,
		details={"source": "boq", "stale_outputs": sorted(BOQ_STALE_OUTPUT_KEYS)},
	)
	return doc


class StdInstanceBoqService:
	"""STD Instance BOQ — create bills/items, validate, stale outputs, addendum."""

	@staticmethod
	def status_blocks_boq_at_instance_level(instance_status: str | None) -> bool:
		return bool(instance_status) and instance_status in INSTANCE_STATUSES_BLOCKING_BOQ_MUTATION

	@staticmethod
	def assert_instance_allows_boq_mutation(
		instance_name: str,
		*,
		ignore_boq_publication_lock: bool = False,
	) -> None:
		if ignore_boq_publication_lock:
			return
		from kentender_procurement.tender_management.std_instance.authorization import (
			StdAuthorizationService,
		)
		from kentender_procurement.tender_management.std_instance.publication_lock import (
			StdPublicationLockService,
		)

		StdAuthorizationService.assert_can_edit_draft_instance(
			instance_name,
			attempted_change="edit BOQ",
		)
		StdPublicationLockService.assert_editable(instance_name, operation_label="edit BOQ")
		st = frappe.db.get_value("Tender STD Instance", instance_name, "instance_status")
		if StdInstanceBoqService.status_blocks_boq_at_instance_level(st):
			frappe.throw(
				_("BOQ cannot be edited while Instance Status is {0}.").format(st),
				title=_("STD Instance BOQ Locked"),
			)

	@staticmethod
	def assert_boq_allows_structure_edit(boq_doc: Document, *, ignore_boq_publication_lock: bool = False) -> None:
		if ignore_boq_publication_lock:
			return
		st = (boq_doc.status or "").strip()
		if st in BOQ_HEADER_BLOCKS_STRUCTURE_STATUSES:
			frappe.throw(
				_("BOQ structure cannot change while BOQ status is {0}.").format(st),
				title=_("STD Instance BOQ Locked"),
			)

	@staticmethod
	def create_boq_for_instance(
		instance_name: str,
		*,
		currency: str = "USD",
		boq_definition_code: str = "DEFAULT",
		ignore_boq_publication_lock: bool = False,
	) -> Document:
		if not frappe.db.exists("Tender STD Instance", instance_name):
			frappe.throw(_("Tender STD Instance {0} not found.").format(instance_name), frappe.DoesNotExistError)

		StdInstanceBoqService.assert_instance_allows_boq_mutation(
			instance_name,
			ignore_boq_publication_lock=ignore_boq_publication_lock,
		)

		if get_boq_for_instance(instance_name):
			frappe.throw(_("A BOQ already exists for this STD Instance."), title=_("STD Instance BOQ"))

		boq = frappe.new_doc("Tender STD Instance BOQ")
		boq.tender_std_instance = instance_name
		boq.boq_definition_code = boq_definition_code
		boq.currency = currency
		boq.flags.ignore_boq_publication_lock = bool(ignore_boq_publication_lock)
		boq.insert(ignore_permissions=True)

		mark_outputs_stale_for_boq_change(instance_name)
		return frappe.get_doc("Tender STD Instance BOQ", boq.name)

	@staticmethod
	def add_bill(
		boq_name: str,
		bill_number: str,
		bill_title: str,
		bill_type: str,
		*,
		order_index: int = 0,
		status: str = "Draft",
		ignore_boq_publication_lock: bool = False,
	) -> Document:
		boq = frappe.get_doc("Tender STD Instance BOQ", boq_name)
		StdInstanceBoqService.assert_instance_allows_boq_mutation(
			boq.tender_std_instance,
			ignore_boq_publication_lock=ignore_boq_publication_lock,
		)
		StdInstanceBoqService.assert_boq_allows_structure_edit(boq, ignore_boq_publication_lock=ignore_boq_publication_lock)
		boq.flags.ignore_boq_publication_lock = bool(ignore_boq_publication_lock)

		bc = f"STD-BILL-{frappe.generate_hash(length=10)}"
		boq.append(
			"boq_bills",
			{
				"bill_instance_code": bc,
				"bill_number": bill_number.strip(),
				"bill_title": bill_title.strip(),
				"bill_type": bill_type.strip(),
				"order_index": int(order_index),
				"status": status,
			},
		)
		boq.save(ignore_permissions=True)
		mark_outputs_stale_for_boq_change(boq.tender_std_instance)
		return frappe.get_doc("Tender STD Instance BOQ", boq_name)

	@staticmethod
	def add_item(
		boq_name: str,
		bill_instance_code: str,
		item_number: str,
		description: str,
		unit: str,
		quantity: float,
		*,
		item_type: str = "Normal",
		supplier_input_mode: str = "Rate Only",
		rate_required_from_supplier: bool = True,
		fixed_amount: float | None = None,
		provisional_sum_amount: float | None = None,
		status: str = "Draft",
		ignore_boq_publication_lock: bool = False,
	) -> Document:
		enforce_sec_authorization(
			action_code="CONFIGURE_WORKS_BOQ",
			actor=frappe.session.user,
			object_type="Tender STD Instance BOQ",
			object_code=boq_name,
			context={"object_exists": bool(frappe.db.exists("Tender STD Instance BOQ", boq_name))},
			fallback_message="Not authorized to configure works BOQ.",
		)
		bic = _strip(bill_instance_code)
		if not bic:
			frappe.throw(_("bill_instance_code is required."), title=_("STD Instance BOQ"))

		boq = frappe.get_doc("Tender STD Instance BOQ", boq_name)
		StdInstanceBoqService.assert_instance_allows_boq_mutation(
			boq.tender_std_instance,
			ignore_boq_publication_lock=ignore_boq_publication_lock,
		)
		StdInstanceBoqService.assert_boq_allows_structure_edit(boq, ignore_boq_publication_lock=ignore_boq_publication_lock)
		boq.flags.ignore_boq_publication_lock = bool(ignore_boq_publication_lock)

		if not any(_strip(b.bill_instance_code) == bic for b in (boq.boq_bills or [])):
			frappe.throw(_("Unknown bill_instance_code {0}.").format(bic), title=_("STD Instance BOQ"))

		ic = f"STD-ITEM-{frappe.generate_hash(length=10)}"
		row = {
			"item_instance_code": ic,
			"bill_instance_code": bic,
			"item_number": item_number.strip(),
			"description": description.strip(),
			"unit": unit.strip(),
			"quantity": float(quantity),
			"item_type": item_type,
			"supplier_input_mode": supplier_input_mode,
			"rate_required_from_supplier": 1 if rate_required_from_supplier else 0,
			"status": status,
		}
		if fixed_amount is not None:
			row["fixed_amount"] = fixed_amount
		if provisional_sum_amount is not None:
			row["provisional_sum_amount"] = provisional_sum_amount

		boq.append("boq_items", row)
		boq.save(ignore_permissions=True)
		mark_outputs_stale_for_boq_change(boq.tender_std_instance)
		return frappe.get_doc("Tender STD Instance BOQ", boq_name)

	@staticmethod
	def update_item_through_draft(
		boq_name: str,
		item_instance_code: str,
		*,
		description: str | None = None,
		quantity: float | None = None,
		item_type: str | None = None,
		ignore_boq_publication_lock: bool = False,
	) -> Document:
		iic = _strip(item_instance_code)
		boq = frappe.get_doc("Tender STD Instance BOQ", boq_name)
		StdInstanceBoqService.assert_instance_allows_boq_mutation(
			boq.tender_std_instance,
			ignore_boq_publication_lock=ignore_boq_publication_lock,
		)
		boq.flags.ignore_boq_publication_lock = bool(ignore_boq_publication_lock)

		target = None
		for row in boq.boq_items or []:
			if _strip(row.item_instance_code) == iic:
				target = row
				break
		if target is None:
			frappe.throw(_("Item {0} not found.").format(iic), frappe.DoesNotExistError)

		if (target.status or "").strip() == "Published":
			frappe.throw(_("Published BOQ item cannot be edited."), title=_("STD Instance BOQ"))

		if description is not None:
			target.description = description.strip()
		if quantity is not None:
			target.quantity = float(quantity)
		if item_type is not None:
			if item_type not in ITEM_TYPES:
				frappe.throw(_("Invalid item_type."), title=_("STD Instance BOQ"))
			target.item_type = item_type

		boq.save(ignore_permissions=True)
		mark_outputs_stale_for_boq_change(boq.tender_std_instance)
		return frappe.get_doc("Tender STD Instance BOQ", boq_name)

	@staticmethod
	def replace_boq_through_addendum(
		instance_name: str,
		source_addendum_code: str,
		*,
		ignore_boq_publication_lock: bool = True,
	) -> Document:
		ad = _strip(source_addendum_code)
		if not ad:
			frappe.throw(_("source_addendum_code is required."), title=_("STD Instance BOQ"))

		boq_doc = get_boq_for_instance(instance_name)
		if not boq_doc:
			frappe.throw(_("No BOQ for this STD Instance."), title=_("STD Instance BOQ"))

		boq = frappe.get_doc("Tender STD Instance BOQ", boq_doc.name)
		boq.flags.ignore_boq_publication_lock = bool(ignore_boq_publication_lock)
		boq.source_addendum_code = ad
		boq.version_number = int(boq.version_number or 1) + 1
		boq.status = "Draft"
		boq.save(ignore_permissions=True)
		mark_outputs_stale_for_boq_change(instance_name)
		return boq

	@staticmethod
	def validate_boq(boq_name: str) -> dict[str, Any]:
		doc = frappe.get_doc("Tender STD Instance BOQ", boq_name)
		errors: list[str] = []
		warnings: list[str] = []

		bill_codes = {_strip(r.bill_instance_code) for r in (doc.boq_bills or []) if _strip(r.bill_instance_code)}
		for row in doc.boq_items or []:
			bref = _strip(row.bill_instance_code)
			if not bref:
				errors.append("item_missing_bill_ref")
			elif bref not in bill_codes:
				errors.append(f"unknown_bill:{bref}")

		for row in doc.boq_items or []:
			it = (row.item_type or "").strip()
			if it not in ITEM_TYPES:
				errors.append(f"invalid_item_type:{_strip(row.item_instance_code)}")

			qty = float(row.quantity or 0)
			if it in ("Normal", "Preliminary", "Daywork") and qty <= 0:
				errors.append(f"non_positive_quantity:{_strip(row.item_instance_code)}")

		ok = not errors
		return {"ok": ok, "errors": errors, "warnings": warnings, "boq": boq_name}
