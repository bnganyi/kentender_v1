# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Form of Tender — Review and Certify (derived legal instrument)."""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any
from urllib.parse import quote

import frappe
from frappe.utils import cstr, format_datetime, get_datetime, now_datetime

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
	get_published_tender_overview,
)
from kentender_procurement.tender_configurations.services.submission_checklist import (
	STATUS_COMPLETE,
	STATUS_IN_PROGRESS,
	STATUS_NEEDS_ATTENTION,
	STATUS_NOT_STARTED,
	portal_workspace_url,
)

SECTION_KEY = "form_of_tender"
CBQ_KEY = "confidential_business_questionnaire"
DOCS_KEY = "tender_documents_and_addenda"
LOTS_KEY = "lot_and_alternative_selection"
PRICE_KEY = "price_schedule"
STATUTORY_KEY = "statutory_declarations"

STATUS_REQUIRES_RECERTIFICATION = "Requires Recertification"

# Commissions: redesign uses yes/no (legacy disclose/none mapped on read).
COMMISSIONS_YES = "yes"
COMMISSIONS_NO = "no"

OFFER_BASE_ID = "base"


def _require_logged_in() -> None:
	if not frappe.session.user or frappe.session.user == "Guest":
		frappe.throw(frappe._("Please sign in to open the Form of Tender."), frappe.PermissionError)


def portal_fot_url(publication_ref: str) -> str:
	return f"/tenders/{quote(cstr(publication_ref or '').strip(), safe='')}/sections/{SECTION_KEY}"


def _fot_section(snapshot: dict[str, Any]) -> dict[str, Any]:
	for sec in snapshot.get("sections") or []:
		if isinstance(sec, dict) and cstr(sec.get("section_key")) == SECTION_KEY:
			return sec
	frappe.throw(
		frappe._("Published template is missing the Form of Tender section."),
		title="KT_FOT_SECTION_MISSING",
	)


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


def _normalize_commissions_choice(raw: Any) -> str:
	v = cstr(raw or "").strip().lower()
	if v in (COMMISSIONS_YES, "disclose", "disclosed"):
		return COMMISSIONS_YES
	if v in (COMMISSIONS_NO, "none", "none_declared"):
		return COMMISSIONS_NO
	return ""


def _commission_columns(section_def: dict[str, Any]) -> list[dict[str, Any]]:
	for table in section_def.get("repeatable_tables") or []:
		if isinstance(table, dict) and table.get("table_key") == "commissions_rows":
			return [c for c in (table.get("columns") or []) if isinstance(c, dict)]
	# Fallback columns when template stub omits them.
	return [
		{"field_key": "recipient_name", "label": "Recipient name", "required": True},
		{"field_key": "recipient_address", "label": "Full address", "required": True},
		{"field_key": "reason", "label": "Reason for payment", "required": True},
		{"field_key": "amount", "label": "Amount", "required": True},
		{"field_key": "currency", "label": "Currency", "required": True},
	]


def validate_commissions(
	section_def: dict[str, Any],
	response: dict[str, Any] | None,
) -> list[dict[str, str]]:
	response = response if isinstance(response, dict) else {}
	issues: list[dict[str, str]] = []
	choice = _normalize_commissions_choice(response.get("commissions_choice"))
	if not choice:
		return issues  # unanswered is allowed until certify
	if choice == COMMISSIONS_NO:
		return issues
	rows = response.get("commissions_rows") or []
	if not isinstance(rows, list) or not rows:
		issues.append(
			{
				"field_key": "commissions_rows",
				"code": "required",
				"message": "Disclose at least one commission, gratuity or fee row.",
			}
		)
		return issues
	cols = _commission_columns(section_def)
	for idx, row in enumerate(rows):
		if not isinstance(row, dict):
			issues.append(
				{
					"field_key": f"commissions_rows[{idx}]",
					"code": "invalid_row",
					"message": f"Commission row {idx + 1} is invalid.",
				}
			)
			continue
		for col in cols:
			if not col.get("required"):
				continue
			ck = cstr(col.get("field_key") or "")
			if not _filled(row.get(ck)):
				issues.append(
					{
						"field_key": f"commissions_rows[{idx}].{ck}",
						"code": "required",
						"message": (
							f"Commission row {idx + 1}: "
							f"{cstr(col.get('label') or ck)} is required."
						),
					}
				)
	return issues


def validate_form_of_tender_response(
	section_def: dict[str, Any],
	response: dict[str, Any] | None,
	*,
	for_completion: bool = True,
) -> dict[str, Any]:
	"""Validate FoT-owned commissions only. Complete requires certification."""
	response = response if isinstance(response, dict) else {}
	issues = validate_commissions(section_def, response)
	instances = _instances_from_response(response)
	all_certified = bool(instances) and all(bool(i.get("certified")) for i in instances)
	choice = _normalize_commissions_choice(response.get("commissions_choice"))
	started = bool(choice) or bool(response.get("commissions_rows")) or any(
		bool(i.get("certified")) or bool(i.get("certification_history")) for i in instances
	)

	if response.get("requires_recertification"):
		status_label = STATUS_REQUIRES_RECERTIFICATION
	elif all_certified and for_completion:
		status_label = STATUS_COMPLETE
	elif issues and for_completion:
		status_label = STATUS_NEEDS_ATTENTION
	elif started:
		status_label = STATUS_IN_PROGRESS
	else:
		status_label = STATUS_NOT_STARTED

	return {
		"ok": not issues,
		"issues": issues,
		"section_status": status_label,
		"issue_count": len(issues),
	}


def derive_fot_section_status(section_def: dict[str, Any], response: dict[str, Any] | None) -> str:
	result = validate_form_of_tender_response(section_def, response, for_completion=True)
	status = cstr(result.get("section_status") or STATUS_NOT_STARTED)
	# Checklist treats Requires Recertification as Needs Attention for blockers.
	if status == STATUS_REQUIRES_RECERTIFICATION:
		return STATUS_NEEDS_ATTENTION
	return status


def _instances_from_response(response: dict[str, Any]) -> list[dict[str, Any]]:
	raw = response.get("instances")
	if isinstance(raw, list) and raw:
		out = []
		for row in raw:
			if isinstance(row, dict) and cstr(row.get("offer_id") or "").strip():
				out.append(row)
		if out:
			return out
	# Legacy single-cert shape
	if response.get("certified"):
		return [
			{
				"offer_id": OFFER_BASE_ID,
				"offer_type": "Base tender",
				"lots": [],
				"certified": 1,
				"certified_at": response.get("certified_at"),
				"certified_by": response.get("certified_by"),
				"certifier_name": response.get("certifier_name"),
				"certifier_title": response.get("certifier_title"),
				"legal_record": response.get("legal_record"),
			}
		]
	return []


def _ensure_instances(response: dict[str, Any], offers: list[dict[str, Any]]) -> list[dict[str, Any]]:
	existing = {cstr(i.get("offer_id")): i for i in _instances_from_response(response)}
	merged = []
	for offer in offers:
		oid = cstr(offer.get("offer_id") or OFFER_BASE_ID)
		prev = existing.get(oid) or {}
		merged.append(
			{
				**prev,
				"offer_id": oid,
				"offer_type": cstr(offer.get("offer_type") or prev.get("offer_type") or "Base tender"),
				"lots": offer.get("lots") if isinstance(offer.get("lots"), list) else (prev.get("lots") or []),
				"certified": 1 if prev.get("certified") else 0,
			}
		)
	return merged


def _assert_bid_owner(doc) -> None:
	user = frappe.session.user
	if user == "Administrator":
		return
	if cstr(doc.owner) != user:
		frappe.throw(
			frappe._("You cannot access another bidder's electronic bid draft."),
			frappe.PermissionError,
		)


def _cbq_bidder_entity(responses: dict[str, Any]) -> dict[str, Any]:
	cbq = responses.get(CBQ_KEY) if isinstance(responses.get(CBQ_KEY), dict) else {}
	entities = cbq.get("entities") if isinstance(cbq.get("entities"), list) else []
	for ent in entities:
		if isinstance(ent, dict) and cstr(ent.get("role") or "") in ("bidder", "lead", ""):
			return ent
	return entities[0] if entities and isinstance(entities[0], dict) else {}


def _signatory_from_cbq(entity: dict[str, Any]) -> dict[str, Any]:
	answers = entity.get("answers") if isinstance(entity.get("answers"), dict) else {}
	name = cstr(answers.get("authorized_signatory_name") or entity.get("certifier_name") or "").strip()
	title = cstr(answers.get("authorized_signatory_title") or entity.get("certifier_title") or "").strip()
	authority = (
		_is_truthy(answers.get("authority_to_bind_confirmed"))
		or bool(entity.get("certified"))
		or _is_truthy(entity.get("authority_affirmed"))
	)
	soe = cstr(answers.get("state_owned_enterprise") or "").strip().lower()
	itt47 = _is_truthy(answers.get("state_owned_itt47_affirmed"))
	return {
		"name": name,
		"title": title,
		"authority_confirmed": 1 if authority else 0,
		"legal_name": cstr(entity.get("legal_name") or "").strip(),
		"cbq_certified": 1 if entity.get("certified") else 0,
		"state_owned_enterprise": soe,
		"state_owned_itt47_affirmed": 1 if itt47 else 0,
	}


def is_price_schedule_complete(resp: Any) -> bool:
	"""True when bidder completed Price Schedule (pack 11).

	Discounts remain a Form of Tender concern — they are not required on the
	Price Schedule payload.
	"""
	if not isinstance(resp, dict):
		return False
	if resp.get("complete_confirmed") in (1, "1", True, "true"):
		return True
	if cstr(resp.get("section_status") or "") == STATUS_COMPLETE or resp.get("complete") in (
		1,
		"1",
		True,
		"true",
	):
		return True
	# Legacy FoT seed payloads that stored discounts on PS
	totals = resp.get("totals") if isinstance(resp.get("totals"), dict) else {}
	dchoice = cstr(resp.get("discounts_offered") or "").strip().lower()
	if dchoice in ("yes", "no") and (
		totals.get("grand_total") is not None or totals.get("total_excluding_vat") is not None
	):
		if dchoice == "yes":
			if not _filled(resp.get("discount_description")) and not _filled(
				resp.get("discount_amount_or_percent")
			):
				return False
		return True
	return False


def price_schedule_projection(resp: Any) -> dict[str, Any]:
	resp = resp if isinstance(resp, dict) else {}
	try:
		from kentender_procurement.tender_configurations.services.price_schedule_bidder import (
			price_schedule_fot_projection,
		)

		base = price_schedule_fot_projection(resp)
	except Exception:
		base = {}
	totals = resp.get("totals") if isinstance(resp.get("totals"), dict) else {}
	computed = resp.get("computed") if isinstance(resp.get("computed"), dict) else {}
	ct = computed.get("totals") if isinstance(computed.get("totals"), dict) else {}
	dchoice = cstr(resp.get("discounts_offered") or "").strip().lower()
	complete = is_price_schedule_complete(resp)
	currency = cstr(
		base.get("currency") or totals.get("currency") or ct.get("currency") or resp.get("currency") or ""
	).strip()
	grand = base.get("grand_total")
	if grand is None:
		grand = totals.get("grand_total")
	if grand is None:
		grand = ct.get("grand_total")
	if grand is None:
		grand = totals.get("total_excluding_vat")
	discount_label = "None"
	if dchoice == "yes":
		parts = [
			cstr(resp.get("discount_description") or "").strip(),
			cstr(resp.get("discount_amount_or_percent") or "").strip(),
			cstr(resp.get("discount_currency") or currency).strip(),
		]
		discount_label = " ".join(p for p in parts if p) or "Declared"
	elif dchoice == "no":
		discount_label = "None"
	else:
		discount_label = "Declared on Form of Tender" if complete else "Not completed"
	grand_display = cstr(base.get("grand_total_display") or "").strip()
	if not grand_display and grand not in (None, ""):
		try:
			from kentender_procurement.tender_configurations.services.price_schedule_bidder import (
				format_money_display,
			)

			grand_display = format_money_display(grand)
		except Exception:
			grand_display = cstr(grand)
	return {
		"complete": 1 if complete else 0,
		"grand_total": grand,
		"grand_total_display": grand_display,
		"currency": currency,
		"total_display": (
			f"{currency} {grand_display}".strip()
			if grand not in (None, "") and complete
			else ("Not completed" if not complete else "—")
		),
		"discounts_offered": dchoice,
		"discounts_label": discount_label,
		"discount_description": cstr(resp.get("discount_description") or ""),
		"discount_applicability": cstr(resp.get("discount_applicability") or ""),
		"discount_amount_or_percent": cstr(resp.get("discount_amount_or_percent") or ""),
		"discount_currency": cstr(resp.get("discount_currency") or ""),
		"discount_calculation_method": cstr(resp.get("discount_calculation_method") or ""),
		"by_currency": base.get("by_currency") or computed.get("by_currency") or {},
	}


def _offers_from_lots(responses: dict[str, Any], snapshot: dict[str, Any]) -> list[dict[str, Any]]:
	"""One FoT instance for base + each confirmed alternative (when lots section present)."""
	has_lots = any(
		isinstance(s, dict) and cstr(s.get("section_key")) == LOTS_KEY for s in (snapshot.get("sections") or [])
	)
	lots_resp = responses.get(LOTS_KEY) if isinstance(responses.get(LOTS_KEY), dict) else {}
	offers = [{"offer_id": OFFER_BASE_ID, "offer_type": "Base tender", "lots": []}]
	if not has_lots:
		return offers
	selected = lots_resp.get("selected_lots") if isinstance(lots_resp.get("selected_lots"), list) else []
	offers[0]["lots"] = [cstr(x) for x in selected if cstr(x).strip()]
	alts = lots_resp.get("confirmed_alternatives") if isinstance(lots_resp.get("confirmed_alternatives"), list) else []
	for alt in alts:
		if not isinstance(alt, dict):
			continue
		oid = cstr(alt.get("offer_id") or alt.get("alternative_id") or "").strip()
		if not oid:
			continue
		offers.append(
			{
				"offer_id": oid,
				"offer_type": cstr(alt.get("label") or alt.get("offer_type") or f"Alternative {oid}"),
				"lots": [cstr(x) for x in (alt.get("lots") or []) if cstr(x).strip()],
			}
		)
	return offers


def _section_url(pub_ref: str, key: str) -> str:
	if key == CBQ_KEY:
		from kentender_procurement.tender_configurations.services.confidential_business_questionnaire import (
			portal_cbq_url,
		)

		return portal_cbq_url(pub_ref)
	if key == DOCS_KEY:
		return f"/tenders/{quote(pub_ref, safe='')}/documents"
	if key == SECTION_KEY:
		return portal_fot_url(pub_ref)
	return f"/tenders/{quote(pub_ref, safe='')}/sections/{quote(key, safe='')}"


def _docs_acknowledged(responses: dict[str, Any], snapshot: dict[str, Any]) -> bool:
	has_docs = any(
		isinstance(s, dict) and cstr(s.get("section_key")) == DOCS_KEY for s in (snapshot.get("sections") or [])
	)
	if not has_docs:
		return True
	resp = responses.get(DOCS_KEY) if isinstance(responses.get(DOCS_KEY), dict) else {}
	if resp.get("acknowledged") or resp.get("section_status") == STATUS_COMPLETE:
		return True
	# lean docs ack shape
	if resp.get("package_acknowledged") or resp.get("acknowledgement"):
		return True
	return cstr(resp.get("section_status") or "") == STATUS_COMPLETE


def _statutory_complete(responses: dict[str, Any], snapshot: dict[str, Any]) -> bool:
	has = any(
		isinstance(s, dict) and cstr(s.get("section_key")) == STATUTORY_KEY for s in (snapshot.get("sections") or [])
	)
	if not has:
		return True
	from kentender_procurement.tender_configurations.services.statutory_declarations import (
		is_statutory_certified,
	)

	return is_statutory_certified(responses)


def _lots_confirmed(responses: dict[str, Any], snapshot: dict[str, Any]) -> bool:
	has = any(
		isinstance(s, dict) and cstr(s.get("section_key")) == LOTS_KEY for s in (snapshot.get("sections") or [])
	)
	if not has:
		return True
	resp = responses.get(LOTS_KEY) if isinstance(responses.get(LOTS_KEY), dict) else {}
	return bool(resp.get("confirmed") or resp.get("complete") or cstr(resp.get("section_status")) == STATUS_COMPLETE)


def build_readiness(
	*,
	pub_ref: str,
	snapshot: dict[str, Any],
	responses: dict[str, Any],
	fot_response: dict[str, Any],
	section_def: dict[str, Any],
) -> dict[str, Any]:
	incomplete: list[dict[str, str]] = []
	titles = {
		cstr(s.get("section_key")): cstr(s.get("title") or s.get("section_key"))
		for s in (snapshot.get("sections") or [])
		if isinstance(s, dict)
	}

	def add(key: str, reason: str = "") -> None:
		incomplete.append(
			{
				"section_key": key,
				"title": titles.get(key) or key.replace("_", " ").title(),
				"url": _section_url(pub_ref, key),
				"reason": reason,
			}
		)

	if not _docs_acknowledged(responses, snapshot):
		add(DOCS_KEY, "Acknowledge tender documents and addenda")
	if not _lots_confirmed(responses, snapshot):
		add(LOTS_KEY, "Confirm lot and alternative selection")

	entity = _cbq_bidder_entity(responses)
	signatory = _signatory_from_cbq(entity)
	if not entity.get("certified"):
		add(CBQ_KEY, "Certify the Confidential Business Questionnaire")
	else:
		if not signatory["name"] or not signatory["title"] or not signatory["authority_confirmed"]:
			add(CBQ_KEY, "Provide authorized signatory details")
		soe = signatory["state_owned_enterprise"]
		if soe == "yes" and not signatory["state_owned_itt47_affirmed"]:
			add(CBQ_KEY, "Confirm ITT 4.7 conditions for state-owned enterprise")
		elif soe not in ("yes", "no"):
			add(CBQ_KEY, "Answer state-owned enterprise question")

	if not _statutory_complete(responses, snapshot):
		add(STATUTORY_KEY, "Complete statutory declarations")

	price = responses.get(PRICE_KEY)
	if not is_price_schedule_complete(price):
		add(PRICE_KEY, "Complete the price schedule and discount declaration")

	comm_issues = validate_commissions(section_def, fot_response)
	choice = _normalize_commissions_choice(fot_response.get("commissions_choice"))
	if not choice:
		incomplete.append(
			{
				"section_key": SECTION_KEY,
				"title": "Commissions disclosure",
				"url": portal_fot_url(pub_ref),
				"reason": "Answer the commissions, gratuities and fees question",
			}
		)
	elif comm_issues:
		incomplete.append(
			{
				"section_key": SECTION_KEY,
				"title": "Commissions disclosure",
				"url": portal_fot_url(pub_ref),
				"reason": comm_issues[0]["message"],
			}
		)

	# Deduplicate by section_key keeping first reason
	seen: set[str] = set()
	unique: list[dict[str, str]] = []
	for row in incomplete:
		k = row["section_key"] + "|" + row.get("reason", "")
		sk = row["section_key"]
		if sk in seen and sk != SECTION_KEY:
			continue
		if sk != SECTION_KEY:
			seen.add(sk)
		unique.append(row)

	return {"ready": 0 if unique else 1, "incomplete_sections": unique, "incomplete_count": len(unique)}


def render_legal_terms(
	section_def: dict[str, Any],
	material: dict[str, Any],
	signatory: dict[str, Any],
) -> str:
	"""Render exact FoT clauses with substituted derived values (no paraphrasing)."""
	preamble = cstr(section_def.get("locked_legal_preamble") or "").strip()
	subs = {
		"procuring_entity_name": cstr(material.get("procuring_entity") or ""),
		"tenderer_name": cstr(material.get("tenderer") or signatory.get("legal_name") or ""),
		"tender_title": cstr(material.get("tender_title") or ""),
		"tender_reference": cstr(material.get("tender_reference") or ""),
		"tender_price": cstr(material.get("total_display") or ""),
		"validity_days": cstr(material.get("validity_days") or ""),
		"signatory_name": cstr(signatory.get("name") or ""),
		"signatory_title": cstr(signatory.get("title") or ""),
	}
	text = preamble
	for key, val in subs.items():
		text = text.replace("{" + key + "}", val or "—")

	clauses: list[str] = []
	for d in section_def.get("declarations") or []:
		if not isinstance(d, dict):
			continue
		if d.get("associated_section_key"):
			continue
		letter = cstr(d.get("clause_letter") or "").strip()
		title = cstr(d.get("title") or "").strip()
		body = cstr(d.get("text") or d.get("body") or title).strip()
		for key, val in subs.items():
			body = body.replace("{" + key + "}", val or "—")
		heading = f"({letter}) {title}".strip() if letter else title
		clauses.append(f"{heading}\n{body}" if body and body != title else heading)

	blocks = [text] if text else []
	if clauses:
		blocks.append("\n\n".join(clauses))
	if not blocks:
		blocks.append(
			"FORM OF TENDER\n\n"
			f"To: {subs['procuring_entity_name'] or '—'}\n\n"
			"We, the undersigned, declare that we have examined and have no reservations "
			"to the Tendering document, including Addenda issued, and offer to supply "
			f"in conformity with the Tendering document for {subs['tender_title'] or '—'}"
			f" ({subs['tender_reference'] or '—'}) at the total tender price of "
			f"{subs['tender_price'] or '—'}, valid for {subs['validity_days'] or '—'} days."
		)
	return "\n\n".join(blocks).strip()


def _material_offer(
	*,
	overview: dict[str, Any],
	section_def: dict[str, Any],
	signatory: dict[str, Any],
	price: dict[str, Any],
	offer: dict[str, Any],
) -> dict[str, Any]:
	tender_owned = section_def.get("tender_owned_values") if isinstance(section_def.get("tender_owned_values"), dict) else {}
	title = cstr(
		tender_owned.get("tender_name_and_identification")
		or overview.get("tender_title")
		or overview.get("title")
		or ""
	)
	ref = cstr(overview.get("published_tender_ref") or overview.get("publication_ref") or "")
	pe = cstr(
		tender_owned.get("procuring_entity_name")
		or overview.get("procuring_entity")
		or overview.get("procuring_entity_name")
		or ""
	)
	validity = cstr(tender_owned.get("tender_validity_days") or overview.get("bid_validity_period") or "")
	lots = offer.get("lots") if isinstance(offer.get("lots"), list) else []
	return {
		"tenderer": cstr(signatory.get("legal_name") or ""),
		"tender_title": title,
		"tender_reference": ref,
		"procuring_entity": pe,
		"offer_type": cstr(offer.get("offer_type") or "Base tender"),
		"offer_id": cstr(offer.get("offer_id") or OFFER_BASE_ID),
		"selected_lots": lots,
		"lots_label": ", ".join(cstr(x) for x in lots) if lots else "—",
		"total_display": price.get("total_display") or "Not completed",
		"grand_total": price.get("grand_total"),
		"currency": price.get("currency") or "",
		"discounts_label": price.get("discounts_label") or "Not completed",
		"validity_days": validity,
		"validity_label": f"{validity} Days" if validity else "—",
	}


def get_form_of_tender(publication_ref: str, *, offer_id: str | None = None) -> dict[str, Any]:
	_require_logged_in()
	from kentender_procurement.tender_configurations.services.published_tender_overview import (
		resolve_published_tender_backend,
	)

	overview = get_published_tender_overview(publication_ref)
	backend = resolve_published_tender_backend(publication_ref)
	pub_ref = cstr(overview.get("published_tender_ref") or publication_ref)
	tmpl = get_published_electronic_template(pub_ref)
	snapshot = tmpl["snapshot"]
	section_def = _fot_section(snapshot)

	cfg_id = cstr(backend.get("configuration_id") or tmpl["configuration_id"])
	draft = create_or_get_draft(cfg_id, schema_snapshot=snapshot, schema_hash=tmpl.get("hash"))
	bid_id = draft.get("bid_id")
	bid = frappe.get_doc("Electronic Bid Submission", bid_id) if bid_id else None
	responses = _parse_json(getattr(bid, "responses", None), {}) if bid else {}
	fot_resp = responses.get(SECTION_KEY) if isinstance(responses.get(SECTION_KEY), dict) else {}

	entity = _cbq_bidder_entity(responses)
	signatory = _signatory_from_cbq(entity)
	price = price_schedule_projection(responses.get(PRICE_KEY))
	offers = _offers_from_lots(responses, snapshot)
	instances = _ensure_instances(fot_resp, offers)

	active_id = cstr(offer_id or fot_resp.get("active_offer_id") or OFFER_BASE_ID)
	if active_id not in {cstr(o.get("offer_id")) for o in offers}:
		active_id = OFFER_BASE_ID
	active_offer = next((o for o in offers if cstr(o.get("offer_id")) == active_id), offers[0])
	active_instance = next((i for i in instances if cstr(i.get("offer_id")) == active_id), instances[0])

	material = _material_offer(
		overview=overview,
		section_def=section_def,
		signatory=signatory,
		price=price,
		offer=active_offer,
	)
	readiness = build_readiness(
		pub_ref=pub_ref,
		snapshot=snapshot,
		responses=responses,
		fot_response=fot_resp,
		section_def=section_def,
	)
	# Per-instance certify readiness still needs commissions answered globally
	instance_ready = bool(readiness["ready"]) and not bool(active_instance.get("certified"))

	legal_terms = render_legal_terms(section_def, material, signatory)
	choice = _normalize_commissions_choice(fot_resp.get("commissions_choice"))
	rows = fot_resp.get("commissions_rows") if isinstance(fot_resp.get("commissions_rows"), list) else []
	commissions_summary = "None declared." if choice == COMMISSIONS_NO else (
		f"{len(rows)} recipient(s) disclosed" if choice == COMMISSIONS_YES else ""
	)

	validation = validate_form_of_tender_response(section_def, fot_resp)
	certified = bool(active_instance.get("certified"))
	certified_at = cstr(active_instance.get("certified_at") or "")
	certified_at_display = ""
	if certified_at:
		try:
			certified_at_display = format_datetime(get_datetime(certified_at))
		except Exception:
			certified_at_display = certified_at

	status_chip = "Certified" if certified else (
		"Requires Recertification"
		if fot_resp.get("requires_recertification")
		else ("Pending Disclosure" if not choice else ("Ready to certify" if instance_ready else "Incomplete"))
	)

	return {
		"published_tender_ref": pub_ref,
		"bid_status": cstr(bid.status) if bid else None,
		"bid_id": bid_id,
		"bid_modified": str(bid.modified) if bid else None,
		"bid_sealed": 1 if bid and cstr(bid.status) == STATUS_SEALED else 0,
		"workspace_url": portal_workspace_url(pub_ref),
		"section_key": SECTION_KEY,
		"section_title": cstr(section_def.get("title") or "Form of Tender"),
		"bidder_instructions": cstr(
			section_def.get("bidder_instructions")
			or "Review the material terms of your offer and certify the Form of Tender."
		),
		"material_offer": material,
		"signatory": signatory,
		"readiness": readiness,
		"commissions": {
			"choice": choice,
			"rows": rows,
			"summary": commissions_summary,
			"columns": _commission_columns(section_def),
		},
		"legal_terms": legal_terms,
		"offers": offers,
		"instances": instances,
		"active_offer_id": active_id,
		"certification": {
			"certified": 1 if certified else 0,
			"certified_at": certified_at,
			"certified_at_display": certified_at_display,
			"certified_by": cstr(active_instance.get("certified_by") or ""),
			"certifier_name": cstr(active_instance.get("certifier_name") or signatory.get("name") or ""),
			"certifier_title": cstr(active_instance.get("certifier_title") or signatory.get("title") or ""),
			"offer_id": active_id,
			"offer_type": cstr(active_offer.get("offer_type") or ""),
			"requires_recertification": 1 if fot_resp.get("requires_recertification") else 0,
		},
		"can_certify": 1 if instance_ready else 0,
		"status_chip": status_chip,
		"section_status": validation["section_status"],
		"validation": validation,
		"response": {
			"commissions_choice": choice,
			"commissions_rows": rows,
			"instances": instances,
			"active_offer_id": active_id,
			"requires_recertification": 1 if fot_resp.get("requires_recertification") else 0,
		},
		"edit_links": {
			"cbq": _section_url(pub_ref, CBQ_KEY),
			"lots": _section_url(pub_ref, LOTS_KEY),
			"price_schedule": _section_url(pub_ref, PRICE_KEY),
			"documents": _section_url(pub_ref, DOCS_KEY),
			"statutory_declarations": _section_url(pub_ref, STATUTORY_KEY),
		},
		"read_only": 1 if bid and cstr(bid.status) == STATUS_SEALED else 0,
		"save_confirms": False,
		"save_submits": False,
		# Compatibility stubs for transitional tests (no duplicate inputs in UI).
		"bidder_owned_fields": [],
		"declarations": [],
		"tender_owned_values": section_def.get("tender_owned_values") or {},
		"locked_legal_preamble": cstr(section_def.get("locked_legal_preamble") or ""),
		"price_summary": {
			"message": "Totals are derived from the Price Schedule when completed.",
			"source": "price_schedule_when_completed",
			"grand_total": price.get("grand_total"),
			"total_excluding_vat": (price.get("grand_total") if isinstance(price, dict) else None),
		},
		"repeatable_tables": section_def.get("repeatable_tables") or [],
	}


def _sanitize_fot_payload(payload: dict[str, Any], section_def: dict[str, Any]) -> dict[str, Any]:
	choice = _normalize_commissions_choice(payload.get("commissions_choice"))
	rows_in = payload.get("commissions_rows") if isinstance(payload.get("commissions_rows"), list) else []
	cols = [cstr(c.get("field_key")) for c in _commission_columns(section_def)]
	rows = []
	for row in rows_in:
		if not isinstance(row, dict):
			continue
		clean = {ck: cstr(row.get(ck) or "").strip() for ck in cols if ck}
		if any(clean.values()):
			rows.append(clean)
	if choice == COMMISSIONS_NO:
		rows = []
	active = cstr(payload.get("active_offer_id") or OFFER_BASE_ID).strip() or OFFER_BASE_ID
	return {
		"commissions_choice": choice,
		"commissions_rows": rows,
		"active_offer_id": active,
	}


def save_form_of_tender(
	publication_ref: str,
	payload: dict[str, Any] | str | None = None,
	*,
	expected_modified: str | None = None,
) -> dict[str, Any]:
	"""Save FoT-owned commissions disclosure only (does not certify)."""
	_require_logged_in()
	if isinstance(payload, str):
		payload = _parse_json(payload, {})
	payload = payload if isinstance(payload, dict) else {}

	dto = get_form_of_tender(publication_ref)
	if dto.get("read_only"):
		frappe.throw(frappe._("Sealed bids cannot be edited."), title="BID_IMMUTABLE")

	from kentender_procurement.tender_configurations.services.published_tender_overview import (
		resolve_published_tender_backend,
	)

	backend = resolve_published_tender_backend(cstr(dto.get("published_tender_ref") or publication_ref))
	cfg_id = cstr(backend.get("configuration_id") or "")
	draft = create_or_get_draft(cfg_id)
	bid_id = cstr(draft.get("bid_id") or "")
	doc = _get_bid(bid_id)
	_assert_bid_owner(doc)

	if expected_modified:
		current = str(doc.modified)
		exp = cstr(expected_modified).strip()
		try:
			if get_datetime(exp) < get_datetime(current) and exp != current:
				frappe.throw(
					frappe._("This Form of Tender was updated elsewhere. Reload and try again."),
					title="KT_FOT_CONFLICT",
				)
		except Exception:
			if exp != current:
				frappe.throw(
					frappe._("This Form of Tender was updated elsewhere. Reload and try again."),
					title="KT_FOT_CONFLICT",
				)

	tmpl = get_published_electronic_template(cstr(dto["published_tender_ref"]))
	section_def = _fot_section(tmpl["snapshot"])
	clean = _sanitize_fot_payload(payload, section_def)

	responses = _parse_json(doc.responses, {})
	prev = responses.get(SECTION_KEY) if isinstance(responses.get(SECTION_KEY), dict) else {}
	prev_choice = _normalize_commissions_choice(prev.get("commissions_choice"))
	prev_rows = prev.get("commissions_rows") if isinstance(prev.get("commissions_rows"), list) else []

	offers = _offers_from_lots(responses, tmpl["snapshot"])
	instances = _ensure_instances(prev, offers)

	material_changed = (
		prev_choice != clean["commissions_choice"]
		or json.dumps(prev_rows, sort_keys=True, default=str)
		!= json.dumps(clean["commissions_rows"], sort_keys=True, default=str)
	)
	if material_changed and any(i.get("certified") for i in instances):
		instances = _withdraw_instances(instances, reason="commissions_changed")

	stored = {
		**prev,
		**clean,
		"instances": instances,
		"requires_recertification": 1 if any(not i.get("certified") and i.get("certification_history") for i in instances) and not all(i.get("certified") for i in instances) and any(i.get("certification_history") for i in instances) else (0 if all(i.get("certified") for i in instances) else int(bool(prev.get("requires_recertification")))),
	}
	# Recompute requires_recertification simply
	if any(i.get("certified") for i in instances):
		stored["requires_recertification"] = 0
	elif any(i.get("certification_history") for i in instances):
		stored["requires_recertification"] = 1
	else:
		stored["requires_recertification"] = 0

	validation = validate_form_of_tender_response(section_def, stored)
	stored["section_status"] = validation["section_status"]
	stored["validation_errors"] = validation["issues"]
	stored["confirmed"] = False
	stored["submitted"] = False

	responses[SECTION_KEY] = stored
	doc.responses = json.dumps(responses, ensure_ascii=False)
	_append_audit(
		doc,
		"section_saved",
		{
			"section_key": SECTION_KEY,
			"section_status": validation["section_status"],
			"issue_count": validation["issue_count"],
			"commissions_choice": clean["commissions_choice"],
		},
	)
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	out = get_form_of_tender(publication_ref, offer_id=clean.get("active_offer_id"))
	out["saved"] = True
	return out


def _withdraw_instances(instances: list[dict[str, Any]], *, reason: str) -> list[dict[str, Any]]:
	out = []
	for inst in instances:
		row = dict(inst)
		if row.get("certified"):
			history = row.get("certification_history") if isinstance(row.get("certification_history"), list) else []
			history.append(
				{
					"withdrawn_at": str(now_datetime()),
					"reason": reason,
					"legal_record": row.get("legal_record"),
					"certified_at": row.get("certified_at"),
					"certified_by": row.get("certified_by"),
				}
			)
			row["certification_history"] = history
			row["certified"] = 0
			row["certified_at"] = ""
			row["certified_by"] = ""
			row["legal_record"] = None
		out.append(row)
	return out


def invalidate_fot_certifications(bid_doc, *, reason: str = "source_changed") -> bool:
	"""Withdraw all FoT certifications on a bid. Returns True if anything changed."""
	responses = _parse_json(getattr(bid_doc, "responses", None), {})
	fot = responses.get(SECTION_KEY) if isinstance(responses.get(SECTION_KEY), dict) else {}
	instances = _instances_from_response(fot)
	if not any(i.get("certified") for i in instances) and not fot.get("certified"):
		return False
	withdrawn = _withdraw_instances(instances or [{"offer_id": OFFER_BASE_ID, "certified": 1, **fot}], reason=reason)
	fot = dict(fot)
	fot["instances"] = withdrawn
	fot["certified"] = 0
	fot["requires_recertification"] = 1
	fot["section_status"] = STATUS_REQUIRES_RECERTIFICATION
	responses[SECTION_KEY] = fot
	bid_doc.responses = json.dumps(responses, ensure_ascii=False)
	_append_audit(
		bid_doc,
		"fot_certification_invalidated",
		{"section_key": SECTION_KEY, "reason": reason, "instances": len(withdrawn)},
	)
	return True


def maybe_invalidate_fot_on_source_save(bid_doc, *, source_section: str) -> None:
	if invalidate_fot_certifications(bid_doc, reason=f"{source_section}_changed"):
		bid_doc.save(ignore_permissions=True)


def certify_form_of_tender(
	publication_ref: str,
	*,
	offer_id: str | None = None,
	expected_modified: str | None = None,
) -> dict[str, Any]:
	"""Atomic certification of one FoT instance (base or alternative)."""
	_require_logged_in()
	dto = get_form_of_tender(publication_ref, offer_id=offer_id)
	if dto.get("read_only"):
		frappe.throw(frappe._("Sealed bids cannot be edited."), title="BID_IMMUTABLE")
	if not dto.get("can_certify"):
		frappe.throw(
			frappe._("Complete all prerequisites and the commissions disclosure before certifying."),
			title="KT_FOT_NOT_READY",
		)

	from kentender_procurement.tender_configurations.services.published_tender_overview import (
		resolve_published_tender_backend,
	)

	backend = resolve_published_tender_backend(cstr(dto.get("published_tender_ref") or publication_ref))
	cfg_id = cstr(backend.get("configuration_id") or "")
	draft = create_or_get_draft(cfg_id)
	doc = _get_bid(cstr(draft.get("bid_id") or ""))
	_assert_bid_owner(doc)

	if expected_modified:
		current = str(doc.modified)
		exp = cstr(expected_modified).strip()
		try:
			if get_datetime(exp) < get_datetime(current) and exp != current:
				frappe.throw(
					frappe._("This Form of Tender was updated elsewhere. Reload and try again."),
					title="KT_FOT_CONFLICT",
				)
		except Exception:
			if exp != current:
				frappe.throw(
					frappe._("This Form of Tender was updated elsewhere. Reload and try again."),
					title="KT_FOT_CONFLICT",
				)

	signatory = dto.get("signatory") or {}
	if not signatory.get("name") or not signatory.get("title") or not signatory.get("authority_confirmed"):
		frappe.throw(
			frappe._("Authorized signatory details are incomplete in the Confidential Business Questionnaire."),
			title="KT_FOT_SIGNATORY",
		)

	active_id = cstr(offer_id or dto.get("active_offer_id") or OFFER_BASE_ID)
	material = dto.get("material_offer") or {}
	legal_text = cstr(dto.get("legal_terms") or "")
	comm = dto.get("commissions") or {}
	now = now_datetime()
	legal_record = {
		"material_offer": deepcopy(material),
		"legal_text": legal_text,
		"commissions_choice": comm.get("choice"),
		"commissions_rows": deepcopy(comm.get("rows") or []),
		"commissions_summary": (
			"None declared." if comm.get("choice") == COMMISSIONS_NO else comm.get("summary")
		),
		"signatory_name": signatory.get("name"),
		"signatory_title": signatory.get("title"),
		"offer_id": active_id,
		"offer_type": material.get("offer_type"),
		"certified_by": frappe.session.user,
		"certified_at": str(now),
	}

	responses = _parse_json(doc.responses, {})
	fot = responses.get(SECTION_KEY) if isinstance(responses.get(SECTION_KEY), dict) else {}
	tmpl = get_published_electronic_template(cstr(dto["published_tender_ref"]))
	offers = _offers_from_lots(responses, tmpl["snapshot"])
	instances = _ensure_instances(fot, offers)
	updated = []
	found = False
	for inst in instances:
		row = dict(inst)
		if cstr(row.get("offer_id")) == active_id:
			found = True
			row["certified"] = 1
			row["certified_at"] = str(now)
			row["certified_by"] = frappe.session.user
			row["certifier_name"] = signatory.get("name")
			row["certifier_title"] = signatory.get("title")
			row["legal_record"] = legal_record
		updated.append(row)
	if not found:
		frappe.throw(frappe._("Unknown offer for Form of Tender certification."), title="KT_FOT_OFFER")

	fot = dict(fot)
	fot["instances"] = updated
	fot["active_offer_id"] = active_id
	fot["requires_recertification"] = 0
	fot["commissions_choice"] = comm.get("choice")
	fot["commissions_rows"] = comm.get("rows") or []
	section_def = _fot_section(tmpl["snapshot"])
	validation = validate_form_of_tender_response(section_def, fot)
	fot["section_status"] = validation["section_status"]
	fot["validation_errors"] = []
	responses[SECTION_KEY] = fot
	doc.responses = json.dumps(responses, ensure_ascii=False)
	_append_audit(
		doc,
		"fot_certified",
		{
			"section_key": SECTION_KEY,
			"event_type": "fot_certified",
			"offer_id": active_id,
			"certified_by": frappe.session.user,
			"section_status": validation["section_status"],
		},
	)
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	out = get_form_of_tender(publication_ref, offer_id=active_id)
	out["certified"] = True
	return out


def seed_price_schedule_for_tests(
	publication_ref: str,
	*,
	grand_total: float | int | str = 1000,
	currency: str = "KES",
	discounts_offered: str = "no",
) -> dict[str, Any]:
	"""Test helper: mark Price Schedule complete with discount declaration."""
	_require_logged_in()
	dto = get_form_of_tender(publication_ref)
	from kentender_procurement.tender_configurations.services.published_tender_overview import (
		resolve_published_tender_backend,
	)

	backend = resolve_published_tender_backend(cstr(dto.get("published_tender_ref") or publication_ref))
	draft = create_or_get_draft(cstr(backend.get("configuration_id") or ""))
	doc = _get_bid(cstr(draft.get("bid_id") or ""))
	_assert_bid_owner(doc)
	price_payload = {
		"complete": True,
		"complete_confirmed": 1,
		"section_status": STATUS_COMPLETE,
		"discounts_offered": discounts_offered,
		"discount_description": "" if discounts_offered == "no" else "Early payment",
		"discount_applicability": "entire_tender",
		"discount_amount_or_percent": "" if discounts_offered == "no" else "2%",
		"discount_currency": currency,
		"discount_calculation_method": "" if discounts_offered == "no" else "Percent of grand total",
		"totals": {"grand_total": grand_total, "currency": currency},
		"computed": {
			"by_currency": {
				currency: {
					"supply_subtotal": str(grand_total),
					"recurrent_subtotal": "0.00",
					"grand_total": str(grand_total),
				}
			},
			"totals": {"grand_total": grand_total, "currency": currency},
		},
		"currency": currency,
		"lines": {},
	}
	responses = _parse_json(doc.responses, {})
	responses[PRICE_KEY] = price_payload
	doc.responses = json.dumps(responses, ensure_ascii=False)
	invalidate_fot_certifications(doc, reason="price_schedule_changed")
	responses = _parse_json(doc.responses, {})
	responses[PRICE_KEY] = price_payload
	doc.responses = json.dumps(responses, ensure_ascii=False)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return price_payload


def assert_fot_not_confirmed_on_save(response: dict[str, Any]) -> bool:
	return not bool(response.get("confirmed")) and not bool(response.get("submitted"))
