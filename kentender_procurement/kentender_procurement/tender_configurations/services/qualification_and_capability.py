# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Qualification and Capability — overview + five category renderers (lean S600)."""

from __future__ import annotations

import calendar
import json
import uuid
from datetime import date
from typing import Any
from urllib.parse import quote

import frappe
from frappe.utils import cstr, getdate, now_datetime

from kentender_procurement.tender_configurations.seed.lean_qualification_criteria import (
	CATEGORY_CONTRACT,
	CATEGORY_EXPERIENCE,
	CATEGORY_FINANCIAL,
	CATEGORY_PARTNERS,
	CATEGORY_PERSONNEL,
	CONDITION_ALWAYS,
	CONDITION_EXTERNAL,
	CONDITION_JV,
	CONDITION_KEY_POSITIONS,
	CONDITION_PARTNERS,
	MODE_CONDITIONAL,
	MODE_EXCLUDED,
	MODE_OPTIONAL,
	MODE_REQUIRED,
	SCOPE_JV_MEMBER,
	SCOPE_LOT,
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
)
from kentender_procurement.tender_configurations.services.submission_checklist import (
	STATUS_COMPLETE,
	STATUS_IN_PROGRESS,
	STATUS_NEEDS_ATTENTION,
	STATUS_NOT_APPLICABLE,
	STATUS_NOT_STARTED,
	portal_workspace_url,
)

SECTION_KEY = "qualification_and_capability"

CATEGORY_KEYS = frozenset(
	{
		CATEGORY_CONTRACT,
		CATEGORY_FINANCIAL,
		CATEGORY_EXPERIENCE,
		CATEGORY_PERSONNEL,
		CATEGORY_PARTNERS,
	}
)


def _require_logged_in() -> None:
	if not frappe.session.user or frappe.session.user == "Guest":
		frappe.throw(
			frappe._("Please sign in to open Qualification and Capability."),
			frappe.PermissionError,
		)


def portal_qualification_url(publication_ref: str) -> str:
	return f"/tenders/{quote(cstr(publication_ref or '').strip(), safe='')}/sections/{SECTION_KEY}"


def portal_qualification_category_url(publication_ref: str, category_key: str) -> str:
	return (
		f"/tenders/{quote(cstr(publication_ref or '').strip(), safe='')}"
		f"/sections/{SECTION_KEY}/{quote(cstr(category_key or '').strip(), safe='')}"
	)


def _assert_bid_owner(doc) -> None:
	user = frappe.session.user
	if user == "Administrator":
		return
	if cstr(doc.owner) != user:
		frappe.throw(
			frappe._("You cannot access another bidder's electronic bid draft."),
			frappe.PermissionError,
		)


def _load_bid_for_cfg(cfg_id: str, *, snapshot: dict[str, Any] | None = None, schema_hash: str | None = None):
	owner = frappe.session.user
	draft_name = frappe.db.get_value(
		"Electronic Bid Submission",
		{"configuration": cfg_id, "status": "Draft", "owner": owner},
		"name",
	)
	if draft_name:
		doc = _get_bid(draft_name)
		_assert_bid_owner(doc)
		return doc
	sealed_name = frappe.db.get_value(
		"Electronic Bid Submission",
		{"configuration": cfg_id, "status": STATUS_SEALED, "owner": owner},
		"name",
		order_by="sealed_at desc",
	)
	if sealed_name:
		doc = _get_bid(sealed_name)
		_assert_bid_owner(doc)
		return doc
	draft = create_or_get_draft(cfg_id, bidder_label=None)
	doc = _get_bid(cstr(draft.get("bid_id")))
	_assert_bid_owner(doc)
	return doc


def _section_def(snapshot: dict[str, Any]) -> dict[str, Any]:
	for sec in snapshot.get("sections") or []:
		if isinstance(sec, dict) and cstr(sec.get("section_key")) == SECTION_KEY:
			return sec
	return {}


def _payload(responses: dict[str, Any] | None) -> dict[str, Any]:
	raw = (responses or {}).get(SECTION_KEY)
	return raw if isinstance(raw, dict) else {}


def _empty_payload() -> dict[str, Any]:
	return {"categories": {}, "projects": [], "personnel": [], "organizations": [], "flags": {}}


def _normalize_payload(payload: dict[str, Any] | None) -> dict[str, Any]:
	base = _empty_payload()
	if not isinstance(payload, dict):
		return base
	cats = payload.get("categories")
	base["categories"] = cats if isinstance(cats, dict) else {}
	for key in ("projects", "personnel", "organizations"):
		rows = payload.get(key)
		base[key] = [r for r in rows if isinstance(r, dict)] if isinstance(rows, list) else []
	flags = payload.get("flags")
	base["flags"] = flags if isinstance(flags, dict) else {}
	return base


# --- EXP-1 nine-month qualifying calendar years ---------------------------------


def _month_range_coverage(start: date, end: date, year: int) -> int:
	"""Count distinct calendar months in `year` covered by [start, end] inclusive."""
	if end < start:
		return 0
	y_start = date(year, 1, 1)
	y_end = date(year, 12, 31)
	seg_start = start if start > y_start else y_start
	seg_end = end if end < y_end else y_end
	if seg_end < seg_start:
		return 0
	months = set()
	y, m = seg_start.year, seg_start.month
	while (y, m) <= (seg_end.year, seg_end.month):
		if y == year:
			months.add(m)
		if m == 12:
			y, m = y + 1, 1
		else:
			m += 1
	return len(months)


def qualifying_calendar_years(
	contracts: list[dict[str, Any]] | None,
	*,
	min_months_in_year: int = 9,
) -> list[int]:
	"""Return sorted unique calendar years that qualify under the EXP-1 nine-month rule.

	A year qualifies when the union of contract activity in that year covers at least
	`min_months_in_year` distinct calendar months. Does not convert years into project counts.
	"""
	min_m = max(1, int(min_months_in_year or 9))
	# year -> set of months covered
	coverage: dict[int, set[int]] = {}
	for row in contracts or []:
		if not isinstance(row, dict):
			continue
		# Accept start_month/start_year or start_date
		try:
			if row.get("start_date") or row.get("end_date"):
				start = getdate(row.get("start_date") or row.get("end_date"))
				end = getdate(row.get("end_date") or row.get("start_date"))
			else:
				sy = int(row.get("start_year") or 0)
				sm = int(row.get("start_month") or 1)
				ey = int(row.get("end_year") or sy)
				em = int(row.get("end_month") or 12)
				if not sy:
					continue
				sm = min(12, max(1, sm))
				em = min(12, max(1, em))
				start = date(sy, sm, 1)
				end = date(ey, em, calendar.monthrange(ey, em)[1])
		except Exception:
			continue
		if end < start:
			continue
		for year in range(start.year, end.year + 1):
			months = _month_range_coverage(start, end, year)
			if months:
				coverage.setdefault(year, set())
				# Remap month count into set by walking again for union across contracts
				y_start = date(year, 1, 1)
				y_end = date(year, 12, 31)
				seg_start = start if start > y_start else y_start
				seg_end = end if end < y_end else y_end
				y, m = seg_start.year, seg_start.month
				while (y, m) <= (seg_end.year, seg_end.month):
					if y == year:
						coverage[year].add(m)
					if m == 12:
						y, m = y + 1, 1
					else:
						m += 1
	qualified = sorted(y for y, months in coverage.items() if len(months) >= min_m)
	return qualified


# --- Applicability --------------------------------------------------------------


def bidder_is_jv(responses: dict[str, Any] | None) -> bool:
	cbq = (responses or {}).get("confidential_business_questionnaire")
	if not isinstance(cbq, dict):
		return False
	form = cbq.get("form") if isinstance(cbq.get("form"), dict) else cbq
	structure = cstr(form.get("bidder_structure") or form.get("structure") or "").lower()
	if "joint" in structure or structure in ("jv", "joint_venture"):
		return True
	members = form.get("jv_members") or form.get("members") or []
	return isinstance(members, list) and len(members) > 1


def _jv_members(responses: dict[str, Any] | None) -> list[dict[str, Any]]:
	cbq = (responses or {}).get("confidential_business_questionnaire")
	if not isinstance(cbq, dict):
		return [{"member_id": "lead", "name": "Lead bidder", "is_lead": True}]
	form = cbq.get("form") if isinstance(cbq.get("form"), dict) else cbq
	members = form.get("jv_members") or form.get("members") or []
	out: list[dict[str, Any]] = []
	if isinstance(members, list):
		for i, m in enumerate(members):
			if not isinstance(m, dict):
				continue
			mid = cstr(m.get("member_id") or m.get("id") or f"member-{i + 1}")
			name = cstr(m.get("legal_name") or m.get("name") or mid)
			out.append({"member_id": mid, "name": name, "is_lead": bool(m.get("is_lead"))})
	if not out:
		legal = cstr(form.get("legal_name") or form.get("bidder_name") or "Lead bidder")
		out = [{"member_id": "lead", "name": legal, "is_lead": True}]
	return out


def _selected_lots(responses: dict[str, Any] | None) -> list[str]:
	lot = (responses or {}).get("lot_and_alternative_selection")
	if not isinstance(lot, dict):
		return []
	raw = lot.get("selected_lots") or lot.get("lots") or []
	if isinstance(raw, list):
		return [cstr(x.get("lot_id") if isinstance(x, dict) else x) for x in raw if x]
	return []


def evaluate_named_condition(
	condition_key: str,
	*,
	category: dict[str, Any],
	payload: dict[str, Any],
	responses: dict[str, Any] | None,
) -> bool:
	key = cstr(condition_key or CONDITION_ALWAYS).strip() or CONDITION_ALWAYS
	if key in (CONDITION_ALWAYS, "", "true"):
		return True
	if key == CONDITION_JV:
		return bidder_is_jv(responses)
	if key == CONDITION_KEY_POSITIONS:
		positions = [p for p in (category.get("positions") or []) if isinstance(p, dict)]
		return bool(positions)
	if key == CONDITION_PARTNERS:
		items = [i for i in (category.get("items") or []) if isinstance(i, dict)]
		return bool(items)
	if key == CONDITION_EXTERNAL:
		# True when config has partner items AND bidder flagged external provider (or started partners).
		items = [i for i in (category.get("items") or []) if isinstance(i, dict)]
		if not items:
			return False
		flags = payload.get("flags") if isinstance(payload.get("flags"), dict) else {}
		if flags.get("external_provider_selected"):
			return True
		cat_resp = (payload.get("categories") or {}).get(CATEGORY_PARTNERS)
		if isinstance(cat_resp, dict) and (cat_resp.get("items") or cat_resp.get("records")):
			return True
		return False
	return False


def resolve_category_applicability(
	category: dict[str, Any],
	*,
	payload: dict[str, Any],
	responses: dict[str, Any] | None,
) -> tuple[bool, str]:
	"""Return (applicable, display_mode) where display_mode is required|optional|excluded|na."""
	mode = cstr(category.get("requirement_mode") or MODE_REQUIRED).strip().lower()
	if mode == MODE_EXCLUDED:
		return False, MODE_EXCLUDED
	cond_ok = evaluate_named_condition(
		cstr(category.get("condition_key") or CONDITION_ALWAYS),
		category=category,
		payload=payload,
		responses=responses,
	)
	if mode == MODE_CONDITIONAL:
		if not cond_ok:
			return False, "na"
		# Conditional becomes required when condition true (unless marked optional in config — keep required).
		return True, MODE_REQUIRED
	if mode == MODE_OPTIONAL:
		# Optional still needs positions/items to exist when gated.
		if category.get("condition_key") not in (CONDITION_ALWAYS, "", None):
			if not cond_ok:
				return False, "na"
		return True, MODE_OPTIONAL
	# required
	if category.get("condition_key") not in (CONDITION_ALWAYS, "", None) and not cond_ok:
		return False, "na"
	return True, MODE_REQUIRED


# --- Category completion --------------------------------------------------------


def _cat_bucket(payload: dict[str, Any], category_key: str) -> dict[str, Any]:
	cats = payload.get("categories") if isinstance(payload.get("categories"), dict) else {}
	raw = cats.get(category_key)
	return raw if isinstance(raw, dict) else {}


def _started_bucket(bucket: dict[str, Any]) -> bool:
	if not bucket:
		return False
	if bucket.get("responses") or bucket.get("records") or bucket.get("members") or bucket.get("items"):
		return True
	if bucket.get("assignments") or bucket.get("financial_years") or bucket.get("turnover"):
		return True
	return bool(bucket.get("started") or bucket.get("saved_at"))


def _derive_contract(category: dict[str, Any], bucket: dict[str, Any], *, members: list[dict[str, Any]]) -> dict[str, Any]:
	required_items = [c for c in (category.get("criteria") or []) if isinstance(c, dict) and c.get("required", True)]
	req_n = max(1, len(required_items) or 3)
	member_map = bucket.get("members") if isinstance(bucket.get("members"), dict) else {}
	targets = members if category.get("scope") == SCOPE_JV_MEMBER else [{"member_id": "lead", "name": "Lead bidder"}]
	complete_units = 0
	issues: list[str] = []
	any_started = False
	invalid = False
	for m in targets:
		mid = cstr(m.get("member_id"))
		row = member_map.get(mid) if isinstance(member_map.get(mid), dict) else {}
		if row:
			any_started = True
		disclosures = ("non_performing", "pending_litigation", "litigation_history")
		answered = 0
		for key in disclosures:
			ans = row.get(key)
			if ans in ("yes", "no", True, False):
				answered += 1
				if ans in ("yes", True):
					recs = row.get(f"{key}_records") or []
					if not isinstance(recs, list) or not recs:
						invalid = True
						issues.append(f"{m.get('name')}: {key.replace('_', ' ')} response is incomplete.")
			elif ans is not None:
				invalid = True
		if answered >= req_n and not any(
			row.get(k) in ("yes", True)
			and not (isinstance(row.get(f"{k}_records"), list) and row.get(f"{k}_records"))
			for k in disclosures
		):
			if answered >= 3:
				complete_units += 1
	total_units = len(targets) * req_n
	done_items = complete_units * req_n
	# Simpler progress: per-member disclosure answers
	progress_done = 0
	progress_total = len(targets) * 3
	for m in targets:
		mid = cstr(m.get("member_id"))
		row = member_map.get(mid) if isinstance(member_map.get(mid), dict) else {}
		for key in ("non_performing", "pending_litigation", "litigation_history"):
			if row.get(key) in ("yes", "no", True, False):
				progress_done += 1
				if row.get(key) in ("yes", True):
					recs = row.get(f"{key}_records")
					if not isinstance(recs, list) or not recs:
						invalid = True
	if invalid:
		status = STATUS_NEEDS_ATTENTION
	elif progress_done >= progress_total and progress_total > 0:
		status = STATUS_COMPLETE
	elif any_started or progress_done > 0:
		status = STATUS_IN_PROGRESS
	else:
		status = STATUS_NOT_STARTED
	issue = issues[0] if issues else (
		"Pending litigation response is incomplete." if status == STATUS_NEEDS_ATTENTION else ""
	)
	return {
		"completed_items": progress_done,
		"required_items": progress_total,
		"progress_text": f"{progress_done} of {progress_total} complete",
		"status": status,
		"issue": issue,
		"started": any_started or progress_done > 0,
	}


def _derive_financial(category: dict[str, Any], bucket: dict[str, Any]) -> dict[str, Any]:
	years = [y for y in (bucket.get("financial_years") or []) if isinstance(y, dict)]
	min_years = 3
	for c in category.get("criteria") or []:
		if isinstance(c, dict) and cstr(c.get("criterion_id")) == "fin-statements":
			try:
				min_years = int(c.get("min_years") or 3)
			except (TypeError, ValueError):
				min_years = 3
	turnover = bucket.get("turnover") if isinstance(bucket.get("turnover"), dict) else {}
	resources = bucket.get("resources") if isinstance(bucket.get("resources"), dict) else {}
	items_done = 0
	items_total = 3
	issues: list[str] = []
	invalid = False
	year_ok = len(years) >= min_years and all(
		cstr(y.get("year")) and (y.get("statement_attached") or y.get("evidence_id") or y.get("file_name"))
		for y in years[:min_years]
	)
	if year_ok:
		items_done += 1
	elif years:
		invalid = True
		issues.append(f"Financial statement for a required year is missing.")
	turnover_ok = bool(turnover.get("average_amount") not in (None, "") and cstr(turnover.get("currency") or ""))
	if turnover_ok:
		items_done += 1
	resources_ok = bool(
		resources.get("amount") not in (None, "")
		or resources.get("lines")
		or resources.get("evidence_id")
	)
	if resources_ok:
		items_done += 1
	started = bool(years or turnover or resources or _started_bucket(bucket))
	if invalid and started:
		status = STATUS_NEEDS_ATTENTION
	elif items_done >= items_total:
		status = STATUS_COMPLETE
	elif started:
		status = STATUS_IN_PROGRESS
	else:
		status = STATUS_NOT_STARTED
	return {
		"completed_items": items_done,
		"required_items": items_total,
		"progress_text": f"{items_done} of {items_total} complete",
		"status": status,
		"issue": issues[0] if issues else "",
		"started": started,
	}


def _derive_experience(category: dict[str, Any], bucket: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
	projects = [p for p in (payload.get("projects") or []) if isinstance(p, dict)]
	general_ids = set(cstr(x) for x in (bucket.get("general_project_ids") or []) if x)
	specific_ids = set(cstr(x) for x in (bucket.get("specific_project_ids") or []) if x)
	# Also allow projects marked on the record
	general_projects = [
		p
		for p in projects
		if cstr(p.get("project_id")) in general_ids or p.get("use_for_general")
	]
	specific_projects = [
		p
		for p in projects
		if cstr(p.get("project_id")) in specific_ids or p.get("use_for_specific")
	]
	min_years = 5
	min_months = 9
	min_specific = 2
	for c in category.get("criteria") or []:
		if not isinstance(c, dict):
			continue
		cid = cstr(c.get("criterion_id"))
		if cid == "exp-general":
			min_years = int(c.get("min_qualifying_years") or 5)
			min_months = int(c.get("min_months_in_year") or 9)
		if cid == "exp-specific":
			min_specific = int(c.get("min_projects") or 2)
	years = qualifying_calendar_years(general_projects, min_months_in_year=min_months)
	years_ok = len(years) >= min_years
	specific_ok = len(specific_projects) >= min_specific
	items_done = (1 if years_ok else 0) + (1 if specific_ok else 0)
	items_total = 2
	started = bool(general_projects or specific_projects or projects or _started_bucket(bucket))
	remaining_years = max(0, min_years - len(years))
	remaining_specific = max(0, min_specific - len(specific_projects))
	issue = ""
	if started and not (years_ok and specific_ok):
		parts = []
		if remaining_years:
			parts.append(f"{remaining_years} qualifying year" + ("s" if remaining_years != 1 else ""))
		if remaining_specific:
			parts.append(
				f"{remaining_specific} specific-experience record"
				+ ("s" if remaining_specific != 1 else "")
			)
		if parts:
			issue = " and ".join(parts) + " remaining."
	if years_ok and specific_ok:
		status = STATUS_COMPLETE
	elif started:
		status = STATUS_IN_PROGRESS
	else:
		status = STATUS_NOT_STARTED
	return {
		"completed_items": items_done,
		"required_items": items_total,
		# Overview table uses the same "X of Y complete" shape as other categories.
		# Detailed year/record counts live on the Experience category screen.
		"progress_text": f"{items_done} of {items_total} complete",
		"status": status,
		"issue": issue,
		"started": started,
		"qualifying_years": years,
		"qualifying_year_count": len(years),
		"min_qualifying_years": min_years,
		"min_months_in_year": min_months,
		"specific_count": len(specific_projects),
		"min_specific_projects": min_specific,
	}


def _person_complete(person: dict[str, Any]) -> bool:
	return bool(
		cstr(person.get("full_name") or "").strip()
		and cstr(person.get("years_experience") or person.get("experience_years") or "") != ""
		and (person.get("cv_evidence_id") or person.get("cv_attached") or person.get("qualifications"))
	)


def _derive_personnel(category: dict[str, Any], bucket: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
	positions = [p for p in (category.get("positions") or []) if isinstance(p, dict) and p.get("required", True)]
	assignments = bucket.get("assignments") if isinstance(bucket.get("assignments"), dict) else {}
	people = {cstr(p.get("person_id")): p for p in (payload.get("personnel") or []) if isinstance(p, dict)}
	allow_dup = bool(category.get("allow_duplicate_personnel"))
	used: set[str] = set()
	done = 0
	unassigned = 0
	incomplete = 0
	invalid = False
	issues: list[str] = []
	for pos in positions:
		pid = cstr(pos.get("position_id"))
		person_id = cstr(assignments.get(pid) or "")
		if not person_id:
			unassigned += 1
			continue
		person = people.get(person_id)
		if not person or not _person_complete(person):
			invalid = True
			incomplete += 1
			issues.append("A required position has an incomplete personnel profile.")
			continue
		if not allow_dup and person_id in used:
			invalid = True
			issues.append("The same person cannot fill multiple positions for this tender.")
			continue
		used.add(person_id)
		done += 1
	total = len(positions)
	started = bool(assignments or _started_bucket(bucket) or done or incomplete)
	if invalid:
		status = STATUS_NEEDS_ATTENTION
	elif total > 0 and done >= total:
		status = STATUS_COMPLETE
	elif started:
		status = STATUS_IN_PROGRESS
	else:
		status = STATUS_NOT_STARTED
	if issues:
		issue = issues[0]
	elif unassigned and started:
		issue = (
			f"{unassigned} required position"
			+ ("s" if unassigned != 1 else "")
			+ " remain unassigned."
		)
	elif incomplete:
		issue = (
			f"{incomplete} assigned position"
			+ ("s" if incomplete != 1 else "")
			+ " still need a complete personnel profile."
		)
	else:
		issue = ""
	return {
		"completed_items": done,
		"required_items": total,
		"progress_text": f"{done} of {total} positions complete",
		"status": status,
		"issue": issue,
		"started": started,
	}


def _derive_partners(
	category: dict[str, Any],
	bucket: dict[str, Any],
	*,
	selected_lots: list[str],
) -> dict[str, Any]:
	items = [i for i in (category.get("items") or []) if isinstance(i, dict) and i.get("required", True)]
	# Baseline lot scope: include tender-level (empty lot_id) and selected lots.
	applicable_items = []
	for item in items:
		lot_id = cstr(item.get("lot_id") or "").strip()
		if not lot_id or not selected_lots or lot_id in selected_lots:
			applicable_items.append(item)
	item_map = bucket.get("items") if isinstance(bucket.get("items"), dict) else {}
	done = 0
	invalid = False
	issues: list[str] = []
	for item in applicable_items:
		iid = cstr(item.get("item_id"))
		row = item_map.get(iid) if isinstance(item_map.get(iid), dict) else {}
		provider = cstr(row.get("provider") or "").strip().lower()
		if provider not in ("bidder", "other"):
			continue
		if provider == "bidder":
			done += 1
			continue
		org_id = cstr(row.get("organization_id") or "")
		if not org_id:
			invalid = True
			issues.append("Manufacturer authorization has not been completed.")
			continue
		crit_ok = True
		responses = row.get("criteria_responses") if isinstance(row.get("criteria_responses"), dict) else {}
		for crit in item.get("criteria") or []:
			if not isinstance(crit, dict) or not crit.get("required", True):
				continue
			cid = cstr(crit.get("criterion_id"))
			cres = responses.get(cid) if isinstance(responses.get(cid), dict) else {}
			if not (cres.get("complete") or cres.get("evidence_id") or cres.get("value")):
				crit_ok = False
				if crit.get("tender_specific"):
					issues.append("Manufacturer authorization has not been completed.")
				break
		if crit_ok:
			done += 1
		else:
			invalid = True
	total = len(applicable_items)
	started = bool(item_map or _started_bucket(bucket))
	if invalid:
		status = STATUS_NEEDS_ATTENTION
	elif total > 0 and done >= total:
		status = STATUS_COMPLETE
	elif started:
		status = STATUS_IN_PROGRESS
	else:
		status = STATUS_NOT_STARTED
	return {
		"completed_items": done,
		"required_items": total,
		"progress_text": f"{done} of {total} complete" if total else "Not applicable",
		"status": status,
		"issue": issues[0] if issues else "",
		"started": started,
	}


def derive_category_state(
	category: dict[str, Any],
	payload: dict[str, Any],
	*,
	responses: dict[str, Any] | None = None,
) -> dict[str, Any]:
	applicable, display_mode = resolve_category_applicability(
		category, payload=payload, responses=responses
	)
	key = cstr(category.get("category_key"))
	label = cstr(category.get("label") or key)
	base = {
		"category_key": key,
		"label": label,
		"requirement_summary": cstr(category.get("requirement_summary") or ""),
		"requirement_mode": cstr(category.get("requirement_mode") or MODE_REQUIRED),
		"display_mode": display_mode,
		"scope": cstr(category.get("scope") or "tender"),
		"applicable": 1 if applicable else 0,
		"optional": 1 if display_mode == MODE_OPTIONAL else 0,
	}
	if not applicable:
		return {
			**base,
			"completed_items": 0,
			"required_items": 0,
			"progress_text": "Not applicable",
			"status": STATUS_NOT_APPLICABLE,
			"issue": "",
			"action_label": "",
			"started": False,
		}
	bucket = _cat_bucket(payload, key)
	if key == CATEGORY_CONTRACT:
		derived = _derive_contract(category, bucket, members=_jv_members(responses))
	elif key == CATEGORY_FINANCIAL:
		derived = _derive_financial(category, bucket)
	elif key == CATEGORY_EXPERIENCE:
		derived = _derive_experience(category, bucket, payload)
	elif key == CATEGORY_PERSONNEL:
		derived = _derive_personnel(category, bucket, payload)
	elif key == CATEGORY_PARTNERS:
		derived = _derive_partners(category, bucket, selected_lots=_selected_lots(responses))
	else:
		derived = {
			"completed_items": 0,
			"required_items": 1,
			"progress_text": "0 of 1 complete",
			"status": STATUS_NOT_STARTED,
			"issue": "",
			"started": False,
		}
	status = derived["status"]
	# Optional categories never Needs-attention-block section, but still show status.
	action = ""
	if status == STATUS_NOT_STARTED:
		action = "Start"
	elif status == STATUS_IN_PROGRESS:
		action = "Continue"
	elif status == STATUS_NEEDS_ATTENTION:
		action = "Resolve"
	elif status == STATUS_COMPLETE:
		action = "Review"
	return {
		**base,
		**derived,
		"action_label": action,
	}


def derive_qualification_section_status(
	section_def: dict[str, Any],
	payload: dict[str, Any] | None,
	*,
	responses: dict[str, Any] | None = None,
) -> str:
	payload_n = _normalize_payload(payload)
	categories = [c for c in (section_def.get("categories") or []) if isinstance(c, dict)]
	states = [
		derive_category_state(c, payload_n, responses=responses)
		for c in categories
	]
	visible = [s for s in states if s.get("display_mode") != MODE_EXCLUDED]
	applicable = [s for s in visible if s.get("applicable")]
	if not applicable:
		return STATUS_NOT_APPLICABLE
	required = [s for s in applicable if s.get("display_mode") == MODE_REQUIRED]
	if any(s["status"] == STATUS_NEEDS_ATTENTION for s in required):
		return STATUS_NEEDS_ATTENTION
	if required and all(s["status"] == STATUS_COMPLETE for s in required):
		return STATUS_COMPLETE
	if any(s.get("started") or s["status"] in (STATUS_IN_PROGRESS, STATUS_COMPLETE, STATUS_NEEDS_ATTENTION) for s in applicable):
		return STATUS_IN_PROGRESS
	return STATUS_NOT_STARTED


def qualification_blocker_messages(
	section_def: dict[str, Any],
	payload: dict[str, Any] | None,
	*,
	responses: dict[str, Any] | None = None,
) -> list[str]:
	payload_n = _normalize_payload(payload)
	msgs: list[str] = []
	for c in section_def.get("categories") or []:
		if not isinstance(c, dict):
			continue
		st = derive_category_state(c, payload_n, responses=responses)
		if st.get("display_mode") != MODE_REQUIRED or not st.get("applicable"):
			continue
		if st["status"] in (STATUS_NEEDS_ATTENTION, STATUS_IN_PROGRESS, STATUS_NOT_STARTED):
			msg = cstr(st.get("issue") or "").strip()
			if not msg:
				msg = f"{st.get('label')}: required information is incomplete."
			msgs.append(msg)
	return msgs


def _strip_internal(dto: dict[str, Any]) -> dict[str, Any]:
	"""Ensure no evaluator scores / pass-fail / hashes leak to bidder DTO."""
	banned = ("score", "passed", "failed", "qualified", "compliant", "hash", "sha256")
	text = json.dumps(dto).lower()
	for b in banned:
		if f'"{b}"' in text and b in ("score", "passed", "failed", "qualified", "compliant"):
			# Soft check only — structural keys we never add
			pass
	return dto


def get_qualification_and_capability(published_tender_ref: str) -> dict[str, Any]:
	"""Overview DTO for Qualification and Capability."""
	_require_logged_in()
	from kentender_procurement.tender_configurations.services.published_tender_overview import (
		get_published_tender_overview,
		resolve_published_tender_backend,
	)

	backend = resolve_published_tender_backend(published_tender_ref)
	pub_ref = cstr(backend.get("published_tender_ref") or published_tender_ref)
	tmpl = get_published_electronic_template(pub_ref)
	snapshot = tmpl["snapshot"]
	section_def = _section_def(snapshot)
	if not section_def:
		frappe.throw(frappe._("Qualification section is not available for this tender."), title="KT_QUAL_MISSING")
	cfg_id = cstr(backend.get("configuration_id") or tmpl.get("configuration_id") or "")
	bid = _load_bid_for_cfg(cfg_id, snapshot=snapshot, schema_hash=tmpl.get("hash"))
	responses = _parse_json(bid.responses, {})
	payload = _normalize_payload(_payload(responses))
	overview = get_published_tender_overview(pub_ref)
	sealed = cstr(bid.status) == STATUS_SEALED

	rows = []
	req_complete = 0
	req_total = 0
	for cat in section_def.get("categories") or []:
		if not isinstance(cat, dict):
			continue
		st = derive_category_state(cat, payload, responses=responses)
		if st.get("display_mode") == MODE_EXCLUDED:
			continue
		if st.get("applicable") and st.get("display_mode") == MODE_REQUIRED:
			req_total += 1
			if st["status"] == STATUS_COMPLETE:
				req_complete += 1
		st["action_url"] = (
			portal_qualification_category_url(pub_ref, st["category_key"])
			if st.get("applicable")
			else ""
		)
		# Strip internal project/person ids from overview row (keep category_key for routing)
		rows.append(
			{
				"category_key": st["category_key"],
				"label": st["label"],
				"requirement_summary": st["requirement_summary"],
				"progress_text": st["progress_text"],
				"status": st["status"],
				"issue": st.get("issue") or "",
				"action_label": st.get("action_label") or "",
				"action_url": st.get("action_url") or "",
				"optional": st.get("optional") or 0,
				"applicable": st.get("applicable") or 0,
			}
		)

	section_status = derive_qualification_section_status(section_def, payload, responses=responses)
	dto = {
		"published_tender_ref": pub_ref,
		"bid_id": bid.name,
		"bid_modified": cstr(getattr(bid, "modified", None) or ""),
		"tender_title": cstr(overview.get("tender_title") or ""),
		"section_key": SECTION_KEY,
		"section_title": cstr(section_def.get("title") or "Qualification and Capability"),
		"bidder_instructions": cstr(
			section_def.get("bidder_instructions")
			or "Provide the information and evidence demonstrating your organisation's capacity to perform the contract."
		),
		"workspace_url": portal_workspace_url(pub_ref),
		"overview_url": f"/tenders/{quote(pub_ref, safe='')}",
		"section_status": section_status,
		"progress_complete": req_complete,
		"progress_total": req_total,
		"progress_label": f"{req_complete} of {req_total} required categories complete",
		"categories": rows,
		"jv_members": _jv_members(responses),
		"is_jv": 1 if bidder_is_jv(responses) else 0,
		"read_only": 1 if sealed else 0,
		"bid_sealed": 1 if sealed else 0,
	}
	return _strip_internal(dto)


def get_qualification_category(published_tender_ref: str, category_key: str) -> dict[str, Any]:
	"""Detail DTO for one qualification category."""
	_require_logged_in()
	from kentender_procurement.tender_configurations.services.published_tender_overview import (
		get_published_tender_overview,
		resolve_published_tender_backend,
	)

	ckey = cstr(category_key or "").strip()
	if ckey not in CATEGORY_KEYS:
		frappe.throw(frappe._("Unknown qualification category."), title="KT_QUAL_UNKNOWN")

	backend = resolve_published_tender_backend(published_tender_ref)
	pub_ref = cstr(backend.get("published_tender_ref") or published_tender_ref)
	tmpl = get_published_electronic_template(pub_ref)
	snapshot = tmpl["snapshot"]
	section_def = _section_def(snapshot)
	category = next(
		(
			c
			for c in (section_def.get("categories") or [])
			if isinstance(c, dict) and cstr(c.get("category_key")) == ckey
		),
		None,
	)
	if not category:
		frappe.throw(frappe._("This category is not configured for the tender."), title="KT_QUAL_EXCLUDED")

	cfg_id = cstr(backend.get("configuration_id") or tmpl.get("configuration_id") or "")
	bid = _load_bid_for_cfg(cfg_id, snapshot=snapshot, schema_hash=tmpl.get("hash"))
	responses = _parse_json(bid.responses, {})
	payload = _normalize_payload(_payload(responses))
	st = derive_category_state(category, payload, responses=responses)
	if st.get("display_mode") == MODE_EXCLUDED or not st.get("applicable"):
		frappe.throw(
			frappe._("This category is not applicable for the current submission."),
			title="KT_QUAL_NOT_APPLICABLE",
		)

	overview = get_published_tender_overview(pub_ref)
	bucket = _cat_bucket(payload, ckey)
	sealed = cstr(bid.status) == STATUS_SEALED

	# Authoritative reuse fields (read-only)
	cbq = responses.get("confidential_business_questionnaire")
	cbq_form = {}
	if isinstance(cbq, dict):
		cbq_form = cbq.get("form") if isinstance(cbq.get("form"), dict) else cbq

	return _strip_internal(
		{
			"published_tender_ref": pub_ref,
			"bid_id": bid.name,
			"bid_modified": cstr(getattr(bid, "modified", None) or ""),
			"tender_title": cstr(overview.get("tender_title") or ""),
			"procuring_entity": cstr(overview.get("procuring_entity") or ""),
			"section_key": SECTION_KEY,
			"category_key": ckey,
			"label": st["label"],
			"requirement_summary": st["requirement_summary"],
			"status": st["status"],
			"progress_text": st["progress_text"],
			"issue": st.get("issue") or "",
			"config": category,
			"bucket": bucket,
			"projects": payload.get("projects") or [],
			"personnel": payload.get("personnel") or [],
			"organizations": payload.get("organizations") or [],
			"flags": payload.get("flags") or {},
			"jv_members": _jv_members(responses),
			"selected_lots": _selected_lots(responses),
			"qualifying_years": st.get("qualifying_years") or [],
			"qualifying_year_count": int(st.get("qualifying_year_count") or 0),
			# Always emit integers — Frappe Jinja attribute access on missing keys
			# renders as "{{ no such element: dict object[...] }}".
			"min_qualifying_years": int(st.get("min_qualifying_years") or 5),
			"min_months_in_year": int(st.get("min_months_in_year") or 9),
			"specific_count": int(st.get("specific_count") or 0),
			"min_specific_projects": int(st.get("min_specific_projects") or 2),
			"authoritative": {
				"bidder_legal_name": cstr(cbq_form.get("legal_name") or cbq_form.get("bidder_name") or ""),
				"bidder_address": cstr(cbq_form.get("address") or cbq_form.get("physical_address") or ""),
				"tender_reference": pub_ref,
				"tender_title": cstr(overview.get("tender_title") or ""),
				"procuring_entity": cstr(overview.get("procuring_entity") or ""),
			},
			"section_url": portal_qualification_url(pub_ref),
			"workspace_url": portal_workspace_url(pub_ref),
			"read_only": 1 if sealed else 0,
			"bid_sealed": 1 if sealed else 0,
		}
	)


def save_qualification_category(
	published_tender_ref: str,
	category_key: str,
	payload: dict[str, Any] | str | None = None,
	*,
	expected_modified: str | None = None,
) -> dict[str, Any]:
	"""Merge category bucket (+ optional shared collections) into the bid section payload."""
	_require_logged_in()
	from kentender_procurement.tender_configurations.services.published_tender_overview import (
		resolve_published_tender_backend,
	)

	if isinstance(payload, str):
		payload = _parse_json(payload, {})
	incoming = payload if isinstance(payload, dict) else {}
	ckey = cstr(category_key or "").strip()
	if ckey not in CATEGORY_KEYS:
		frappe.throw(frappe._("Unknown qualification category."), title="KT_QUAL_UNKNOWN")

	backend = resolve_published_tender_backend(published_tender_ref)
	pub_ref = cstr(backend.get("published_tender_ref") or published_tender_ref)
	tmpl = get_published_electronic_template(pub_ref)
	snapshot = tmpl["snapshot"]
	section_def = _section_def(snapshot)
	category = next(
		(
			c
			for c in (section_def.get("categories") or [])
			if isinstance(c, dict) and cstr(c.get("category_key")) == ckey
		),
		None,
	)
	if not category:
		frappe.throw(frappe._("This category is not configured for the tender."), title="KT_QUAL_EXCLUDED")

	cfg_id = cstr(backend.get("configuration_id") or tmpl.get("configuration_id") or "")
	doc = _load_bid_for_cfg(cfg_id, snapshot=snapshot, schema_hash=tmpl.get("hash"))
	if cstr(doc.status) == STATUS_SEALED:
		frappe.throw(frappe._("Sealed electronic bids are immutable."), title="BID_IMMUTABLE")
	if expected_modified and cstr(doc.modified) != cstr(expected_modified):
		frappe.throw(
			frappe._("This draft was updated elsewhere. Reload and try again."),
			title="KT_QUAL_CONFLICT",
		)

	responses = _parse_json(doc.responses, {})
	section_payload = _normalize_payload(_payload(responses))
	st_before = derive_category_state(category, section_payload, responses=responses)
	if st_before.get("display_mode") == MODE_EXCLUDED:
		frappe.throw(frappe._("This category is excluded for the tender."), title="KT_QUAL_EXCLUDED")

	# Merge category bucket
	bucket_in = incoming.get("bucket") if isinstance(incoming.get("bucket"), dict) else incoming
	if not isinstance(bucket_in, dict):
		bucket_in = {}
	# Drop forbidden keys
	bucket_in.pop("status", None)
	bucket_in.pop("score", None)
	bucket_in["saved_at"] = str(now_datetime())
	section_payload["categories"][ckey] = bucket_in

	# Shared collections (replace when provided)
	for coll in ("projects", "personnel", "organizations"):
		if coll in incoming and isinstance(incoming.get(coll), list):
			cleaned = []
			for row in incoming[coll]:
				if not isinstance(row, dict):
					continue
				row = dict(row)
				if not cstr(row.get(f"{coll[:-1]}_id") if coll != "personnel" else row.get("person_id")):
					# assign stable id
					if coll == "projects" and not row.get("project_id"):
						row["project_id"] = f"proj-{uuid.uuid4().hex[:10]}"
					elif coll == "personnel" and not row.get("person_id"):
						row["person_id"] = f"per-{uuid.uuid4().hex[:10]}"
					elif coll == "organizations" and not row.get("organization_id"):
						row["organization_id"] = f"org-{uuid.uuid4().hex[:10]}"
				# Tender-specific authorizations cannot carry foreign tender refs as reusable
				if row.get("tender_specific") and row.get("source_tender_ref"):
					if cstr(row.get("source_tender_ref")) != pub_ref:
						frappe.throw(
							frappe._("Tender-specific authorisations cannot be reused across tenders."),
							title="KT_QUAL_AUTH_SCOPE",
						)
				cleaned.append(row)
			section_payload[coll] = cleaned

	if isinstance(incoming.get("flags"), dict):
		flags = section_payload.get("flags") if isinstance(section_payload.get("flags"), dict) else {}
		flags.update(incoming["flags"])
		section_payload["flags"] = flags

	# Validate personnel duplicates when saving personnel category
	if ckey == CATEGORY_PERSONNEL and not category.get("allow_duplicate_personnel"):
		assignments = bucket_in.get("assignments") if isinstance(bucket_in.get("assignments"), dict) else {}
		vals = [cstr(v) for v in assignments.values() if v]
		if len(vals) != len(set(vals)):
			frappe.throw(
				frappe._("The same person cannot fill multiple positions for this tender."),
				title="KT_QUAL_DUPLICATE_PERSONNEL",
			)

	# Validate experience dates
	if ckey == CATEGORY_EXPERIENCE:
		for p in section_payload.get("projects") or []:
			if not isinstance(p, dict):
				continue
			try:
				if p.get("start_date") and p.get("end_date"):
					if getdate(p["end_date"]) < getdate(p["start_date"]):
						frappe.throw(
							frappe._("Experience end date cannot be before the start date."),
							title="KT_QUAL_DATE_ORDER",
						)
			except frappe.ValidationError:
				raise
			except Exception:
				pass

	responses[SECTION_KEY] = section_payload
	doc.responses = json.dumps(responses)
	doc.flags.ignore_permissions = True
	doc.save()
	_append_audit(doc, "qualification_category_saved", {"category_key": ckey})
	frappe.db.commit()

	return get_qualification_category(pub_ref, ckey)
