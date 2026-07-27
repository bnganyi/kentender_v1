# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""S300 — Confidential Business Questionnaire (Stitch-aligned electronic section)."""

from __future__ import annotations

import hashlib
import json
from typing import Any
from urllib.parse import quote

import frappe
from frappe.utils import cstr, format_datetime, now_datetime

from kentender_procurement.tender_configurations.services.electronic_bid import (
	STATUS_SEALED,
	_append_audit,
	_get_bid,
	_parse_json,
	create_or_get_draft,
)
from kentender_procurement.tender_configurations.services.electronic_std_template import (
	get_published_electronic_template,
)
from kentender_procurement.tender_configurations.services.published_tender_overview import (
	resolve_published_tender_backend,
)
from kentender_procurement.tender_configurations.services.section_status import (
	issue_item,
	issue_result,
)
from kentender_procurement.tender_configurations.services.submission_checklist import (
	STATUS_COMPLETE,
	STATUS_IN_PROGRESS,
	STATUS_NEEDS_ATTENTION,
	STATUS_NOT_STARTED,
	portal_workspace_url,
)

SECTION_KEY = "confidential_business_questionnaire"

ENTITY_TYPES = frozenset({"sole_proprietor", "partnership", "company"})

CONFLICT_ROW_KEYS = (
	"q1_common_ownership",
	"q2_subsidy_from_tenderer",
	"q3_same_legal_representative",
	"q4_influence_relationship",
	"q5_affiliate_preparing_specs",
	"q6_conflicting_supply_role",
	"q7_relationship_prep_eval_staff",
	"q8_relationship_impl_supervision_staff",
	"q9_conflict_resolved",
)

CONFLICT_ROW_LABELS = {
	"q1_common_ownership": "Common ownership or control with another tenderer",
	"q2_subsidy_from_tenderer": "Subsidy received from another tenderer",
	"q3_same_legal_representative": "Same legal representative as another tenderer",
	"q4_influence_relationship": "Relationship capable of influencing another tenderer or the Procuring Entity",
	"q5_affiliate_preparing_specs": "Affiliate involved in preparing the design or technical specifications",
	"q6_conflicting_supply_role": "Conflicting role in supplying goods or services during contract implementation",
	"q7_relationship_prep_eval_staff": "Business or family relationship with staff involved in tender preparation or evaluation",
	"q8_relationship_impl_supervision_staff": "Business or family relationship with staff involved in contract implementation or supervision",
	"q9_conflict_resolved": "Whether any conflict under questions 7 or 8 has been resolved",
}

# Legacy keys accepted on read and remapped into the Stitch nine-row matrix.
_LEGACY_CONFLICT_MAP = {
	"common_ownership_with_competitor": "q1_common_ownership",
	"employee_of_procuring_entity": "q7_relationship_prep_eval_staff",
	"relative_of_pe_officer": "q7_relationship_prep_eval_staff",
	"consultant_to_pe": "q5_affiliate_preparing_specs",
	"other_conflict": "q4_influence_relationship",
}

ALLOWED_ANSWER_KEYS = frozenset(
	{
		"submission_type",
		"country",
		"city",
		"location",
		"building",
		"floor",
		"postal_address",
		"contact_person",
		"contact_email",
		"nature_of_business",
		"max_business_value",
		"currency",
		"trade_licence_number",
		"licence_expiry",
		"registration_body",
		"registering_body",
		"stock_exchange_listed",
		"stock_exchange_details",
		"stock_exchange",
		"pe_interest_disclosure",
		"pe_interest_details",
		"pe_interest_people",
		"proprietor_name",
		"proprietor_id_number",
		"proprietor_age",
		"proprietor_citizenship",
		"proprietor_country_of_origin",
		"partners",
		"company_type",
		"share_capital",
		"share_capital_nominal",
		"share_capital_issued",
		"directors",
		# FoT / Statutory projection — authorized declarant (owned by CBQ).
		"authorized_signatory_name",
		"authorized_signatory_title",
		"authority_to_bind_confirmed",
		"declarant_postal_address",
		"declarant_place_of_residence",
		"declarant_country_of_residence",
		"state_owned_enterprise",
		"state_owned_itt47_affirmed",
	}
)

FORBIDDEN_OVERRIDE_KEYS = frozenset(
	{
		"verified_full_name_override",
		"verified_email_override",
		"full_name",
		"email",
		"user_id",
		"configuration_id",
	}
)

_NESTED_OBJECT_KEYS = frozenset({"registering_body", "stock_exchange"})
_PEOPLE_LIST_KEYS = frozenset({"pe_interest_people", "partners", "directors"})


def _require_logged_in() -> None:
	if not frappe.session.user or frappe.session.user == "Guest":
		frappe.throw(
			frappe._("Please sign in to open the Confidential Business Questionnaire."),
			frappe.PermissionError,
		)


def portal_cbq_url(publication_ref: str) -> str:
	return (
		f"/tenders/{quote(cstr(publication_ref or '').strip(), safe='')}"
		f"/sections/{SECTION_KEY}"
	)


def _new_entity_id() -> str:
	return f"ENT-{frappe.generate_hash(length=10).upper()}"


def format_certified_at_display(value: Any) -> str:
	"""Human-readable certified-on for CBQ UI (no raw timestamps or microseconds).

	Example: ``25 July 2026, 1:47 p.m. EAT``.
	"""
	if value in (None, ""):
		return ""
	try:
		from datetime import datetime
		from zoneinfo import ZoneInfo

		from frappe.utils import get_datetime, get_system_timezone

		dt = get_datetime(value)
		if not isinstance(dt, datetime):
			return ""
		tz_name = cstr(get_system_timezone() or "Africa/Nairobi") or "Africa/Nairobi"
		tz = ZoneInfo(tz_name)
		if dt.tzinfo is None:
			dt = dt.replace(tzinfo=tz)
		else:
			dt = dt.astimezone(tz)
		hour12 = dt.hour % 12 or 12
		ampm = "a.m." if dt.hour < 12 else "p.m."
		tz_abbr = dt.tzname() or "EAT"
		return (
			f"{dt.day} {dt.strftime('%B')} {dt.year}, "
			f"{hour12}:{dt.minute:02d} {ampm} {tz_abbr}"
		)
	except Exception:
		return ""


def _decorate_entities_for_ui(entities: list[Any]) -> list[dict[str, Any]]:
	out: list[dict[str, Any]] = []
	for ent in entities or []:
		if not isinstance(ent, dict):
			continue
		row = dict(ent)
		if row.get("certified") and row.get("certified_at"):
			row["certified_at_display"] = format_certified_at_display(row.get("certified_at"))
		else:
			row["certified_at_display"] = ""
		# Prefer snapshot at certify time; fall back to current Bidder Details legal name.
		if row.get("certified"):
			row["certified_for"] = cstr(row.get("certified_for") or row.get("legal_name") or "").strip()
		out.append(row)
	return out


def _default_conflict_rows() -> dict[str, dict[str, str]]:
	return {k: {"answer": "", "details": ""} for k in CONFLICT_ROW_KEYS}


def _blank_entity(*, role: str, legal_name: str = "") -> dict[str, Any]:
	return {
		"entity_id": _new_entity_id(),
		"role": role,
		"legal_name": cstr(legal_name or "").strip(),
		"entity_type": "",
		"answers": {},
		"conflict_rows": _default_conflict_rows(),
		"certified": 0,
		"certified_at": "",
		"certified_by": "",
		"certified_for": "",
		"certifier_name": "",
		"certifier_title": "",
		"authority_affirmed": 0,
		"cert_digest": "",
	}


def _ensure_payload(raw: Any) -> dict[str, Any]:
	data = raw if isinstance(raw, dict) else {}
	entities = data.get("entities")
	if not isinstance(entities, list) or not entities:
		# Stitch: leave bidder fields blank — do not prefill from account profile.
		entities = [_blank_entity(role="bidder", legal_name="")]
	# Normalize legacy conflict keys on load.
	normalized = []
	for ent in entities:
		if not isinstance(ent, dict):
			continue
		ent = dict(ent)
		ent["conflict_rows"] = _sanitize_conflict_rows(ent.get("conflict_rows"))
		normalized.append(ent)
	return {
		"entities": normalized or [_blank_entity(role="bidder")],
		"history": data.get("history") if isinstance(data.get("history"), list) else [],
	}


def _sanitize_nested_object(val: Any) -> dict[str, str]:
	src = val if isinstance(val, dict) else {}
	return {cstr(k): cstr(v).strip() for k, v in src.items() if cstr(k).strip()}


def _sanitize_people_rows(val: Any, *, kind: str) -> list[dict[str, str]]:
	if not isinstance(val, list):
		return []
	out: list[dict[str, str]] = []
	for row in val:
		if not isinstance(row, dict):
			continue
		if kind == "pe_interest_people":
			out.append(
				{
					"name": cstr(row.get("name") or "").strip(),
					"designation": cstr(row.get("designation") or "").strip(),
					"interest": cstr(row.get("interest") or "").strip(),
				}
			)
		else:
			out.append(
				{
					"name": cstr(row.get("name") or "").strip(),
					"nationality": cstr(row.get("nationality") or "").strip(),
					"citizenship": cstr(row.get("citizenship") or "").strip(),
					"shares_percent": cstr(row.get("shares_percent") or "").strip(),
				}
			)
	return out


def _sanitize_answers(answers: Any) -> dict[str, Any]:
	src = answers if isinstance(answers, dict) else {}
	out: dict[str, Any] = {}
	for k, v in src.items():
		key = cstr(k)
		if key in FORBIDDEN_OVERRIDE_KEYS or key not in ALLOWED_ANSWER_KEYS:
			continue
		if key in _NESTED_OBJECT_KEYS:
			out[key] = _sanitize_nested_object(v)
			continue
		if key in _PEOPLE_LIST_KEYS:
			out[key] = _sanitize_people_rows(v, kind=key)
			continue
		out[key] = v if isinstance(v, (int, float, bool)) else cstr(v).strip()
	# Normalize registering_body string → object name
	if isinstance(out.get("registration_body"), str) and out["registration_body"]:
		rb = out.get("registering_body") if isinstance(out.get("registering_body"), dict) else {}
		if not rb.get("name"):
			out["registering_body"] = {**(rb or {}), "name": out["registration_body"]}
	return out


def _sanitize_conflict_rows(rows: Any) -> dict[str, dict[str, str]]:
	src = rows if isinstance(rows, dict) else {}
	# Remap legacy keys
	mapped: dict[str, Any] = {}
	for k, v in src.items():
		key = cstr(k)
		mapped[_LEGACY_CONFLICT_MAP.get(key, key)] = v
	out = _default_conflict_rows()
	for key in CONFLICT_ROW_KEYS:
		row = mapped.get(key) if isinstance(mapped.get(key), dict) else {}
		ans = cstr(row.get("answer") or "").strip().lower()
		if ans in ("yes", "y", "true", "1"):
			ans = "yes"
		elif ans in ("no", "n", "false", "0"):
			ans = "no"
		else:
			ans = ""
		out[key] = {"answer": ans, "details": cstr(row.get("details") or "").strip()}
	return out


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
		return any(_filled(v) for v in val.values())
	return bool(cstr(val).strip())


def _yn(val: Any) -> str:
	s = cstr(val or "").strip().lower()
	if s in ("yes", "y", "true", "1"):
		return "yes"
	if s in ("no", "n", "false", "0"):
		return "no"
	return ""


def _registering_body_name(answers: dict[str, Any]) -> str:
	rb = answers.get("registering_body")
	if isinstance(rb, dict) and _filled(rb.get("name")):
		return cstr(rb.get("name"))
	return cstr(answers.get("registration_body") or "")


def validate_cbq_entity(entity: dict[str, Any]) -> list[dict[str, Any]]:
	issues: list[dict[str, str]] = []
	eid = cstr(entity.get("entity_id") or "")
	etype = cstr(entity.get("entity_type") or "").strip()
	answers = entity.get("answers") if isinstance(entity.get("answers"), dict) else {}
	conflicts = entity.get("conflict_rows") if isinstance(entity.get("conflict_rows"), dict) else {}

	if not cstr(entity.get("legal_name") or "").strip():
		issues.append(
			{"code": "cbq_legal_name_required", "field_key": "legal_name", "message": "Legal name is required."}
		)
	for fk, label in (
		("country", "Country"),
		("contact_person", "Contact person"),
		("contact_email", "Contact email"),
	):
		if not _filled(answers.get(fk)):
			issues.append(
				{"code": f"cbq_{fk}_required", "field_key": fk, "message": f"{label} is required."}
			)

	if etype not in ENTITY_TYPES:
		issues.append(
			{
				"code": "cbq_entity_type_required",
				"field_key": "entity_type",
				"message": "Select sole proprietor, partnership, or company.",
			}
		)

	for fk, label in (
		("nature_of_business", "Nature of business"),
		("max_business_value", "Maximum value of business"),
		("trade_licence_number", "Trade licence number"),
		("licence_expiry", "Licence expiry"),
	):
		if not _filled(answers.get(fk)):
			issues.append(
				{"code": f"cbq_{fk}_required", "field_key": fk, "message": f"{label} is required."}
			)
	if not _filled(_registering_body_name(answers)):
		issues.append(
			{
				"code": "cbq_registration_body_required",
				"field_key": "registering_body",
				"message": "Registering body name is required.",
			}
		)

	listed = _yn(answers.get("stock_exchange_listed"))
	if not listed:
		issues.append(
			{
				"code": "cbq_stock_listed_required",
				"field_key": "stock_exchange_listed",
				"message": "Disclose whether the entity is listed on a stock exchange.",
			}
		)
	elif listed == "yes":
		stock = answers.get("stock_exchange") if isinstance(answers.get("stock_exchange"), dict) else {}
		if not (_filled(stock.get("name")) or _filled(answers.get("stock_exchange_details"))):
			issues.append(
				{
					"code": "cbq_stock_details_conditional",
					"field_key": "stock_exchange",
					"message": "Stock exchange details are required when listed.",
				}
			)

	pe = _yn(answers.get("pe_interest_disclosure"))
	if not pe:
		issues.append(
			{
				"code": "cbq_pe_interest_required",
				"field_key": "pe_interest_disclosure",
				"message": "Answer the procuring-entity interest disclosure.",
			}
		)
	elif pe == "yes":
		people = answers.get("pe_interest_people") if isinstance(answers.get("pe_interest_people"), list) else []
		if not people and not _filled(answers.get("pe_interest_details")):
			issues.append(
				{
					"code": "cbq_pe_interest_details_conditional",
					"field_key": "pe_interest_people",
					"message": "List persons with an interest or relationship, or provide details.",
				}
			)

	if etype == "sole_proprietor":
		if not _filled(answers.get("proprietor_name")):
			issues.append(
				{
					"code": "cbq_proprietor_name_required",
					"field_key": "proprietor_name",
					"message": "Proprietor name is required.",
				}
			)
	elif etype == "partnership":
		partners = answers.get("partners") if isinstance(answers.get("partners"), list) else []
		if not partners:
			issues.append(
				{"code": "cbq_partners_required", "field_key": "partners", "message": "List partnership members."}
			)
		else:
			total = 0.0
			for p in partners:
				if not isinstance(p, dict) or not _filled(p.get("name")):
					issues.append(
						{
							"code": "cbq_partner_name_required",
							"field_key": "partners",
							"message": "Each partner needs a name.",
						}
					)
					break
				try:
					total += float(cstr(p.get("shares_percent") or "0") or 0)
				except ValueError:
					pass
			if partners and total < 99.9:
				issues.append(
					{
						"code": "cbq_partner_ownership_incomplete",
						"field_key": "partners",
						"message": "Partnership ownership percentages must total 100%.",
					}
				)
	elif etype == "company":
		if not _filled(answers.get("company_type")):
			issues.append(
				{
					"code": "cbq_company_type_required",
					"field_key": "company_type",
					"message": "Company type is required.",
				}
			)
		directors = answers.get("directors") if isinstance(answers.get("directors"), list) else []
		if not directors:
			issues.append(
				{"code": "cbq_directors_required", "field_key": "directors", "message": "List company directors."}
			)

	for key in CONFLICT_ROW_KEYS:
		row = conflicts.get(key) if isinstance(conflicts.get(key), dict) else {}
		ans = _yn(row.get("answer"))
		label = CONFLICT_ROW_LABELS.get(key, key.replace("_", " "))
		if not ans:
			issues.append(
				{
					"code": "cbq_conflict_row_required",
					"field_key": key,
					"message": f"Answer conflict disclosure: {label}.",
				}
			)
		elif ans == "yes" and not _filled(row.get("details")):
			issues.append(
				{
					"code": "cbq_conflict_details_conditional",
					"field_key": key,
					"message": f"Details required for conflict disclosure: {label}.",
				}
			)

	for issue in issues:
		issue["entity_id"] = eid
	return issues


def _entity_digest(entity: dict[str, Any]) -> str:
	material = {
		"entity_id": entity.get("entity_id"),
		"role": entity.get("role"),
		"legal_name": entity.get("legal_name"),
		"entity_type": entity.get("entity_type"),
		"answers": entity.get("answers"),
		"conflict_rows": entity.get("conflict_rows"),
	}
	raw = json.dumps(material, sort_keys=True, ensure_ascii=False, default=str)
	return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def validate_cbq_payload(payload: dict[str, Any]) -> dict[str, Any]:
	entities = payload.get("entities") if isinstance(payload.get("entities"), list) else []
	issues: list[dict[str, str]] = []
	if not entities:
		issues.append(
			{
				"code": "cbq_entity_required",
				"field_key": "entities",
				"message": "At least one tendering entity is required.",
			}
		)
	for ent in entities:
		if isinstance(ent, dict):
			issues.extend(validate_cbq_entity(ent))
	return {"ok": 0 if issues else 1, "issues": issues}


def derive_cbq_section_status(payload: dict[str, Any] | None, section_def: dict | None = None) -> str:
	_ = section_def
	data = _ensure_payload(payload if isinstance(payload, dict) else {})
	entities = data.get("entities") or []
	any_progress = False
	for ent in entities:
		if not isinstance(ent, dict):
			continue
		if (
			cstr(ent.get("entity_type") or "").strip()
			or cstr(ent.get("legal_name") or "").strip()
			or (ent.get("answers") or {})
		):
			any_progress = True
			break
	if not any_progress:
		return STATUS_NOT_STARTED

	validation = validate_cbq_payload(data)
	if validation.get("issues"):
		return STATUS_NEEDS_ATTENTION

	for ent in entities:
		if not isinstance(ent, dict):
			continue
		if not ent.get("certified"):
			return STATUS_IN_PROGRESS
	return STATUS_COMPLETE


def _load_response(bid) -> dict[str, Any]:
	responses = _parse_json(getattr(bid, "responses", None), {})
	if not isinstance(responses, dict):
		responses = {}
	return _ensure_payload(responses.get(SECTION_KEY))


def _store_response(bid, payload: dict[str, Any], *, event: str = "section_saved") -> None:
	responses = _parse_json(getattr(bid, "responses", None), {})
	if not isinstance(responses, dict):
		responses = {}
	responses[SECTION_KEY] = {
		"entities": payload.get("entities") or [],
		"history": payload.get("history") or [],
	}
	bid.responses = json.dumps(responses, ensure_ascii=False)
	_append_audit(bid, event, {"section_key": SECTION_KEY})
	# FoT / Statutory are derived instruments — CBQ changes withdraw certifications.
	from kentender_procurement.tender_configurations.services.form_of_tender import (
		invalidate_fot_certifications,
	)
	from kentender_procurement.tender_configurations.services.statutory_declarations import (
		invalidate_statutory_certifications,
	)

	invalidate_fot_certifications(bid, reason="cbq_changed")
	invalidate_statutory_certifications(bid, reason="cbq_changed")
	from kentender_procurement.tender_configurations.services.tender_security import (
		invalidate_tender_securing_declaration,
	)

	invalidate_tender_securing_declaration(bid, reason="cbq_changed")
	bid.save(ignore_permissions=True)
	frappe.db.commit()


def _materially_changed(before: dict[str, Any], after: dict[str, Any]) -> bool:
	keys = ("legal_name", "entity_type", "answers", "conflict_rows", "role")
	for k in keys:
		if json.dumps(before.get(k), sort_keys=True, default=str) != json.dumps(
			after.get(k), sort_keys=True, default=str
		):
			return True
	return False


def _fmt_dt(value: Any) -> str:
	if not value:
		return ""
	try:
		return format_datetime(value)
	except Exception:
		return cstr(value)


def _tender_info(backend: dict[str, Any], pub_ref: str, cfg_id: str) -> dict[str, str]:
	pub = backend.get("publication")
	pe = ""
	opening = ""
	deadline = ""
	if pub is not None:
		for attr in ("procuring_entity_name", "procuring_entity", "entity_name"):
			pe = cstr(getattr(pub, attr, None) or "")
			if pe:
				break
		opening = _fmt_dt(getattr(pub, "opening_datetime", None))
		deadline = _fmt_dt(getattr(pub, "submission_deadline", None))
	if not pe and cfg_id:
		pe = cstr(frappe.db.get_value("Tender Configuration", cfg_id, "procuring_entity_name") or "")
	title = cstr(frappe.db.get_value("Tender Configuration", cfg_id, "tender_title") or "")
	method = ""
	if cfg_id:
		method = cstr(frappe.db.get_value("Tender Configuration", cfg_id, "procurement_method") or "")
	return {
		"procuring_entity": pe,
		"publication_ref": pub_ref,
		"opening_datetime": opening,
		"submission_deadline": deadline,
		"procurement_method": method,
		"tender_title": title,
	}


def get_confidential_business_questionnaire(published_tender_ref: str) -> dict[str, Any]:
	_require_logged_in()
	backend = resolve_published_tender_backend(published_tender_ref)
	pub_ref = cstr(backend.get("published_tender_ref") or published_tender_ref)
	cfg_id = cstr(backend.get("configuration_id") or "")
	bid_info = create_or_get_draft(cfg_id)
	bid = _get_bid(cstr(bid_info.get("bid_id") or ""))
	payload = _load_response(bid)
	if not payload.get("entities"):
		payload = _ensure_payload({})
		_store_response(bid, payload)

	tmpl = get_published_electronic_template(pub_ref) or {}
	snapshot = tmpl.get("snapshot") if isinstance(tmpl, dict) else {}
	if not isinstance(snapshot, dict):
		snapshot = tmpl if isinstance(tmpl, dict) else {}
	section_def = {}
	for sec in snapshot.get("sections") or []:
		if isinstance(sec, dict) and cstr(sec.get("section_key")) == SECTION_KEY:
			section_def = sec
			break

	status = derive_cbq_section_status(payload, section_def)
	validation = validate_cbq_payload(payload)
	tender_info = _tender_info(backend, pub_ref, cfg_id)
	entities = _decorate_entities_for_ui(payload.get("entities") or [])

	return {
		"section_key": SECTION_KEY,
		"section_title": cstr(section_def.get("title") or "Confidential Business Questionnaire"),
		"bidder_instructions": cstr(section_def.get("bidder_instructions") or ""),
		"published_tender_ref": pub_ref,
		"tender_title": tender_info.get("tender_title") or "",
		"tender_info": tender_info,
		"workspace_url": portal_workspace_url(pub_ref),
		"cbq_url": portal_cbq_url(pub_ref),
		"bid_id": cstr(bid.name),
		"read_only": 1 if cstr(getattr(bid, "status", "")) == STATUS_SEALED else 0,
		"section_status": status,
		"display_status": status,
		"entities": entities,
		"task_groups": section_def.get("task_groups") or [],
		"conflict_row_keys": list(CONFLICT_ROW_KEYS),
		"conflict_row_labels": dict(CONFLICT_ROW_LABELS),
		"validation": validation,
		"empty": 0,
	}


def save_confidential_business_questionnaire(
	published_tender_ref: str, payload: dict[str, Any] | None
) -> dict[str, Any]:
	_require_logged_in()
	backend = resolve_published_tender_backend(published_tender_ref)
	cfg_id = cstr(backend.get("configuration_id") or "")
	bid_info = create_or_get_draft(cfg_id)
	bid = _get_bid(cstr(bid_info.get("bid_id") or ""))
	if cstr(getattr(bid, "status", "")) == STATUS_SEALED:
		frappe.throw(frappe._("Sealed bids cannot be edited."), frappe.ValidationError)

	incoming = payload if isinstance(payload, dict) else {}
	prior = _load_response(bid)
	prior_by_id = {
		cstr(e.get("entity_id")): e
		for e in (prior.get("entities") or [])
		if isinstance(e, dict) and e.get("entity_id")
	}

	clean_entities: list[dict[str, Any]] = []
	raw_entities = incoming.get("entities")
	if not isinstance(raw_entities, list) or not raw_entities:
		raw_entities = prior.get("entities") or [_blank_entity(role="bidder")]

	for raw in raw_entities:
		if not isinstance(raw, dict):
			continue
		eid = cstr(raw.get("entity_id") or "").strip() or _new_entity_id()
		prev = prior_by_id.get(eid) or {}
		etype = cstr(raw.get("entity_type") or "").strip()
		if etype and etype not in ENTITY_TYPES:
			etype = cstr(prev.get("entity_type") or "")
		entity = {
			"entity_id": eid,
			"role": cstr(raw.get("role") or prev.get("role") or "bidder").strip() or "bidder",
			"legal_name": cstr(raw.get("legal_name") or prev.get("legal_name") or "").strip(),
			"entity_type": etype,
			"answers": _sanitize_answers(raw.get("answers")),
			"conflict_rows": _sanitize_conflict_rows(raw.get("conflict_rows")),
			"certified": 0,
			"certified_at": "",
			"certified_by": "",
			"certified_for": "",
			"certifier_name": "",
			"certifier_title": "",
			"authority_affirmed": 0,
			"cert_digest": "",
		}
		if prev.get("certified") and not _materially_changed(prev, entity):
			entity["certified"] = 1
			entity["certified_at"] = cstr(prev.get("certified_at") or "")
			entity["certified_by"] = cstr(prev.get("certified_by") or "")
			entity["certified_for"] = cstr(
				prev.get("certified_for") or prev.get("legal_name") or entity.get("legal_name") or ""
			).strip()
			entity["certifier_name"] = cstr(prev.get("certifier_name") or "")
			entity["certifier_title"] = cstr(prev.get("certifier_title") or "")
			entity["authority_affirmed"] = 1 if prev.get("authority_affirmed") else 0
			entity["cert_digest"] = cstr(prev.get("cert_digest") or "")
		elif prev.get("certified") and _materially_changed(prev, entity):
			history = prior.get("history") if isinstance(prior.get("history"), list) else []
			history.append(
				{
					"event": "certification_invalidated",
					"entity_id": eid,
					"at": str(now_datetime()),
					"reason": "material_change",
				}
			)
			prior["history"] = history
		clean_entities.append(entity)

	if not any(cstr(e.get("role")) == "bidder" for e in clean_entities):
		clean_entities.insert(0, _blank_entity(role="bidder"))

	stored = {
		"entities": clean_entities,
		"history": prior.get("history") if isinstance(prior.get("history"), list) else [],
	}
	_store_response(bid, stored, event="section_saved")
	return get_confidential_business_questionnaire(published_tender_ref)


def add_jv_entity(published_tender_ref: str, legal_name: str = "") -> dict[str, Any]:
	_require_logged_in()
	dto = get_confidential_business_questionnaire(published_tender_ref)
	entities = list(dto.get("entities") or [])
	entities.append(_blank_entity(role="jv_member", legal_name=legal_name))
	# Mark lead submission type as jv on first entity
	if entities and isinstance(entities[0], dict):
		ans = entities[0].get("answers") if isinstance(entities[0].get("answers"), dict) else {}
		ans = dict(ans)
		ans["submission_type"] = "jv"
		entities[0]["answers"] = ans
	return save_confidential_business_questionnaire(published_tender_ref, {"entities": entities})


def certify_cbq_entity(
	published_tender_ref: str,
	entity_id: str,
	certifier_name: str | None = None,
	certifier_title: str | None = None,
	authority_affirmed: int | str | bool | None = None,
) -> dict[str, Any]:
	_require_logged_in()
	backend = resolve_published_tender_backend(published_tender_ref)
	cfg_id = cstr(backend.get("configuration_id") or "")
	bid_info = create_or_get_draft(cfg_id)
	bid = _get_bid(cstr(bid_info.get("bid_id") or ""))
	if cstr(getattr(bid, "status", "")) == STATUS_SEALED:
		frappe.throw(frappe._("Sealed bids cannot be edited."), frappe.ValidationError)

	payload = _load_response(bid)
	eid = cstr(entity_id or "").strip()
	found = None
	for ent in payload.get("entities") or []:
		if isinstance(ent, dict) and cstr(ent.get("entity_id")) == eid:
			found = ent
			break
	if not found:
		frappe.throw(frappe._("Entity not found."), frappe.DoesNotExistError)

	issues = validate_cbq_entity(found)
	if issues:
		frappe.throw(
			frappe._("Cannot certify until all required questionnaire fields are complete."),
			frappe.ValidationError,
		)

	name = cstr(certifier_name or "").strip()
	title = cstr(certifier_title or "").strip()
	affirmed = authority_affirmed in (True, 1, "1", "true", "True", "yes", "Yes")
	if not name or not title:
		frappe.throw(
			frappe._("Full name and title of the person certifying are required."),
			frappe.ValidationError,
		)
	if not affirmed:
		frappe.throw(
			frappe._("You must confirm that you are authorised to certify this questionnaire."),
			frappe.ValidationError,
		)

	legal_name = cstr(found.get("legal_name") or "").strip()
	if not legal_name:
		frappe.throw(
			frappe._("Legal name of the bidding entity is required before certification."),
			frappe.ValidationError,
		)

	digest = _entity_digest(found)
	found["certified"] = 1
	found["certified_at"] = str(now_datetime())
	found["certified_by"] = frappe.session.user
	# Snapshot the bidder legal name from Bidder Details at certify time.
	found["certified_for"] = legal_name
	found["certifier_name"] = name
	found["certifier_title"] = title
	found["authority_affirmed"] = 1
	found["cert_digest"] = digest
	_store_response(bid, payload, event="section_saved")
	return get_confidential_business_questionnaire(published_tender_ref)


def amend_cbq_certification(published_tender_ref: str, entity_id: str) -> dict[str, Any]:
	"""Explicit amend after certification — clears the cert record immediately."""
	_require_logged_in()
	backend = resolve_published_tender_backend(published_tender_ref)
	cfg_id = cstr(backend.get("configuration_id") or "")
	bid_info = create_or_get_draft(cfg_id)
	bid = _get_bid(cstr(bid_info.get("bid_id") or ""))
	if cstr(getattr(bid, "status", "")) == STATUS_SEALED:
		frappe.throw(frappe._("Sealed bids cannot be edited."), frappe.ValidationError)

	payload = _load_response(bid)
	eid = cstr(entity_id or "").strip()
	found = None
	for ent in payload.get("entities") or []:
		if isinstance(ent, dict) and cstr(ent.get("entity_id")) == eid:
			found = ent
			break
	if not found:
		frappe.throw(frappe._("Entity not found."), frappe.DoesNotExistError)

	if not found.get("certified"):
		return get_confidential_business_questionnaire(published_tender_ref)

	found["certified"] = 0
	found["certified_at"] = ""
	found["certified_by"] = ""
	found["certified_for"] = ""
	found["certifier_name"] = ""
	found["certifier_title"] = ""
	found["authority_affirmed"] = 0
	found["cert_digest"] = ""
	history = payload.get("history") if isinstance(payload.get("history"), list) else []
	history.append(
		{
			"event": "certification_amended",
			"entity_id": eid,
			"at": str(now_datetime()),
			"reason": "user_amend",
		}
	)
	payload["history"] = history
	_store_response(bid, payload, event="section_saved")
	return get_confidential_business_questionnaire(published_tender_ref)


def derive_cbq_issue_result(
	section_def: dict[str, Any],
	payload: dict[str, Any] | None,
) -> dict[str, Any]:
	status = derive_cbq_section_status(payload, section_def)
	validation = validate_cbq_payload(_ensure_payload(payload if isinstance(payload, dict) else {}))
	issues = []
	for raw in validation.get("issues") or []:
		issues.append(
			issue_item(
				code=cstr(raw.get("code")),
				severity="blocker",
				message=cstr(raw.get("message")),
				section_key=SECTION_KEY,
				field_key=cstr(raw.get("field_key")),
				task_key=cstr(raw.get("entity_id") or ""),
				correction_route="",
				resolved=0,
			)
		)
	return issue_result(ok=not issues, section_status=status, issues=issues)
