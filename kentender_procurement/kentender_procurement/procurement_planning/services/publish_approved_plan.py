# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SVC-013 — publish / export the current Approved Plan Version."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, now_datetime

from kentender_procurement.procurement_planning.mvp1_constants import (
	DOCTYPE_PUBLICATION,
	PUB_FAILED,
	PUB_PUBLISHED,
	VERSION_APPROVED,
)
from kentender_procurement.procurement_planning.services.planning_permissions import (
	CAP_PLAN_ITEM_EDIT,
	require_capability,
)

DEFAULT_CHANNEL = "Tender Portal"


def publish_approved_plan(
	*,
	plan: str,
	channel: str | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	actor = (user or frappe.session.user or "").strip()
	if not actor or actor == "Guest":
		return {"ok": False, "errors": {"form": "Login required."}}

	plan_name = cstr(plan).strip()
	if not plan_name or not frappe.db.exists("Procurement Plan", plan_name):
		return {"ok": False, "errors": {"form": "Procurement Plan not found."}}

	plan_doc = frappe.get_doc("Procurement Plan", plan_name)
	pe = cstr(plan_doc.procuring_entity).strip()
	ou = cstr(plan_doc.coordinating_org_unit or "").strip() or None
	try:
		require_capability(
			CAP_PLAN_ITEM_EDIT,
			procuring_entity=pe,
			org_unit=ou,
			user=actor,
			require_write=True,
		)
	except frappe.PermissionError as exc:
		return {
			"ok": False,
			"errors": {"form": str(exc).split(":", 1)[-1].strip() or "Not permitted"},
		}

	approved = cstr(plan_doc.current_approved_version or "").strip()
	if not approved:
		return {
			"ok": False,
			"errors": {"form": "Only the current Approved Version can be published."},
		}

	ver_status = cstr(frappe.db.get_value("Procurement Plan Version", approved, "status"))
	if ver_status != VERSION_APPROVED:
		return {
			"ok": False,
			"errors": {"form": "Only the current Approved Version can be published."},
		}

	dest = cstr(channel or DEFAULT_CHANNEL).strip() or DEFAULT_CHANNEL
	existing = frappe.get_all(
		DOCTYPE_PUBLICATION,
		filters={"plan_version": approved, "status": PUB_PUBLISHED},
		fields=["name", "channel", "published_at", "external_reference"],
		limit=1,
	)
	if existing:
		row = existing[0]
		return {
			"ok": True,
			"idempotent": True,
			"event": row.name,
			"status": PUB_PUBLISHED,
			"destination": cstr(row.channel) or dest,
			"published_at": str(row.published_at or ""),
			"external_reference": cstr(row.external_reference or ""),
			"plan": plan_name,
			"version": approved,
			"version_status": VERSION_APPROVED,
		}

	try:
		event = frappe.get_doc(
			{
				"doctype": DOCTYPE_PUBLICATION,
				"plan_version": approved,
				"channel": dest,
				"status": PUB_PUBLISHED,
				"submitted_by": actor,
				"published_at": now_datetime(),
				"external_reference": f"PUB-{plan_doc.plan_code}-{approved}",
			}
		)
		event.insert(ignore_permissions=True)
	except Exception as exc:
		failed = frappe.get_doc(
			{
				"doctype": DOCTYPE_PUBLICATION,
				"plan_version": approved,
				"channel": dest,
				"status": PUB_FAILED,
				"submitted_by": actor,
				"failure_reason": str(exc),
			}
		)
		failed.insert(ignore_permissions=True)
		return {
			"ok": False,
			"errors": {"form": "Publication failed. The plan remains Approved."},
			"event": failed.name,
			"status": PUB_FAILED,
			"plan": plan_name,
			"version": approved,
			"version_status": cstr(
				frappe.db.get_value("Procurement Plan Version", approved, "status")
			),
		}

	return {
		"ok": True,
		"idempotent": False,
		"event": event.name,
		"status": PUB_PUBLISHED,
		"destination": dest,
		"published_at": str(event.published_at or ""),
		"external_reference": cstr(event.external_reference or ""),
		"plan": plan_name,
		"version": approved,
		"version_status": VERSION_APPROVED,
	}
