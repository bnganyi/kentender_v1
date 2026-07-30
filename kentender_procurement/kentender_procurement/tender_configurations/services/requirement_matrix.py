# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""A4 — Requirement Matrix section detail (Screen D for requirement_matrix)."""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import quote

import frappe
from frappe.utils import cstr, format_time, get_datetime, now_datetime

from kentender_procurement.tender_configurations.services.electronic_bid import (
	STATUS_SEALED,
	create_or_get_draft,
	save_section_responses,
)
from kentender_procurement.tender_configurations.services.published_tender_overview import (
	ACTION_CLOSED,
	ACTION_UNAVAILABLE,
	ACTION_VIEW_SUBMITTED,
	get_published_tender_overview,
	start_or_get_bid_workspace,
)
from kentender_procurement.tender_configurations.services.schema_compiler import (
	persist_compiled_schema,
)
from kentender_procurement.tender_configurations.services.submission_checklist import (
	STATUS_COMPLETE,
	STATUS_IN_PROGRESS,
	STATUS_NEEDS_ATTENTION,
	STATUS_NOT_APPLICABLE,
	STATUS_NOT_STARTED,
	portal_workspace_url,
)

# Portal-suppressed: electronic-only rule (no PDF page-reference workflow).
SUPPRESSED_FIELD_KEYS = frozenset({"reference_pages"})
SUPPORTED_FIELD_TYPES = frozenset(
	{"text", "narrative", "file", "boolean", "select", "number", "money", "percentage", "date", "period", "repeating_table"}
)

DEFAULT_PAGE_SIZE = 10
SECTION_KEY_RC = "requirements_compliance"

MODE_REQUIRED = "required"
MODE_OPTIONAL = "optional"
MODE_CONDITIONAL = "conditional"
MODE_INFORMATIONAL = "informational"
MODE_EXCLUDED = "excluded"

ACTION_START = "Start"
ACTION_CONTINUE = "Continue"
ACTION_REVIEW = "Review"
ACTION_RESOLVE = "Resolve"


def _parse_json(raw: Any, default: Any = None) -> Any:
	if raw is None or raw == "":
		return default if default is not None else {}
	if isinstance(raw, (dict, list)):
		return raw
	try:
		return json.loads(raw)
	except (TypeError, ValueError):
		return default if default is not None else {}


def _require_logged_in() -> None:
	if not frappe.session.user or frappe.session.user == "Guest":
		frappe.throw(frappe._("Please sign in to open this bid section."), frappe.PermissionError)


def _section_key(sec: dict[str, Any]) -> str:
	return cstr(sec.get("key") or sec.get("section_key") or sec.get("id") or "").strip()


def _section_label(sec: dict[str, Any]) -> str:
	return cstr(sec.get("label") or sec.get("title") or _section_key(sec)).strip()


def _req_id(req: dict[str, Any]) -> str:
	return cstr(req.get("requirement_id") or req.get("id") or "").strip()


def _norm_display_text(value: Any) -> str:
	return " ".join(cstr(value or "").split()).strip().lower()


def _strip_title_prefix(title: str, statement: str) -> str:
	"""Remove a short title prefix from a longer statement (e.g. M1 NSSF rows)."""
	if not title or not statement:
		return statement or ""
	nt, ns = _norm_display_text(title), _norm_display_text(statement)
	if not nt or not ns:
		return statement
	if ns == nt:
		return ""
	if ns.startswith(nt):
		# Strip by normalized length approximation using original title length + separators.
		rest = statement[len(title) :].lstrip(" \t\r\n.:;—-–")
		return rest.strip()
	return statement


def requirement_display(req: dict[str, Any]) -> dict[str, str]:
	"""Title / detail hierarchy for list + drawer (A4 mock pattern).

	When a short title exists (e.g. ``M1: Implementation Methodology and Strategy``):
	- list + drawer header use the title
	- Description uses detail only (title prefix stripped — never repeated)

	When title and statement are the same long blob (many NSSF A-series rows):
	- list shows one line; drawer header uses the tender-facing reference; Description
	  shows the text once.

	Never put the internal ``requirement_id`` in bidder-facing headers.
	"""
	rid = _req_id(req)
	ref = cstr(req.get("tender_facing_reference") or req.get("reference") or "").strip()
	raw_title = cstr(req.get("requirement_title") or req.get("title") or "").strip()
	raw_statement = cstr(req.get("requirement_statement") or req.get("description") or "").strip()
	short_cap = 80
	has_short_title = bool(raw_title) and len(raw_title) <= short_cap
	facing = ref or raw_title or "Requirement"

	if has_short_title:
		detail = _strip_title_prefix(raw_title, raw_statement) if raw_statement else ""
		# Short title identical to statement → treat as undifferentiated blob.
		if raw_statement and not detail:
			blob = raw_title
			return {
				"requirement_id": rid,
				"list_title": blob,
				"list_subtitle": "",
				"header_title": f"{ref}: {blob}" if ref else blob,
				"description": blob,
				"has_short_title": "0",
				"title": blob,
				"statement": "",
			}
		header_title = f"{ref}: {raw_title}" if ref else raw_title
		return {
			"requirement_id": rid,
			"list_title": raw_title,
			"list_subtitle": detail,
			"header_title": header_title,
			"description": detail,
			"has_short_title": "1",
			"title": raw_title,
			"statement": detail,
		}

	# Long / undifferentiated blob — one copy only.
	blob = raw_title or raw_statement or facing
	return {
		"requirement_id": rid,
		"list_title": blob,
		"list_subtitle": "",
		"header_title": f"{ref}: {blob}" if ref and ref not in blob else (ref or blob),
		"description": blob,
		"has_short_title": "0",
		"title": blob,
		"statement": "",
	}


def collect_in_progress_field_errors(
	req: dict[str, Any],
	response: dict[str, Any] | None,
	fields: list[dict[str, Any]],
	*,
	status: str,
) -> dict[str, str]:
	"""Per-field errors for In Progress / Needs Attention drawers only (not Not Started)."""
	if status not in (STATUS_IN_PROGRESS, STATUS_NEEDS_ATTENTION):
		return {}
	resp = response if isinstance(response, dict) else {}
	errors: dict[str, str] = {}
	for f in fields:
		fk = cstr(f.get("field_key") or "")
		if not fk:
			continue
		if f.get("required") and not _is_filled(resp.get(fk)):
			label = cstr(f.get("label") or fk)
			if cstr(f.get("type")) == "file":
				errors[fk] = "Required technical evidence has not been added."
			else:
				errors[fk] = f"{label} is required."
	brt = cstr(req.get("bidder_response_type") or "").lower()
	if "evidence" in brt:
		for f in fields:
			if cstr(f.get("type")) != "file":
				continue
			fk = cstr(f.get("field_key") or "")
			if fk and not _is_filled(resp.get(fk)):
				errors[fk] = "Required technical evidence has not been added."
	return errors


# Portal helper copy for schema field keys (electronic bid response fields).
FIELD_HELP = {
	"compliant_yes_no": "Confirm whether your offer meets this requirement.",
	"compliance_statement": "Briefly explain how you meet this requirement.",
	"deviation_note_if_any": "Optional. Note any exceptions or partial non-compliance.",
	"evidence_uploads": "Add one or more supporting files (PDF, DOCX, or JPG).",
	"numeric_value": "Enter a number. Zero is a valid response.",
	"acknowledged": "Confirm you have read and understood this informational requirement.",
	"schedule_rows": "Add one row for each planned activity and when it will occur.",
}


def _normalize_file_list(val: Any) -> list[dict[str, Any]]:
	"""Accept single mock file dict or a list; return list of file dicts."""
	if val is None or val == "" or val == []:
		return []
	if isinstance(val, dict):
		return [val] if (val.get("file_name") or val.get("mock") or val.get("url")) else []
	if isinstance(val, list):
		out: list[dict[str, Any]] = []
		for item in val:
			if isinstance(item, dict) and (item.get("file_name") or item.get("mock") or item.get("url")):
				out.append(item)
			elif cstr(item).strip():
				out.append({"file_name": cstr(item).strip(), "mock": 1})
		return out
	return []


def _is_filled(val: Any) -> bool:
	if val is None:
		return False
	if isinstance(val, bool):
		return val
	if isinstance(val, (int, float)):
		return True
	if isinstance(val, dict):
		if val.get("file_name") or val.get("mock") or val.get("uploaded_at") or val.get("url"):
			return True
		# Treat empty file-shaped dict as empty.
		return False
	if isinstance(val, list):
		return len(_normalize_file_list(val)) > 0
	return bool(cstr(val).strip())


def is_requirement_matrix_section(sec: dict[str, Any] | None) -> bool:
	"""True when section is a requirement matrix (type or structural)."""
	if not isinstance(sec, dict):
		return False
	if _section_key(sec) == SECTION_KEY_RC:
		return True
	stype = cstr(sec.get("section_type") or sec.get("type") or "").strip().lower()
	if stype == "requirement_matrix":
		return True
	reqs = sec.get("requirements")
	fields = sec.get("response_fields_per_requirement")
	return isinstance(reqs, list) and len(reqs) > 0 and isinstance(fields, (list, tuple)) and len(fields) > 0


def _lean_rc_fields_need_refresh(reqs: list[dict[str, Any]]) -> bool:
	"""True when lean fixture rows still carry developer-jargon / incomplete controls."""
	if not reqs:
		return True
	leanish = all(cstr(_req_id(r)).startswith("rc-") for r in reqs)
	if not leanish:
		return False
	for req in reqs:
		for f in req.get("response_fields") or []:
			if not isinstance(f, dict):
				continue
			ftype = cstr(f.get("type") or "").strip().lower()
			label = cstr(f.get("label") or "").strip()
			if ftype == "repeating_table" and (
				label in ("Schedule rows", "schedule_rows") or not f.get("columns")
			):
				return True
			if ftype == "boolean" and label in ("Acknowledgement", "acknowledged"):
				return True
			if ftype == "number" and label in ("Value", "numeric_value"):
				return True
	return False


def hydrate_requirements_compliance_section(
	sec: dict[str, Any] | None,
	*,
	schema: dict[str, Any] | None = None,
	bid_doc: Any = None,
) -> dict[str, Any] | None:
	"""Fill empty / route-only Requirements Compliance stubs with lean pack fixtures.

	Older lean publishes left ``slice_status=route_only_not_editable_in_lean_slice`` with
	zero requirements; hydrate in-memory (and persist onto the bid schema snapshot when
	provided) so the Website workspace does not 404. Also refreshes lean fixture field
	labels/columns when prior snapshots still use developer-jargon controls.
	"""
	if not isinstance(sec, dict):
		return sec
	if _section_key(sec) != SECTION_KEY_RC:
		return sec
	reqs = [r for r in (sec.get("requirements") or []) if isinstance(r, dict) and _req_id(r)]
	fields = sec.get("response_fields_per_requirement")
	needs_seed = not reqs or not (isinstance(fields, (list, tuple)) and len(fields) > 0)
	needs_refresh = _lean_rc_fields_need_refresh(reqs)
	if not needs_seed and not needs_refresh:
		if cstr(sec.get("section_type") or "") != "requirement_matrix":
			sec["section_type"] = "requirement_matrix"
		return sec

	from kentender_procurement.tender_configurations.services.electronic_std_template import (
		materialize_requirements_compliance,
	)

	rc_rows, rc_fields, rc_flags = materialize_requirements_compliance({})
	active = [
		r
		for r in rc_rows
		if cstr(r.get("requirement_mode")) != "excluded" and not r.get("withdrawn")
	]
	sec["requirements"] = active
	sec["requirements_history"] = rc_rows
	sec["response_fields_per_requirement"] = rc_fields
	sec["section_type"] = "requirement_matrix"
	sec["requirements_compliance_flags"] = rc_flags
	sec["slice_status"] = "requirements_compliance_implemented"
	if not cstr(sec.get("bidder_instructions") or "").strip():
		sec["bidder_instructions"] = (
			"Respond to each applicable requirement and provide the requested supporting evidence."
		)

	if bid_doc is not None and isinstance(schema, dict) and schema.get("sections"):
		try:
			bid_doc.db_set(
				"schema_snapshot",
				json.dumps(schema, ensure_ascii=False),
				update_modified=False,
			)
		except Exception:
			pass
	return sec


def portal_section_url(publication_ref: str, section_key: str) -> str:
	ref = quote(cstr(publication_ref or "").strip(), safe="")
	key = quote(cstr(section_key or "").strip(), safe="")
	return f"/tenders/{ref}/sections/{key}"


def portal_requirements_compliance_url(publication_ref: str) -> str:
	return portal_section_url(publication_ref, SECTION_KEY_RC)


def portal_requirements_compliance_review_url(publication_ref: str) -> str:
	return f"{portal_requirements_compliance_url(publication_ref)}/review"


def _desk_bridge(configuration_id: str) -> str:
	return f"/app/it-electronic-bidder-workspace/{quote(configuration_id, safe='')}"


def _load_schema(cfg, bid_doc) -> dict[str, Any]:
	if bid_doc:
		schema = _parse_json(getattr(bid_doc, "schema_snapshot", None), {})
		if schema.get("sections"):
			return schema
	schema = _parse_json(getattr(cfg, "bidder_submission_schema", None), {})
	if not schema.get("sections"):
		schema = persist_compiled_schema(cfg.name)
	return schema


def _response_fields(sec: dict[str, Any], req: dict[str, Any] | None = None) -> list[dict[str, Any]]:
	"""Prefer per-requirement fields; fall back to section-level catalog."""
	raw = None
	if isinstance(req, dict):
		raw = req.get("response_fields")
	if not isinstance(raw, list) or not raw:
		raw = sec.get("response_fields_per_requirement") or []
	out: list[dict[str, Any]] = []
	for f in raw:
		if not isinstance(f, dict):
			continue
		key = cstr(f.get("field_key") or f.get("key") or "").strip()
		if not key or key in SUPPRESSED_FIELD_KEYS:
			continue
		out.append(dict(f))
	return out


def _group_key(req: dict[str, Any]) -> str:
	return (
		cstr(req.get("category_label") or req.get("requirement_family") or req.get("group") or "").strip()
		or "General"
	)


def _requirement_mode(req: dict[str, Any]) -> str:
	mode = cstr(req.get("requirement_mode") or "").strip().lower()
	if mode in (MODE_REQUIRED, MODE_OPTIONAL, MODE_CONDITIONAL, MODE_INFORMATIONAL, MODE_EXCLUDED):
		return mode
	if req.get("mandatory") in (0, "0", False, "false"):
		return MODE_OPTIONAL
	return MODE_REQUIRED


def _mode_label(mode: str) -> str:
	return {
		MODE_REQUIRED: "Required",
		MODE_OPTIONAL: "Optional",
		MODE_CONDITIONAL: "Conditional",
		MODE_INFORMATIONAL: "Informational",
		MODE_EXCLUDED: "Excluded",
	}.get(mode, "Required")


def _rc_flags(sec: dict[str, Any]) -> dict[str, Any]:
	flags = sec.get("requirements_compliance_flags")
	return flags if isinstance(flags, dict) else {}


def resolve_requirement_applicability(
	req: dict[str, Any],
	*,
	sec: dict[str, Any] | None = None,
	responses: dict[str, Any] | None = None,
) -> tuple[bool, str]:
	"""Return (applicable, display_mode)."""
	mode = _requirement_mode(req)
	if mode == MODE_EXCLUDED or req.get("withdrawn") in (1, "1", True, "true"):
		return False, MODE_EXCLUDED
	flags = _rc_flags(sec or {})
	cond = cstr(req.get("condition_key") or "always").strip().lower()
	scope = cstr(req.get("scope") or "tender").strip().lower()
	if mode == MODE_CONDITIONAL or cond not in ("", "always"):
		if cond == "technical_alternatives_permitted":
			if not flags.get("technical_alternatives_permitted"):
				return False, MODE_EXCLUDED
		elif cond == "lot_topic_selected":
			lots = flags.get("selected_lots") if isinstance(flags.get("selected_lots"), list) else []
			if not flags.get("lot_topic_selected") and not lots:
				return False, MODE_EXCLUDED
		elif cond not in ("", "always"):
			# Unknown named condition → treat inactive until configured
			if not flags.get(cond):
				return False, MODE_EXCLUDED
	if scope == "lot":
		lots = flags.get("selected_lots") if isinstance(flags.get("selected_lots"), list) else []
		if not lots and not flags.get("lot_topic_selected"):
			return False, MODE_EXCLUDED
	if mode == MODE_INFORMATIONAL:
		return True, MODE_INFORMATIONAL
	if mode == MODE_OPTIONAL:
		return True, MODE_OPTIONAL
	if mode == MODE_CONDITIONAL:
		# Active conditional follows required behaviour unless optional flagged
		return True, MODE_REQUIRED if req.get("mandatory", True) else MODE_OPTIONAL
	return True, mode


def _fields_for_req(sec: dict[str, Any], req: dict[str, Any]) -> list[dict[str, Any]]:
	return _response_fields(sec, req)


def resolve_requirement_status(
	req: dict[str, Any],
	response: dict[str, Any] | None,
	fields: list[dict[str, Any]],
	*,
	sec: dict[str, Any] | None = None,
) -> str:
	applicable, display_mode = resolve_requirement_applicability(req, sec=sec)
	if not applicable or display_mode == MODE_EXCLUDED:
		return STATUS_NOT_APPLICABLE
	if display_mode == MODE_INFORMATIONAL:
		# Informational never blocks and requires no response.
		return STATUS_COMPLETE

	resp = response if isinstance(response, dict) else {}
	# Addendum-changed responses require explicit resave
	if cstr(req.get("updated_by_addendum") or "").strip() and not resp.get("addendum_reviewed"):
		meta_keys = {"validation_errors", "needs_attention", "status", "addendum_reviewed"}
		any_prior = any(_is_filled(v) for k, v in resp.items() if k not in meta_keys)
		if any_prior or resp:
			return STATUS_NEEDS_ATTENTION

	if resp.get("needs_attention") or (
		isinstance(resp.get("validation_errors"), list) and resp.get("validation_errors")
	):
		return STATUS_NEEDS_ATTENTION

	use_fields = fields or _fields_for_req(sec or {}, req)
	required_fields = [f for f in use_fields if f.get("required")]
	if not required_fields and display_mode == MODE_REQUIRED:
		required_fields = [f for f in use_fields if cstr(f.get("type")) != "file"][:2]

	filled_required = 0
	missing_required = 0
	for f in required_fields:
		fk = cstr(f.get("field_key") or "")
		val = resp.get(fk)
		if cstr(f.get("type")) == "repeating_table":
			rows = val if isinstance(val, list) else []
			min_n = int(f.get("min_rows") or 1)
			complete_rows = [r for r in rows if isinstance(r, dict) and any(_is_filled(v) for v in r.values())]
			if len(complete_rows) >= min_n:
				filled_required += 1
			else:
				missing_required += 1
			continue
		if _is_filled(val):
			filled_required += 1
		else:
			missing_required += 1

	meta_keys = {"validation_errors", "needs_attention", "status", "addendum_reviewed"}
	any_filled = any(_is_filled(v) for k, v in resp.items() if k not in meta_keys)
	if not any_filled and filled_required == 0:
		return STATUS_NOT_STARTED

	brt = cstr(req.get("bidder_response_type") or "").lower()
	evidence_needed = "evidence" in brt or bool(req.get("evidence_required"))
	if evidence_needed and missing_required == 0:
		for f in use_fields:
			if cstr(f.get("type")) != "file":
				continue
			fk = cstr(f.get("field_key") or "")
			if not _is_filled(resp.get(fk)):
				return STATUS_NEEDS_ATTENTION

	if missing_required == 0 and (filled_required >= len(required_fields) or not required_fields):
		if display_mode == MODE_OPTIONAL and not any_filled:
			return STATUS_NOT_STARTED
		return STATUS_COMPLETE
	if any_filled or filled_required:
		return STATUS_IN_PROGRESS
	return STATUS_NOT_STARTED


def resolve_group_status(*, complete: int, total: int, needs_attention: int, started: int) -> str:
	if total <= 0:
		return STATUS_NOT_APPLICABLE
	if needs_attention:
		return STATUS_NEEDS_ATTENTION
	if complete >= total:
		return STATUS_COMPLETE
	if started or complete:
		return STATUS_IN_PROGRESS
	return STATUS_NOT_STARTED


def _response_summary(
	resp: dict[str, Any] | None,
	fields: list[dict[str, Any]],
	*,
	req: dict[str, Any] | None = None,
	status: str = "",
) -> str:
	"""Plain-language summary — never Compliant / Passed / Failed."""
	if status == STATUS_NEEDS_ATTENTION and req and cstr(req.get("updated_by_addendum") or "").strip():
		return f"Review required after addendum {cstr(req.get('updated_by_addendum'))}"
	if not isinstance(resp, dict) or not resp:
		return "No response"
	num = resp.get("numeric_value")
	if num is not None and num != "" and _is_filled(num):
		return cstr(num).strip()
	yes_no = cstr(resp.get("compliant_yes_no") or "").strip()
	statement = cstr(resp.get("compliance_statement") or "").strip()
	files = _normalize_file_list(resp.get("evidence_uploads"))
	table = resp.get("schedule_rows") if isinstance(resp.get("schedule_rows"), list) else []
	if table:
		done = sum(1 for r in table if isinstance(r, dict) and any(_is_filled(v) for v in r.values()))
		return f"{done} schedule rows completed"
	if statement and files:
		return "Response and evidence provided"
	if statement:
		return "Explanation provided"
	if yes_no and statement:
		short = statement if len(statement) <= 48 else statement[:45] + "…"
		return short
	if yes_no:
		return yes_no
	if files:
		if len(files) == 1:
			return cstr(files[0].get("file_name") or "Evidence provided")
		return f"{len(files)} evidence files"
	if resp.get("acknowledged"):
		return "Acknowledged"
	for f in fields:
		fk = cstr(f.get("field_key") or "")
		val = resp.get(fk)
		if cstr(f.get("type")) == "file":
			flist = _normalize_file_list(val)
			if flist:
				return "Evidence provided"
		if _is_filled(val) and not isinstance(val, (dict, list)):
			text = cstr(val).strip()
			return text if len(text) <= 56 else text[:53] + "…"
	return "No response"


def _action_for_req_status(status: str, *, mode: str = MODE_REQUIRED) -> str:
	if status == STATUS_NOT_APPLICABLE:
		return ""
	if mode == MODE_INFORMATIONAL:
		return ACTION_REVIEW
	if status == STATUS_COMPLETE:
		return ACTION_REVIEW
	if status == STATUS_NEEDS_ATTENTION:
		return ACTION_RESOLVE
	if status == STATUS_IN_PROGRESS:
		return ACTION_CONTINUE
	return ACTION_START


def _portal_fields(fields: list[dict[str, Any]]) -> list[dict[str, Any]]:
	out: list[dict[str, Any]] = []
	for f in fields:
		ftype = cstr(f.get("type") or "text").strip().lower()
		row = dict(f)
		fkey = cstr(f.get("field_key") or "")
		explicit = cstr(f.get("control") or "").strip().lower()
		if ftype not in SUPPORTED_FIELD_TYPES:
			row["unsupported"] = 1
			row["unsupported_message"] = f"Unsupported response type '{ftype}'"
		else:
			row["unsupported"] = 0
		if explicit in {"yes_no", "textarea", "file", "select", "checkbox", "number", "date", "period", "repeating_table"}:
			row["control"] = explicit
		elif fkey == "compliant_yes_no" or explicit == "yes_no":
			row["control"] = "yes_no"
		elif ftype == "narrative":
			row["control"] = "textarea"
		elif ftype == "file":
			row["control"] = "file"
			row["multiple"] = 1
		elif ftype == "boolean":
			row["control"] = "checkbox"
		elif ftype in {"number", "money", "percentage"}:
			row["control"] = "number"
		elif ftype == "date":
			row["control"] = "date"
		elif ftype == "period":
			row["control"] = "period"
		elif ftype == "repeating_table":
			row["control"] = "repeating_table"
			cols = f.get("columns")
			if not isinstance(cols, list) or not cols:
				row["columns"] = [
					{"key": "activity", "label": "Activity"},
					{"key": "timing", "label": "Timing"},
				]
		elif ftype == "select":
			row["control"] = "select"
		else:
			row["control"] = "text"
		if ftype == "file":
			row["multiple"] = 1
		# Prefer configured help_text; fall back to shared FIELD_HELP.
		if not cstr(row.get("help_text") or "").strip() and fkey in FIELD_HELP:
			row["help_text"] = FIELD_HELP[fkey]
		out.append(row)
	return out


def build_groups(
	requirements: list[dict[str, Any]],
	responses: dict[str, Any],
	fields: list[dict[str, Any]],
	*,
	sec: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
	order: list[str] = []
	buckets: dict[str, list[dict[str, Any]]] = {}
	for req in requirements:
		if not isinstance(req, dict) or not _req_id(req):
			continue
		applicable, display_mode = resolve_requirement_applicability(req, sec=sec)
		if not applicable or display_mode == MODE_EXCLUDED:
			continue
		gk = _group_key(req)
		if gk not in buckets:
			buckets[gk] = []
			order.append(gk)
		buckets[gk].append(req)

	groups: list[dict[str, Any]] = []
	for gk in order:
		reqs = buckets[gk]
		needs = started = 0
		req_total = 0
		req_complete = 0
		# Display counters for optional-only domains (required still owns section gates).
		opt_total = opt_complete = opt_needs = opt_started = 0
		for req in reqs:
			rid = _req_id(req)
			req_fields = _fields_for_req(sec or {}, req) or fields
			st = resolve_requirement_status(
				req, responses.get(rid) if isinstance(responses, dict) else {}, req_fields, sec=sec
			)
			_applicable, display_mode = resolve_requirement_applicability(req, sec=sec)
			counts_required = display_mode == MODE_REQUIRED
			if counts_required:
				req_total += 1
				if st == STATUS_COMPLETE:
					req_complete += 1
					started += 1
				elif st == STATUS_NEEDS_ATTENTION:
					needs += 1
					started += 1
				elif st == STATUS_IN_PROGRESS:
					started += 1
				continue
			# Informational never drives domain progress labels.
			if display_mode == MODE_INFORMATIONAL:
				continue
			# Optional rows: surface completion in the rail when the domain has no required items.
			opt_total += 1
			if st == STATUS_COMPLETE:
				opt_complete += 1
				opt_started += 1
			elif st == STATUS_NEEDS_ATTENTION:
				opt_needs += 1
				opt_started += 1
			elif st == STATUS_IN_PROGRESS:
				opt_started += 1
		if req_total:
			total = req_total
			complete = req_complete
			status = resolve_group_status(
				complete=req_complete,
				total=req_total,
				needs_attention=needs,
				started=started,
			)
			progress_label = f"{req_complete} of {req_total}"
			not_started = max(0, req_total - req_complete - needs)
		elif opt_total:
			total = opt_total
			complete = opt_complete
			needs = opt_needs
			status = resolve_group_status(
				complete=opt_complete,
				total=opt_total,
				needs_attention=opt_needs,
				started=opt_started,
			)
			progress_label = f"{opt_complete} of {opt_total}"
			not_started = max(0, opt_total - opt_complete - opt_needs)
		else:
			total = 0
			complete = 0
			status = STATUS_NOT_APPLICABLE
			progress_label = "0 of 0"
			not_started = 0
		groups.append(
			{
				"group_key": gk,
				"title": gk,
				"complete": complete,
				"total": total,
				"status": status,
				"progress_label": progress_label,
				"needs_attention": needs,
				"not_started": not_started,
			}
		)
	return groups


def _find_section(schema: dict[str, Any], section_key: str) -> dict[str, Any] | None:
	want = cstr(section_key or "").strip()
	for sec in schema.get("sections") or []:
		if isinstance(sec, dict) and _section_key(sec) == want:
			return sec
	return None


def _next_section_url(
	schema: dict[str, Any],
	current_key: str,
	*,
	publication_ref: str,
	configuration_id: str,
) -> str:
	sections = [s for s in (schema.get("sections") or []) if isinstance(s, dict) and _section_key(s)]
	idx = next((i for i, s in enumerate(sections) if _section_key(s) == current_key), -1)
	for s in sections[idx + 1 :]:
		if s.get("not_applicable") or s.get("applicable") is False:
			continue
		key = _section_key(s)
		if is_requirement_matrix_section(s):
			return portal_section_url(publication_ref, key)
		# Document acknowledgement → documents portal
		from kentender_procurement.tender_configurations.services.tender_documents_addenda import (
			is_document_acknowledgement_section,
			portal_documents_url,
		)

		if is_document_acknowledgement_section(s):
			return portal_documents_url(publication_ref)
		# Stay on the bidder portal — never expose desk configuration_id bridges.
		_ = configuration_id
		return portal_workspace_url(publication_ref)
	return portal_workspace_url(publication_ref)


def _ensure_bid(published_tender_ref: str) -> tuple[dict[str, Any], Any, dict[str, Any], dict[str, Any]]:
	from kentender_procurement.tender_configurations.services.published_tender_overview import (
		resolve_published_tender_backend,
	)

	overview = get_published_tender_overview(published_tender_ref)
	backend = resolve_published_tender_backend(published_tender_ref)
	action = overview.get("primary_action")
	if action in (ACTION_CLOSED, ACTION_UNAVAILABLE):
		frappe.throw(
			frappe._("Bidding is not available ({0}).").format(action),
			title="BID_WORKSPACE_UNAVAILABLE",
		)
	pub_ref = cstr(overview.get("published_tender_ref") or published_tender_ref)
	cfg_id = cstr(backend.get("configuration_id") or "")
	if action == ACTION_VIEW_SUBMITTED or overview.get("bid_status") == STATUS_SEALED:
		started = start_or_get_bid_workspace(pub_ref)
		bid_id = started.get("bid_id") or backend.get("bid_id")
	else:
		draft = create_or_get_draft(cfg_id)
		bid_id = draft.get("bid_id")
	bid_doc = frappe.get_doc("Electronic Bid Submission", bid_id)
	cfg = backend.get("configuration") or frappe.get_doc("Tender Configuration", cfg_id)
	schema = _load_schema(cfg, bid_doc)
	return overview, bid_doc, schema, {"pub_ref": pub_ref, "cfg_id": cfg_id}


def get_requirement_matrix(
	published_tender_ref: str,
	section_key: str,
	*,
	group: str | None = None,
	q: str | None = None,
	status: str | None = None,
	page: int = 1,
	page_size: int = DEFAULT_PAGE_SIZE,
) -> dict[str, Any]:
	_require_logged_in()
	overview, bid_doc, schema, ids = _ensure_bid(published_tender_ref)
	pub_ref = ids["pub_ref"]
	cfg_id = ids["cfg_id"]
	sec = _find_section(schema, section_key)
	if sec and _section_key(sec) == SECTION_KEY_RC:
		hydrate_requirements_compliance_section(sec, schema=schema, bid_doc=bid_doc)
	if not sec or not is_requirement_matrix_section(sec):
		frappe.throw(frappe._("Requirement matrix section not found."), frappe.DoesNotExistError)

	fields = _response_fields(sec)
	requirements = [r for r in (sec.get("requirements") or []) if isinstance(r, dict) and _req_id(r)]
	section_responses = _section_response_map(
		_parse_json(getattr(bid_doc, "responses", None), {}).get(_section_key(sec))
	)

	groups = build_groups(requirements, section_responses, fields, sec=sec)
	selected_group = cstr(group or "").strip()
	if not selected_group and groups:
		selected_group = groups[0]["group_key"]

	q_norm = cstr(q or "").strip().lower()
	status_filter = cstr(status or "").strip()
	rows_src = [r for r in requirements if _group_key(r) == selected_group] if selected_group else list(requirements)

	rows: list[dict[str, Any]] = []
	req_complete = req_total = needs_all = started_all = 0
	in_progress_all = not_started_all = 0
	for req in requirements:
		applicable, display_mode = resolve_requirement_applicability(req, sec=sec)
		if not applicable:
			continue
		rid = _req_id(req)
		req_fields = _fields_for_req(sec, req) or fields
		st = resolve_requirement_status(req, section_responses.get(rid), req_fields, sec=sec)
		counts_required = display_mode == MODE_REQUIRED
		if counts_required:
			req_total += 1
		if st == STATUS_COMPLETE:
			if counts_required:
				req_complete += 1
			started_all += 1
		elif st == STATUS_NEEDS_ATTENTION:
			# KPI / blockers: only required responses need attention for Complete Section.
			if counts_required:
				needs_all += 1
			started_all += 1
		elif st == STATUS_IN_PROGRESS:
			if counts_required:
				in_progress_all += 1
			started_all += 1
		elif st == STATUS_NOT_STARTED and counts_required:
			not_started_all += 1

	for req in rows_src:
		applicable, display_mode = resolve_requirement_applicability(req, sec=sec)
		if not applicable:
			continue
		rid = _req_id(req)
		resp = section_responses.get(rid) if isinstance(section_responses.get(rid), dict) else {}
		req_fields = _fields_for_req(sec, req) or fields
		st = resolve_requirement_status(req, resp, req_fields, sec=sec)
		disp = requirement_display(req)
		title = disp["list_title"]
		subtitle = disp.get("list_subtitle") or ""
		description = disp["description"]
		ref = cstr(req.get("tender_facing_reference") or rid)
		if (
			q_norm
			and q_norm not in rid.lower()
			and q_norm not in ref.lower()
			and q_norm not in title.lower()
			and q_norm not in subtitle.lower()
			and q_norm not in description.lower()
		):
			continue
		if status_filter and st != status_filter:
			continue
		mode = _requirement_mode(req)
		rows.append(
			{
				"requirement_id": rid,
				"tender_facing_reference": ref,
				"title": title,
				"subtitle": subtitle,
				"statement": subtitle,
				"description": description,
				"has_short_title": 1 if disp.get("has_short_title") == "1" else 0,
				"mandatory": 1 if display_mode == MODE_REQUIRED else 0,
				"mandatory_label": _mode_label(display_mode if display_mode != MODE_REQUIRED else mode),
				"requirement_mode": mode,
				"mode_label": _mode_label(display_mode if mode != MODE_CONDITIONAL else MODE_CONDITIONAL),
				"response_summary": _response_summary(resp, req_fields, req=req, status=st),
				"status": st,
				"action_label": _action_for_req_status(st, mode=display_mode),
				"group_key": _group_key(req),
				"updated_by_addendum": cstr(req.get("updated_by_addendum") or ""),
				"change_summary": cstr(req.get("bidder_facing_change_summary") or ""),
			}
		)

	page = max(1, int(page or 1))
	page_size = max(1, min(50, int(page_size or DEFAULT_PAGE_SIZE)))
	total = len(rows)
	start = (page - 1) * page_size
	page_rows = rows[start : start + page_size]
	pct = int(round(100.0 * float(req_complete) / float(req_total))) if req_total else 0

	modified = getattr(bid_doc, "modified", None)
	last_saved = ""
	if modified:
		try:
			dt = get_datetime(modified)
			last_saved = f"Last saved: {format_time(dt)}"
		except Exception:
			last_saved = f"Last saved: {cstr(modified)}"

	section_status, _blockers = matrix_section_roll_up(sec, section_responses)
	return {
		"published_tender_ref": pub_ref,
		"section_key": _section_key(sec),
		"section_title": _section_label(sec) or "Requirements Compliance",
		"section_instructions": cstr(
			sec.get("bidder_instructions")
			or sec.get("instructions")
			or "Respond to each applicable requirement and provide the requested supporting evidence."
		),
		"progress_complete": req_complete,
		"progress_total": req_total,
		"progress_percent": pct,
		"progress_label": f"{req_complete} of {req_total} required responses complete",
		"blocker_count": needs_all,
		"counts": {
			"required": req_total,
			"complete": req_complete,
			"in_progress": in_progress_all,
			"needs_attention": needs_all,
			"not_started": not_started_all,
		},
		"section_status": section_status,
		"groups": groups,
		"selected_group": selected_group,
		"rows": page_rows,
		"pagination": {
			"page": page,
			"page_size": page_size,
			"total": total,
			"total_pages": max(1, (total + page_size - 1) // page_size),
			"from": start + 1 if total else 0,
			"to": min(start + page_size, total),
		},
		"filters": {"q": cstr(q or ""), "status": status_filter},
		"workspace_url": portal_workspace_url(pub_ref),
		"review_url": portal_requirements_compliance_review_url(pub_ref),
		"next_section_url": _next_section_url(
			schema, _section_key(sec), publication_ref=pub_ref, configuration_id=cfg_id
		),
		"last_saved_display": last_saved or "—",
		"bid_sealed": 1 if cstr(bid_doc.status) == STATUS_SEALED else 0,
		"bid_id": bid_doc.name,
		"bid_modified": cstr(getattr(bid_doc, "modified", None) or ""),
		"section_complete_confirmed": 1
		if isinstance(section_responses.get("_section_meta"), dict)
		and section_responses["_section_meta"].get("complete_confirmed")
		else 0,
		"tender_title": overview.get("tender_title") or "",
		"procuring_entity": overview.get("procuring_entity") or "",
		"documents_url": f"/tenders/{quote(pub_ref, safe='')}/documents",
		"overview_url": f"/tenders/{quote(pub_ref, safe='')}",
		"evidence_url": f"/tenders/{quote(pub_ref, safe='')}/evidence",
	}


def _applicable_group_reqs(
	requirements: list[dict[str, Any]],
	group_key: str,
	*,
	sec: dict[str, Any] | None,
) -> list[dict[str, Any]]:
	return [
		r
		for r in requirements
		if _group_key(r) == group_key and resolve_requirement_applicability(r, sec=sec)[0]
	]


def _adjacent_requirement_ids(
	requirements: list[dict[str, Any]],
	requirement_id: str,
	*,
	sec: dict[str, Any] | None,
	fields: list[dict[str, Any]] | None = None,
) -> tuple[str, str]:
	"""Previous / next requirement ids across domain groups (same order as group rail).

	Save & Next already crossed groups when the current domain ended; Previous must
	mirror that so navigation is bidirectional across domains.
	"""
	rid = cstr(requirement_id or "").strip()
	req = next((r for r in requirements if _req_id(r) == rid), None)
	if not req:
		return "", ""
	gk = _group_key(req)
	group_reqs = _applicable_group_reqs(requirements, gk, sec=sec)
	pos = next((i for i, r in enumerate(group_reqs) if _req_id(r) == rid), -1)
	prev_id = _req_id(group_reqs[pos - 1]) if pos > 0 else ""
	next_id = _req_id(group_reqs[pos + 1]) if 0 <= pos < len(group_reqs) - 1 else ""

	groups = build_groups(requirements, {}, fields or [], sec=sec)
	gkeys = [g["group_key"] for g in groups]
	if gk not in gkeys:
		return prev_id, next_id
	gi = gkeys.index(gk)

	if not next_id:
		for ng in gkeys[gi + 1 :]:
			nreqs = _applicable_group_reqs(requirements, ng, sec=sec)
			if nreqs:
				next_id = _req_id(nreqs[0])
				break

	if not prev_id:
		for pg in reversed(gkeys[:gi]):
			preqs = _applicable_group_reqs(requirements, pg, sec=sec)
			if preqs:
				prev_id = _req_id(preqs[-1])
				break

	return prev_id, next_id


def get_requirement_drawer(
	published_tender_ref: str,
	section_key: str,
	requirement_id: str,
) -> dict[str, Any]:
	_require_logged_in()
	_overview, bid_doc, schema, ids = _ensure_bid(published_tender_ref)
	sec = _find_section(schema, section_key)
	if sec and _section_key(sec) == SECTION_KEY_RC:
		hydrate_requirements_compliance_section(sec, schema=schema, bid_doc=bid_doc)
	if not sec or not is_requirement_matrix_section(sec):
		frappe.throw(frappe._("Requirement matrix section not found."), frappe.DoesNotExistError)

	requirements = [r for r in (sec.get("requirements") or []) if isinstance(r, dict) and _req_id(r)]
	rid = cstr(requirement_id or "").strip()
	req = next((r for r in requirements if _req_id(r) == rid), None)
	if not req:
		frappe.throw(frappe._("Requirement not found."), frappe.DoesNotExistError)

	fields = _fields_for_req(sec, req) or _response_fields(sec)
	portal_fields = _portal_fields(fields)
	applicable, display_mode = resolve_requirement_applicability(req, sec=sec)
	gk = _group_key(req)
	group_reqs = [
		r
		for r in requirements
		if _group_key(r) == gk and resolve_requirement_applicability(r, sec=sec)[0]
	]
	pos = next((i for i, r in enumerate(group_reqs) if _req_id(r) == rid), 0)
	prev_id, next_id = _adjacent_requirement_ids(requirements, rid, sec=sec, fields=fields)

	section_responses = _parse_json(getattr(bid_doc, "responses", None), {}).get(_section_key(sec)) or {}
	resp = section_responses.get(rid) if isinstance(section_responses, dict) else {}
	if not isinstance(resp, dict):
		resp = {}
	resp_view = dict(resp)
	for f in fields:
		if cstr(f.get("type")) == "file":
			fk = cstr(f.get("field_key") or "")
			resp_view[fk] = _normalize_file_list(resp.get(fk))
	st = resolve_requirement_status(req, resp_view, fields, sec=sec)
	disp = requirement_display(req)
	field_errors = collect_in_progress_field_errors(req, resp_view, fields, status=st)
	show_attention = bool(field_errors) and st == STATUS_IN_PROGRESS
	for f in portal_fields:
		fk = cstr(f.get("field_key") or "")
		if fk in field_errors:
			f["error"] = field_errors[fk]
		else:
			f["error"] = ""
	validation_messages = list(dict.fromkeys(field_errors.values()))
	addendum = cstr(req.get("updated_by_addendum") or "").strip()

	return {
		"published_tender_ref": ids["pub_ref"],
		"section_key": _section_key(sec),
		"requirement_id": rid,
		"tender_facing_reference": cstr(req.get("tender_facing_reference") or rid),
		"title": disp["header_title"],
		"header_title": disp["header_title"],
		"statement": "",
		"description": disp["description"],
		"requirement_statement": disp["description"],
		"has_short_title": 1 if disp.get("has_short_title") == "1" else 0,
		"group_key": gk,
		"position_label": f"Requirement {pos + 1} of {len(group_reqs)}",
		"status": st,
		"header_status": STATUS_NEEDS_ATTENTION if show_attention else st,
		"show_attention": 1 if show_attention else 0,
		"field_errors": field_errors,
		"mandatory": 1 if display_mode == MODE_REQUIRED else 0,
		"mode_label": _mode_label(
			MODE_CONDITIONAL if _requirement_mode(req) == MODE_CONDITIONAL else display_mode
		),
		"requirement_mode": _requirement_mode(req),
		"applicable": 1 if applicable else 0,
		"fields": portal_fields,
		"response": resp_view,
		"validation_messages": validation_messages,
		"prev_requirement_id": prev_id,
		"next_requirement_id": next_id,
		"bid_sealed": 1 if cstr(bid_doc.status) == STATUS_SEALED else 0,
		"updated_by_addendum": addendum,
		"addendum_banner": f"Updated by Addendum {addendum}" if addendum else "",
		"change_summary": cstr(req.get("bidder_facing_change_summary") or ""),
		"technical_alternative_permitted": 1 if req.get("technical_alternative_permitted") else 0,
		"evidence_url": f"/tenders/{quote(ids['pub_ref'], safe='')}/evidence",
	}


def save_requirement_response(
	published_tender_ref: str,
	section_key: str,
	requirement_id: str,
	payload: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
	_require_logged_in()
	_overview, bid_doc, schema, ids = _ensure_bid(published_tender_ref)
	if cstr(bid_doc.status) == STATUS_SEALED:
		frappe.throw(frappe._("Sealed electronic bids are immutable."), title="BID_IMMUTABLE")
	sec = _find_section(schema, section_key)
	if sec and _section_key(sec) == SECTION_KEY_RC:
		hydrate_requirements_compliance_section(sec, schema=schema, bid_doc=bid_doc)
	if not sec or not is_requirement_matrix_section(sec):
		frappe.throw(frappe._("Requirement matrix section not found."), frappe.DoesNotExistError)
	rid = cstr(requirement_id or "").strip()
	if not rid:
		frappe.throw(frappe._("requirement_id is required."), title="BID_REQUIREMENT")
	if isinstance(payload, str):
		payload = _parse_json(payload, {})
	payload = dict(payload or {})
	# Never persist suppressed PDF page refs from portal
	payload.pop("reference_pages", None)
	req_row = next(
		(r for r in (sec.get("requirements") or []) if isinstance(r, dict) and _req_id(r) == rid),
		None,
	)
	# Normalize typed fields for portal save payloads.
	fields = _fields_for_req(sec, req_row or {}) or _response_fields(sec)
	for f in fields:
		fk = cstr(f.get("field_key") or "")
		if not fk or fk not in payload:
			continue
		ftype = cstr(f.get("type") or "").strip().lower()
		if ftype == "file":
			payload[fk] = _normalize_file_list(payload.get(fk))
		elif ftype == "boolean":
			val = payload.get(fk)
			payload[fk] = 1 if val in (1, "1", True, "true", "True", "yes", "Yes", "on") else 0
		elif ftype == "repeating_table":
			val = payload.get(fk)
			if isinstance(val, str):
				try:
					val = json.loads(val)
				except (TypeError, ValueError):
					val = []
			if not isinstance(val, list):
				val = []
			norm_rows: list[dict[str, Any]] = []
			for row in val:
				if isinstance(row, dict) and any(_is_filled(v) for v in row.values()):
					norm_rows.append(row)
			payload[fk] = norm_rows
		elif ftype in {"number", "money", "percentage"}:
			val = payload.get(fk)
			if val in ("", None):
				continue
			try:
				payload[fk] = float(val) if "." in cstr(val) else int(val)
			except (TypeError, ValueError):
				pass

	responses = _parse_json(getattr(bid_doc, "responses", None), {})
	section_map = responses.get(_section_key(sec))
	if not isinstance(section_map, dict):
		section_map = {}
	existing = section_map.get(rid) if isinstance(section_map.get(rid), dict) else {}
	merged = dict(existing)
	merged.update(payload)
	# Resaving after an addendum clears Needs Attention for amendment review.
	if req_row and cstr(req_row.get("updated_by_addendum") or "").strip():
		merged["addendum_reviewed"] = 1
	merged.pop("needs_attention", None)
	section_map[rid] = merged
	save_section_responses(bid_doc.name, _section_key(sec), section_map)

	matrix = get_requirement_matrix(
		published_tender_ref,
		section_key,
		group=_group_key(
			next(
				(r for r in (sec.get("requirements") or []) if isinstance(r, dict) and _req_id(r) == rid),
				{"category_label": "General"},
			)
		),
	)
	drawer = get_requirement_drawer(published_tender_ref, section_key, rid)
	return {"matrix": matrix, "drawer": drawer}


def _section_response_map(section_responses: Any) -> dict[str, Any]:
	"""Normalize bare payload or envelope to requirement_id → response dict."""
	if not isinstance(section_responses, dict):
		return {}
	if "payload" in section_responses and (
		"section_key" in section_responses or "meta" in section_responses
	):
		inner = section_responses.get("payload")
		return inner if isinstance(inner, dict) else {}
	return section_responses


def matrix_section_roll_up(sec: dict[str, Any], section_responses: Any) -> tuple[str, int]:
	"""Return (checklist_status, blocker_count) for a matrix section.

	Only **required** applicable responses gate section completion. Optional /
	informational rows never contribute blockers (including Needs Attention).
	"""
	if not is_requirement_matrix_section(sec):
		return STATUS_NOT_STARTED, 0
	fields = _response_fields(sec)
	requirements = [r for r in (sec.get("requirements") or []) if isinstance(r, dict) and _req_id(r)]
	resp_map = _section_response_map(section_responses)
	if not requirements:
		return STATUS_NOT_STARTED, 0
	needs = started = 0
	mandatory_total = 0
	mandatory_complete = 0
	for req in requirements:
		applicable, display_mode = resolve_requirement_applicability(req, sec=sec)
		if not applicable:
			continue
		rid = _req_id(req)
		req_fields = _fields_for_req(sec, req) or fields
		st = resolve_requirement_status(req, resp_map.get(rid), req_fields, sec=sec)
		counts_required = display_mode == MODE_REQUIRED
		if not counts_required:
			# Optional / informational never block Complete Section.
			continue
		mandatory_total += 1
		if st == STATUS_COMPLETE:
			started += 1
			mandatory_complete += 1
		elif st == STATUS_NEEDS_ATTENTION:
			needs += 1
			started += 1
		elif st == STATUS_IN_PROGRESS:
			started += 1
	if needs:
		return STATUS_NEEDS_ATTENTION, needs
	if mandatory_total and mandatory_complete >= mandatory_total:
		return STATUS_COMPLETE, 0
	if started:
		return STATUS_IN_PROGRESS, 0
	return STATUS_NOT_STARTED, 0


def requirements_compliance_first_action_url(
	published_tender_ref: str,
	sec: dict[str, Any],
	section_responses: dict[str, Any] | None = None,
) -> str:
	"""Deep-link Resolve to first incomplete/needs-attention required requirement."""
	base = portal_requirements_compliance_url(published_tender_ref)
	resp_map = section_responses if isinstance(section_responses, dict) else {}
	fields = _response_fields(sec)
	for req in sec.get("requirements") or []:
		if not isinstance(req, dict):
			continue
		applicable, display_mode = resolve_requirement_applicability(req, sec=sec)
		if not applicable or display_mode != MODE_REQUIRED:
			continue
		rid = _req_id(req)
		st = resolve_requirement_status(
			req, resp_map.get(rid), _fields_for_req(sec, req) or fields, sec=sec
		)
		if st in (STATUS_NEEDS_ATTENTION, STATUS_IN_PROGRESS, STATUS_NOT_STARTED):
			gk = quote(_group_key(req), safe="")
			return f"{base}?group={gk}&requirement_id={quote(rid, safe='')}"
	return base


def get_requirements_compliance_review(published_tender_ref: str) -> dict[str, Any]:
	"""Review DTO — KPIs, group table, unresolved issues (§12)."""
	# Single load path: matrix hydrates RC and is the source of truth for KPIs / readiness.
	matrix = get_requirement_matrix(published_tender_ref, SECTION_KEY_RC, page_size=50)
	overview, bid_doc, schema, ids = _ensure_bid(published_tender_ref)
	sec = _find_section(schema, SECTION_KEY_RC) or {}
	if sec:
		hydrate_requirements_compliance_section(sec, schema=schema, bid_doc=bid_doc)
	fields = _response_fields(sec)
	requirements = [r for r in (sec.get("requirements") or []) if isinstance(r, dict) and _req_id(r)]
	section_responses = _section_response_map(
		_parse_json(getattr(bid_doc, "responses", None), {}).get(SECTION_KEY_RC)
	)

	issues: list[dict[str, Any]] = []
	for req in requirements:
		applicable, display_mode = resolve_requirement_applicability(req, sec=sec)
		if not applicable or display_mode != MODE_REQUIRED:
			continue
		rid = _req_id(req)
		req_fields = _fields_for_req(sec, req) or fields
		resp = section_responses.get(rid) if isinstance(section_responses.get(rid), dict) else {}
		st = resolve_requirement_status(req, resp, req_fields, sec=sec)
		if st not in (STATUS_NEEDS_ATTENTION, STATUS_IN_PROGRESS, STATUS_NOT_STARTED):
			continue
		errs = collect_in_progress_field_errors(req, resp, req_fields, status=st)
		issue = next(iter(errs.values()), "")
		if not issue:
			if st == STATUS_NOT_STARTED:
				issue = "Required response has not been provided."
			elif cstr(req.get("updated_by_addendum") or "").strip() and not resp.get("addendum_reviewed"):
				issue = f"Response must be reviewed after Addendum {cstr(req.get('updated_by_addendum'))}."
			else:
				issue = "Required information is incomplete."
		disp = requirement_display(req)
		issues.append(
			{
				"requirement_id": rid,
				"tender_facing_reference": cstr(req.get("tender_facing_reference") or rid),
				"title": disp["list_title"],
				"issue": issue,
				"group_key": _group_key(req),
				"status": st,
				"action_url": (
					f"{portal_requirements_compliance_url(ids['pub_ref'])}"
					f"?group={quote(_group_key(req), safe='')}"
					f"&requirement_id={quote(rid, safe='')}"
				),
			}
		)

	counts = matrix.get("counts") or {}
	status, blockers = matrix_section_roll_up(sec, section_responses)
	# Prefer matrix roll-up when hydrated matrix already computed it (same bid snapshot).
	matrix_status = cstr(matrix.get("section_status") or "")
	if matrix_status == STATUS_COMPLETE and not int(matrix.get("blocker_count") or 0):
		status = STATUS_COMPLETE
		blockers = 0
	ready = status == STATUS_COMPLETE and blockers == 0 and not issues
	meta = (
		section_responses.get("_section_meta")
		if isinstance(section_responses.get("_section_meta"), dict)
		else {}
	)
	return {
		**matrix,
		"page_title": "Review Requirements Compliance",
		"section_url": portal_requirements_compliance_url(ids["pub_ref"]),
		"review_url": portal_requirements_compliance_review_url(ids["pub_ref"]),
		"unresolved_issues": issues,
		"section_status": status,
		"complete_enabled": 1 if ready else 0,
		"section_complete_confirmed": 1 if meta.get("complete_confirmed") else 0,
		"counts": {
			"required": int(counts.get("required") or 0),
			"complete": int(counts.get("complete") or 0),
			"in_progress": int(counts.get("in_progress") or 0),
			"needs_attention": int(counts.get("needs_attention") or 0),
			"not_started": int(counts.get("not_started") or 0),
		},
		"tender_title": overview.get("tender_title") or matrix.get("tender_title") or "",
		"procuring_entity": overview.get("procuring_entity") or "",
		"read_only": 1 if cstr(bid_doc.status) == STATUS_SEALED else 0,
	}


def complete_requirements_compliance_section(published_tender_ref: str) -> dict[str, Any]:
	"""Mark section complete when ready — does not seal the bid."""
	_require_logged_in()
	_overview, bid_doc, schema, ids = _ensure_bid(published_tender_ref)
	if cstr(bid_doc.status) == STATUS_SEALED:
		frappe.throw(frappe._("Sealed electronic bids are immutable."), title="BID_IMMUTABLE")
	sec = _find_section(schema, SECTION_KEY_RC)
	if sec:
		hydrate_requirements_compliance_section(sec, schema=schema, bid_doc=bid_doc)
	if not sec or not is_requirement_matrix_section(sec):
		frappe.throw(frappe._("Requirements Compliance section not found."), frappe.DoesNotExistError)
	responses = _parse_json(getattr(bid_doc, "responses", None), {})
	section_map = _section_response_map(responses.get(SECTION_KEY_RC))
	status, blockers = matrix_section_roll_up(sec, section_map)
	if status != STATUS_COMPLETE or blockers:
		frappe.throw(
			frappe._("Complete all applicable required responses before completing this section."),
			title="KT_RC_NOT_READY",
		)
	# Persist onto the stored section map (preserve sibling keys / meta).
	stored = responses.get(SECTION_KEY_RC)
	if isinstance(stored, dict) and "payload" in stored and (
		"section_key" in stored or "meta" in stored
	):
		body = stored.get("payload") if isinstance(stored.get("payload"), dict) else {}
		section_map = dict(body)
		responses[SECTION_KEY_RC] = section_map
	elif not isinstance(stored, dict):
		responses[SECTION_KEY_RC] = section_map
	else:
		section_map = stored
	meta = section_map.get("_section_meta") if isinstance(section_map.get("_section_meta"), dict) else {}
	meta = dict(meta)
	meta["complete_confirmed"] = 1
	meta["completed_by"] = frappe.session.user
	meta["completed_at"] = str(now_datetime())
	section_map["_section_meta"] = meta
	save_section_responses(bid_doc.name, SECTION_KEY_RC, section_map)
	return get_requirements_compliance_review(published_tender_ref)
