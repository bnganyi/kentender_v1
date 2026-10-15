# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Who a native operation runs as (CM-CHG-001 v0.8 sections 7, 9.1, 12; plan D5).

A purchase order, a receipt of accepted units and the draft of a supplier's invoice are not the signing person's work: the person's act (a signature, a claim) is recorded, and **the service** creates the
native document afterwards (`PostAcceptedReceipt` is "service-only"). A supplier is not an ERPNext user at all, and an inspector holds no stock rights, so running these as the person fails with a
permission error exactly when it matters. `acting()` therefore runs the native call as the site's service principal (the Administrator account, which no one signs in with for business work). The Finance
maker and approver, by contrast, act natively **as themselves** (`acting_as(user)`), so the native workflow checks them.

Both are `frappe.set_user` underneath, and `set_user` is not safe to call and undo inside a web request: it replaces the session's id with the user name, empties the session data and the request's form
values, and Frappe then writes that id back to the browser's `sid` cookie, so the next request arrives as a Guest (found live 15 Oct 2026: the supplier's page went forbidden right after their invoice was
accepted). These helpers restore the session, its id, its data and the request's form values exactly."""

from __future__ import annotations

from contextlib import contextmanager

import frappe

SERVICE_USER = "Administrator"


@contextmanager
def acting_as(user: str):
	"""Run as `user`, then put the request back exactly as it was."""
	session = frappe.local.session
	form = frappe.local.form_dict
	saved = (session.user, session.sid, session.data)
	if saved[0] == user:
		yield
		return
	frappe.set_user(user)
	try:
		yield
	finally:
		frappe.set_user(saved[0])
		frappe.local.session.sid, frappe.local.session.data = saved[1], saved[2]
		frappe.local.form_dict = form


def acting():
	"""The service principal."""
	return acting_as(SERVICE_USER)
