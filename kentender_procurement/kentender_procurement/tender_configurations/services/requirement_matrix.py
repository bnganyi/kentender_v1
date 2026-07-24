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
SUPPORTED_FIELD_TYPES = frozenset({"text", "narrative", "file", "boolean", "select", "number", "money"})

DEFAULT_PAGE_SIZE = 10


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
	- list shows one line; drawer header is the ID; Description shows the text once.
	"""
	rid = _req_id(req)
	raw_title = cstr(req.get("requirement_title") or req.get("title") or "").strip()
	raw_statement = cstr(req.get("requirement_statement") or req.get("description") or "").strip()
	short_cap = 80
	has_short_title = bool(raw_title) and len(raw_title) <= short_cap

	if has_short_title:
		detail = _strip_title_prefix(raw_title, raw_statement) if raw_statement else ""
		# Short title identical to statement → treat as undifferentiated blob (ID header).
		if raw_statement and not detail:
			blob = raw_title
			return {
				"requirement_id": rid,
				"list_title": blob,
				"list_subtitle": "",
				"header_title": rid or blob,
				"description": blob,
				"has_short_title": "0",
				"title": blob,
				"statement": "",
			}
		header_title = f"{rid}: {raw_title}" if rid else raw_title
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
	blob = raw_title or raw_statement or rid
	return {
		"requirement_id": rid,
		"list_title": blob,
		"list_subtitle": "",
		"header_title": rid or blob,
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
	stype = cstr(sec.get("section_type") or sec.get("type") or "").strip().lower()
	if stype == "requirement_matrix":
		return True
	reqs = sec.get("requirements")
	fields = sec.get("response_fields_per_requirement")
	return isinstance(reqs, list) and len(reqs) > 0 and isinstance(fields, (list, tuple)) and len(fields) > 0


def portal_section_url(publication_ref: str, section_key: str) -> str:
	ref = quote(cstr(publication_ref or "").strip(), safe="")
	key = quote(cstr(section_key or "").strip(), safe="")
	return f"/tenders/{ref}/sections/{key}"


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


def _response_fields(sec: dict[str, Any]) -> list[dict[str, Any]]:
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


def resolve_requirement_status(
	req: dict[str, Any],
	response: dict[str, Any] | None,
	fields: list[dict[str, Any]],
) -> str:
	if req.get("not_applicable") or req.get("applicable") is False:
		return STATUS_NOT_APPLICABLE
	resp = response if isinstance(response, dict) else {}
	if resp.get("needs_attention") or (
		isinstance(resp.get("validation_errors"), list) and resp.get("validation_errors")
	):
		return STATUS_NEEDS_ATTENTION

	required_fields = [f for f in fields if f.get("required")]
	if not required_fields:
		required_fields = [f for f in fields if cstr(f.get("type")) != "file"][:2]

	filled_required = 0
	missing_required = 0
	for f in required_fields:
		fk = cstr(f.get("field_key") or "")
		if _is_filled(resp.get(fk)):
			filled_required += 1
		else:
			missing_required += 1

	meta_keys = {"validation_errors", "needs_attention", "status"}
	any_filled = any(_is_filled(v) for k, v in resp.items() if k not in meta_keys)
	if not any_filled and filled_required == 0:
		return STATUS_NOT_STARTED

	# Evidence implied by response type: once required text is filled, missing file → Needs Attention.
	brt = cstr(req.get("bidder_response_type") or "").lower()
	evidence_needed = "evidence" in brt
	if evidence_needed and missing_required == 0:
		for f in fields:
			if cstr(f.get("type")) != "file":
				continue
			fk = cstr(f.get("field_key") or "")
			if not _is_filled(resp.get(fk)):
				return STATUS_NEEDS_ATTENTION

	if missing_required == 0 and filled_required >= len(required_fields):
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


def _response_summary(resp: dict[str, Any] | None, fields: list[dict[str, Any]]) -> str:
	if not isinstance(resp, dict) or not resp:
		return "—"
	yes_no = cstr(resp.get("compliant_yes_no") or "").strip()
	statement = cstr(resp.get("compliance_statement") or "").strip()
	if yes_no and statement:
		short = statement if len(statement) <= 48 else statement[:45] + "…"
		return f"{yes_no}: {short}"
	if yes_no:
		return yes_no
	if statement:
		return statement if len(statement) <= 56 else statement[:53] + "…"
	for f in fields:
		fk = cstr(f.get("field_key") or "")
		val = resp.get(fk)
		if cstr(f.get("type")) == "file":
			files = _normalize_file_list(val)
			if files:
				if len(files) == 1:
					return cstr(files[0].get("file_name") or "1 file")
				return f"{len(files)} files"
		if _is_filled(val) and not isinstance(val, (dict, list)):
			text = cstr(val).strip()
			return text if len(text) <= 56 else text[:53] + "…"
	return "—"


def _action_for_req_status(status: str) -> str:
	if status == STATUS_COMPLETE:
		return "Review"
	if status == STATUS_NEEDS_ATTENTION:
		return "Continue"
	if status == STATUS_IN_PROGRESS:
		return "Continue"
	if status == STATUS_NOT_APPLICABLE:
		return "View"
	return "Start"


def _portal_fields(fields: list[dict[str, Any]]) -> list[dict[str, Any]]:
	out: list[dict[str, Any]] = []
	for f in fields:
		ftype = cstr(f.get("type") or "text").strip().lower()
		row = dict(f)
		fkey = cstr(f.get("field_key") or "")
		if ftype not in SUPPORTED_FIELD_TYPES:
			row["unsupported"] = 1
			row["unsupported_message"] = f"Unsupported response type '{ftype}'"
		else:
			row["unsupported"] = 0
		# Yes/No UX hint for compliant_yes_no
		if fkey == "compliant_yes_no":
			row["control"] = "yes_no"
		elif ftype == "narrative":
			row["control"] = "textarea"
		elif ftype == "file":
			row["control"] = "file"
			row["multiple"] = 1
		elif ftype == "select":
			row["control"] = "select"
		else:
			row["control"] = "text"
		if fkey in FIELD_HELP:
			row["help_text"] = FIELD_HELP[fkey]
		out.append(row)
	return out


def build_groups(
	requirements: list[dict[str, Any]],
	responses: dict[str, Any],
	fields: list[dict[str, Any]],
) -> list[dict[str, Any]]:
	order: list[str] = []
	buckets: dict[str, list[dict[str, Any]]] = {}
	for req in requirements:
		if not isinstance(req, dict) or not _req_id(req):
			continue
		gk = _group_key(req)
		if gk not in buckets:
			buckets[gk] = []
			order.append(gk)
		buckets[gk].append(req)

	groups: list[dict[str, Any]] = []
	for gk in order:
		reqs = buckets[gk]
		complete = needs = started = 0
		for req in reqs:
			rid = _req_id(req)
			st = resolve_requirement_status(req, responses.get(rid) if isinstance(responses, dict) else {}, fields)
			if st == STATUS_COMPLETE:
				complete += 1
				started += 1
			elif st == STATUS_NEEDS_ATTENTION:
				needs += 1
				started += 1
			elif st == STATUS_IN_PROGRESS:
				started += 1
		total = len(reqs)
		status = resolve_group_status(
			complete=complete, total=total, needs_attention=needs, started=started
		)
		groups.append(
			{
				"group_key": gk,
				"title": gk,
				"complete": complete,
				"total": total,
				"status": status,
				"progress_label": f"{complete} / {total}",
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
		return _desk_bridge(configuration_id)
	return portal_workspace_url(publication_ref)


def _ensure_bid(published_tender_ref: str) -> tuple[dict[str, Any], Any, dict[str, Any], dict[str, Any]]:
	overview = get_published_tender_overview(published_tender_ref)
	action = overview.get("primary_action")
	if action in (ACTION_CLOSED, ACTION_UNAVAILABLE):
		frappe.throw(
			frappe._("Bidding is not available ({0}).").format(action),
			title="BID_WORKSPACE_UNAVAILABLE",
		)
	pub_ref = cstr(overview.get("published_tender_ref") or published_tender_ref)
	cfg_id = cstr(overview.get("configuration_id") or "")
	if action == ACTION_VIEW_SUBMITTED or overview.get("bid_status") == STATUS_SEALED:
		started = start_or_get_bid_workspace(pub_ref)
		bid_id = started.get("bid_id") or overview.get("bid_id")
	else:
		draft = create_or_get_draft(cfg_id)
		bid_id = draft.get("bid_id")
	bid_doc = frappe.get_doc("Electronic Bid Submission", bid_id)
	cfg = frappe.get_doc("Tender Configuration", cfg_id)
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
	if not sec or not is_requirement_matrix_section(sec):
		frappe.throw(frappe._("Requirement matrix section not found."), frappe.DoesNotExistError)

	fields = _response_fields(sec)
	requirements = [r for r in (sec.get("requirements") or []) if isinstance(r, dict) and _req_id(r)]
	section_responses = _parse_json(getattr(bid_doc, "responses", None), {}).get(_section_key(sec)) or {}
	if not isinstance(section_responses, dict):
		section_responses = {}

	groups = build_groups(requirements, section_responses, fields)
	selected_group = cstr(group or "").strip()
	if not selected_group and groups:
		selected_group = groups[0]["group_key"]

	q_norm = cstr(q or "").strip().lower()
	status_filter = cstr(status or "").strip()
	rows_src = [r for r in requirements if _group_key(r) == selected_group] if selected_group else list(requirements)

	rows: list[dict[str, Any]] = []
	complete_all = needs_all = started_all = 0
	for req in requirements:
		rid = _req_id(req)
		st = resolve_requirement_status(req, section_responses.get(rid), fields)
		if st == STATUS_COMPLETE:
			complete_all += 1
			started_all += 1
		elif st == STATUS_NEEDS_ATTENTION:
			needs_all += 1
			started_all += 1
		elif st == STATUS_IN_PROGRESS:
			started_all += 1

	for req in rows_src:
		rid = _req_id(req)
		resp = section_responses.get(rid) if isinstance(section_responses.get(rid), dict) else {}
		st = resolve_requirement_status(req, resp, fields)
		disp = requirement_display(req)
		title = disp["list_title"]
		subtitle = disp.get("list_subtitle") or ""
		description = disp["description"]
		if (
			q_norm
			and q_norm not in rid.lower()
			and q_norm not in title.lower()
			and q_norm not in subtitle.lower()
			and q_norm not in description.lower()
		):
			continue
		if status_filter and st != status_filter:
			continue
		mandatory = bool(req.get("mandatory", True))
		rows.append(
			{
				"requirement_id": rid,
				"title": title,
				"subtitle": subtitle,
				"statement": subtitle,
				"description": description,
				"has_short_title": 1 if disp.get("has_short_title") == "1" else 0,
				"mandatory": 1 if mandatory else 0,
				"mandatory_label": "Mandatory" if mandatory else "Optional",
				"response_summary": _response_summary(resp, fields),
				"status": st,
				"action_label": _action_for_req_status(st),
				"group_key": _group_key(req),
			}
		)

	page = max(1, int(page or 1))
	page_size = max(1, min(50, int(page_size or DEFAULT_PAGE_SIZE)))
	total = len(rows)
	start = (page - 1) * page_size
	page_rows = rows[start : start + page_size]
	total_reqs = len(requirements)
	pct = int(round(100.0 * float(complete_all) / float(total_reqs))) if total_reqs else 0

	modified = getattr(bid_doc, "modified", None)
	last_saved = ""
	if modified:
		try:
			dt = get_datetime(modified)
			last_saved = f"Last saved: {format_time(dt)}"
		except Exception:
			last_saved = f"Last saved: {cstr(modified)}"

	return {
		"published_tender_ref": pub_ref,
		"configuration_id": cfg_id,
		"bid_id": bid_doc.name,
		"section_key": _section_key(sec),
		"section_title": _section_label(sec),
		"section_instructions": cstr(
			sec.get("instructions")
			or "Complete each requirement below. Open a requirement to enter or review your response."
		),
		"progress_complete": complete_all,
		"progress_total": total_reqs,
		"progress_percent": pct,
		"progress_label": f"{complete_all} / {total_reqs} requirements complete",
		"blocker_count": needs_all,
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
		"next_section_url": _next_section_url(
			schema, _section_key(sec), publication_ref=pub_ref, configuration_id=cfg_id
		),
		"last_saved_display": last_saved or "—",
		"bid_sealed": 1 if cstr(bid_doc.status) == STATUS_SEALED else 0,
		"tender_title": overview.get("tender_title") or "",
		"documents_url": f"/tenders/{quote(pub_ref, safe='')}/documents",
		"overview_url": f"/tenders/{quote(pub_ref, safe='')}",
	}


def get_requirement_drawer(
	published_tender_ref: str,
	section_key: str,
	requirement_id: str,
) -> dict[str, Any]:
	_require_logged_in()
	_overview, bid_doc, schema, ids = _ensure_bid(published_tender_ref)
	sec = _find_section(schema, section_key)
	if not sec or not is_requirement_matrix_section(sec):
		frappe.throw(frappe._("Requirement matrix section not found."), frappe.DoesNotExistError)

	fields = _response_fields(sec)
	portal_fields = _portal_fields(fields)
	requirements = [r for r in (sec.get("requirements") or []) if isinstance(r, dict) and _req_id(r)]
	rid = cstr(requirement_id or "").strip()
	req = next((r for r in requirements if _req_id(r) == rid), None)
	if not req:
		frappe.throw(frappe._("Requirement not found."), frappe.DoesNotExistError)

	gk = _group_key(req)
	group_reqs = [r for r in requirements if _group_key(r) == gk]
	pos = next((i for i, r in enumerate(group_reqs) if _req_id(r) == rid), 0)
	prev_id = _req_id(group_reqs[pos - 1]) if pos > 0 else ""
	next_id = _req_id(group_reqs[pos + 1]) if pos + 1 < len(group_reqs) else ""
	# Continue into next group when current ends
	if not next_id:
		groups = build_groups(requirements, {}, fields)
		gkeys = [g["group_key"] for g in groups]
		if gk in gkeys:
			gi = gkeys.index(gk)
			for ng in gkeys[gi + 1 :]:
				nreqs = [r for r in requirements if _group_key(r) == ng]
				if nreqs:
					next_id = _req_id(nreqs[0])
					break

	section_responses = _parse_json(getattr(bid_doc, "responses", None), {}).get(_section_key(sec)) or {}
	resp = section_responses.get(rid) if isinstance(section_responses, dict) else {}
	if not isinstance(resp, dict):
		resp = {}
	# Present file fields as lists for the portal drawer.
	resp_view = dict(resp)
	for f in fields:
		if cstr(f.get("type")) == "file":
			fk = cstr(f.get("field_key") or "")
			resp_view[fk] = _normalize_file_list(resp.get(fk))
	st = resolve_requirement_status(req, resp_view, fields)
	disp = requirement_display(req)
	field_errors = collect_in_progress_field_errors(req, resp_view, fields, status=st)
	# Badge only beside In Progress — when status is already Needs Attention, avoid duplicating.
	show_attention = bool(field_errors) and st == STATUS_IN_PROGRESS
	# Attach errors onto field DTOs for under-input rendering.
	for f in portal_fields:
		fk = cstr(f.get("field_key") or "")
		if fk in field_errors:
			f["error"] = field_errors[fk]
		else:
			f["error"] = ""
	validation_messages = list(dict.fromkeys(field_errors.values()))

	return {
		"published_tender_ref": ids["pub_ref"],
		"section_key": _section_key(sec),
		"requirement_id": rid,
		"title": disp["header_title"],
		"header_title": disp["header_title"],
		"statement": "",  # never mirror title into a second top block
		"description": disp["description"],
		"has_short_title": 1 if disp.get("has_short_title") == "1" else 0,
		"group_key": gk,
		"position_label": f"Requirement {pos + 1} of {len(group_reqs)}",
		"status": st,
		# Drawer chrome: keep list status, surface Needs Attention when in-progress gaps exist.
		"header_status": STATUS_NEEDS_ATTENTION if show_attention else st,
		"show_attention": 1 if show_attention else 0,
		"field_errors": field_errors,
		"mandatory": 1 if req.get("mandatory", True) else 0,
		"fields": portal_fields,
		"response": resp_view,
		"validation_messages": validation_messages,
		"prev_requirement_id": prev_id,
		"next_requirement_id": next_id,
		"bid_sealed": 1 if cstr(bid_doc.status) == STATUS_SEALED else 0,
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
	# Normalize file fields to a list (multi-evidence); empty list clears attachments.
	fields = _response_fields(sec)
	for f in fields:
		if cstr(f.get("type")) != "file":
			continue
		fk = cstr(f.get("field_key") or "")
		if fk in payload:
			payload[fk] = _normalize_file_list(payload.get(fk))

	responses = _parse_json(getattr(bid_doc, "responses", None), {})
	section_map = responses.get(_section_key(sec))
	if not isinstance(section_map, dict):
		section_map = {}
	existing = section_map.get(rid) if isinstance(section_map.get(rid), dict) else {}
	merged = dict(existing)
	merged.update(payload)
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


def matrix_section_roll_up(sec: dict[str, Any], section_responses: Any) -> tuple[str, int]:
	"""Return (checklist_status, blocker_count) for a matrix section."""
	if not is_requirement_matrix_section(sec):
		return STATUS_NOT_STARTED, 0
	fields = _response_fields(sec)
	requirements = [r for r in (sec.get("requirements") or []) if isinstance(r, dict) and _req_id(r)]
	resp_map = section_responses if isinstance(section_responses, dict) else {}
	if not requirements:
		return STATUS_NOT_STARTED, 0
	complete = needs = started = 0
	mandatory_total = 0
	mandatory_complete = 0
	for req in requirements:
		rid = _req_id(req)
		st = resolve_requirement_status(req, resp_map.get(rid), fields)
		mandatory = bool(req.get("mandatory", True))
		if mandatory and st != STATUS_NOT_APPLICABLE:
			mandatory_total += 1
		if st == STATUS_COMPLETE:
			complete += 1
			started += 1
			if mandatory:
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
