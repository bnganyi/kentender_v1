# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The default package renderer (BOP-CHG-001 v0.10 plan D5; FU-BOP-04).

It renders a `kt-bds-package/1` package to a fixed, versioned HTML layout and
then to PDF (wkhtmltopdf through Frappe), and reads back the page count and
the page carrying the price schedule. The facts read aloud (tenderer name,
submitted total and currency, tender security given) come from the package
itself, unchanged. For this product there is no permitted price modification
or discount (BOP-CHG-001 v0.10 §5), so there are no change locations.

The render digest covers the renderer version, the exact HTML and the page
facts, so the same package always gives the same digest; each page's target
digest is bound to it. Whether this is the operating profile's "approved
rendering" is an owner decision (FU-BOP-04). Each task and answer carries
the published bid definition's own label (Tenders' opening seam,
`definition_labels`), with the bidder's name filled in from the package; an
answer the definition does not name keeps its field key made readable."""

from __future__ import annotations

import hashlib
import io
import json
from typing import Any

from frappe.utils import cstr, escape_html

RENDERER = "kt-bop-render/1"
SCHEMA = "kt-bds-package/1"
PRICE_HEADING = "Price schedule"
SECURITY_KEYS = {"security_form": "form", "issuer": "issuer", "guarantee_reference": "reference", "instrument_amount": "amount"}
PDF_OPTIONS = {"page-size": "A4", "margin-top": "15mm", "margin-bottom": "15mm", "margin-left": "15mm", "margin-right": "15mm"}


def _rejected(reason: str) -> dict[str, Any]:
	return {"outcome": "Rejected", "reason": reason}


def _label(key: str) -> str:
	text = cstr(key).replace("_", " ").strip()
	return text[:1].upper() + text[1:]


def _value(value: Any) -> str:
	if isinstance(value, (list, dict)):
		return json.dumps(value, sort_keys=True, ensure_ascii=False)
	if isinstance(value, bool):
		return "Yes" if value else "No"
	return cstr(value)


def facts_of(body: dict[str, Any]) -> dict[str, Any]:
	price = body.get("price") or {}
	security: dict[str, Any] = {}
	for row in body.get("responses") or []:
		if row.get("field_key") in SECURITY_KEYS and row.get("value") not in (None, ""):
			security[SECURITY_KEYS[row["field_key"]]] = cstr(row["value"])
	if security:
		security["currency"] = cstr(price.get("currency"))
	return {"tenderer_name": cstr((body.get("bid") or {}).get("tenderer_name")), "submitted_total": cstr(price.get("total")), "currency": cstr(price.get("currency")),
		"security_given": security}


def html_of(body: dict[str, Any], *, envelope_id: str, receipt_reference: str, labels: dict[str, Any] | None = None) -> str:
	e = escape_html
	facts = facts_of(body)
	labels = labels or {}
	task_labels, response_labels = labels.get("tasks") or {}, labels.get("responses") or {}
	columns, entity_responses = labels.get("columns") or {}, set(labels.get("entity_responses") or [])
	names = {m.get("organisation_id"): cstr(m.get("legal_name")) for m in (body.get("bid") or {}).get("members") or []}
	lead = ((body.get("organisation_snapshot") or {}).get("facts") or {}).get("organisation") or {}
	names.setdefault(lead.get("organisation_id"), cstr(lead.get("legal_name")))

	def task_label(task: str) -> str:
		return task_labels.get(f"TASK-{cstr(task).upper()}") or _label(task)

	def response_label(row: dict[str, Any]) -> str:
		text = response_labels.get(cstr(row.get("response_id")))
		text = text.replace("{bidder_name}", facts["tenderer_name"]) if text else _label(row.get("field_key"))
		# a business profile is one per entity of the bid: say whose each answer is
		entity = names.get(row.get("member")) if cstr(row.get("response_id")) in entity_responses else ""
		return f"{text} — {entity}" if entity else text

	def cell(row: dict[str, Any]) -> str:
		heads, value = columns.get(cstr(row.get("response_id"))), row.get("value")
		if not heads or not isinstance(value, list) or not all(isinstance(r, dict) for r in value):
			return e(_value(value))
		head = "".join(f"<th>{e(cstr(h.get('label')))}</th>" for h in heads)
		body_rows = "".join("<tr>" + "".join(f"<td>{e(cstr(r.get(h['key'])))}</td>" for h in heads) + "</tr>" for r in value)
		return f"<table><tr>{head}</tr>{body_rows}</table>"
	parts = [
		"<html><head><meta charset='utf-8'><style>body{font-family:sans-serif;font-size:11pt}table{border-collapse:collapse;width:100%}"
		"td,th{border:1px solid #999;padding:3px 5px;text-align:left;vertical-align:top}.page{page-break-before:always}</style></head><body>",
		f"<h1>{e(facts['tenderer_name'])}</h1>",
		f"<p>Tender {e(cstr((body.get('tender') or {}).get('tender_reference')))}</p>",
		f"<p>Receipt {e(receipt_reference)}. Envelope {e(envelope_id)}.</p>",
	]
	by_task: dict[str, list[dict[str, Any]]] = {}
	for row in body.get("responses") or []:
		by_task.setdefault(cstr(row.get("task")), []).append(row)
	for task in sorted(by_task):
		parts.append(f"<div class='page'><h2>{e(task_label(task))}</h2><table>")
		parts += [f"<tr><th>{e(response_label(r))}</th><td>{cell(r)}</td></tr>" for r in by_task[task]]
		parts.append("</table></div>")
	price = body.get("price") or {}
	parts.append(f"<div class='page'><h2>{PRICE_HEADING}</h2><table><tr><th>Line</th><th>Description</th><th>Quantity</th><th>Unit price</th><th>Line total</th></tr>")
	for line in price.get("lines") or []:
		parts.append("<tr>" + "".join(f"<td>{e(cstr(line.get(k)))}</td>" for k in ("line", "description", "quantity", "unit_price", "line_total")) + "</tr>")
	parts.append(f"</table><p>Total {e(cstr(price.get('currency')))} {e(cstr(price.get('total')))}</p></div>")
	files = [f for item in body.get("evidence") or [] for f in item.get("files") or []]
	parts.append("<div class='page'><h2>Supporting documents</h2><table><tr><th>File</th><th>Digest</th></tr>")
	parts += [f"<tr><td>{e(cstr(f.get('original_filename')))}</td><td>{e(cstr(f.get('file_digest')))}</td></tr>" for f in files]
	signatory = body.get("signatory") or {}
	parts.append(f"</table><h2>Signed by</h2><p>{e(cstr(signatory.get('full_name')))}, {e(cstr(signatory.get('job_title')))}</p></div></body></html>")
	return "".join(parts)


def _definition_labels(body: dict[str, Any]) -> dict[str, Any]:
	tender = body.get("tender") or {}
	if not tender.get("tender"):
		return {}
	from kentender_procurement.tenders.services import opening_seam

	return opening_seam.definition_labels(cstr(tender["tender"]), tender.get("definition_version"))


class PackageRenderer:
	name = "KenTender package renderer"

	def render(self, *, package: bytes, envelope_id: str, receipt_reference: str) -> dict[str, Any]:
		from frappe.utils.pdf import get_pdf
		from pypdf import PdfReader

		try:
			body = json.loads(package.decode("utf-8"))
		except (UnicodeDecodeError, ValueError):
			return _rejected("unreadable")
		if not isinstance(body, dict) or body.get("schema") != SCHEMA:
			return _rejected("unreadable")
		facts = facts_of(body)
		if not facts["tenderer_name"] or not facts["submitted_total"] or not facts["currency"]:
			return _rejected("unreadable")
		html = html_of(body, envelope_id=envelope_id, receipt_reference=receipt_reference, labels=_definition_labels(body))
		pdf = get_pdf(html, options=dict(PDF_OPTIONS))
		pages = PdfReader(io.BytesIO(pdf)).pages
		price_page = next((n for n, page in enumerate(pages, 1) if PRICE_HEADING in (page.extract_text() or "")), None)
		if not pages or price_page is None:
			return _rejected("unreadable")
		render_digest = hashlib.sha256(f"{RENDERER}\n{len(pages)}:{price_page}\n{html}".encode("utf-8")).hexdigest()
		return {
			"outcome": "Accepted/Verified", "renderer": RENDERER, "pdf": pdf, "page_count": len(pages), "price_page": price_page, "change_pages": [],
			"page_digests": [hashlib.sha256(f"{render_digest}:{n}".encode()).hexdigest() for n in range(1, len(pages) + 1)], "render_digest": render_digest,
			"facts": facts,
		}


def service() -> PackageRenderer:
	return PackageRenderer()
