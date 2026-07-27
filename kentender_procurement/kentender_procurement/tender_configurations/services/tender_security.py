# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Tender Security — instrument OR tender-securing declaration (never both)."""

from __future__ import annotations

import json
import re
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import quote

import frappe
from frappe.utils import (
	add_to_date,
	cstr,
	flt,
	format_datetime,
	get_datetime,
	getdate,
	now_datetime,
)

from kentender_procurement.tender_configurations.services.electronic_bid import (
	STATUS_SEALED,
	_append_audit,
	_get_bid,
	_parse_json,
	create_or_get_draft,
)
from kentender_procurement.tender_configurations.services.electronic_std_template import (
	get_published_electronic_template,
	resolve_tender_security_mode,
)
from kentender_procurement.tender_configurations.services.published_tender_overview import (
	get_published_tender_overview,
)
from kentender_procurement.tender_configurations.services.submission_checklist import (
	STATUS_COMPLETE,
	STATUS_IN_PROGRESS,
	STATUS_NEEDS_ATTENTION,
	STATUS_NOT_STARTED,
	portal_workspace_url,
)

SECTION_KEY = "tender_security"
CBQ_KEY = "confidential_business_questionnaire"

MODE_INSTRUMENT = "instrument"
MODE_DECLARATION = "securing_declaration"
MODE_NONE = "none"

STATUS_REQUIRES_RECERTIFICATION = "Requires Recertification"

INSTRUMENT_FIELDS = (
	"instrument_type",
	"instrument_number",
	"issuer_legal_name",
	"issuer_registered_address",
	"issuer_country",
	"issue_date",
	"expiry_date",
	"guaranteed_amount",
	"currency",
	"electronic_route",
	"upload_file_url",
	"upload_file_name",
	"issuer_hosted_url",
	"guarantee_reference",
	"issuer_is_foreign_non_bank",
	"correspondent_institution_name",
	"correspondent_details",
	"waiver_reference",
	"lot_coverage",
)

# Used when a published snapshot predates template defaults (still no NSSF hard-coding).
FALLBACK_INSTRUMENT_TYPES = (
	"Bank Guarantee",
	"Insurance Bond",
	"Letter of Credit",
)
FALLBACK_ELECTRONIC_ROUTES = (
	{
		"route_key": "upload",
		"label": "Upload electronic guarantee",
		"help": "Attach the issuer-issued electronic guarantee. A scanned paper document is not an electronic original.",
	},
	{
		"route_key": "issuer_hosted",
		"label": "Use issuer-hosted guarantee",
		"help": "Provide the verification location or URL and the guarantee reference that identifies the complete terms.",
	},
)
FALLBACK_ISSUER_ELIGIBILITY = (
	"The instrument must be issued by a bank or financial institution acceptable to the "
	"Procuring Entity. The tenderer cannot issue its own security."
)


def _require_logged_in() -> None:
	if not frappe.session.user or frappe.session.user == "Guest":
		frappe.throw(
			frappe._("Please sign in to open Tender Security."),
			frappe.PermissionError,
		)


def portal_tender_security_url(publication_ref: str) -> str:
	return f"/tenders/{quote(cstr(publication_ref or '').strip(), safe='')}/sections/{SECTION_KEY}"


def _filled(val: Any) -> bool:
	if val is None:
		return False
	if isinstance(val, bool):
		return val
	if isinstance(val, (int, float)):
		return True
	if isinstance(val, list):
		return len(val) > 0
	if isinstance(val, dict):
		return bool(val)
	return bool(cstr(val).strip())


def _is_truthy(val: Any) -> bool:
	return val in (True, 1, "1", "true", "True", "yes", "Yes", "on")


def _assert_bid_owner(doc) -> None:
	user = frappe.session.user
	if user == "Administrator":
		return
	if cstr(doc.owner) != user:
		frappe.throw(
			frappe._("You cannot access another bidder's electronic bid draft."),
			frappe.PermissionError,
		)


def _security_section(snapshot: dict[str, Any]) -> dict[str, Any]:
	for sec in snapshot.get("sections") or []:
		if isinstance(sec, dict) and cstr(sec.get("section_key")) == SECTION_KEY:
			return sec
	frappe.throw(
		frappe._("Published template is missing the Tender Security section."),
		title="KT_SEC_SECTION_MISSING",
	)


def _cbq_bidder_entity(responses: dict[str, Any]) -> dict[str, Any]:
	cbq = responses.get(CBQ_KEY) if isinstance(responses.get(CBQ_KEY), dict) else {}
	entities = cbq.get("entities") if isinstance(cbq.get("entities"), list) else []
	for ent in entities:
		if isinstance(ent, dict) and cstr(ent.get("role") or "").strip().lower() in (
			"bidder",
			"lead",
			"lead_member",
			"",
		):
			return ent
	return entities[0] if entities and isinstance(entities[0], dict) else {}


def tender_wide_signatory(responses: dict[str, Any]) -> dict[str, Any]:
	"""Thin read helper over CBQ answers — no claim that CBQ cert proves authority."""
	entity = _cbq_bidder_entity(responses)
	answers = entity.get("answers") if isinstance(entity.get("answers"), dict) else {}
	name = cstr(answers.get("authorized_signatory_name") or "").strip()
	title = cstr(answers.get("authorized_signatory_title") or "").strip()
	return {
		"name": name,
		"title": title,
		"legal_name": cstr(entity.get("legal_name") or "").strip(),
		"has_signatory_details": 1 if (name and title) else 0,
	}


def applicant_name_from_responses(responses: dict[str, Any]) -> str:
	"""Single bidder legal name; constituted JV name; intended JV member list."""
	entity = _cbq_bidder_entity(responses)
	answers = entity.get("answers") if isinstance(entity.get("answers"), dict) else {}
	entity_type = cstr(entity.get("entity_type") or answers.get("entity_type") or "").strip().lower()
	legal = cstr(entity.get("legal_name") or "").strip()
	jv_mode = cstr(answers.get("jv_mode") or answers.get("joint_venture_status") or "").strip().lower()
	if "intended" in jv_mode or entity_type == "intended_jv":
		members = answers.get("jv_intended_members") or answers.get("future_members") or []
		if isinstance(members, list) and members:
			names = [cstr(m.get("legal_name") if isinstance(m, dict) else m).strip() for m in members]
			names = [n for n in names if n]
			if names:
				return "; ".join(names)
	if "constituted" in jv_mode or entity_type in ("jv", "joint_venture", "constituted_jv"):
		jv_name = cstr(answers.get("jv_legal_name") or legal).strip()
		if jv_name:
			return jv_name
	return legal


def resolve_security_mode(publication_ref: str) -> str:
	"""Public mode resolver for a published tender."""
	from kentender_procurement.tender_configurations.services.published_tender_overview import (
		resolve_published_tender_backend,
	)

	backend = resolve_published_tender_backend(publication_ref)
	cfg_id = cstr(backend.get("configuration_id") or "")
	if not cfg_id:
		return MODE_NONE
	raw = frappe.db.get_value("Tender Configuration", cfg_id, "tds_values")
	tds = _parse_json(raw, {})
	return resolve_tender_security_mode(tds if isinstance(tds, dict) else {})


def _permitted_types(section_def: dict[str, Any], tender_owned: dict[str, Any]) -> list[str]:
	raw = tender_owned.get("permitted_instrument_types") or section_def.get(
		"default_permitted_instrument_types"
	)
	if isinstance(raw, str) and raw.strip():
		return [p.strip() for p in raw.split(",") if p.strip()]
	if isinstance(raw, list):
		out = [cstr(x).strip() for x in raw if cstr(x).strip()]
		if out:
			return out
	return list(FALLBACK_INSTRUMENT_TYPES)


def _permitted_routes(section_def: dict[str, Any], tender_owned: dict[str, Any]) -> list[dict[str, Any]]:
	raw = tender_owned.get("permitted_electronic_routes") or section_def.get(
		"default_permitted_electronic_routes"
	)
	if isinstance(raw, list):
		out = []
		for row in raw:
			if isinstance(row, dict) and cstr(row.get("route_key") or "").strip():
				out.append(
					{
						"route_key": cstr(row.get("route_key")).strip(),
						"label": cstr(row.get("label") or row.get("route_key")).strip(),
						"help": cstr(row.get("help") or "").strip(),
					}
				)
			elif isinstance(row, str) and row.strip():
				out.append({"route_key": row.strip(), "label": row.strip(), "help": ""})
		if out:
			return out
	return [dict(r) for r in FALLBACK_ELECTRONIC_ROUTES]


def _permitted_currencies(tender_owned: dict[str, Any]) -> list[str]:
	raw = tender_owned.get("permitted_currencies")
	if isinstance(raw, list) and raw:
		return [cstr(c).strip() for c in raw if cstr(c).strip()]
	single = cstr(tender_owned.get("required_currency") or "").strip()
	return [single] if single else []


def _format_amount_display(amount: Any, currency: str) -> str:
	cur = cstr(currency or "").strip()
	raw = cstr(amount or "").strip()
	if not raw:
		return cur or "—"
	try:
		num = Decimal(raw.replace(",", ""))
		formatted = f"{num:,.2f}"
	except (InvalidOperation, ValueError):
		formatted = raw
	return f"{cur} {formatted}".strip() if cur else formatted


def _format_validity_display(raw: str) -> str:
	val = cstr(raw or "").strip()
	if not val:
		return ""
	try:
		return getdate(val).strftime("%B %d, %Y").upper()
	except Exception:
		return val.upper()


def _enrich_tender_owned_from_tds(
	tender_owned: dict[str, Any], tds: dict[str, Any]
) -> dict[str, Any]:
	"""Fill missing requirement slots from live TDS (older published snapshots)."""
	out = dict(tender_owned or {})
	mapping = {
		"required_amount": "tender_security_amount",
		"required_currency": "tender_security_currency",
		"validity_period": "tender_security_validity_period",
		"validity_unit": "tender_security_validity_unit",
		"security_type": "tender_security_type",
		"bid_validity_period": "bid_validity_period",
		"bid_validity_unit": "bid_validity_unit",
	}
	for dest, src in mapping.items():
		if not cstr(out.get(dest) or "").strip():
			val = tds.get(src)
			if val not in (None, ""):
				out[dest] = val
	# Security currency often omitted in lean seeds — fall back to tender currency.
	if not cstr(out.get("required_currency") or "").strip():
		for key in ("tender_currency", "currency"):
			val = tds.get(key)
			if val not in (None, ""):
				out["required_currency"] = val
				break
	if not cstr(out.get("validity_unit") or "").strip():
		out["validity_unit"] = "days"
	return out


def _overview_submission_deadline(overview: dict[str, Any]) -> str:
	dates = overview.get("dates") if isinstance(overview.get("dates"), dict) else {}
	return cstr(
		overview.get("submission_deadline")
		or overview.get("tender_submission_deadline")
		or overview.get("closing_datetime")
		or dates.get("submission_deadline")
		or ""
	).strip()


def _required_validity_date(tender_owned: dict[str, Any], overview: dict[str, Any]) -> str:
	"""Compute required instrument expiry floor from TDS validity after submission deadline."""
	explicit = cstr(tender_owned.get("required_validity_date") or "").strip()
	if explicit:
		return explicit
	period = tender_owned.get("validity_period")
	unit = cstr(tender_owned.get("validity_unit") or "days").strip().lower() or "days"
	deadline = _overview_submission_deadline(overview)
	if period in (None, "") or not deadline:
		return ""
	try:
		days = int(flt(period))
	except (TypeError, ValueError):
		return ""
	base = get_datetime(deadline)
	if unit.startswith("month"):
		return str(getdate(add_to_date(base, months=days)))
	if unit.startswith("week"):
		return str(getdate(add_to_date(base, days=days * 7)))
	return str(getdate(add_to_date(base, days=days)))


def _tender_validity_end(tender_owned: dict[str, Any], overview: dict[str, Any]) -> str:
	period = tender_owned.get("bid_validity_period")
	unit = cstr(tender_owned.get("bid_validity_unit") or "days").strip().lower() or "days"
	deadline = _overview_submission_deadline(overview)
	if period in (None, "") or not deadline:
		return cstr(overview.get("tender_validity_end_date") or "")
	try:
		n = int(flt(period))
	except (TypeError, ValueError):
		return ""
	base = get_datetime(deadline)
	if unit.startswith("month"):
		return str(getdate(add_to_date(base, months=n)))
	if unit.startswith("week"):
		return str(getdate(add_to_date(base, days=n * 7)))
	return str(getdate(add_to_date(base, days=n)))


def _render_declaration_legal(template: str, subs: dict[str, str]) -> str:
	text = cstr(template or "")
	for key, val in subs.items():
		text = text.replace("{{" + key + "}}", cstr(val))
	# Strip any leftover unresolved placeholders for bidder display.
	text = re.sub(r"\{\{[a-zA-Z0-9_]+\}\}", "—", text)
	return text


def _decimal(val: Any) -> Decimal | None:
	if val in (None, ""):
		return None
	try:
		return Decimal(cstr(val).replace(",", "").strip())
	except (InvalidOperation, ValueError):
		return None


def validate_instrument_response(
	section_def: dict[str, Any],
	tender_owned: dict[str, Any],
	instrument: dict[str, Any],
	*,
	applicant_name: str,
	required_validity_date: str,
) -> dict[str, Any]:
	issues: list[dict[str, str]] = []

	def add(field: str, message: str) -> None:
		issues.append({"field": field, "message": message})

	types = _permitted_types(section_def, tender_owned)
	routes = {r["route_key"] for r in _permitted_routes(section_def, tender_owned)}
	currencies = _permitted_currencies(tender_owned)

	itype = cstr(instrument.get("instrument_type") or "").strip()
	if not itype:
		add("instrument_type", "Select a permitted instrument type.")
	elif types and itype not in types:
		add("instrument_type", "Instrument type is not permitted for this tender.")

	if not _filled(instrument.get("instrument_number")):
		add("instrument_number", "Provide the instrument or guarantee number.")
	if not _filled(instrument.get("issuer_legal_name")):
		add("issuer_legal_name", "Provide the issuing institution's legal name.")
	if not _filled(instrument.get("issuer_registered_address")):
		add("issuer_registered_address", "Provide the issuer registered address.")
	if not _filled(instrument.get("issuer_country")):
		add("issuer_country", "Provide the issuer country.")

	issuer = cstr(instrument.get("issuer_legal_name") or "").strip().lower()
	applicant = cstr(applicant_name or "").strip().lower()
	if issuer and applicant and issuer == applicant:
		add("issuer_legal_name", "The issuer cannot be the tenderer.")

	issue_date = cstr(instrument.get("issue_date") or "").strip()
	expiry_date = cstr(instrument.get("expiry_date") or "").strip()
	if not issue_date:
		add("issue_date", "Provide the issue date.")
	else:
		try:
			getdate(issue_date)
		except Exception:
			add("issue_date", "Issue date is not valid.")
	if not expiry_date:
		add("expiry_date", "Provide the expiry date.")
	else:
		try:
			exp = getdate(expiry_date)
			if required_validity_date:
				req = getdate(required_validity_date)
				if exp < req:
					add(
						"expiry_date",
						"Expiry must be on or after the required security validity date.",
					)
		except Exception:
			add("expiry_date", "Expiry date is not valid.")

	amt = _decimal(instrument.get("guaranteed_amount"))
	req_amt = _decimal(tender_owned.get("required_amount"))
	if amt is None:
		add("guaranteed_amount", "Provide the guaranteed amount.")
	elif req_amt is not None and amt < req_amt:
		add("guaranteed_amount", "Guaranteed amount does not meet the required amount.")

	cur = cstr(instrument.get("currency") or "").strip()
	if len(currencies) == 1:
		if cur and cur != currencies[0]:
			add("currency", "Currency must match the required currency.")
		elif not cur:
			# Single currency is implied; treat as filled when omitted.
			pass
	elif not cur:
		add("currency", "Select a permitted currency.")
	elif currencies and cur not in currencies:
		add("currency", "Currency is not permitted for this tender.")

	route = cstr(instrument.get("electronic_route") or "").strip()
	if not route:
		add("electronic_route", "Select a permitted electronic submission route.")
	elif routes and route not in routes:
		add("electronic_route", "Electronic submission route is not permitted.")
	elif route == "upload" and not _filled(instrument.get("upload_file_url")):
		add("upload_file_url", "Upload the issuer-issued electronic guarantee.")
	elif route == "issuer_hosted":
		if not _filled(instrument.get("issuer_hosted_url")):
			add("issuer_hosted_url", "Provide the issuer-hosted verification location or URL.")
		if not _filled(instrument.get("guarantee_reference")):
			add("guarantee_reference", "Provide the guarantee reference number.")

	foreign = _is_truthy(instrument.get("issuer_is_foreign_non_bank"))
	if foreign:
		has_corr = _filled(instrument.get("correspondent_institution_name")) and _filled(
			instrument.get("correspondent_details")
		)
		has_waiver = _filled(instrument.get("waiver_reference"))
		if not has_corr and not has_waiver:
			add(
				"correspondent_institution_name",
				"Provide Kenyan correspondent details or a PE waiver reference.",
			)

	lot_mode = cstr(section_def.get("lot_coverage_mode") or "tender_level").strip()
	if lot_mode == "lot_specific":
		lots = instrument.get("lot_coverage")
		if not isinstance(lots, list) or not lots:
			add("lot_coverage", "Complete required lot coverage.")

	any_filled = any(_filled(instrument.get(k)) for k in INSTRUMENT_FIELDS if k != "currency")
	if not any_filled and not issues:
		status = STATUS_NOT_STARTED
	elif issues:
		status = STATUS_NEEDS_ATTENTION if any_filled else STATUS_NOT_STARTED
		if not any_filled:
			# Keep Not Started for empty form even with missing-field issues list for save preview.
			status = STATUS_NOT_STARTED
			issues = []
		else:
			status = STATUS_NEEDS_ATTENTION
	else:
		status = STATUS_COMPLETE

	# Recompute cleanly:
	if not any_filled:
		return {"ok": 1, "section_status": STATUS_NOT_STARTED, "issues": [], "complete": 0}
	if issues:
		return {"ok": 0, "section_status": STATUS_NEEDS_ATTENTION, "issues": issues, "complete": 0}
	return {"ok": 1, "section_status": STATUS_COMPLETE, "issues": [], "complete": 1}


def validate_declaration_response(payload: dict[str, Any]) -> dict[str, Any]:
	certified = bool(payload.get("certified"))
	needs = bool(payload.get("requires_recertification"))
	if certified and not needs:
		return {"ok": 1, "section_status": STATUS_COMPLETE, "issues": [], "complete": 1}
	if needs:
		return {
			"ok": 0,
			"section_status": STATUS_NEEDS_ATTENTION,
			"issues": [{"field": "certification", "message": "Declaration needs recertification."}],
			"complete": 0,
		}
	if payload.get("opened") or payload.get("section_status") == STATUS_IN_PROGRESS:
		return {"ok": 1, "section_status": STATUS_IN_PROGRESS, "issues": [], "complete": 0}
	return {"ok": 1, "section_status": STATUS_NOT_STARTED, "issues": [], "complete": 0}


def derive_tender_security_section_status(sec: dict[str, Any], payload: dict[str, Any] | None) -> str:
	payload = payload if isinstance(payload, dict) else {}
	mode = cstr(sec.get("security_mode") or payload.get("mode") or "").strip()
	if mode == MODE_DECLARATION or payload.get("mode") == MODE_DECLARATION:
		return validate_declaration_response(payload)["section_status"]
	# Instrument
	stored = cstr(payload.get("section_status") or "").strip()
	if stored in (
		STATUS_COMPLETE,
		STATUS_IN_PROGRESS,
		STATUS_NEEDS_ATTENTION,
		STATUS_NOT_STARTED,
	):
		return stored
	instrument = payload.get("instrument") if isinstance(payload.get("instrument"), dict) else payload
	any_filled = any(_filled(instrument.get(k)) for k in INSTRUMENT_FIELDS)
	if not any_filled:
		return STATUS_NOT_STARTED
	errs = payload.get("validation_errors") or []
	if errs:
		return STATUS_NEEDS_ATTENTION
	if payload.get("complete") or stored == STATUS_COMPLETE:
		return STATUS_COMPLETE
	return STATUS_IN_PROGRESS


def _sanitize_instrument(payload: dict[str, Any]) -> dict[str, Any]:
	src = payload.get("instrument") if isinstance(payload.get("instrument"), dict) else payload
	out: dict[str, Any] = {}
	for key in INSTRUMENT_FIELDS:
		if key == "issuer_is_foreign_non_bank":
			out[key] = 1 if _is_truthy(src.get(key)) else 0
		elif key == "lot_coverage":
			lots = src.get(key)
			out[key] = lots if isinstance(lots, list) else []
		elif key in ("guaranteed_amount",):
			out[key] = cstr(src.get(key) or "").strip()
		else:
			out[key] = cstr(src.get(key) or "").strip() if src.get(key) is not None else ""
	return out


def get_tender_security(publication_ref: str) -> dict[str, Any]:
	_require_logged_in()
	from kentender_procurement.tender_configurations.services.confidential_business_questionnaire import (
		portal_cbq_url,
	)
	from kentender_procurement.tender_configurations.services.published_tender_overview import (
		resolve_published_tender_backend,
	)

	overview = get_published_tender_overview(publication_ref)
	backend = resolve_published_tender_backend(publication_ref)
	pub_ref = cstr(overview.get("published_tender_ref") or publication_ref)
	tmpl = get_published_electronic_template(pub_ref)
	snapshot = tmpl["snapshot"]
	section_def = _security_section(snapshot)
	tender_owned = (
		section_def.get("tender_owned_values")
		if isinstance(section_def.get("tender_owned_values"), dict)
		else {}
	)

	cfg_id = cstr(backend.get("configuration_id") or tmpl["configuration_id"])
	raw_tds = frappe.db.get_value("Tender Configuration", cfg_id, "tds_values")
	tds = _parse_json(raw_tds, {})
	if not isinstance(tds, dict):
		tds = {}
	tender_owned = _enrich_tender_owned_from_tds(tender_owned, tds)
	mode = cstr(section_def.get("security_mode") or "").strip() or resolve_tender_security_mode(tds)
	if mode == MODE_NONE:
		frappe.throw(
			frappe._("Tender Security is not required for this tender."),
			title="KT_SEC_NOT_APPLICABLE",
		)

	draft = create_or_get_draft(cfg_id, schema_snapshot=snapshot, schema_hash=tmpl.get("hash"))
	bid_id = draft.get("bid_id")
	bid = frappe.get_doc("Electronic Bid Submission", bid_id) if bid_id else None
	responses = _parse_json(getattr(bid, "responses", None), {}) if bid else {}
	stored = responses.get(SECTION_KEY) if isinstance(responses.get(SECTION_KEY), dict) else {}

	applicant = applicant_name_from_responses(responses)
	signatory = tender_wide_signatory(responses)
	req_validity = _required_validity_date(tender_owned, overview)
	currencies = _permitted_currencies(tender_owned)
	types = _permitted_types(section_def, tender_owned)
	routes = _permitted_routes(section_def, tender_owned)
	beneficiary = cstr(
		tender_owned.get("beneficiary")
		or overview.get("procuring_entity")
		or ""
	).strip()
	issuer_eligibility = cstr(
		tender_owned.get("issuer_eligibility")
		or section_def.get("default_issuer_eligibility")
		or FALLBACK_ISSUER_ELIGIBILITY
	).strip()

	base = {
		"published_tender_ref": pub_ref,
		"bid_status": cstr(bid.status) if bid else None,
		"bid_id": bid_id,
		"bid_modified": str(bid.modified) if bid else None,
		"bid_sealed": 1 if bid and cstr(bid.status) == STATUS_SEALED else 0,
		"workspace_url": portal_workspace_url(pub_ref),
		"section_key": SECTION_KEY,
		"mode": mode,
		"tender_title": cstr(overview.get("tender_title") or ""),
		"procuring_entity": cstr(overview.get("procuring_entity") or ""),
		"applicant_name": applicant,
		"signatory": signatory,
		"edit_links": {"cbq": portal_cbq_url(pub_ref)},
		"read_only": 1 if bid and cstr(bid.status) == STATUS_SEALED else 0,
	}

	if mode == MODE_INSTRUMENT:
		instrument = stored.get("instrument") if isinstance(stored.get("instrument"), dict) else {}
		if not instrument and stored:
			# Allow flat legacy payload shape.
			instrument = {k: stored.get(k) for k in INSTRUMENT_FIELDS if k in stored}
		# Single currency: surface as read-only default without forcing a prior selection.
		display_currency = cstr(instrument.get("currency") or "").strip()
		if not display_currency and len(currencies) == 1:
			display_currency = currencies[0]
		validation = validate_instrument_response(
			section_def,
			tender_owned,
			instrument,
			applicant_name=applicant,
			required_validity_date=req_validity,
		)
		# Empty → Not Started even though validate clears issues
		any_filled = any(_filled(instrument.get(k)) for k in INSTRUMENT_FIELDS)
		if any_filled and not instrument.get("currency") and len(currencies) == 1:
			# Re-validate with implied currency for structural completeness.
			probe = dict(instrument)
			probe["currency"] = currencies[0]
			validation = validate_instrument_response(
				section_def,
				tender_owned,
				probe,
				applicant_name=applicant,
				required_validity_date=req_validity,
			)
		status = validation["section_status"]
		if any_filled and status == STATUS_NOT_STARTED:
			status = STATUS_IN_PROGRESS
		status_chip = {
			STATUS_COMPLETE: "Ready",
			STATUS_NEEDS_ATTENTION: "Needs attention",
			STATUS_IN_PROGRESS: "In progress",
		}.get(status, "Incomplete")
		req_currency = cstr(tender_owned.get("required_currency") or (currencies[0] if currencies else ""))
		req_amount = cstr(tender_owned.get("required_amount") or "")
		return {
			**base,
			"section_title": "Tender Security",
			"bidder_instructions": cstr(section_def.get("bidder_instructions") or ""),
			"requirements": {
				"required_amount": req_amount,
				"required_currency": req_currency,
				"required_amount_display": _format_amount_display(req_amount, req_currency),
				"permitted_currencies": currencies or ([req_currency] if req_currency else []),
				"currency_readonly": 1 if len(currencies or ([req_currency] if req_currency else [])) == 1 else 0,
				"required_validity_date": req_validity,
				"required_validity_display": _format_validity_display(req_validity),
				"validity_period": cstr(tender_owned.get("validity_period") or ""),
				"validity_unit": cstr(tender_owned.get("validity_unit") or ""),
				"permitted_instrument_types": types,
				"issuer_eligibility": issuer_eligibility,
				"beneficiary": beneficiary,
				"applicant_name": applicant,
				"lot_coverage_mode": cstr(section_def.get("lot_coverage_mode") or "tender_level"),
				"permitted_electronic_routes": routes,
				"foreign_non_bank_help": cstr(
					(section_def.get("foreign_non_bank_rule") or {}).get("help") or ""
				),
			},
			"instrument": {**{k: "" for k in INSTRUMENT_FIELDS}, **instrument, "currency": display_currency},
			"validation": validation,
			"section_status": status,
			"status_chip": status_chip,
			"can_save": 0 if (bid and cstr(bid.status) == STATUS_SEALED) else 1,
		}

	# Declaration mode
	decl_cfg = section_def.get("declaration") if isinstance(section_def.get("declaration"), dict) else {}
	validity_end = _tender_validity_end(tender_owned, overview)
	subs = {
		"procuring_entity_name": cstr(overview.get("procuring_entity") or ""),
		"tender_title": cstr(overview.get("tender_title") or ""),
		"tender_reference": pub_ref,
		"tenderer_name": applicant or "—",
		"signatory_name": signatory.get("name") or "—",
		"signatory_title": signatory.get("title") or "—",
		"tender_validity_end_date": validity_end or "—",
		"suspension_period_days": cstr(decl_cfg.get("suspension_period_days") or ""),
	}
	legal = _render_declaration_legal(cstr(decl_cfg.get("legal_text_template") or ""), subs)
	if stored.get("certified") and isinstance(stored.get("legal_text_snapshot"), str):
		legal_display = cstr(stored.get("legal_text_snapshot"))
	else:
		legal_display = legal

	validation = validate_declaration_response(stored)
	certified = bool(stored.get("certified")) and not stored.get("requires_recertification")
	certified_at = cstr(stored.get("certified_at") or "")
	certified_at_display = ""
	if certified_at:
		try:
			certified_at_display = format_datetime(get_datetime(certified_at))
		except Exception:
			certified_at_display = certified_at
	can_certify = (
		(not certified)
		and bool(signatory.get("has_signatory_details"))
		and bool(applicant)
		and not (bid and cstr(bid.status) == STATUS_SEALED)
	)
	if stored.get("requires_recertification"):
		status_chip = STATUS_REQUIRES_RECERTIFICATION
	elif certified:
		status_chip = "Certified"
	elif can_certify:
		status_chip = "Not certified"
	else:
		status_chip = "Not certified"

	triggers = decl_cfg.get("suspension_triggers") or []
	return {
		**base,
		"section_title": "Tender-Securing Declaration",
		"bidder_instructions": cstr(section_def.get("bidder_instructions") or ""),
		"declaration": {
			"title": cstr(decl_cfg.get("title") or "Tender-Securing Declaration"),
			"summary_intro": cstr(decl_cfg.get("summary_intro") or ""),
			"suspension_triggers": triggers,
			"suspension_period_days": decl_cfg.get("suspension_period_days"),
			"suspension_commencement": cstr(decl_cfg.get("suspension_commencement") or ""),
			"expiry_conditions": decl_cfg.get("expiry_conditions") or [],
			"tender_validity_end_date": validity_end,
			"legal_text": legal_display,
		},
		"certification": {
			"certified": 1 if certified else 0,
			"certified_at": certified_at,
			"certified_at_display": certified_at_display,
			"certified_by": cstr(stored.get("certified_by") or ""),
			"certifier_name": cstr(stored.get("certifier_name") or signatory.get("name") or ""),
			"certifier_title": cstr(stored.get("certifier_title") or signatory.get("title") or ""),
			"requires_recertification": 1 if stored.get("requires_recertification") else 0,
		},
		"can_certify": 1 if can_certify else 0,
		"validation": validation,
		"section_status": validation["section_status"] if not certified else STATUS_COMPLETE,
		"status_chip": status_chip,
	}


def save_tender_security(
	publication_ref: str,
	payload: dict[str, Any] | str | None = None,
	*,
	expected_modified: str | None = None,
) -> dict[str, Any]:
	_require_logged_in()
	from kentender_procurement.tender_configurations.services.published_tender_overview import (
		resolve_published_tender_backend,
	)

	if isinstance(payload, str):
		payload = _parse_json(payload, {})
	payload = payload if isinstance(payload, dict) else {}

	dto = get_tender_security(publication_ref)
	if dto.get("mode") != MODE_INSTRUMENT:
		frappe.throw(
			frappe._("This tender uses a Tender-Securing Declaration, not an instrument form."),
			title="KT_SEC_MODE",
		)
	if dto.get("read_only"):
		frappe.throw(frappe._("Sealed bids cannot be edited."), title="BID_IMMUTABLE")

	backend = resolve_published_tender_backend(cstr(dto.get("published_tender_ref") or publication_ref))
	cfg_id = cstr(backend.get("configuration_id") or "")
	draft = create_or_get_draft(cfg_id)
	doc = _get_bid(cstr(draft.get("bid_id") or ""))
	_assert_bid_owner(doc)

	if expected_modified:
		current = str(doc.modified)
		exp = cstr(expected_modified).strip()
		if exp and exp != current:
			try:
				if get_datetime(exp) < get_datetime(current):
					frappe.throw(
						frappe._("This section was updated elsewhere. Reload and try again."),
						title="KT_SEC_CONFLICT",
					)
			except Exception:
				if exp != current:
					frappe.throw(
						frappe._("This section was updated elsewhere. Reload and try again."),
						title="KT_SEC_CONFLICT",
					)

	tmpl = get_published_electronic_template(cstr(dto["published_tender_ref"]))
	section_def = _security_section(tmpl["snapshot"])
	tender_owned = (
		section_def.get("tender_owned_values")
		if isinstance(section_def.get("tender_owned_values"), dict)
		else {}
	)
	raw_tds = frappe.db.get_value("Tender Configuration", cfg_id, "tds_values")
	tender_owned = _enrich_tender_owned_from_tds(tender_owned, _parse_json(raw_tds, {}))
	instrument = _sanitize_instrument(payload)
	currencies = _permitted_currencies(tender_owned)
	if not instrument.get("currency") and len(currencies) == 1:
		instrument["currency"] = currencies[0]

	overview = get_published_tender_overview(cstr(dto["published_tender_ref"]))
	req_validity = _required_validity_date(tender_owned, overview)
	responses = _parse_json(doc.responses, {})
	applicant = applicant_name_from_responses(responses)
	validation = validate_instrument_response(
		section_def,
		tender_owned,
		instrument,
		applicant_name=applicant,
		required_validity_date=req_validity,
	)
	any_filled = any(_filled(instrument.get(k)) for k in INSTRUMENT_FIELDS)
	status = validation["section_status"]
	if any_filled and status == STATUS_NOT_STARTED:
		status = STATUS_IN_PROGRESS

	merged = {
		"mode": MODE_INSTRUMENT,
		"instrument": instrument,
		"section_status": status,
		"complete": 1 if status == STATUS_COMPLETE else 0,
		"validation_errors": [i["message"] for i in validation["issues"]],
	}
	responses[SECTION_KEY] = merged
	doc.responses = json.dumps(responses, ensure_ascii=False)
	_append_audit(
		doc,
		"section_saved",
		{"section_key": SECTION_KEY, "mode": MODE_INSTRUMENT, "section_status": status},
	)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	out = get_tender_security(publication_ref)
	out["saved"] = True
	return out


def invalidate_tender_securing_declaration(bid_doc, *, reason: str = "source_changed") -> bool:
	responses = _parse_json(getattr(bid_doc, "responses", None), {})
	sec = responses.get(SECTION_KEY) if isinstance(responses.get(SECTION_KEY), dict) else {}
	if cstr(sec.get("mode") or "") != MODE_DECLARATION and not sec.get("certified"):
		return False
	if not sec.get("certified") and not sec.get("legal_text_snapshot"):
		return False
	history = sec.get("certification_history") if isinstance(sec.get("certification_history"), list) else []
	history.append(
		{
			"withdrawn_at": str(now_datetime()),
			"reason": reason,
			"legal_text_snapshot": sec.get("legal_text_snapshot"),
			"certified_at": sec.get("certified_at"),
			"certified_by": sec.get("certified_by"),
			"certifier_name": sec.get("certifier_name"),
			"certifier_title": sec.get("certifier_title"),
		}
	)
	sec = dict(sec)
	sec["certification_history"] = history
	sec["certified"] = 0
	sec["certified_at"] = ""
	sec["certified_by"] = ""
	sec["legal_text_snapshot"] = ""
	sec["requires_recertification"] = 1
	sec["section_status"] = STATUS_NEEDS_ATTENTION
	sec["mode"] = MODE_DECLARATION
	responses[SECTION_KEY] = sec
	bid_doc.responses = json.dumps(responses, ensure_ascii=False)
	_append_audit(
		bid_doc,
		"tender_securing_declaration_invalidated",
		{"section_key": SECTION_KEY, "reason": reason},
	)
	return True


def certify_tender_securing_declaration(
	publication_ref: str,
	*,
	expected_modified: str | None = None,
) -> dict[str, Any]:
	_require_logged_in()
	from kentender_procurement.tender_configurations.services.published_tender_overview import (
		resolve_published_tender_backend,
	)

	dto = get_tender_security(publication_ref)
	if dto.get("mode") != MODE_DECLARATION:
		frappe.throw(
			frappe._("This tender requires a Tender Security instrument, not a declaration."),
			title="KT_SEC_MODE",
		)
	if dto.get("read_only"):
		frappe.throw(frappe._("Sealed bids cannot be edited."), title="BID_IMMUTABLE")
	if dto.get("certification", {}).get("certified"):
		frappe.throw(
			frappe._("Declaration is already certified."),
			title="KT_SEC_ALREADY_CERTIFIED",
		)
	if not dto.get("can_certify"):
		frappe.throw(
			frappe._("Authorised signatory details are incomplete. Update them in the Confidential Business Questionnaire."),
			title="KT_SEC_SIGNATORY",
		)

	backend = resolve_published_tender_backend(cstr(dto.get("published_tender_ref") or publication_ref))
	cfg_id = cstr(backend.get("configuration_id") or "")
	draft = create_or_get_draft(cfg_id)
	doc = _get_bid(cstr(draft.get("bid_id") or ""))
	_assert_bid_owner(doc)

	if expected_modified:
		current = str(doc.modified)
		exp = cstr(expected_modified).strip()
		if exp and exp != current:
			try:
				if get_datetime(exp) < get_datetime(current):
					frappe.throw(
						frappe._("This section was updated elsewhere. Reload and try again."),
						title="KT_SEC_CONFLICT",
					)
			except Exception:
				if exp != current:
					frappe.throw(
						frappe._("This section was updated elsewhere. Reload and try again."),
						title="KT_SEC_CONFLICT",
					)

	signatory = dto.get("signatory") or {}
	legal = cstr((dto.get("declaration") or {}).get("legal_text") or "")
	now = now_datetime()
	responses = _parse_json(doc.responses, {})
	prev = responses.get(SECTION_KEY) if isinstance(responses.get(SECTION_KEY), dict) else {}
	merged = dict(prev)
	merged.update(
		{
			"mode": MODE_DECLARATION,
			"certified": 1,
			"certified_at": str(now),
			"certified_by": frappe.session.user,
			"certifier_name": signatory.get("name"),
			"certifier_title": signatory.get("title"),
			"tenderer_name": dto.get("applicant_name"),
			"legal_text_snapshot": legal,
			"material_fingerprint": {
				"applicant_name": dto.get("applicant_name"),
				"signatory_name": signatory.get("name"),
				"signatory_title": signatory.get("title"),
				"legal_text": legal,
				"suspension_period_days": (dto.get("declaration") or {}).get("suspension_period_days"),
				"tender_validity_end_date": (dto.get("declaration") or {}).get(
					"tender_validity_end_date"
				),
			},
			"requires_recertification": 0,
			"section_status": STATUS_COMPLETE,
			"opened": 1,
		}
	)
	responses[SECTION_KEY] = merged
	doc.responses = json.dumps(responses, ensure_ascii=False)
	_append_audit(
		doc,
		"tender_securing_declaration_certified",
		{
			"section_key": SECTION_KEY,
			"certifier_name": signatory.get("name"),
			"certifier_title": signatory.get("title"),
		},
	)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	out = get_tender_security(publication_ref)
	out["certified"] = True
	return out


def maybe_invalidate_declaration_on_source_change(bid_doc) -> bool:
	"""Invalidate certified declaration when identity/signatory/legal fingerprint drifts."""
	responses = _parse_json(getattr(bid_doc, "responses", None), {})
	sec = responses.get(SECTION_KEY) if isinstance(responses.get(SECTION_KEY), dict) else {}
	if not sec.get("certified"):
		return False
	fp = sec.get("material_fingerprint") if isinstance(sec.get("material_fingerprint"), dict) else {}
	applicant = applicant_name_from_responses(responses)
	signatory = tender_wide_signatory(responses)
	if (
		cstr(fp.get("applicant_name") or "") != cstr(applicant or "")
		or cstr(fp.get("signatory_name") or "") != cstr(signatory.get("name") or "")
		or cstr(fp.get("signatory_title") or "") != cstr(signatory.get("title") or "")
	):
		return invalidate_tender_securing_declaration(bid_doc, reason="identity_or_signatory_changed")
	return False
