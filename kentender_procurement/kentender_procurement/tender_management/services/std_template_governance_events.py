# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD template governance — lifecycle audit events (doc 7 §13.5, §17, STD-GOV-005).

``write_std_template_lifecycle_event`` appends one row to ``STD Template.lifecycle_events``,
persists the parent, and never swallows save errors (doc 7 §17).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import frappe
from frappe import _
from frappe.utils import now_datetime

from kentender_procurement.tender_management.services.std_template_governance import (
	canonicalize_std_package_payload,
)

if TYPE_CHECKING:
	from frappe.model.document import Document


def write_std_template_lifecycle_event(
	doc: Document | str,
	event_code: str,
	event_type: str,
	payload: dict | None = None,
	from_status: str | None = None,
	to_status: str | None = None,
	reason: str | None = None,
	override_used: bool = False,
	override_reason: str | None = None,
	*,
	save: bool = True,
) -> None:
	"""Append a lifecycle event child row and optionally ``save`` the parent ``STD Template``.

	When ``save=False`` (STD-GOV-006 batching), the caller must ``save`` the parent once after
	all governance mutations are applied.

	- Does not modify existing child rows (append-only).
	- Sets ``actor``, ``event_at``, ``actor_roles`` from the current session user.
	- Copies ``package_hash`` from the parent when present.
	- Serializes ``payload`` to ``payload_json`` with sorted keys (same canonical JSON as
	  ``canonicalize_std_package_payload``).
	- Optionally denormalizes ``validation_run_id`` / ``related_tender`` / ``comment`` from
	  ``payload`` into child columns when those keys are present.
	- ``related_template`` defaults to the parent template name if omitted in ``payload``.
	"""
	if isinstance(doc, str):
		doc = frappe.get_doc("STD Template", doc)

	if doc.doctype != "STD Template":
		frappe.throw(
			_("write_std_template_lifecycle_event expects STD Template, got {0}").format(
				doc.doctype
			)
		)

	user = frappe.session.user
	if not user or user == "Guest":
		frappe.throw(_("A signed-in user is required to record STD Template lifecycle events"))

	payload = dict(payload) if payload else {}
	validation_run_id = payload.get("validation_run_id") or payload.get("run_id")
	related_tender = payload.get("related_tender")
	comment = payload.get("comment")
	related_template = payload.get("related_template") or doc.name

	payload_json: str | None
	if payload:
		payload_json = canonicalize_std_package_payload(payload)
	else:
		payload_json = None

	row: dict = {
		"event_code": event_code,
		"event_type": event_type,
		"from_status": from_status,
		"to_status": to_status,
		"actor": user,
		"actor_roles": ", ".join(sorted(frappe.get_roles(user))),
		"event_at": now_datetime(),
		"reason": reason,
		"comment": comment,
		"package_hash": doc.get("package_hash"),
		"validation_run_id": validation_run_id,
		"related_template": related_template,
		"related_tender": related_tender,
		"override_used": 1 if override_used else 0,
		"override_reason": override_reason,
		"payload_json": payload_json,
	}

	doc.append("lifecycle_events", row)
	if save:
		doc.save()
