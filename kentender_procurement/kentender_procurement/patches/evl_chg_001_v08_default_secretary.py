# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""EVL-CHG-001 v0.8 §3 (Owner decisions D7–D11, 8 October 2026): the Head of
Procurement Function is the evaluation secretary by office. Appointments made
before v0.8 relied on a separate secretary-assignment task, so an evaluation
with a committee but no current secretary gets the secretary by office now.

Only where the Head is clear: exactly one Active Head of Procurement Function
who is not the Accounting Officer. Otherwise the case is left as it is and
named in the log, so an administrator can correct the responsibility
assignments and the Head can delegate. The record is written without a
Proceedings owner event (the roster is unchanged and the instant is the
original appointment's). Idempotent: a case that has a current secretary is
never touched, and no earlier secretary record is edited."""

from __future__ import annotations

import frappe

from kentender_procurement.bid_evaluation.services import people, records, references, separation
from kentender_procurement.services import sequence

SECRETARY = "Evaluation Secretary Appointment"


def _label_earlier_assignments() -> None:
	"""A secretary record made before v0.8 was the Head's own assignment (no committee appointment behind it): it is a written appointment by that
	Head, not "By office" (the new column's default). Records made by this change carry a source appointment and are left alone."""
	for row in frappe.get_all(SECRETARY, filters={"source_appointment": ("is", "not set")}, fields=["name", "assigned_by", "basis", "appointing_authority"]):
		if row.basis == "Written appointment" and row.appointing_authority:
			continue
		frappe.db.set_value(SECRETARY, row.name, {"basis": "Written appointment",
			"appointing_authority": f"{people.full_name(row.assigned_by)}, Head of Procurement Function — written appointment, section 46(4)(c) of the Act"}, update_modified=False)


def execute() -> None:
	if not frappe.db.exists("DocType", "Evaluation Case") or not frappe.db.table_exists("Evaluation Case"):
		return
	_label_earlier_assignments()
	cases = frappe.get_all("Evaluation Case", filters={"current_appointment": ("is", "set")}, fields=["name", "tender_reference", "current_appointment"], order_by="creation asc")
	pending = [c for c in cases if not frappe.db.exists(SECRETARY, {"evaluation_case": c.name, "status": "Current"})]
	if not pending:
		return
	holders = people.head_holders()
	head = holders[0] if len(holders) == 1 else ""
	if not head or separation.panel_refusal(head, as_member=False, as_secretary=True):
		frappe.logger("kentender.patch").warning("evl_chg_001_v08_default_secretary: the Head of Procurement Function is not clear (%s); left %s", holders, [c.name for c in pending])
		return
	for case in pending:
		appointment = frappe.db.get_value("Evaluation Appointment", case.current_appointment, ["name", "appointment_reference", "appointed_by", "appointed_at"], as_dict=True)
		if not appointment:
			continue
		number = sequence.next_count(SECRETARY, {"evaluation_case": case.name})
		authority = (f"{people.full_name(appointment.appointed_by)}, Accounting Officer — committee appointment {appointment.appointment_reference}, "
			f"{frappe.utils.get_datetime(appointment.appointed_at):%-d %b %Y, %H:%M} EAT")
		row = records.insert(frappe.get_doc({
			"doctype": SECRETARY, "secretary_appointment_id": f"{case.name}-SEC-{number:02d}", "evaluation_case": case.name, "secretary_user": head,
			"full_name": people.full_name(head), "appointment_reference": references.secretary(case.tender_reference, number - 1), "basis": "By office",
			"appointing_authority": authority, "source_appointment": appointment.name, "assigned_by": appointment.appointed_by, "assigned_at": appointment.appointed_at,
			"status": "Current",
		}))
		frappe.db.set_value("Evaluation Case", case.name, "secretary_appointment", row.name, update_modified=False)
