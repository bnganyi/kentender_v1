# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 test world (plan D18) — extends Procurement
Requisitions' own fixture world (which itself extends Planning's
`KENTENDER_TEST` world): an authorised, unconsumed `AuthorisedRequisitionHandoff
v1.4` can only come from Requisitions' own commands, and the Planning/
Requisitions actors already hold Head of Procurement Function, Accounting
Officer and Auditor. Tenders adds a Procurement Officer, a "both" actor who
holds every Tenders responsibility (segregation tests) and a nobody.

`authorised_handoff()` runs Requisitions' own REQ-CHG-001 v1.11 test helpers
(not a re-derived copy), so the Tenders tests never build a subtly different
Requisition than the one Requisitions itself proves.
"""

from __future__ import annotations

from uuid import uuid4

import frappe

from kentender_procurement.procurement_requisitions.tests import fixtures as req_fx

NS = req_fx.NS
OFFICER = "tndt.officer@example.test"
HOPF = req_fx.HOPF
AO = req_fx.ACCOUNTING_OFFICER
BOTH = "tndt.both@example.test"  # Procurement Officer + HoPF + AO — the segregation subject
AUDITOR = req_fx.AUDITOR
OUTSIDER = req_fx.OUTSIDER  # Departmental Author in OU_BETA — never a contributing unit
NOBODY = "tndt.nobody@example.test"
PRODUCER = "tndt.producer@example.test"  # the bidder-facing service identity (plan D8)
# Departmental Author in OU_ALPHA only — the neutral reader. Tenders' own
# actor: REQ-CHG-001 v1.11's fixtures give their Author OU_BETA too.
DEPARTMENTAL = "tndt.departmental@example.test"
TENDER_ACTORS = (OFFICER, BOTH, NOBODY, PRODUCER, DEPARTMENTAL)

LOCATION = "Test Delivery Location — Tenders"
CONTACT_OFFICE = "Test Contact Office — Tenders"

TENDER_DOCTYPES = (
	"Tender Event", "Tender Command Journal", "Tender Document", "Tender Submission Handoff", "Tender Channel Confirmation",
	"Tender Addendum Inquiry", "Tender Addendum", "Tender Cancellation", "Tender Publication", "Tender Decision", "Tender Task",
	"Tender Version", "Tender",
)


def key() -> str:
	return uuid4().hex


def _user(email: str, full_name: str) -> None:
	if not frappe.db.exists("User", email):
		user = frappe.get_doc({"doctype": "User", "email": email, "first_name": full_name, "send_welcome_email": 0, "enabled": 1}).insert(ignore_permissions=True)
	else:
		user = frappe.get_doc("User", email)
	if frappe.db.get_value("User", email, "user_type") != "System User":
		user.add_roles("Desk User")


def _grant(email: str, role: str, unit: str = "") -> None:
	from kentender_core.services import responsibility_administration as administration

	administration.grant(user=email, business_role=role, organisation_unit=unit, fixture_namespace=NS, actor="Administrator")


def ensure_world() -> None:
	frappe.set_user("Administrator")
	req_fx.ensure_world()
	from kentender_core.services.business_role_registry import ensure_roles

	ensure_roles()
	for email, name in ((OFFICER, "TNDT Procurement Officer"), (BOTH, "TNDT Officer and Approver"), (NOBODY, "TNDT Nobody"), (PRODUCER, "TNDT Bidder Service"), (DEPARTMENTAL, "TNDT Departmental Reader")):
		_user(email, name)
	from kentender_procurement.tenders.services import inquiries
	from kentender_procurement.tenders.services.tender_roles import INQUIRY_PRODUCER_ROLE

	inquiries.ensure_producer_role()
	frappe.get_doc("User", PRODUCER).add_roles(INQUIRY_PRODUCER_ROLE)
	_grant(OFFICER, "Procurement Officer")
	_grant(BOTH, "Procurement Officer")
	_grant(BOTH, "Head of Procurement Function")
	_grant(BOTH, "Accounting Officer")
	_grant(DEPARTMENTAL, "Departmental Author", req_fx.ou_alpha())
	for doctype, field, name in (("Delivery Location", "location_name", LOCATION), ("Contact Office", "office_name", CONTACT_OFFICE)):
		if not frappe.db.exists(doctype, name):
			values = {"doctype": doctype, field: name, "address": "1 Test Street", "status": "Active", "fixture_namespace": NS}
			if doctype == "Contact Office":
				values.update({"contact_email": "procurement@example.test", "contact_phone": "+254 700 000000"})
			frappe.get_doc(values).insert(ignore_permissions=True)
	from kentender_procurement.std_templates.services import installer as std_installer

	std_installer.ensure_site_release()
	# The publication rule the §10.1 fixture cites (site rows; find-or-create).
	from kentender_core.seeds import site_setup

	site_setup._seed_publication_obligations()


def wipe_tender_rows() -> None:
	frappe.set_user("Administrator")
	for doctype in TENDER_DOCTYPES:
		for name in frappe.get_all(doctype, pluck="name"):
			doc = frappe.get_doc(doctype, name)
			doc.flags.kt_fixture_wipe = True
			doc.delete(ignore_permissions=True, force=True)
	frappe.db.commit()


def wipe_requisition_rows() -> None:
	req_fx.wipe_requisition_rows()


def wipe_planning_rows() -> None:
	req_fx.wipe_planning_rows()


def wipe_all() -> None:
	wipe_tender_rows()
	wipe_requisition_rows()
	wipe_planning_rows()


def restore_site() -> None:
	wipe_tender_rows()
	frappe.set_user("Administrator")
	for email in TENDER_ACTORS:
		for doctype in ("User Responsibility Assignment",):
			for name in frappe.get_all(doctype, filters={"user": email}, pluck="name"):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		if frappe.db.exists("User", email):
			frappe.delete_doc("User", email, force=True, ignore_permissions=True)
	for doctype, name in (("Delivery Location", LOCATION), ("Contact Office", CONTACT_OFFICE)):
		if frappe.db.exists(doctype, name):
			frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
	frappe.db.commit()
	req_fx.restore_site()


# --------------------------------------------------------------------------
# An authorised, unconsumed handoff built through Requisitions' own commands
# --------------------------------------------------------------------------


def evidence_file(file_name: str = "NB-MOH-2027-033.png") -> str:
	"""A real one-pixel image as a private File (Frappe runs images through
	Pillow on insert), for channel-confirmation evidence."""
	from io import BytesIO

	from PIL import Image

	buffer = BytesIO()
	Image.new("RGB", (1, 1), (255, 255, 255)).save(buffer, format="JPEG" if file_name.lower().endswith((".jpg", ".jpeg")) else "PNG")
	doc = frappe.get_doc({"doctype": "File", "file_name": file_name, "is_private": 1, "content": buffer.getvalue()}).insert(ignore_permissions=True)
	return doc.name


def authorised_handoff(*, items: tuple[tuple[str, int, str], ...] = (("Business laptops", 1, "Clinical training"),)) -> dict:
	"""Returns Requisitions' own `authorise_requisition` result (`handoff`,
	`requisition`, `requisition_version`, ...) for a fresh Active Plan Item,
	built with Requisitions' own REQ-CHG-001 v1.11 test sequence (prepare,
	request details, same-specification items, the standard requirement
	package, send, Head of User Department submit, HOPF authorise). The item
	name comes from `items`; quantities are the Plan Item's own lines."""
	_, item_id = req_fx.active_item()
	requisition = req_fx.prepare(item_id)["requisition"]
	req_fx.fill_request_information(requisition)
	req_fx.add_laptops(requisition, item_name=items[0][0])
	req_fx.apply_standard_package(requisition)
	req_fx.send(requisition)
	req_fx.submit_as_hod(requisition)
	authorised = req_fx.authorise(requisition)
	frappe.set_user("Administrator")
	return authorised
