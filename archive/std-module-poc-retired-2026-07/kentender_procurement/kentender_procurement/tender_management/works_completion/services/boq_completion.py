# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS-COMP-0300 — BOQ completion (pack payload + stable blocker codes).

Delegates persistence to ``StdInstanceBoqService`` / ``Tender STD Instance BOQ``.

Canonical save payload::

    {
      "header": {
        "currency": "USD",
        "pricing_model": "Bills of Quantities",
        "quantity_owner": "Procuring Entity",
        "supplier_input_mode": "Rate Only",
        "amount_computation_rule": "quantity_times_rate",
        "arithmetic_correction_stage": "Evaluation",
        "boq_definition_code": "DEFAULT"
      },
      "bills": [
        {
          "bill_number": "B1",
          "bill_title": "Preliminaries",
          "bill_type": "Standard",
          "order_index": 0,
          "items": [
            {
              "item_number": "1.1",
              "description": "Site clearance",
              "unit": "m2",
              "quantity": 100,
              "item_type": "Normal",
              "supplier_input_mode": "Rate Only",
              "rate_required_from_supplier": true,
              "fixed_amount": null,
              "provisional_sum_amount": null
            }
          ]
        }
      ]
    }

``import_boq`` accepts the same object under ``{"boq": {...}}``, or a root object with
``"bills"`` and optional ``"header"``, or ``{"format": "nested", "header": ..., "bills": ...}``,
or ``{"format": "csv", "csv_text": "item_number,description,unit,quantity\\n1.1,Item,nr,10"}``.
"""

from __future__ import annotations

import csv
from io import StringIO
from typing import Any

import frappe
from frappe import _

from kentender_procurement.tender_management.std_instance.boq import (
	ITEM_TYPES,
	StdInstanceBoqService,
	get_boq_for_instance,
)
from kentender_procurement.tender_management.works_completion.audit import (
	WORKS_BOQ_CHANGED,
	emit_works_completion_audit,
	emit_works_output_stale_if_new,
	stale_logical_outputs_snapshot,
)
from kentender_procurement.tender_management.works_completion.services.context_validator import (
	validate_works_completion_context,
)

SEVERITY_CRITICAL = "Critical"


def _boq_dict_from_simple_csv(csv_text: str) -> dict[str, Any]:
	"""Minimal CSV → pack BOQ shape (header defaults; single bill)."""
	reader = csv.DictReader(StringIO((csv_text or "").strip()))
	items: list[dict[str, Any]] = []
	for raw_row in reader:
		row = {((k or "").strip().lower()): ((v or "").strip()) for k, v in (raw_row or {}).items() if k}
		num = row.get("item_number") or row.get("item") or ""
		desc = row.get("description") or row.get("desc") or ""
		unit = row.get("unit") or "nr"
		qty_s = row.get("quantity") or row.get("qty") or "0"
		try:
			qty = float(qty_s)
		except Exception:
			qty = 0.0
		if not num and not desc:
			continue
		items.append(
			{
				"item_number": num or str(len(items) + 1),
				"description": desc or _("Item"),
				"unit": unit,
				"quantity": qty,
				"item_type": "Normal",
				"supplier_input_mode": "Rate Only",
			}
		)
	if not items:
		frappe.throw(_("CSV contained no BOQ item rows."), title=_("Works BOQ completion"))
	return {
		"header": {
			"currency": "USD",
			"pricing_model": "Bills of Quantities",
			"quantity_owner": "Procuring Entity",
			"supplier_input_mode": "Rate Only",
			"amount_computation_rule": "quantity_times_rate",
			"arithmetic_correction_stage": "Evaluation",
			"boq_definition_code": "DEFAULT",
		},
		"bills": [
			{
				"bill_number": "B-CSV",
				"bill_title": "Imported",
				"bill_type": "Standard",
				"order_index": 0,
				"items": items,
			}
		],
	}


SEVERITY_HIGH = "High"

# Phase 1: Works tender-stage completion expects a persisted BOQ when validating.
BOQ_REQUIRED: bool = True

DEFAULT_PRICING_MODEL = "Bills of Quantities"
DEFAULT_QUANTITY_OWNER = "Procuring Entity"
DEFAULT_SUPPLIER_INPUT_MODE_HEADER = "Rate Only"
DEFAULT_AMOUNT_RULE = "quantity_times_rate"
DEFAULT_ARITHMETIC_STAGE = "Evaluation"

VALID_PRICING_MODELS: frozenset[str] = frozenset({"Bills of Quantities", "Other"})
VALID_HEADER_SUPPLIER_INPUT: frozenset[str] = frozenset({"Rate Only"})
VALID_ITEM_SUPPLIER_INPUT: frozenset[str] = frozenset({"Rate Only", "None", "Fixed Amount"})

_PROHIBITED_PAYLOAD_KEYS: frozenset[str] = frozenset(
	{
		"supplier_rate",
		"submitted_rate",
		"tender_stage_rate",
		"contract_price",
		"contract_price_override",
		"total_amount",
		"bid_amount",
		"arithmetic_correction_amount",
		"opening_correction",
		"evaluation_correction",
	}
)

_CODE_MESSAGES: dict[str, str] = {
	"WORKS_INSTANCE_NOT_FOUND": _("Tender STD Instance was not found."),
	"BOQ_MISSING": _("A Bills of Quantities document is required for this Works instance."),
	"BOQ_INVALID": _("BOQ structure failed validation."),
	"BOQ_CURRENCY_MISSING": _("BOQ currency is required."),
	"BOQ_PRICING_MODEL_INVALID": _("Pricing model must be Bills of Quantities for Works completion."),
	"BOQ_HEADER_SUPPLIER_INPUT_INVALID": _("BOQ header supplier input mode must be Rate Only at tender completion."),
	"BOQ_QUANTITY_OWNER_INVALID": _("Quantity owner must be Procuring Entity."),
	"BOQ_BILL_EMPTY": _("Each bill must contain at least one BOQ item."),
	"BOQ_ITEM_DESCRIPTION_MISSING": _("Each BOQ item must have a description."),
	"BOQ_ITEM_UNIT_MISSING": _("Each BOQ item must have a unit."),
	"BOQ_ITEM_QUANTITY_MISSING": _("BOQ item quantity is missing or zero where required."),
	"BOQ_ITEM_QUANTITY_INVALID": _("BOQ item quantity is invalid (negative)."),
	"BOQ_ITEM_TYPE_INVALID": _("BOQ item_type is not supported."),
	"BOQ_SUPPLIER_INPUT_MODE_INVALID": _("BOQ item supplier_input_mode is invalid."),
	"BOQ_PROVISIONAL_SUM_AMOUNT_MISSING": _("Provisional Sum items require provisional_sum_amount."),
	"BOQ_DUPLICATE_ITEM_NUMBER": _("Duplicate item_number across the BOQ."),
	"BOQ_PROHIBITED_FIELDS": _("Supplier rates, tender arithmetic correction, or contract overrides are not allowed here."),
}


def _norm(value: str | None) -> str:
	return (value or "").strip()


def _truthy(val: Any) -> bool:
	if isinstance(val, bool):
		return val
	s = str(val).strip().lower()
	return s in ("1", "true", "yes", "y", "on")


def _reject_prohibited_boq_payload(obj: Any, *, path: str = "") -> None:
	if isinstance(obj, dict):
		for k, v in obj.items():
			kn = str(k).strip().lower()
			if kn in {x.lower() for x in _PROHIBITED_PAYLOAD_KEYS}:
				frappe.throw(
					str(_CODE_MESSAGES["BOQ_PROHIBITED_FIELDS"]),
					title=_("Works BOQ completion"),
				)
			_reject_prohibited_boq_payload(v, path=f"{path}.{k}" if path else str(k))
	elif isinstance(obj, list):
		for i, v in enumerate(obj):
			_reject_prohibited_boq_payload(v, path=f"{path}[{i}]")


def _clear_boq_children(boq_name: str) -> None:
	boq = frappe.get_doc("Tender STD Instance BOQ", boq_name)
	StdInstanceBoqService.assert_instance_allows_boq_mutation(boq.tender_std_instance)
	StdInstanceBoqService.assert_boq_allows_structure_edit(boq)
	for row in list(boq.boq_items or []):
		boq.remove(row)
	for row in list(boq.boq_bills or []):
		boq.remove(row)
	boq.save(ignore_permissions=True)


def _validate_boq_document_pack_rules(boq_doc: Any) -> list[dict[str, str]]:
	"""Return blocker dicts for ``Tender STD Instance BOQ`` (loaded doc)."""
	blockers: list[dict[str, str]] = []

	cur = _norm(boq_doc.currency)
	if not cur:
		blockers.append(
			{
				"code": "BOQ_CURRENCY_MISSING",
				"message": str(_CODE_MESSAGES["BOQ_CURRENCY_MISSING"]),
				"severity": SEVERITY_CRITICAL,
			}
		)

	pm = _norm(boq_doc.pricing_model)
	if pm not in VALID_PRICING_MODELS:
		blockers.append(
			{
				"code": "BOQ_PRICING_MODEL_INVALID",
				"message": str(_CODE_MESSAGES["BOQ_PRICING_MODEL_INVALID"]),
				"severity": SEVERITY_CRITICAL,
			}
		)
	elif pm != DEFAULT_PRICING_MODEL:
		blockers.append(
			{
				"code": "BOQ_PRICING_MODEL_INVALID",
				"message": str(_CODE_MESSAGES["BOQ_PRICING_MODEL_INVALID"]),
				"severity": SEVERITY_CRITICAL,
			}
		)

	qo = _norm(boq_doc.quantity_owner)
	if qo != DEFAULT_QUANTITY_OWNER:
		blockers.append(
			{
				"code": "BOQ_QUANTITY_OWNER_INVALID",
				"message": str(_CODE_MESSAGES["BOQ_QUANTITY_OWNER_INVALID"]),
				"severity": SEVERITY_CRITICAL,
			}
		)

	h_sim = _norm(boq_doc.supplier_input_mode)
	if h_sim not in VALID_HEADER_SUPPLIER_INPUT:
		blockers.append(
			{
				"code": "BOQ_HEADER_SUPPLIER_INPUT_INVALID",
				"message": str(_CODE_MESSAGES["BOQ_HEADER_SUPPLIER_INPUT_INVALID"]),
				"severity": SEVERITY_CRITICAL,
			}
		)

	bills = list(boq_doc.boq_bills or [])
	items = list(boq_doc.boq_items or [])

	if not bills:
		blockers.append(
			{
				"code": "BOQ_BILL_EMPTY",
				"message": str(_CODE_MESSAGES["BOQ_BILL_EMPTY"]),
				"severity": SEVERITY_CRITICAL,
			}
		)

	bill_codes = {_norm(r.bill_instance_code) for r in bills if _norm(r.bill_instance_code)}
	items_by_bill: dict[str, int] = {}
	for row in items:
		bref = _norm(row.bill_instance_code)
		if bref:
			items_by_bill[bref] = items_by_bill.get(bref, 0) + 1

	for bc in bill_codes:
		if items_by_bill.get(bc, 0) < 1:
			blockers.append(
				{
					"code": "BOQ_BILL_EMPTY",
					"message": str(_CODE_MESSAGES["BOQ_BILL_EMPTY"]),
					"severity": SEVERITY_CRITICAL,
				}
			)

	seen_numbers: set[str] = set()
	dup_item_number = False
	for row in items:
		inum = _norm(row.item_number)
		if inum:
			if inum in seen_numbers:
				dup_item_number = True
			seen_numbers.add(inum)
	if dup_item_number:
		blockers.append(
			{
				"code": "BOQ_DUPLICATE_ITEM_NUMBER",
				"message": str(_CODE_MESSAGES["BOQ_DUPLICATE_ITEM_NUMBER"]),
				"severity": SEVERITY_CRITICAL,
			}
		)

	for row in items:
		it = _norm(row.item_type)
		if it not in ITEM_TYPES:
			blockers.append(
				{
					"code": "BOQ_ITEM_TYPE_INVALID",
					"message": str(_CODE_MESSAGES["BOQ_ITEM_TYPE_INVALID"]),
					"severity": SEVERITY_CRITICAL,
				}
			)

		sim = _norm(row.supplier_input_mode)
		if sim not in VALID_ITEM_SUPPLIER_INPUT:
			blockers.append(
				{
					"code": "BOQ_SUPPLIER_INPUT_MODE_INVALID",
					"message": str(_CODE_MESSAGES["BOQ_SUPPLIER_INPUT_MODE_INVALID"]),
					"severity": SEVERITY_CRITICAL,
				}
			)

		if not _norm(row.description):
			blockers.append(
				{
					"code": "BOQ_ITEM_DESCRIPTION_MISSING",
					"message": str(_CODE_MESSAGES["BOQ_ITEM_DESCRIPTION_MISSING"]),
					"severity": SEVERITY_CRITICAL,
				}
			)

		if not _norm(row.unit):
			blockers.append(
				{
					"code": "BOQ_ITEM_UNIT_MISSING",
					"message": str(_CODE_MESSAGES["BOQ_ITEM_UNIT_MISSING"]),
					"severity": SEVERITY_CRITICAL,
				}
			)

		qty = float(row.quantity or 0)
		if qty < 0:
			blockers.append(
				{
					"code": "BOQ_ITEM_QUANTITY_INVALID",
					"message": str(_CODE_MESSAGES["BOQ_ITEM_QUANTITY_INVALID"]),
					"severity": SEVERITY_CRITICAL,
				}
			)

		if it in ("Normal", "Preliminary", "Daywork"):
			if qty <= 0:
				blockers.append(
					{
						"code": "BOQ_ITEM_QUANTITY_MISSING",
						"message": str(_CODE_MESSAGES["BOQ_ITEM_QUANTITY_MISSING"]),
						"severity": SEVERITY_CRITICAL,
					}
				)

		if it == "Provisional Sum":
			psa = float(row.provisional_sum_amount or 0)
			if psa <= 0:
				blockers.append(
					{
						"code": "BOQ_PROVISIONAL_SUM_AMOUNT_MISSING",
						"message": str(_CODE_MESSAGES["BOQ_PROVISIONAL_SUM_AMOUNT_MISSING"]),
						"severity": SEVERITY_CRITICAL,
					}
				)

	return blockers


class WorksBoqCompletionService:
	"""Validate, save, import, and summarize Works BOQ for tender-stage completion."""

	@staticmethod
	def validate_boq(instance_code: str) -> dict[str, Any]:
		"""Return ``{"valid": bool, "blockers": [{"code","message","severity"}, ...]}``."""
		code = _norm(instance_code)
		if not code or not frappe.db.exists("Tender STD Instance", code):
			return {
				"valid": False,
				"blockers": [
					{
						"code": "WORKS_INSTANCE_NOT_FOUND",
						"message": str(_CODE_MESSAGES["WORKS_INSTANCE_NOT_FOUND"]),
						"severity": SEVERITY_CRITICAL,
					}
				],
			}

		boq_doc = get_boq_for_instance(code)
		if BOQ_REQUIRED and boq_doc is None:
			return {
				"valid": False,
				"blockers": [
					{
						"code": "BOQ_MISSING",
						"message": str(_CODE_MESSAGES["BOQ_MISSING"]),
						"severity": SEVERITY_CRITICAL,
					}
				],
			}

		assert boq_doc is not None
		boq_doc = frappe.get_doc("Tender STD Instance BOQ", boq_doc.name)

		blockers = _validate_boq_document_pack_rules(boq_doc)

		std_res = StdInstanceBoqService.validate_boq(boq_doc.name)
		if not std_res.get("ok") and not blockers:
			blockers.append(
				{
					"code": "BOQ_INVALID",
					"message": str(_CODE_MESSAGES["BOQ_INVALID"]),
					"severity": SEVERITY_CRITICAL,
				}
			)

		return {"valid": not blockers, "blockers": blockers}

	@staticmethod
	def save_boq(
		instance_code: str,
		boq_payload: dict[str, Any],
		actor: str | None = None,
	) -> dict[str, Any]:
		code = _norm(instance_code)
		ctx = validate_works_completion_context(code)
		if not ctx.get("valid"):
			msgs = ", ".join(str(b.get("message") or b.get("code")) for b in (ctx.get("blockers") or []))
			frappe.throw(
				_("Cannot save BOQ: {0}").format(msgs or _("invalid Works completion context")),
				title=_("Works BOQ completion"),
			)

		payload = boq_payload if isinstance(boq_payload, dict) else {}
		_reject_prohibited_boq_payload(payload)

		stale_before = stale_logical_outputs_snapshot(code)

		header = payload.get("header")
		header = header if isinstance(header, dict) else {}
		bills_raw = payload.get("bills")
		if bills_raw is None:
			bills_raw = []
		if not isinstance(bills_raw, list):
			frappe.throw(_("Payload must include a \"bills\" array."), title=_("Works BOQ completion"))

		boq_doc = get_boq_for_instance(code)
		currency = _norm(header.get("currency")) or "USD"
		bdq = _norm(header.get("boq_definition_code")) or "DEFAULT"

		if boq_doc is None:
			boq_doc = StdInstanceBoqService.create_boq_for_instance(
				code,
				currency=currency,
				boq_definition_code=bdq,
			)
		else:
			boq_doc = frappe.get_doc("Tender STD Instance BOQ", boq_doc.name)

		boq_doc.currency = currency
		boq_doc.boq_definition_code = bdq or boq_doc.boq_definition_code
		boq_doc.pricing_model = _norm(header.get("pricing_model")) or DEFAULT_PRICING_MODEL
		boq_doc.quantity_owner = _norm(header.get("quantity_owner")) or DEFAULT_QUANTITY_OWNER
		boq_doc.supplier_input_mode = _norm(header.get("supplier_input_mode")) or DEFAULT_SUPPLIER_INPUT_MODE_HEADER
		boq_doc.amount_computation_rule = _norm(header.get("amount_computation_rule")) or DEFAULT_AMOUNT_RULE
		boq_doc.arithmetic_correction_stage = (
			_norm(header.get("arithmetic_correction_stage")) or DEFAULT_ARITHMETIC_STAGE
		)
		boq_doc.save(ignore_permissions=True)

		_clear_boq_children(boq_doc.name)

		boq_name = boq_doc.name
		for idx, bill in enumerate(bills_raw):
			if not isinstance(bill, dict):
				frappe.throw(_("Each bill must be an object."), title=_("Works BOQ completion"))
			bn = _norm(bill.get("bill_number"))
			bt = _norm(bill.get("bill_title"))
			btyp = _norm(bill.get("bill_type")) or "Standard"
			oi = bill.get("order_index")
			try:
				order_index = int(oi) if oi is not None else idx
			except Exception:
				order_index = idx
			if not bn or not bt:
				frappe.throw(_("Each bill requires bill_number and bill_title."), title=_("Works BOQ completion"))

			StdInstanceBoqService.add_bill(
				boq_name,
				bn,
				bt,
				btyp,
				order_index=order_index,
				status="Draft",
			)

			refreshed = frappe.get_doc("Tender STD Instance BOQ", boq_name)
			bic = ""
			for b_row in reversed(refreshed.boq_bills or []):
				if _norm(b_row.bill_number) == bn:
					bic = _norm(b_row.bill_instance_code)
					break
			if not bic:
				frappe.throw(_("Could not resolve bill_instance_code after save."), title=_("Works BOQ completion"))

			items = bill.get("items")
			if items is None:
				items = []
			if not isinstance(items, list):
				frappe.throw(_("Each bill \"items\" must be an array."), title=_("Works BOQ completion"))

			for it_row in items:
				if not isinstance(it_row, dict):
					frappe.throw(_("Each BOQ item must be an object."), title=_("Works BOQ completion"))
				item_number = _norm(it_row.get("item_number"))
				description = _norm(it_row.get("description"))
				unit = _norm(it_row.get("unit"))
				qty_raw = it_row.get("quantity")
				try:
					quantity = float(qty_raw) if qty_raw is not None else 0.0
				except Exception:
					frappe.throw(_("Invalid quantity value."), title=_("Works BOQ completion"))
				item_type = _norm(it_row.get("item_type")) or "Normal"
				supplier_input_mode = _norm(it_row.get("supplier_input_mode")) or DEFAULT_SUPPLIER_INPUT_MODE_HEADER
				rate_req = _truthy(it_row.get("rate_required_from_supplier", True))

				fa = it_row.get("fixed_amount")
				psa = it_row.get("provisional_sum_amount")
				fixed_amount = float(fa) if fa is not None and str(fa).strip() != "" else None
				provisional_sum_amount = (
					float(psa) if psa is not None and str(psa).strip() != "" else None
				)

				if not item_number:
					frappe.throw(_("Each item requires item_number."), title=_("Works BOQ completion"))

				StdInstanceBoqService.add_item(
					boq_name,
					bic,
					item_number,
					description,
					unit,
					quantity,
					item_type=item_type,
					supplier_input_mode=supplier_input_mode,
					rate_required_from_supplier=rate_req,
					fixed_amount=fixed_amount,
					provisional_sum_amount=provisional_sum_amount,
					status="Draft",
				)

		val = WorksBoqCompletionService.validate_boq(code)
		if not val.get("valid"):
			parts = [str(b.get("message") or b.get("code")) for b in (val.get("blockers") or [])]
			frappe.throw(
				_("BOQ validation failed: {0}").format("; ".join(parts)),
				title=_("Works BOQ completion"),
			)

		user = actor or frappe.session.user
		emit_works_completion_audit(
			WORKS_BOQ_CHANGED,
			code,
			details={"boq": boq_name},
			performed_by=user,
		)
		emit_works_output_stale_if_new(code, stale_before, source="boq", performed_by=user)

		return {"ok": True, "instance_code": code, "boq": boq_name}

	@staticmethod
	def import_boq(
		instance_code: str,
		import_payload: dict[str, Any],
		actor: str | None = None,
	) -> dict[str, Any]:
		raw = import_payload if isinstance(import_payload, dict) else {}
		if raw.get("format") == "csv":
			txt = raw.get("csv_text")
			if not isinstance(txt, str) or not str(txt).strip():
				frappe.throw(
					_('When format is "csv", import_payload must include a non-empty string "csv_text".'),
					title=_("Works BOQ completion"),
				)
			inner_csv = _boq_dict_from_simple_csv(txt)
			return WorksBoqCompletionService.save_boq(instance_code, inner_csv, actor=actor)
		inner: dict[str, Any] | None = None
		if isinstance(raw.get("boq"), dict):
			inner = raw["boq"]
		elif raw.get("format") == "nested" and isinstance(raw.get("bills"), list):
			inner = {k: v for k, v in raw.items() if k != "format"}
		elif isinstance(raw.get("bills"), list):
			inner = raw
		if inner is None:
			frappe.throw(
				_("import_payload must include \"boq\", or \"bills\" at root, or format=nested."),
				title=_("Works BOQ completion"),
			)
		return WorksBoqCompletionService.save_boq(instance_code, inner, actor=actor)

	@staticmethod
	def get_boq_summary(instance_code: str) -> dict[str, Any]:
		code = _norm(instance_code)
		val = WorksBoqCompletionService.validate_boq(code)
		boq_doc = get_boq_for_instance(code)
		if boq_doc is None:
			return {
				"instance_code": code,
				"has_boq": False,
				"bill_count": 0,
				"item_count": 0,
				"validation": val,
			}

		full = frappe.get_doc("Tender STD Instance BOQ", boq_doc.name)
		return {
			"instance_code": code,
			"has_boq": True,
			"boq_name": full.name,
			"header": {
				"currency": _norm(full.currency),
				"pricing_model": _norm(full.pricing_model),
				"quantity_owner": _norm(full.quantity_owner),
				"supplier_input_mode": _norm(full.supplier_input_mode),
				"amount_computation_rule": _norm(full.amount_computation_rule),
				"arithmetic_correction_stage": _norm(full.arithmetic_correction_stage),
				"boq_definition_code": _norm(full.boq_definition_code),
				"status": _norm(full.status),
			},
			"bill_count": len(full.boq_bills or []),
			"item_count": len(full.boq_items or []),
			"validation": val,
		}
