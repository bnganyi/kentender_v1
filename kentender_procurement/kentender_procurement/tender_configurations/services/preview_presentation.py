# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Bidder-facing presentation layer for WG-03 tender document preview.

Section-specific renderers produce legal tender wording — not raw DB dumps
or generic admin summary tables.
"""

from __future__ import annotations

import html
import re
from datetime import datetime
from typing import Any

from frappe.utils import cstr

REQUIRED_PREVIEW_SECTIONS = frozenset(
	{"tds", "evaluation", "price", "itt", "gcc", "inventory"}
)

FORBIDDEN_OUTPUT_MARKERS = (
	"No configured rows.",
	"Fixture locked",
	"fixture locked",
	"Standard ITT text.",
	"Standard GCC text.",
	"See IT Requirements above.",
	"Locked standard text from bound STD version.",
	"No additional requirements are specified under this section.",
	"Price for requirement:",
	"Technical compliance for:",
	"Readiness issue:",
	"generation_blocked",
	"kt-preview-exception",
	"Source NSSF",
	"PoC submission deadline",
	"Confirm Yes/No, cite reference",
	"tenderer shall prepare the tender in accordance",
	"[source_id=",
	"KenTender PoC applies",
	"Notes to the Procuring Entity",
	"demo_submission_deadline",
	"source_submission_deadline",
	"PoC uses",
	"advanced for demo",
)

PE_ONLY_CONTRACT_FORM_MARKERS = (
	"Notes to the Procuring Entity on preparing the Contract Forms",
	"Notes to the Procuring Entity",
)

ALLOWED_PRICE_UNITS = frozenset(
	{"Users", "Lump sum", "Per month", "Per GB/month", "Annual", "Lot"}
)

# Never render these TDS keys in the bidder-facing PDF (AUDIT_ONLY).
TDS_AUDIT_ONLY_KEYS = frozenset(
	{
		"opening_notes",
		"poc_audit_notes",
		"source_deadline_note",
		"demo_override_note",
	}
)

LOCKED_STD_UNAVAILABLE_MSG = (
	"Locked STD text unavailable for {section}. "
	"Load approved STD Engine text before generating preview."
)

TRUNCATION_HINT_RE = re.compile(
	r"(?:\b\w{1,3}$)|(?:\bFlo$)|(?:\bas a fu$)|(?:\bproject$)|(?:,\s*$)",
	re.IGNORECASE,
)


def generation_block(
	*,
	blocking_area: str,
	message: str,
	action: str,
	owner_step: str | None = None,
) -> dict[str, str]:
	"""Structured block for UI banner — never embed in tender HTML/PDF.

	When ``owner_step`` (or a CFG-NN prefix in ``blocking_area``) resolves, the
	preview banner CTA routes to that configuration step — not WG-01 readiness,
	which can still show green while preview generation is blocked.
	"""
	from kentender_procurement.tender_configurations.services.configuration_steps import (
		STEP_ROUTES,
	)

	step = cstr(owner_step or "").strip().upper()
	if not step:
		m = re.match(r"(CFG-\d+)\b", cstr(blocking_area or ""), re.IGNORECASE)
		if m:
			step = m.group(1).upper()
	route = STEP_ROUTES.get(step, "") if step else ""
	cta = f"Open {step}" if step and route else "Open Readiness Check"
	return {
		"status": "generation_blocked",
		"blocking_area": blocking_area,
		"message": message,
		"action": action,
		"owner_step": step,
		"owner_route": route,
		"cta_label": cta,
	}

INTERNAL_ID_RE = re.compile(
	r"\b(REQ|PRI|PS|ITEM|EV|CRIT)[-_]?\d+\b",
	re.IGNORECASE,
)

TECHNICAL_CATEGORY_MARKERS = (
	"technical",
	"infrastructure",
	"security",
	"compliance",
	"support",
	"warranty",
	"integration",
	"deliverable",
	"acceptance",
)

IS_CATEGORY_MARKERS = (
	"business",
	"functional",
	"system",
	"informational",
	"background",
)

TDS_ITEM_LABELS: dict[str, str] = {
	"contact_officer": "Contact officer",
	"contact_email": "Contact email",
	"clarification_submission_method": "Clarification method",
	"clarification_deadline": "Clarification deadline",
	"pre_tender_meeting": "Pre-tender meeting",
	"pre_tender_meeting_details": "Pre-tender meeting details",
	"tender_publication_date": "Tender publication date",
	"tender_submission_deadline": "Submission deadline",
	"tender_opening_datetime": "Tender opening date and time",
	"bid_validity_period": "Bid validity",
	"submission_channel": "Submission channel",
	"submission_language": "Language",
	"tender_currency": "Currency",
	"alternative_tenders_allowed": "Alternative tenders",
	"lots_allowed": "Lots allowed",
	"joint_ventures_allowed": "Joint ventures",
	"eligible_tenderers": "Eligible tenderers",
	"reserved_procurement": "Reserved procurement",
	"reservation_category": "Reservation category",
	"local_participation_requirement": "Local participation requirement",
	"tender_security_required": "Tender security",
	"professional_indemnity_required": "Professional indemnity cover",
	"professional_indemnity_amount": "Professional indemnity amount",
	"professional_indemnity_evidence": "Professional indemnity evidence",
	"margin_of_preference_applies": "Margin of preference",
	"preference_basis": "Preference basis",
	"preference_evidence_required": "Preference evidence",
	"opening_method": "Opening method",
	"opening_location": "Opening location",
	"opening_attendance_allowed": "Opening attendance",
	"opening_notes": "Opening notes",
}

TDS_COMPOSITE_CONSUMED = frozenset(
	{
		"bid_validity_unit",
		"tender_security_type",
		"tender_security_amount",
		"tender_security_currency",
		"tender_security_validity_period",
		"tender_security_validity_unit",
	}
)

TDS_ORDER = (
	"contact_officer",
	"contact_email",
	"clarification_submission_method",
	"clarification_deadline",
	"pre_tender_meeting",
	"pre_tender_meeting_details",
	"submission_channel",
	"tender_submission_deadline",
	"opening_method",
	"tender_opening_datetime",
	"opening_location",
	"opening_attendance_allowed",
	"tender_security_required",
	"professional_indemnity_required",
	"professional_indemnity_amount",
	"professional_indemnity_evidence",
	"bid_validity_period",
	"submission_language",
	"tender_currency",
	"alternative_tenders_allowed",
	"lots_allowed",
	"joint_ventures_allowed",
	"eligible_tenderers",
	"reserved_procurement",
	"reservation_category",
	"local_participation_requirement",
	"margin_of_preference_applies",
	"preference_basis",
	"preference_evidence_required",
	"tender_publication_date",
)


def _esc(val: Any) -> str:
	return html.escape(cstr(val or ""), quote=True)


def _is_blank(val: Any) -> bool:
	s = cstr(val or "").strip()
	return not s or s in ("—", "-", "N/A", "n/a")


def format_currency_amount(amount: Any, currency: str = "KES") -> str:
	"""Format money as 'KES 50,000'."""
	cur = cstr(currency or "KES").strip() or "KES"
	raw = cstr(amount or "").strip().replace(",", "")
	if not raw:
		return cur
	try:
		number = float(raw)
		if number.is_integer():
			formatted = f"{int(number):,}"
		else:
			formatted = f"{number:,.2f}"
		return f"{cur} {formatted}"
	except ValueError:
		return f"{cur} {raw}"


def format_datetime_bidder(value: Any) -> str:
	"""Format ISO-ish datetimes as '30 August 2026, 3:30 PM EAT'."""
	raw = cstr(value or "").strip()
	if not raw or raw in ("—", "-"):
		return ""
	normalized = raw.replace("Z", "+00:00") if raw.endswith("Z") else raw
	dt = None
	for candidate, fmt in (
		(normalized[:19], "%Y-%m-%dT%H:%M:%S"),
		(normalized[:16], "%Y-%m-%dT%H:%M"),
		(normalized[:19], "%Y-%m-%d %H:%M:%S"),
		(normalized[:16], "%Y-%m-%d %H:%M"),
		(normalized[:10], "%Y-%m-%d"),
	):
		try:
			dt = datetime.strptime(candidate, fmt)
			break
		except ValueError:
			continue
	if dt is None:
		try:
			dt = datetime.fromisoformat(normalized)
		except ValueError:
			return raw
	day = dt.day
	month = dt.strftime("%B")
	year = dt.year
	has_time = "T" in raw or (len(raw) > 10 and " " in raw)
	if has_time or dt.hour or dt.minute:
		hour12 = dt.strftime("%I").lstrip("0") or "12"
		minute = dt.strftime("%M")
		ampm = dt.strftime("%p")
		return f"{day} {month} {year}, {hour12}:{minute} {ampm} EAT"
	return f"{day} {month} {year}"


def _requirement_display_title(req: dict[str, Any]) -> str:
	"""Prefer a bidder-facing title; CFG-03 mock rows sometimes store REQ-NNN in ``title``."""
	title = cstr(req.get("title") or req.get("name") or "").strip()
	desc = cstr(
		req.get("description") or req.get("requirement_statement") or ""
	).strip()
	if title and not _is_internal_label(title):
		return title
	# Short description used as the human label when title is an internal id.
	if desc and not _is_internal_label(desc) and len(desc) <= 160 and "\n" not in desc:
		return desc
	return title or desc


def _requirement_title_map(requirements: list[dict[str, Any]]) -> dict[str, str]:
	out: dict[str, str] = {}
	for req in requirements:
		rid = cstr(req.get("requirement_id") or req.get("code") or "").strip()
		title = _requirement_display_title(req)
		if rid and title and not _is_internal_label(title):
			out[rid.upper()] = title
			out[rid] = title
	return out


def expand_requirement_reference(text: str, req_map: dict[str, str]) -> str:
	"""Replace REQ-001 style tokens / phrases with requirement titles."""
	value = cstr(text or "").strip()
	if not value:
		return ""

	def _lookup(token: str) -> str:
		return req_map.get(token.upper()) or req_map.get(token) or ""

	# "REQ-001 technical compliance" → "<title> technical compliance"
	m_ref_first = re.match(
		r"^(REQ[-_]?\d+)\s+technical compliance\.?$",
		value,
		re.IGNORECASE,
	)
	if m_ref_first:
		title = _lookup(m_ref_first.group(1))
		if title:
			return f"{title} technical compliance"

	def _repl(match: re.Match) -> str:
		token = match.group(0)
		return _lookup(token) or token

	expanded = INTERNAL_ID_RE.sub(_repl, value)
	# "Technical compliance for: <title|REQ>" → "<title> technical compliance"
	m = re.match(
		r"^(Technical compliance for|Price for requirement)\s*:\s*(.+)$",
		expanded,
		re.IGNORECASE,
	)
	if m:
		subject = m.group(2).strip()
		subject = _lookup(subject) or subject
		if m.group(1).lower().startswith("technical"):
			return f"{subject} technical compliance"
		return subject
	return expanded


def _is_internal_label(value: str) -> bool:
	s = cstr(value or "").strip()
	if not s:
		return True
	if re.fullmatch(r"(REQ|PRI|PS|ITEM|EV|CRIT)[-_]?\d+", s, re.I):
		return True
	if re.fullmatch(r"Item\s+\d+", s, re.I):
		return True
	return False


def classify_requirement(req: dict[str, Any]) -> str:
	"""Return 'technical' or 'information_system' (mutually exclusive)."""
	category = cstr(req.get("category_label") or "").strip().lower()
	for marker in TECHNICAL_CATEGORY_MARKERS:
		if marker in category:
			return "technical"
	for marker in IS_CATEGORY_MARKERS:
		if marker in category:
			return "information_system"
	# Default: treat unspecified as information-system functional/business bucket.
	return "information_system"


def split_requirements(
	requirements: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
	is_rows: list[dict[str, Any]] = []
	tech_rows: list[dict[str, Any]] = []
	for req in requirements:
		if classify_requirement(req) == "technical":
			tech_rows.append(req)
		else:
			is_rows.append(req)
	return is_rows, tech_rows


def format_tds_clause(key: str, values: dict[str, Any]) -> str | None:
	"""Clause-aware TDS requirement wording."""
	raw = values.get(key)
	if key in TDS_COMPOSITE_CONSUMED:
		return None

	if key == "contact_officer":
		v = cstr(raw or "").strip()
		return f"Enquiries shall be directed to {v}." if not _is_blank(v) else None
	if key == "contact_email":
		v = cstr(raw or "").strip()
		return f"Written contact may be made at {v}." if not _is_blank(v) else None
	if key == "clarification_submission_method":
		v = cstr(raw or "").strip()
		return (
			f"Clarifications shall be submitted through the {v}."
			if not _is_blank(v)
			else None
		)
	if key == "clarification_deadline":
		dt = format_datetime_bidder(raw)
		return (
			f"Clarifications must be submitted through the E-Procurement Portal by {dt}."
			if dt
			else None
		)
	if key == "pre_tender_meeting":
		v = cstr(raw or "").strip().lower()
		if _is_blank(v):
			return None
		if v in ("no", "n", "false", "0"):
			return "No pre-tender meeting will be held for this tender."
		details = cstr(values.get("pre_tender_meeting_details") or "").strip()
		if details:
			return f"A pre-tender meeting will be held. {details}"
		return "A pre-tender meeting will be held as notified by the Procuring Entity."
	if key == "pre_tender_meeting_details":
		# Consumed into pre_tender_meeting clause when meeting = Yes.
		return None
	if key == "submission_channel":
		v = cstr(raw or "").strip()
		return f"Tenders shall be submitted through the {v}." if not _is_blank(v) else None
	if key == "tender_submission_deadline":
		dt = format_datetime_bidder(raw)
		return f"Tenders must be submitted by {dt}." if dt else None
	if key == "opening_method":
		v = cstr(raw or "").strip()
		return f"Tenders will be opened by {v}." if not _is_blank(v) else None
	if key == "tender_opening_datetime":
		dt = format_datetime_bidder(raw)
		return f"Tender opening will take place on {dt}." if dt else None
	if key == "opening_location":
		v = cstr(raw or "").strip()
		return f"Opening will be conducted at {v}." if not _is_blank(v) else None
	if key == "opening_attendance_allowed":
		v = cstr(raw or "").strip()
		if _is_blank(v):
			return None
		if v.lower() in ("yes", "y", "true", "1"):
			return "Tenderers may attend the opening as provided in the Instructions to Tenderers."
		return "Opening attendance by tenderers is not permitted for this tender."
	if key == "tender_security_required":
		req = cstr(raw or "").strip()
		if _is_blank(req):
			return None
		if req.lower() in ("no", "n", "false", "0"):
			return "A tender security is not required for this tender."
		amount = cstr(values.get("tender_security_amount") or "").strip()
		currency = cstr(values.get("tender_security_currency") or "KES").strip() or "KES"
		validity = cstr(values.get("tender_security_validity_period") or "").strip()
		unit = cstr(values.get("tender_security_validity_unit") or "days").strip() or "days"
		money = format_currency_amount(amount, currency) if amount else ""
		if money and validity:
			return (
				f"A tender security is required in the amount of {money} "
				f"and must remain valid for {validity} {unit}."
			)
		if money:
			return f"A tender security is required in the amount of {money}."
		return "A tender security is required as specified by the Procuring Entity."
	if key == "professional_indemnity_required":
		v = cstr(raw or "").strip()
		if _is_blank(v):
			return None
		if v.lower() in ("no", "n", "false", "0", "not required"):
			return "Professional indemnity cover is not required for this tender."
		return "Professional indemnity cover: Required."
	if key == "professional_indemnity_amount":
		amount = cstr(raw or "").strip()
		if _is_blank(amount):
			return None
		money = format_currency_amount(amount, "KES")
		return f"Professional indemnity amount: {money}."
	if key == "professional_indemnity_evidence":
		v = cstr(raw or "").strip()
		if _is_blank(v):
			return None
		return v if v.lower().startswith("evidence") else f"Evidence: {v}"
	if key == "bid_validity_period":
		period = cstr(raw or "").strip()
		unit = cstr(values.get("bid_validity_unit") or "days").strip() or "days"
		if _is_blank(period):
			return None
		return f"Tenders shall remain valid for {period} {unit} after the submission deadline."
	if key == "submission_language":
		v = cstr(raw or "").strip()
		return f"The tender shall be prepared in {v}." if not _is_blank(v) else None
	if key == "tender_currency":
		v = cstr(raw or "").strip()
		return f"Prices shall be quoted in {v}." if not _is_blank(v) else None
	if key == "alternative_tenders_allowed":
		v = cstr(raw or "").strip()
		if _is_blank(v):
			return None
		if v.lower() in ("yes", "y", "true", "1"):
			return "Alternative tenders are permitted subject to the Instructions to Tenderers."
		return "Alternative tenders are not permitted."
	if key == "lots_allowed":
		v = cstr(raw or "").strip()
		if _is_blank(v):
			return None
		if v.lower() in ("yes", "y", "true", "1"):
			return "Tenders may be submitted for one or more lots as specified."
		return "This tender is not structured as multiple lots for selective bidding."
	if key == "joint_ventures_allowed":
		v = cstr(raw or "").strip()
		if _is_blank(v):
			return None
		if v.lower() in ("yes", "y", "true", "1"):
			return "Joint ventures and consortia are permitted subject to the eligibility rules."
		return "Joint ventures are not permitted for this tender."
	if key == "eligible_tenderers":
		v = cstr(raw or "").strip()
		return v if not _is_blank(v) else None
	if key == "reserved_procurement":
		v = cstr(raw or "").strip()
		if _is_blank(v):
			return None
		if v.lower() in ("no", "n", "false", "0"):
			return "This procurement is not reserved."
		cat = cstr(values.get("reservation_category") or "").strip()
		if cat:
			return f"This procurement is reserved under the category: {cat}."
		return "This procurement is reserved as specified by the Procuring Entity."
	if key == "reservation_category":
		return None
	if key == "local_participation_requirement":
		v = cstr(raw or "").strip()
		return v if not _is_blank(v) else None
	if key == "margin_of_preference_applies":
		v = cstr(raw or "").strip()
		if _is_blank(v):
			return None
		if v.lower() in ("yes", "y", "true", "1"):
			basis = cstr(values.get("preference_basis") or "").strip()
			if basis:
				return f"Margin of preference applies on the following basis: {basis}."
			return "Margin of preference applies to this tender."
		return "Margin of preference does not apply to this tender."
	if key in ("preference_basis", "preference_evidence_required"):
		# Consumed / optional follow-on only when margin applies and not already in clause.
		if key == "preference_evidence_required":
			applies = cstr(values.get("margin_of_preference_applies") or "").strip().lower()
			v = cstr(raw or "").strip()
			if applies in ("yes", "y", "true", "1") and not _is_blank(v):
				return f"Preference evidence required: {v}."
		return None
	if key in TDS_AUDIT_ONLY_KEYS:
		return None
	if key == "tender_publication_date":
		v = cstr(raw or "").strip()
		if _is_blank(v) or v == "—":
			return None
		dt = format_datetime_bidder(v) or v
		return f"The tender was published on {dt}."
	if _is_blank(raw):
		return None
	return cstr(raw).strip()


def render_tds_section(tds: dict[str, Any]) -> tuple[str, str | None]:
	rows: list[tuple[str, str]] = []
	seen: set[str] = set()
	for key in TDS_ORDER:
		if key in seen:
			continue
		seen.add(key)
		label = TDS_ITEM_LABELS.get(key)
		if not label:
			continue
		clause = format_tds_clause(key, tds)
		if clause is None:
			continue
		rows.append((label, clause))
	for key, label in sorted(TDS_ITEM_LABELS.items(), key=lambda kv: kv[1]):
		if key in seen or key in TDS_COMPOSITE_CONSUMED:
			continue
		clause = format_tds_clause(key, tds)
		if clause is None:
			continue
		rows.append((label, clause))
	if not rows:
		return (
			"",
			generation_block(
				blocking_area="CFG-02 Tender Data Sheet",
				message="Tender Data Sheet has no bidder-facing content.",
				action="Complete CFG-02 before generating the preview.",
			),
		)
	intro = (
		"<p>The following Tender Data Sheet provisions apply to this tender and shall be "
		"read with the Instructions to Tenderers.</p>"
	)
	return intro + _bidder_table(["TDS item", "Requirement"], rows), None


def _scoring_basis_line(item: dict[str, Any]) -> str:
	basis = cstr(item.get("evaluation_basis_label") or item.get("evaluation_basis") or "").strip()
	marks = cstr(item.get("marks") or "").strip()
	rule = cstr(
		item.get("pass_fail_rule")
		or item.get("financial_evaluation_rule")
		or item.get("preference_rule")
		or item.get("marks_or_rule_display")
		or ""
	).strip()
	evidence = cstr(
		item.get("evidence_instruction") or item.get("bidder_evidence") or ""
	).strip()
	if marks and "scored" in basis.lower():
		line = f"Scored out of {marks} marks based on compliance with the technical requirement"
		if evidence:
			line += " and supporting evidence"
		return line + "."
	if rule:
		return rule
	if basis:
		return basis
	return "As specified in the evaluation criteria."


def render_evaluation_section(
	criteria: list[dict[str, Any]],
	requirements: list[dict[str, Any]] | None = None,
) -> tuple[str, str | None]:
	req_map = _requirement_title_map(requirements or [])
	rows: list[list[str]] = []
	for item in criteria:
		raw_name = cstr(
			item.get("bidder_facing_wording")
			or item.get("criterion_name")
			or item.get("name")
			or ""
		).strip()
		if not raw_name:
			continue
		related = cstr(item.get("related_requirement_id") or "").strip()
		related_title = (
			req_map.get(related.upper()) or req_map.get(related) or ""
			if related
			else ""
		)
		if related_title and (
			INTERNAL_ID_RE.search(raw_name) or "compliance for" in raw_name.lower()
		):
			raw_name = f"{related_title} technical compliance"
		name = expand_requirement_reference(raw_name, req_map)
		if _is_internal_label(name) or INTERNAL_ID_RE.search(name):
			if related_title:
				name = f"{related_title} technical compliance"
			else:
				continue
		stage = cstr(item.get("stage_label") or item.get("stage") or "").strip()
		basis = cstr(
			item.get("evaluation_basis_label") or item.get("evaluation_basis") or ""
		).strip()
		scoring = expand_requirement_reference(_scoring_basis_line(item), req_map)
		evidence = cstr(
			item.get("bidder_evidence_label")
			or item.get("bidder_evidence")
			or item.get("evidence_instruction")
			or ""
		).strip()
		rows.append(
			[
				stage or "—",
				name,
				basis or "—",
				scoring,
				evidence or "As specified",
			]
		)
	if not rows:
		return (
			"",
			generation_block(
				blocking_area="CFG-07 Evaluation Setup",
				message="Evaluation and Qualification Criteria has no bidder-facing content.",
				action="Complete CFG-07 before generating the preview.",
			),
		)
	intro = (
		"<p>Tenders will be evaluated in accordance with the following criteria. "
		"Tenderers shall submit the evidence required for each criterion. "
		"Interactive responses are completed in the electronic submission workspace.</p>"
	)
	return (
		intro
		+ _bidder_table(
			[
				"Stage",
				"Criterion",
				"Basis",
				"Maximum marks / pass-fail rule",
				"Evidence required",
			],
			rows,
		),
		None,
	)


def render_price_section(
	items: list[dict[str, Any]],
	requirements: list[dict[str, Any]] | None = None,
	*,
	default_currency: str = "KES",
) -> tuple[str, str | None]:
	req_map = _requirement_title_map(requirements or [])
	rows: list[list[str]] = []
	for idx, item in enumerate(items, start=1):
		related = cstr(item.get("related_requirement_id") or "").strip()
		related_title = ""
		if related:
			related_title = req_map.get(related.upper()) or req_map.get(related) or ""

		raw_name = cstr(item.get("item_name") or item.get("price_item") or "").strip()
		raw_name = expand_requirement_reference(raw_name, req_map)
		if _is_internal_label(raw_name) or not raw_name or INTERNAL_ID_RE.search(raw_name):
			raw_name = related_title or ""

		description = cstr(item.get("bidder_facing_description") or "").strip()
		description = expand_requirement_reference(description, req_map)
		if not description or _is_internal_label(description) or INTERNAL_ID_RE.search(
			description
		):
			if related_title:
				description = (
					f"Supply, install, and commission works and services meeting the "
					f"{related_title} requirement."
				)
			elif raw_name and not INTERNAL_ID_RE.search(raw_name):
				description = raw_name
			else:
				description = ""
		if not description:
			continue
		if not raw_name:
			# Derive a short item title from description first sentence / related title.
			raw_name = related_title or description.split(".")[0][:80].strip() or f"Price item {idx}"
		if INTERNAL_ID_RE.search(raw_name):
			continue

		unit = cstr(item.get("unit") or "").strip() or "Lot"
		qty = cstr(item.get("quantity") or "").strip() or "1"
		currency = cstr(item.get("currency") or default_currency or "KES").strip() or "KES"
		rows.append(
			[raw_name, description, unit, qty, currency, "Electronic price entry"]
		)
	if not rows:
		return (
			"",
			generation_block(
				blocking_area="CFG-06 Price Schedule",
				message="Price Schedules has no bidder-facing content.",
				action="Complete CFG-06 before generating the preview.",
			),
		)
	intro = (
		"<p>The Price Schedule below sets out the priced items for this tender. "
		"Bidders shall complete prices in the electronic submission workspace.</p>"
	)
	return (
		intro
		+ _bidder_table(
			[
				"Item",
				"Description",
				"Unit",
				"Quantity",
				"Currency",
				"Bidder completion method",
			],
			rows,
		),
		None,
	)


def electronic_schema_reference_html() -> str:
	return (
		'<p class="kt-preview-electronic-ref" data-render-block="ELECTRONIC_SCHEMA_REFERENCE">'
		"Tenderers shall complete Yes/No confirmations, compliance statements, evidence uploads, "
		"price entries, and declarations in the electronic submission workspace generated from "
		"this configuration. Interactive controls are not included in this tender document.</p>"
	)


def find_truncated_requirement_texts(
	requirements: list[dict[str, Any]],
) -> list[str]:
	"""Return requirement ids whose PDF-facing text appears truncated."""
	bad: list[str] = []
	# Exact end-fragment corruptions (substring match would false-positive on full words).
	known_endings = (
		"Podium Flo",
		"as a fu",
		"project management experienc",
		"without vendor dependenc",
		"ERP project",
	)
	for item in requirements or []:
		rid = cstr(item.get("requirement_id") or item.get("title") or "").strip()
		for field in ("title", "description", "requirement_statement"):
			text = cstr(item.get(field) or "").strip()
			if not text:
				continue
			# Strip audit/source appendices before checking.
			text = re.split(r"\n\nSource family:|\n\n\[source_id=", text, maxsplit=1)[0].strip()
			if any(text.endswith(frag) for frag in known_endings):
				bad.append(rid or text[:40])
				break
			# Mid-word cut: ends with lowercase letter and no terminal punctuation,
			# and last token looks incomplete (< 4 chars).
			if text and text[-1].islower() and text[-1] not in ".!?\"'”":
				last = text.split()[-1] if text.split() else ""
				# Ignore trailing tokens that are full words or comma-joined addresses.
				if "," in last:
					continue
				if 1 <= len(last) <= 3 and last.isalpha():
					bad.append(rid or text[:40])
					break
	return bad


def _requirement_group_label(item: dict[str, Any]) -> str:
	family = cstr(
		item.get("requirement_family")
		or item.get("category_label")
		or item.get("source_family")
		or ""
	).strip()
	rid = cstr(item.get("requirement_id") or "").strip().upper()
	letter = rid[0] if rid and rid[0].isalpha() else ""
	letter_map = {
		"A": "A. General Requirements",
		"B": "B. Pension Management Requirements",
		"C": "C. General Ledger Requirements",
		"D": "D. Procurement Module",
		"E": "E. Inventory / Stores",
		"F": "F. Fixed Assets",
		"G": "G. Human Resources / Payroll",
		"H": "H. Budgeting",
		"I": "I. Reporting",
		"J": "J. Integration",
		"K": "K. Security",
		"L": "L. Training",
		"M": "M. Project Management",
		"N": "N. Non-functional",
		"S": "S. Support / SLA",
		"T": "T. Technical / Infrastructure",
		"W": "W. Warranty / Continuity",
	}
	if letter in letter_map:
		return letter_map[letter]
	return family or "Requirements"


def _compact_response_label(item: dict[str, Any]) -> str:
	raw = cstr(item.get("bidder_response_format") or "").strip()
	low = raw.lower()
	if "yes" in low and "no" in low:
		return "Yes/No + compliance statement"
	if "compliance" in low:
		return "Compliance statement"
	return raw or "As specified"


def _compact_evidence_label(item: dict[str, Any]) -> str:
	raw = cstr(
		item.get("evidence_requirement") or item.get("evidence_instruction") or ""
	).strip()
	low = raw.lower()
	if "confirm yes/no" in low or "cite reference" in low:
		return "Reference pages / upload"
	if "upload" in low or "evidence required" in low:
		return "Evidence upload"
	if "optional" in low:
		return "Reference pages / optional evidence"
	# Avoid long workspace instruction paragraphs in PDF.
	if len(raw) > 80:
		return "As specified in electronic workspace"
	return raw or "As specified"


def _render_requirement_matrix(requirements: list[dict[str, Any]]) -> str:
	"""Grouped compliance matrices — CONFIGURED_TABLE, no interactive controls."""
	groups: dict[str, list[dict[str, Any]]] = {}
	for item in requirements:
		groups.setdefault(_requirement_group_label(item), []).append(item)

	parts: list[str] = [electronic_schema_reference_html()]
	for group_name, items in groups.items():
		rows: list[list[str]] = []
		for item in items:
			rid = cstr(item.get("requirement_id") or "").strip()
			title = _requirement_display_title(item)
			statement = cstr(item.get("requirement_statement") or "").strip()
			desc = cstr(item.get("description") or "").strip()
			desc = re.split(r"\n\nSource family:|\n\n\[source_id=", desc, maxsplit=1)[0].strip()
			body = statement or desc
			if body and title and body == title:
				req_text = body
			elif body and title and body.startswith(title):
				req_text = body
			elif title and body and title != body:
				req_text = f"{title}. {body}" if not body.startswith(title) else body
			else:
				req_text = title or body
			if not req_text or _is_internal_label(req_text):
				continue
			treatment = cstr(item.get("treatment_label") or "").strip() or "Mandatory"
			rows.append(
				[
					rid or "—",
					req_text,
					treatment,
					_compact_response_label(item),
					_compact_evidence_label(item),
				]
			)
		if not rows:
			continue
		parts.append(f"<h3>{_esc(group_name)}</h3>")
		parts.append(
			_bidder_table(
				[
					"Requirement ID",
					"Requirement",
					"Treatment",
					"Bidder response required",
					"Evidence / reference required",
				],
				rows,
			)
		)
	return "".join(parts)


def render_information_system_requirements(
	requirements: list[dict[str, Any]],
) -> tuple[str, str | None]:
	truncated = find_truncated_requirement_texts(requirements)
	if truncated:
		return (
			"",
			generation_block(
				blocking_area="CFG-03 IT Requirements",
				message=(
					"Requirement text appears truncated for: "
					+ ", ".join(truncated[:8])
					+ ". Re-extract full wording from the source tender before generating preview."
				),
				action="Fix truncated requirement rows, then regenerate.",
			),
		)
	is_rows, _tech = split_requirements(requirements)
	if not is_rows:
		if requirements:
			return (
				"<p>Functional and business requirements for this tender are addressed "
				"through the Technical Requirements section and related schedules.</p>",
				None,
			)
		return (
			"<p>No functional or business requirements are specified under this section "
			"beyond the locked standard text and Tender Data Sheet.</p>",
			None,
		)
	intro = (
		"<p>The Procuring Entity’s requirements for the Information System are set out "
		"in the compliance matrices below.</p>"
	)
	return intro + _render_requirement_matrix(is_rows), None


def render_technical_requirements_section(
	requirements: list[dict[str, Any]],
) -> tuple[str, str | None]:
	_is_rows, tech_rows = split_requirements(requirements)
	if not tech_rows:
		if requirements:
			return (
				"<p>Technical specifications for this tender are incorporated in the "
				"Requirements of the Information System and the evaluation criteria.</p>",
				None,
			)
		return (
			"<p>No separate technical specifications are specified beyond the standard "
			"conditions and schedules of this tender.</p>",
			None,
		)
	intro = (
		"<p>Tenderers shall comply with the following technical, infrastructure, support, "
		"warranty, and compliance requirements.</p>"
	)
	return intro + _render_requirement_matrix(tech_rows), None


def render_forms_section(items: list[dict[str, Any]]) -> tuple[str, str | None]:
	"""CFG evidence appendix only — standard legal forms render from LOCKED_STD_TEXT."""
	rows: list[list[str]] = []
	for item in items:
		name = cstr(item.get("item_name") or item.get("name") or "").strip()
		if not name or _is_internal_label(name):
			continue
		category = cstr(item.get("category") or "").strip()
		# Skip items that are STD form titles; locked STD section owns those.
		if category.lower() in ("standard form", "std form"):
			continue
		requirement = cstr(item.get("requirement") or "").strip() or "Mandatory"
		response = cstr(item.get("accepted_response_format") or "").strip() or "Evidence"
		rows.append([name, requirement, response])
	if not rows:
		return electronic_schema_reference_html(), None
	intro = (
		"<p>In addition to the locked standard tendering forms, the following "
		"tender-specific evidence items are required. Interactive completion is "
		"via the electronic submission workspace.</p>"
	)
	return (
		intro
		+ _bidder_table(
			["Evidence item", "Requirement", "Bidder completion method"],
			rows,
		),
		None,
	)


def render_schedule_section(milestones: list[dict[str, Any]]) -> tuple[str, str | None]:
	rows: list[list[str]] = []
	for m in milestones:
		name = cstr(m.get("name") or m.get("milestone_name") or "").strip()
		if not name:
			continue
		duration = cstr(m.get("expected_duration_value") or "").strip()
		unit = cstr(m.get("expected_duration_unit") or "").strip()
		dur = f"{duration} {unit}".strip() if duration else "As specified"
		rows.append([name, dur])
	if not rows:
		return (
			"<p>The implementation schedule shall be as agreed in the Contract and Special "
			"Conditions of Contract.</p>",
			None,
		)
	intro = "<p>The expected implementation milestones for this tender are as follows.</p>"
	return intro + _bidder_table(["Milestone", "Expected duration"], rows), None


def render_inventory_section(
	items: list[dict[str, Any]],
	*,
	not_applicable: bool = False,
) -> tuple[str, dict[str, str] | None]:
	"""Render CFG-05 inventory using the step's persisted field names.

	CFG-05 stores ``item_title`` / ``item_description`` / ``bidder_consideration``
	(not ``item_name`` / ``description``). Only items marked Safe to disclose
	enter the bidder-facing preview.
	"""
	if not_applicable:
		return (
			"<p>System inventory disclosure is not applicable to this tender.</p>",
			None,
		)
	rows: list[list[str]] = []
	skipped_disclosure = 0
	for i in items:
		# Align with system_inventory.enrich_item field contract.
		name = cstr(
			i.get("item_title") or i.get("item_name") or i.get("name") or ""
		).strip()
		if not name or _is_internal_label(name):
			continue
		disclosure = cstr(i.get("disclosure_status_label") or "").strip()
		# Legacy rows without disclosure still render; configured non-safe rows do not.
		if disclosure and disclosure != "Safe to disclose":
			skipped_disclosure += 1
			continue
		desc = cstr(
			i.get("bidder_consideration")
			or i.get("item_description")
			or i.get("description")
			or i.get("background_note")
			or ""
		).strip()
		rows.append([name, desc or "As described by the Procuring Entity"])
	if not rows:
		if items and skipped_disclosure:
			message = (
				"System Inventory has configured items, but none are marked "
				"Safe to disclose for the bidder document."
			)
			action = (
				"In CFG-05, set Disclosure Status to Safe to disclose for at least one "
				"item, or mark inventory as not applicable, then regenerate the preview."
			)
		elif items:
			message = (
				"System Inventory items are present but have no bidder-facing title "
				"or disclosure-ready content."
			)
			action = (
				"In CFG-05, ensure each disclosed item has a title, description or bidder "
				"consideration, and Disclosure Status = Safe to disclose — or mark "
				"inventory as not applicable — then regenerate."
			)
		else:
			message = "System Inventory and Bidder Background has no bidder-facing content."
			action = (
				"Complete CFG-05 with at least one Safe to disclose item, or mark "
				"inventory as not applicable before generating the preview."
			)
		return (
			"",
			generation_block(
				blocking_area="CFG-05 System Inventory and Bidder Background",
				message=message,
				action=action,
			),
		)
	intro = (
		"<p>The following system inventory and background information is provided for "
		"tenderers. Disclosure-sensitive material is limited to information approved for release.</p>"
	)
	return intro + _bidder_table(["Item", "Description"], rows), None


def _scc_value(row: dict[str, Any]) -> str:
	return cstr(
		row.get("value_or_obligation")
		or row.get("source_value")
		or row.get("value")
		or row.get("configured_value")
		or ""
	).strip()


def assert_scc_values_complete(
	values: list[dict[str, Any]],
	*,
	std_version: str = "",
	tds: dict[str, Any] | None = None,
	requirements: list[dict[str, Any]] | None = None,
	milestones: list[dict[str, Any]] | None = None,
	single_delivery: dict[str, Any] | None = None,
	delivery_approach: str = "",
) -> dict[str, str] | None:
	"""Hard-fail preview when an applicable required STD contract parameter is unresolved.

	Uses STD-declared parameter readiness (not a hard-coded generic IT topic checklist).
	Categories such as Support & Warranty are organisational only and are never
	treated as missing-topic keys.
	"""
	from kentender_procurement.tender_configurations.services.contract_parameter_readiness import (
		assert_applicable_contract_parameters_resolved,
	)

	return assert_applicable_contract_parameters_resolved(
		values,
		std_version=std_version,
		tds=tds,
		requirements=requirements,
		milestones=milestones,
		single_delivery=single_delivery,
		delivery_approach=delivery_approach,
	)


def assert_price_units_normalized(
	items: list[dict[str, Any]],
) -> dict[str, str] | None:
	if not items:
		return generation_block(
			blocking_area="CFG-06 Price Schedule",
			message="Price schedule lines are missing.",
			action="Complete CFG-06 with normalized units before generating preview.",
		)
	bad = []
	for item in items:
		unit = cstr(item.get("unit") or "").strip()
		name = cstr(item.get("item_name") or item.get("item_id") or "price line")
		if unit not in ALLOWED_PRICE_UNITS:
			bad.append(f"{name}={unit or '(blank)'}")
	if bad:
		return generation_block(
			blocking_area="CFG-06 Price Schedule",
			message=(
				"Price schedule units are not normalized "
				f"(expected Users / Lump sum / Per month / Per GB/month / Annual): "
				+ ", ".join(bad[:8])
			),
			action="Normalize CFG-06 units before generating preview.",
		)
	return None


def strip_pe_only_contract_form_notes(html_body: str) -> str:
	"""Remove PE preparation notes from bidder-facing Contract Forms locked text."""
	text = html_body or ""
	# Drop the PE-only preamble through (but not including) tenderer notes / form 1.
	text = re.sub(
		r"Notes to the Procuring Entity on preparing the Contract Forms\.?"
		r".*?(?=Notes to Tenderers|1\.\s*Noti(?:fi|ﬁ)cation of Intention|$)",
		"",
		text,
		flags=re.I | re.S,
	)
	patterns = [
		r"<p[^>]*>[^<]*Notes to the Procuring Entity[^<]*</p>",
		r"<div[^>]*>[^<]*Notes to the Procuring Entity[^<]*</div>",
	]
	for pat in patterns:
		text = re.sub(pat, "", text, flags=re.I)
	text = re.sub(
		r"Notes to the Procuring Entity\.?",
		"",
		text,
		flags=re.I,
	)
	return text


def build_render_validation_report(
	*,
	doc: Any = None,
	tds: dict[str, Any] | None = None,
	contract_values: list[dict[str, Any]] | None = None,
	price_items: list[dict[str, Any]] | None = None,
	poc_audit_notes: dict[str, Any] | None = None,
	generation_block: dict[str, str] | None = None,
	std_version: str = "",
) -> dict[str, Any]:
	"""AUDIT_ONLY report — never embedded in bidder-facing preview HTML/PDF."""
	tds = tds or {}
	report = {
		"report_type": "Render Validation / Audit Report",
		"bidder_facing": False,
		"std_version": std_version,
		"configuration_ref": cstr(getattr(doc, "configuration_ref", None) or getattr(doc, "name", None)),
		"deadlines": {
			"tender_submission_deadline": cstr(tds.get("tender_submission_deadline") or ""),
			"tender_opening_datetime": cstr(tds.get("tender_opening_datetime") or ""),
			"clarification_deadline": cstr(tds.get("clarification_deadline") or ""),
		},
		"poc_audit_notes": poc_audit_notes or {},
		"scc_row_count": len(contract_values or []),
		"price_line_count": len(price_items or []),
		"price_units": sorted(
			{
				cstr(i.get("unit") or "")
				for i in (price_items or [])
				if cstr(i.get("unit") or "")
			}
		),
		"generation_block": generation_block,
		"notes": [
			"PoC source facts, demo overrides, and mapping comments belong only in this report.",
			"Bidder-facing tender PDF must not contain those diagnostics.",
		],
	}
	if isinstance(poc_audit_notes, dict):
		report["source_submission_deadline"] = poc_audit_notes.get("source_submission_deadline")
		report["demo_submission_deadline"] = poc_audit_notes.get("demo_submission_deadline")
	return report


def render_scc_section(
	values: list[dict[str, Any]],
	*,
	std_version: str = "",
	tds: dict[str, Any] | None = None,
	requirements: list[dict[str, Any]] | None = None,
	milestones: list[dict[str, Any]] | None = None,
	single_delivery: dict[str, Any] | None = None,
	delivery_approach: str = "",
) -> tuple[str, str | None]:
	gate = assert_scc_values_complete(
		values,
		std_version=std_version,
		tds=tds,
		requirements=requirements,
		milestones=milestones,
		single_delivery=single_delivery,
		delivery_approach=delivery_approach,
	)
	if gate:
		return "", gate
	rows: list[list[str]] = []
	for v in values:
		label = cstr(v.get("item_label") or v.get("label") or v.get("name") or "").strip()
		if not label or _is_internal_label(label):
			continue
		val = _scc_value(v)
		if re.fullmatch(r"[\d.]+", val or ""):
			if any(tok in label.lower() for tok in ("amount", "sum", "price", "value", "security")):
				val = format_currency_amount(val, "KES")
		if not val:
			continue
		rows.append([label, val])
	if not rows:
		return (
			"",
			generation_block(
				blocking_area="CFG-09 Contract Values",
				message="SCC values are missing for tender preview.",
				action="Complete CFG-09 before generating preview.",
			),
		)
	intro = (
		"<p>The following Special Conditions of Contract amend or supplement the General "
		"Conditions of Contract.</p>"
	)
	return intro + _bidder_table(["Special condition", "Value"], rows), None


def assert_no_forbidden_preview_markers(html_doc: str) -> dict[str, str] | None:
	for marker in FORBIDDEN_OUTPUT_MARKERS:
		if marker in (html_doc or ""):
			return generation_block(
				blocking_area="Document Preview Quality Gate",
				message=f"Preview output contains forbidden diagnostic or debug content ({marker!r}).",
				action="Regenerate after fixing configuration or STD binding content.",
			)
	if re.search(
		r">contact_officer<|>clarification_deadline<|>tender_security_required<",
		html_doc or "",
	):
		return generation_block(
			blocking_area="Document Preview Quality Gate",
			message="Preview output contains raw configuration field names.",
			action="Regenerate after fixing the presentation layer mapping.",
		)
	# Allow REQ-* only in Requirement ID matrix cells (data-col="requirement-id").
	# Flag misuse as headings / bare table cells / Item N labels.
	if re.search(
		r"<h3>\s*REQ-\d+\s*</h3>|<td>\s*REQ-\d+\s*</td>|>Item \d+<",
		html_doc or "",
		re.I,
	):
		return generation_block(
			blocking_area="CFG-03 IT Requirements / CFG-06 Price / CFG-07 Evaluation",
			message=(
				"Preview output still contains internal requirement identifiers "
				"(for example REQ-001) instead of bidder-facing titles."
			),
			action=(
				"In CFG-03, ensure each requirement has a clear title (not only REQ-NNN). "
				"Then check CFG-06 and CFG-07 use those titles, and regenerate the preview."
			),
			owner_step="CFG-03",
		)
	return None


def _bidder_table(headers: list[str], rows: list[Any]) -> str:
	th = "".join(f"<th>{_esc(h)}</th>" for h in headers)
	body = ""
	for row in rows:
		cells = list(row)
		tds = []
		for i, c in enumerate(cells):
			# Bold first column for item/criterion style tables when header is Item.
			if i == 0 and headers and headers[0] in ("Item", "Milestone", "TDS item"):
				tds.append(f"<td><strong>{_esc(c)}</strong></td>")
			elif i == 0 and headers and headers[0] == "Requirement ID":
				tds.append(f'<td data-col="requirement-id">{_esc(c)}</td>')
			else:
				tds.append(f"<td>{_esc(c)}</td>")
		body += "<tr>" + "".join(tds) + "</tr>"
	return (
		f'<table class="kt-preview-table"><thead><tr>{th}</tr></thead>'
		f"<tbody>{body}</tbody></table>"
	)
