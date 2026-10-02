# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""`BuildCanonicalBidPackage` (BDS-CHG-001 v0.8 §4.9, §5.7 items 3 and 8, §7.4;
BDS05-AC-006).

The one package that is signed and deposited, built only from what the
server holds: the exact bound definition's identity and digest; the bid and
arrangement; the Account-owned organisation snapshot the bid signed; every
applicable response in definition order under its published response
identity and downstream mappings; the Accepted evidence of each requirement
with its bytes and digest; the server's price calculation; the submitting
signatory; and the final confirmation. Nothing comes from the browser but
the confirmation tick, and nothing in it depends on the time it is built,
so the same Draft always gives the same bytes (canonical JSON: sorted keys,
no insignificant whitespace, UTF-8).

The package bytes are handed to the tender box and never stored by Bid
Submission; only their digests are kept (plan D7)."""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_submission.services import labels, price, readiness
from kentender_procurement.bid_submission.services.bid_context import BidContext

SCHEMA = "kt-bds-package/1"
CONFIRMED_FIELD = "confirmed"


def canonical(value: Any) -> bytes:
	return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=_plain).encode("utf-8")


def _plain(value):
	if isinstance(value, Decimal):
		return str(value)
	return str(value)


def sha256(data: bytes) -> str:
	return hashlib.sha256(data).hexdigest()


@dataclass
class Package:
	content: bytes
	package_digest: str
	response_snapshot_digest: str
	evidence_set_digest: str
	summary: dict[str, str]


def _mappings(ctx: BidContext) -> dict[str, dict[str, str]]:
	return {
		r["response_id"]: {"evaluation_mapping_id": cstr(r.get("evaluation_mapping_id")), "contract_mapping_id": cstr(r.get("contract_mapping_id"))}
		for r in ctx.model.definition.get("response_rows") or []
	}


def _evidence_files(ids: list[str]) -> list[dict[str, Any]]:
	from kentender_core.services.file_integrity import read_bytes

	files = []
	for name in ids:
		row = frappe.db.get_value("Bid Evidence", name, ["file", "file_digest", "size_bytes", "media_type", "original_filename"], as_dict=True)
		content = read_bytes(row.file)
		if sha256(content) != row.file_digest:
			frappe.throw("An evidence file no longer matches its recorded digest.")
		files.append({"file_digest": row.file_digest, "size_bytes": int(row.size_bytes or 0), "media_type": cstr(row.media_type), "original_filename": cstr(row.original_filename), "content": content})
	return sorted(files, key=lambda f: (f["file_digest"], f["original_filename"]))


def _summary(ctx: BidContext, calc: dict[str, Any], responses: list[dict[str, Any]]) -> dict[str, str]:
	def values(field_key):
		return [cstr(r["value"]) for r in responses if r["field_key"] == field_key and r["value"] not in (None, "")]

	lines = calc["lines"]
	return {
		"bid_total": labels.money_label(calc["total"], calc["currency"]) if calc["total"] is not None else "",
		# the total in words, so the record states the amount both ways as the Form of Tender does
		"bid_total_words": cstr(frappe.utils.money_in_words(calc["total"], calc["currency"])) if calc["total"] is not None else "",
		"offered_item": "; ".join(values("offered_make_model")),
		"quantity": "; ".join(f"{line['quantity']} {line['unit']}".strip() for line in lines),
		"delivery_date": "; ".join(labels.date_label(v) for v in values("offered_delivery_date")),
	}


def build(ctx: BidContext, *, signatory: dict[str, Any], confirmed: bool) -> Package:
	"""`signatory`: the submitting Authorised Signatory's assignment facts
	(`assignment_id`, `full_name`, `job_title`)."""
	tasks = readiness.evaluate(ctx)
	mappings = _mappings(ctx)
	signed_by = {"assignment_id": cstr(signatory.get("assignment_id")), "full_name": cstr(signatory.get("full_name")), "job_title": cstr(signatory.get("job_title"))}
	responses, evidence, confirmation = [], [], None
	for task in ctx.model.tasks:
		for state in tasks[task.key].fields:
			field = state.field
			if not state.visible:
				continue
			entry = {"response_id": field.response_id, "field_key": field.field_key, "task": task.key, "member": field.member or "", **mappings.get(field.response_id, {})}
			if field.kind == "evidence":
				files = _evidence_files(state.value or [])
				evidence.append({**entry, "files": files})
				continue
			if task.key == readiness.REVIEW_TASK:
				if field.field_key == CONFIRMED_FIELD:
					confirmation = {**entry, "confirmed": bool(confirmed)}
					continue
				value = {"full_name": signed_by["full_name"], "job_title": signed_by["job_title"]}.get((field.supplied or {}).get("fact"))
			else:
				value = state.value
			responses.append({**entry, "value": value})
	calc = price.calculate(ctx)
	ws, arrangement = ctx.workspace, ctx.arrangement
	manifest = [{"response_id": e["response_id"], "member": e["member"], "files": [f["file_digest"] for f in e["files"]]} for e in evidence]
	body = {
		"schema": SCHEMA,
		"tender": {"tender": ws.tender, "tender_reference": ws.tender_reference, "bid_definition_id": ws.bid_definition_id, "definition_version": int(ws.definition_version), "definition_digest": ws.definition_digest},
		"bid": {
			"bid_reference": ws.name, "draft_version": int(ws.current_draft_version or 0), "arrangement_id": arrangement.bidder_arrangement_id, "arrangement_type": arrangement.arrangement_type,
			"tenderer_name": ctx.tenderer_name, "members": [{"organisation_id": m.organisation_id, "legal_name": cstr(m.get("legal_name"))} for m in arrangement.members],
		},
		"organisation_snapshot": {"id": ws.organisation_snapshot, "version": int(ws.organisation_snapshot_version or 0), "facts": ctx.snapshot},
		"responses": responses,
		"evidence": [{**e, "files": [{**{k: v for k, v in f.items() if k != "content"}, "content_base64": base64.b64encode(f["content"]).decode("ascii")} for f in e["files"]]} for e in evidence],
		"price": {
			"currency": calc["currency"], "complete": calc["complete"], "subtotal": calc["subtotal"], "tax": calc["tax"], "total": calc["total"],
			"lines": [{k: line[k] for k in ("line", "description", "quantity", "unit", "unit_price", "tax_amount", "amount_before_tax", "line_total")} for line in calc["lines"]],
		},
		"signatory": signed_by,
		"confirmation": confirmation,
	}
	content = canonical(body)
	return Package(
		content=content, package_digest=sha256(content), response_snapshot_digest=sha256(canonical(responses)), evidence_set_digest=sha256(canonical(manifest)),
		summary=_summary(ctx, calc, responses),
	)
