# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.desk.search import validate_and_sanitize_search_inputs


def _like_txt(txt: str) -> str:
	return f"%{(txt or '').strip()}%"


def _run_profile_search(doctype: str, txt: str, start: int, page_len: int):
	like_txt = _like_txt(txt)
	return frappe.db.sql(
		f"""
		select
			name,
			coalesce(profile_name, name) as label,
			coalesce(profile_code, '')
		from `tab{doctype}`
		where (
			name like %(txt)s
			or coalesce(profile_name, '') like %(txt)s
			or coalesce(profile_code, '') like %(txt)s
		  )
		order by
			case when coalesce(profile_name, '') like %(txt)s then 0 else 1 end,
			modified desc
		limit %(start)s, %(page_len)s
		""",
		{"txt": like_txt, "start": start, "page_len": page_len},
	)


@frappe.whitelist()
@validate_and_sanitize_search_inputs
def search_procurement_plan(doctype, txt, searchfield, start, page_len, filters):
	like_txt = _like_txt(txt)
	return frappe.db.sql(
		"""
		select
			name,
			coalesce(plan_name, name) as label,
			trim(
				concat(
					coalesce(plan_code, ''),
					case when fiscal_year is not null then concat(' · FY', fiscal_year) else '' end
				)
			) as description
		from `tabProcurement Plan`
		where ifnull(is_active, 1) = 1
		  and (
			name like %(txt)s
			or coalesce(plan_name, '') like %(txt)s
			or coalesce(plan_code, '') like %(txt)s
		  )
		order by
			case when coalesce(plan_name, '') like %(txt)s then 0 else 1 end,
			modified desc
		limit %(start)s, %(page_len)s
		""",
		{"txt": like_txt, "start": start, "page_len": page_len},
	)


@frappe.whitelist()
@validate_and_sanitize_search_inputs
def search_procurement_template(doctype, txt, searchfield, start, page_len, filters):
	like_txt = _like_txt(txt)
	return frappe.db.sql(
		"""
		select
			name,
			coalesce(template_name, name) as label,
			coalesce(template_code, '')
		from `tabProcurement Template`
		where ifnull(is_active, 1) = 1
		  and (
			name like %(txt)s
			or coalesce(template_name, '') like %(txt)s
			or coalesce(template_code, '') like %(txt)s
		  )
		order by
			case when coalesce(template_name, '') like %(txt)s then 0 else 1 end,
			modified desc
		limit %(start)s, %(page_len)s
		""",
		{"txt": like_txt, "start": start, "page_len": page_len},
	)


@frappe.whitelist()
@validate_and_sanitize_search_inputs
def search_risk_profile(doctype, txt, searchfield, start, page_len, filters):
	return _run_profile_search("Risk Profile", txt, start, page_len)


@frappe.whitelist()
@validate_and_sanitize_search_inputs
def search_kpi_profile(doctype, txt, searchfield, start, page_len, filters):
	return _run_profile_search("KPI Profile", txt, start, page_len)


@frappe.whitelist()
@validate_and_sanitize_search_inputs
def search_decision_criteria_profile(doctype, txt, searchfield, start, page_len, filters):
	return _run_profile_search("Decision Criteria Profile", txt, start, page_len)


@frappe.whitelist()
@validate_and_sanitize_search_inputs
def search_vendor_management_profile(doctype, txt, searchfield, start, page_len, filters):
	return _run_profile_search("Vendor Management Profile", txt, start, page_len)
