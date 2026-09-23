# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Planning's subscriber to accepted Departmental Needs (PLN §7.1, NDS §7.1).

Departmental Needs appends `DepartmentalNeedAccepted.v2` to its outbox inside
the accepting command's own transaction, so the event exists if and only if
the acceptance committed. Planning listens for that row and makes sure the
department has a Draft departmental plan carrying the requirement.

Why a subscriber and not a call from the acceptance command: Planning consumes
Needs, Needs knows nothing about Planning (decision D5), so the reaction is
registered on Planning's side, against the published event contract — the one
surface a consumer is allowed to read. `hooks.py` wires it to
`Departmental Need Event`'s `after_insert`.

Starting the plan is a consequence of the acceptance, never a condition of it.
The work runs in its own savepoint and a failure is logged and dropped: an
accepted Need must not be lost because Planning could not open a Draft, and
`Start departmental plan` on the Planning workspace is still there to open one
by hand.
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr

SAVEPOINT = "kt_dpp_autostart"


def _payload(doc) -> dict[str, Any]:
	"""The event body. A JSON field reads back as text or as an already
	decoded value depending on how the document was loaded."""
	raw = doc.get("payload")
	if isinstance(raw, dict):
		return raw
	try:
		body = json.loads(cstr(raw) or "{}")
	except ValueError:
		return {}
	return body if isinstance(body, dict) else {}


def on_need_event(doc, method: str | None = None) -> None:
	"""Start the accepting department's Draft plan, once per acceptance."""
	from kentender_procurement.departmental_needs.services.events import EVENT_ACCEPTED

	if cstr(doc.get("event_type")) != EVENT_ACCEPTED:
		return
	body = _payload(doc)
	# §7.1 frozen wire keys — the event says which department and which year.
	organisation_unit = cstr(body.get("org_unit_id")).strip()
	fiscal_year = cstr(body.get("financial_year_id")).strip()
	if not organisation_unit or not fiscal_year:
		return

	from kentender_procurement.procurement_planning.services import dpp_lifecycle

	frappe.db.savepoint(SAVEPOINT)
	try:
		dpp_lifecycle.ensure_departmental_plan(
			organisation_unit=organisation_unit,
			fiscal_year=fiscal_year,
			trigger_event=cstr(doc.get("event_id")),
			fixture_namespace=cstr(doc.get("fixture_namespace")),
		)
	except Exception:
		frappe.db.rollback(save_point=SAVEPOINT)
		frappe.log_error(
			title="Departmental plan autostart failed",
			message=(
				f"Accepted Need event {cstr(doc.get('event_id'))} "
				f"({organisation_unit} / {fiscal_year}) did not start a departmental plan.\n\n"
				f"{frappe.get_traceback()}"
			),
		)
	else:
		frappe.db.release_savepoint(SAVEPOINT)
