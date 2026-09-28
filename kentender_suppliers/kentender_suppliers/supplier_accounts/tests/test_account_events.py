# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 §12.1 (BDS01-AC-089; follow-up FU-V08-65): every
successful Supplier Account command's audit event carries the event
minimum — schema version, command name and request-key hash, the
organisation and its resulting record version, the actor and acting
assignment, the instant in UTC and as displayed in EAT, and the Account's
previous and resulting status."""

from __future__ import annotations

import hashlib
import json

import frappe

from kentender_core.utils.instants import to_utc_iso

from kentender_suppliers.supplier_accounts.services import access
from kentender_suppliers.supplier_accounts.tests.support import AMINA, MARY, AccountsCase, key


class TestAccountEventMinimum(AccountsCase):
	def event(self, organisation: str, action: str) -> dict:
		rows = frappe.get_all("Audit Event", filters={"document_name": organisation, "action": action}, fields=["metadata", "timestamp", "performed_by"], order_by="creation desc", limit=1)
		self.assertTrue(rows, action)
		metadata = rows[0].metadata
		return {"metadata": json.loads(metadata) if isinstance(metadata, str) else metadata, "timestamp": rows[0].timestamp, "actor": rows[0].performed_by}

	def test_register_and_suspend_record_the_event_minimum(self):
		org = self.active_account()
		registered = self.event(org, "register_supplier_organisation")["metadata"]["event"]
		self.assertEqual((registered["schema_version"], registered["command"], registered["organisation"]), (1, "RegisterSupplierOrganisation", org))
		self.assertRegex(registered["idempotency_key_hash"], r"^[0-9a-f]{64}$")
		self.at("2027-05-19 08:00:00")
		request = key()
		version = frappe.db.get_value("Supplier Organisation", org, "record_version")
		access.suspend_supplier_account(organisation=org, reason="Reported misuse of the account.", expected_version=version, idempotency_key=request, user=AMINA)
		row = self.event(org, "suspend_supplier_account")
		event = row["metadata"]["event"]
		self.assertEqual(
			(event["command"], event["idempotency_key_hash"], event["previous_status"], event["resulting_status"], event["record_version"]),
			("SuspendSupplierAccount", hashlib.sha256(request.encode()).hexdigest(), "Active", "Suspended", frappe.db.get_value("Supplier Organisation", org, "record_version")),
		)
		self.assertEqual((event["occurred_at_utc"], event["occurred_at_eat"]), (to_utc_iso(row["timestamp"]), "19 May 2027, 08:00:00 EAT"))
		self.assertEqual(row["actor"], AMINA)
		self.assertTrue(event["assignment"])  # the support officer's responsibility assignment
		mary = self.event(org, "register_supplier_organisation")
		self.assertEqual(mary["actor"], MARY)
