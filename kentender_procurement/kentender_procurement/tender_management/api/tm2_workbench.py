# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Desk **TM2 workbench** whitelisted APIs (P9-03+).

Doc 9 §19.1 ``GET /api/tm2/tenders?queue=…&search=…&filters=…`` is implemented for desk
and integrations as :func:`list_workbench_tenders` (``frappe.call`` / REST resource
handler pattern used elsewhere in tender_management).

Doc 9 §19.2 ``GET /api/tm2/tenders/{tender_code}`` is implemented as
:func:`get_workbench_tender_detail_section_19_2` (same transport pattern).

Doc 9 §19.3 ``POST /api/tm2/action-availability`` (single action + optional ``context``)
is implemented as :func:`post_tm2_action_availability`; batch evaluation for one tender
is :func:`batch_workbench_tender_action_availability` (``frappe.call`` / REST whitelist
pattern; §7.3-shaped ``availability`` per action).
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr

from kentender_procurement.tender_management.services.tm2_workbench_wizard import (
	list_new_tender_wizard_std_options as list_new_tender_wizard_std_options_service,
	submit_new_tender_wizard_completion,
)
from kentender_procurement.tender_management.services.tm2_workbench_kpis import (
	get_workbench_kpi_counts as get_workbench_kpi_counts_service,
)
from kentender_procurement.tender_management.services.tm2_workbench_tender_list import (
	list_workbench_tenders as list_workbench_tenders_service,
)
from kentender_procurement.tender_management.services.tm2_workbench_package_picker import (
	list_packages_for_new_tender as list_packages_for_new_tender_service,
)
from kentender_procurement.tender_management.services.tm2_workbench_actor_context import (
	tm2_workbench_desk_security_context,
)
from kentender_procurement.tender_management.services.tm2_workbench_tender_detail import (
	batch_workbench_tender_action_availability as batch_workbench_tender_action_availability_service,
	get_workbench_tender_action_availability as get_workbench_tender_action_availability_service,
	get_workbench_tender_detail as get_workbench_tender_detail_service,
	post_section_19_3_tm2_action_availability as post_section_19_3_tm2_action_availability_service,
)
from kentender_procurement.tender_management.services.tm2_workbench_section_19_2 import (
	get_section_19_2_tender_detail as get_section_19_2_tender_detail_service,
)
from kentender_procurement.tender_management.services.export_tender_evidence import export_tender_evidence
from kentender_procurement.tender_management.services.publish_tender import publish_tender


@frappe.whitelist()
def get_workbench_kpi_counts() -> dict[str, Any]:
	"""P9-04 / P9-05 — KPI strip + queue bar counts (doc 9 §14.6–14.7)."""
	return get_workbench_kpi_counts_service(frappe.session.user)


@frappe.whitelist()
def get_workbench_tender_detail_section_19_2(tender_code: str | None = None) -> dict[str, Any]:
	"""P9-24 — doc 9 §19.2 tender detail contract (summary + readiness + handoff rollups).

	Exposes the nine required areas (tender summary, timeline, STD binding, output refs,
	publication snapshot, blockers, tab counts, action availability, recent audit events)
	plus ``readiness_summary`` and ``handoff_summaries`` for integration clients.
	"""
	return get_section_19_2_tender_detail_service(frappe.session.user, cstr(tender_code or "").strip())


@frappe.whitelist()
def get_workbench_tender_detail(tender_code: str | None = None) -> dict[str, Any]:
	"""P9-08+ — detail header, state cards, action bar, overview through audit & evidence tab (§16–17.12)."""
	return get_workbench_tender_detail_service(frappe.session.user, cstr(tender_code or "").strip())


@frappe.whitelist()
def get_workbench_tender_action_availability(
	tender_code: str | None = None,
	action_code: str | None = None,
) -> dict[str, Any]:
	"""P9-08 — refresh one action before execute (doc 9 §16.3)."""
	return get_workbench_tender_action_availability_service(
		frappe.session.user,
		cstr(tender_code or "").strip(),
		cstr(action_code or "").strip(),
	)


def _parse_tm2_extra_context(raw: Any) -> dict[str, Any]:
	"""Parse doc 9 §19.3 ``context`` from a dict or JSON string (empty → {})."""
	if raw is None:
		return {}
	if isinstance(raw, dict):
		return dict(raw)
	s = cstr(raw).strip()
	if not s:
		return {}
	try:
		p = frappe.parse_json(s)
		return dict(p) if isinstance(p, dict) else {}
	except Exception:
		return {}


def _parse_action_codes_arg(raw: Any) -> list[str]:
	"""Parse ``action_codes`` as JSON array string or list (from desk / integrations)."""
	if raw is None:
		return []
	if isinstance(raw, (list, tuple)):
		return [cstr(x or "").strip() for x in raw if cstr(x or "").strip()]
	s = cstr(raw).strip()
	if not s:
		return []
	try:
		p = frappe.parse_json(s)
		if isinstance(p, list):
			return [cstr(x or "").strip() for x in p if cstr(x or "").strip()]
	except Exception:
		return []
	return []


@frappe.whitelist()
def post_tm2_action_availability(
	payload: str | None = None,
	action_code: str | None = None,
	object_type: str | None = None,
	object_code: str | None = None,
	context: str | dict | None = None,
) -> dict[str, Any]:
	"""P9-25 — doc 9 §19.3 single action availability (§7.3 ``availability`` on success).

	Accepts a JSON ``payload`` object and/or discrete args. Discrete non-empty values
	override the same keys after parsing ``payload``. ``context`` may be a dict or
	JSON string; merged into the workbench availability context server-side.
	"""
	actor = frappe.session.user
	body: dict[str, Any] = {}
	if payload is not None and cstr(payload).strip():
		try:
			p = frappe.parse_json(cstr(payload).strip())
			if not isinstance(p, dict):
				return {"ok": False, "message": _("Payload must be a JSON object.")}
			body = dict(p)
		except Exception:
			return {"ok": False, "message": _("Invalid payload JSON.")}
	if action_code is not None and cstr(action_code).strip():
		body["action_code"] = cstr(action_code).strip()
	if object_type is not None and cstr(object_type).strip():
		body["object_type"] = cstr(object_type).strip()
	if object_code is not None and cstr(object_code).strip():
		body["object_code"] = cstr(object_code).strip()
	extra_raw = body.get("context")
	if extra_raw is None:
		extra_raw = context
	extra = _parse_tm2_extra_context(extra_raw)
	return post_section_19_3_tm2_action_availability_service(
		actor,
		cstr(body.get("action_code") or "").strip(),
		cstr(body.get("object_code") or "").strip(),
		object_type=body.get("object_type"),
		extra_context=extra or None,
	)


@frappe.whitelist()
def batch_workbench_tender_action_availability(
	tender_code: str | None = None,
	action_codes: str | list | None = None,
	context: str | dict | None = None,
) -> dict[str, Any]:
	"""P9-25 — doc 9 §19.3 batch: many ``action_codes`` for one tender; each item §7.3-shaped."""
	actor = frappe.session.user
	tc = cstr(tender_code or "").strip()
	codes = _parse_action_codes_arg(action_codes)
	extra = _parse_tm2_extra_context(context)
	return batch_workbench_tender_action_availability_service(
		actor,
		tc,
		codes,
		extra_context=extra or None,
	)


@frappe.whitelist()
def execute_workbench_tender_publish(tender_code: str | None = None, reason: str | None = None) -> dict[str, Any]:
	"""P9-08 — desk-whitelisted publish (doc 9 §16.4 / §9.6). ``reason`` reserved for audit extensions."""
	actor = frappe.session.user
	tc = cstr(tender_code or "").strip()
	if not tc:
		return {"ok": False, "message": _("Tender code is required.")}
	fresh = get_workbench_tender_action_availability_service(actor, tc, "TND2_PUBLISH")
	if not fresh.get("ok"):
		return fresh
	avail = fresh.get("availability") or {}
	if not avail.get("allowed"):
		return {
			"ok": False,
			"message": str(avail.get("user_message") or avail.get("message") or _("Publish is not allowed.")),
			"availability": avail,
		}
	ctx: dict[str, Any] = dict(tm2_workbench_desk_security_context(actor))
	if reason and str(reason).strip():
		ctx["workbench_publish_reason"] = str(reason).strip()
	return publish_tender(actor, tc, context=ctx)


@frappe.whitelist()
def export_workbench_tender_evidence(
	tender_code: str | None = None,
	include_confidential: int | str | None = None,
) -> dict[str, Any]:
	"""P9-19 — desk-whitelisted §13.3 evidence export (doc 9 §17.12). ``include_confidential`` only honored post-opening."""
	actor = frappe.session.user
	tc = cstr(tender_code or "").strip()
	if not tc:
		return {"ok": False, "message": _("Tender code is required.")}
	fresh = get_workbench_tender_action_availability_service(actor, tc, "AUD2_EXPORT_EVIDENCE")
	if not fresh.get("ok"):
		return fresh
	avail = fresh.get("availability") or {}
	if not avail.get("allowed"):
		return {
			"ok": False,
			"message": str(avail.get("user_message") or avail.get("message") or _("Evidence export is not allowed.")),
			"availability": avail,
		}
	raw_inc = include_confidential
	inc = False
	if isinstance(raw_inc, bool):
		inc = raw_inc
	elif raw_inc is not None and str(raw_inc).strip() in {"1", "true", "True", "yes"}:
		inc = True
	ctx: dict[str, Any] = dict(tm2_workbench_desk_security_context(actor))
	return export_tender_evidence(actor, tc, inc, context=ctx)


def _parse_section_19_1_filters(raw: Any) -> dict[str, Any] | None:
	"""Parse optional §19.1 ``filters`` JSON object (reserved for future server-side filtering)."""
	if raw is None:
		return None
	if isinstance(raw, dict):
		return dict(raw)
	s = cstr(raw).strip()
	if not s:
		return None
	try:
		p = frappe.parse_json(s)
		return dict(p) if isinstance(p, dict) else {}
	except Exception:
		return {}


@frappe.whitelist()
def list_workbench_tenders(
	queue: str | None = None,
	search: str | None = None,
	limit: int | None = None,
	filters: str | None = None,
) -> dict[str, Any]:
	"""P9-06 / **P9-23** — workbench tender list (doc 9 §14.8 / **§19.1**).

	Response includes ``items`` and ``counts`` (queue bucket totals, snake_case keys).
	Optional ``filters`` is accepted as a JSON string for §19.1 alignment; values are
	not yet applied to the query.
	"""
	lim = int(limit) if limit is not None else 50
	if lim < 1:
		lim = 1
	if lim > 200:
		lim = 200
	fp = _parse_section_19_1_filters(filters)
	return list_workbench_tenders_service(frappe.session.user, queue, search, limit=lim, _filters=fp)


@frappe.whitelist()
def list_packages_for_new_tender(search: str | None = None, limit: int | None = None) -> dict[str, Any]:
	"""P9-03 — packages for **New Tender** picker (not free-form create)."""
	lim = int(limit) if limit is not None else 50
	if lim < 1:
		lim = 1
	if lim > 200:
		lim = 200
	return list_packages_for_new_tender_service(frappe.session.user, search, limit=lim)


@frappe.whitelist()
def list_new_tender_wizard_std_options(package_code: str | None = None) -> dict[str, Any]:
	"""P9-07 — STD template/version/profile options for the New Tender wizard (doc 9 §15)."""
	return list_new_tender_wizard_std_options_service(frappe.session.user, package_code)


@frappe.whitelist()
def complete_new_tender_wizard(
	package_code: str | None = None,
	preferred_std_template: str | None = None,
	std_template_version_code: str | None = None,
	applicability_profile_code: str | None = None,
	wizard_timeline_dates: str | dict | None = None,
) -> dict[str, Any]:
	"""P9-07 — create Draft ``TM2 Tender`` + bind STD instance (doc 9 §15.5–15.6)."""
	actor = frappe.session.user
	ctx: dict[str, Any] = {}
	if wizard_timeline_dates:
		if isinstance(wizard_timeline_dates, str):
			try:
				ctx["wizard_timeline_dates"] = json.loads(wizard_timeline_dates)
			except json.JSONDecodeError:
				return {"ok": False, "message": _("Invalid wizard_timeline_dates JSON.")}
		elif isinstance(wizard_timeline_dates, dict):
			ctx["wizard_timeline_dates"] = wizard_timeline_dates
	return submit_new_tender_wizard_completion(
		actor,
		cstr(package_code or "").strip(),
		cstr(preferred_std_template or "").strip(),
		cstr(std_template_version_code or "").strip(),
		cstr(applicability_profile_code or "").strip(),
		context=ctx,
	)
