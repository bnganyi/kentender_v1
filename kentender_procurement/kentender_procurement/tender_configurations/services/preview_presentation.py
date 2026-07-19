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
	"opening_notes",
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
	if key == "opening_notes":
		v = cstr(raw or "").strip()
		return v if not _is_blank(v) else None
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
	blocks: list[str] = []
	for item in criteria:
		raw_name = cstr(
			item.get("bidder_facing_wording")
			or item.get("criterion_name")
			or item.get("name")
			or ""
		).strip()
		if not raw_name:
			continue
		# Expand related requirement id into title when criterion is a stub.
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
		blocks.append(
			'<article class="kt-preview-criterion">'
			f"<h3>{_esc(name)}</h3>"
			f"<p><strong>Stage:</strong> {_esc(stage or '—')}</p>"
			f"<p><strong>Evaluation basis:</strong> {_esc(basis or '—')}</p>"
			f"<p><strong>Scoring / rule:</strong> {_esc(scoring)}</p>"
			f"<p><strong>Bidder evidence:</strong> {_esc(evidence or 'As specified')}</p>"
			"</article>"
		)
	if not blocks:
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
		"Tenderers shall submit the evidence required for each criterion.</p>"
	)
	return intro + "".join(blocks), None


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
			[raw_name, description, unit, qty, currency, "[Bidder to complete]"]
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
		"Bidders shall complete prices in the electronic price form generated from this schedule; "
		"the Bidder price column in this preview is left for completion in that form.</p>"
	)
	return (
		intro
		+ _bidder_table(
			["Item", "Description", "Unit", "Quantity", "Currency", "Bidder price"],
			rows,
		),
		None,
	)


def _render_requirement_articles(requirements: list[dict[str, Any]]) -> str:
	parts: list[str] = []
	for item in requirements:
		title = _requirement_display_title(item)
		statement = cstr(
			item.get("requirement_statement")
			or item.get("bidder_response_instruction")
			or ""
		).strip()
		desc = cstr(item.get("description") or "").strip()
		# When description was promoted to the title, do not repeat it as the body.
		if not statement:
			if desc and desc != title and not _is_internal_label(desc):
				statement = desc
			else:
				statement = ""
		if not title and not statement:
			continue
		if _is_internal_label(title):
			# Still no bidder-facing label — skip rather than emit REQ-NNN headings.
			continue
		treatment = cstr(item.get("treatment_label") or "").strip()
		response = cstr(item.get("bidder_response_format") or "").strip()
		evidence = cstr(
			item.get("evidence_instruction") or item.get("evidence_requirement") or ""
		).strip()
		parts.append(
			'<article class="kt-preview-requirement">'
			f"<h3>{_esc(title or 'Requirement')}</h3>"
			f"<p>{_esc(statement or 'As specified by the Procuring Entity')}</p>"
			+ (
				f"<p><strong>Treatment:</strong> {_esc(treatment)}</p>"
				if treatment
				else ""
			)
			+ (
				f"<p><strong>Bidder response:</strong> {_esc(response)}</p>"
				if response
				else ""
			)
			+ (
				f"<p><strong>Evidence:</strong> {_esc(evidence)}</p>"
				if evidence
				else ""
			)
			+ "</article>"
		)
	return "".join(parts)


def render_information_system_requirements(
	requirements: list[dict[str, Any]],
) -> tuple[str, str | None]:
	is_rows, _tech = split_requirements(requirements)
	if not is_rows:
		# Optional section when all requirements are technical — cross-reference only.
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
		"<p>The Procuring Entity’s requirements for the Information System include "
		"the following functional, system, and business provisions.</p>"
	)
	return intro + _render_requirement_articles(is_rows), None


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
	return intro + _render_requirement_articles(tech_rows), None


def render_forms_section(items: list[dict[str, Any]]) -> tuple[str, str | None]:
	articles: list[str] = []
	for item in items:
		name = cstr(item.get("item_name") or item.get("name") or "").strip()
		if not name or _is_internal_label(name):
			continue
		instruction = cstr(
			item.get("bidder_instruction") or item.get("evidence_instruction") or ""
		).strip()
		articles.append(
			'<article class="kt-preview-form-item">'
			f"<h3>{_esc(name)}</h3>"
			f"<p>{_esc(instruction or 'This form or evidence item is required for tender submission.')}</p>"
			"</article>"
		)
	if not articles:
		return (
			"<p>Tendering forms and evidence items shall be completed as specified in the "
			"Instructions to Tenderers and the electronic tendering forms issued with this tender.</p>",
			None,
		)
	intro = "<p>Tenderers shall complete and submit the following forms and evidence items.</p>"
	return intro + "".join(articles), None


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


def render_scc_section(values: list[dict[str, Any]]) -> tuple[str, str | None]:
	rows: list[list[str]] = []
	for v in values:
		label = cstr(v.get("item_label") or v.get("label") or v.get("name") or "").strip()
		if not label or _is_internal_label(label):
			continue
		val = cstr(v.get("value") or v.get("configured_value") or "").strip()
		if re.fullmatch(r"[\d.]+", val or ""):
			# Prefer currency formatting when label suggests money.
			if any(tok in label.lower() for tok in ("amount", "sum", "price", "value", "security")):
				val = format_currency_amount(val, "KES")
		rows.append([label, val or "As specified"])
	if not rows:
		return (
			"<p>Special Conditions of Contract, where applicable, are as configured for this "
			"tender and prevail over the General Conditions to the extent of any inconsistency.</p>",
			None,
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
	if re.search(r">REQ-\d+<|>Item \d+<", html_doc or "", re.I):
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
			else:
				tds.append(f"<td>{_esc(c)}</td>")
		body += "<tr>" + "".join(tds) + "</tr>"
	return (
		f'<table class="kt-preview-table"><thead><tr>{th}</tr></thead>'
		f"<tbody>{body}</tbody></table>"
	)
