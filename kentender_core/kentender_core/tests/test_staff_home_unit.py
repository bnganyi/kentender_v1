# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AUTH-ADR-001 v1.12 §4.8 / CFG-CHG-002 v0.19 §4.10A, §7, §12 /
CFG19-AC-001…005, AUTH-AC-045…048 — the staff home organisation unit.

`bench run-tests` has no rollback on this bench: every test restores the
staff account it touched, and the audit and journal rows its commands write
are purged on cleanup.
"""

from __future__ import annotations

import uuid

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services import staff_home_unit as home
from kentender_core.services.configuration_errors import ConfigurationError

STAFF = "pw.home.staff@example.test"
PLAIN = "pw.home.plain@example.test"
SUPPLIER = "pw.home.supplier@example.test"


def _key() -> str:
	return f"test-home-{uuid.uuid4().hex}"


def _make_user(email: str, *, user_type: str = "System User", enabled: int = 1) -> None:
	if not frappe.db.exists("User", email):
		frappe.get_doc({"doctype": "User", "email": email, "first_name": email.split("@")[0], "send_welcome_email": 0, "enabled": enabled,
			"user_type": user_type}).insert(ignore_permissions=True)
	frappe.db.set_value("User", email, {"enabled": enabled, "user_type": user_type, home.FIELD: None})


def _purge() -> None:
	frappe.db.delete("Reference Data Command Journal", {"idempotency_key": ("like", "test-home-%")})
	frappe.db.delete("Audit Event", {"action": "set_staff_home_organisation_unit", "document_name": ("in", (STAFF, PLAIN, SUPPLIER))})
	for email in (STAFF, PLAIN, SUPPLIER):
		if frappe.db.exists("User", email):
			frappe.delete_doc("User", email, force=True, ignore_permissions=True)
	frappe.db.commit()


class TestStaffHomeUnit(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.addClassCleanup(_purge)

	def setUp(self):
		frappe.set_user("Administrator")
		_make_user(STAFF)
		_make_user(PLAIN)
		units = frappe.get_all("Organisation Unit", filters={"status": "Active"}, pluck="name", order_by="creation asc", limit_page_length=0)
		self.assertGreaterEqual(len(units), 2, "the canonical world has at least two active units")
		self.unit, self.other = units[0], units[1]
		self.events: list[dict] = []
		self._handlers = home._handlers
		home._handlers = lambda: [self.events.append]
		self.addCleanup(lambda: setattr(home, "_handlers", self._handlers))

	def _token(self, user=STAFF) -> str:
		return home.get_staff_home_organisation_unit(user)["token"]

	def _set(self, unit, *, user=STAFF, key=None, token=None):
		return home.set_staff_home_organisation_unit(user=user, organisation_unit=unit, expected_token=token or self._token(user), idempotency_key=key or _key())

	# CFG19-AC-001 — Administrator and System Manager only.
	def test_only_setup_administrators_may_set_the_home_unit(self):
		frappe.set_user(PLAIN)
		with self.assertRaises(ConfigurationError) as caught:
			home.set_staff_home_organisation_unit(user=STAFF, organisation_unit=self.unit, expected_token="x", idempotency_key=_key())
		self.assertEqual(caught.exception.code, "CFG_AUTHORITY_REQUIRED")
		frappe.set_user("Administrator")
		self.assertIsNone(frappe.db.get_value("User", STAFF, home.FIELD))  # nothing was written

	def test_set_change_and_clear(self):
		out = self._set(self.unit)
		self.assertTrue(out["ok"] and out["changed"], out)
		self.assertEqual(frappe.db.get_value("User", STAFF, home.FIELD), self.unit)
		read = home.get_staff_home_organisation_unit(STAFF)
		self.assertEqual(read["state"], "Recorded")
		self.assertEqual(read["organisation_unit"], self.unit)
		self.assertEqual(read["unit_name"], frappe.db.get_value("Organisation Unit", self.unit, "unit_name"))
		self.assertEqual(read["unit_status"], "Active")
		self._set(self.other)
		self.assertEqual(frappe.db.get_value("User", STAFF, home.FIELD), self.other)
		self._set("")
		self.assertIsNone(frappe.db.get_value("User", STAFF, home.FIELD) or None)
		self.assertEqual(home.get_staff_home_organisation_unit(STAFF)["state"], "Not recorded")

	# CFG19-AC-002 — only an Active unit and an enabled staff account; no partial write.
	def test_an_inactive_unknown_or_ineligible_target_is_refused_with_no_write(self):
		frappe.db.set_value("Organisation Unit", self.other, "status", "Inactive")
		self.addCleanup(lambda: (frappe.db.set_value("Organisation Unit", self.other, "status", "Active"), frappe.db.commit()))
		for unit, user in ((self.other, STAFF), ("OU-DOES-NOT-EXIST", STAFF), (self.unit, "Administrator"), (self.unit, "Guest"), (self.unit, "nobody@example.test")):
			with self.assertRaises(ConfigurationError) as caught:
				home.set_staff_home_organisation_unit(user=user, organisation_unit=unit, expected_token="x", idempotency_key=_key())
			self.assertEqual(caught.exception.code, "CFG_HOME_UNIT_INVALID", (unit, user))
		_make_user(SUPPLIER, user_type="Website User")
		for target in (SUPPLIER,):
			with self.assertRaises(ConfigurationError) as caught:
				home.set_staff_home_organisation_unit(user=target, organisation_unit=self.unit, expected_token="x", idempotency_key=_key())
			self.assertEqual(caught.exception.code, "CFG_HOME_UNIT_INVALID")
		frappe.db.set_value("User", PLAIN, "enabled", 0)
		with self.assertRaises(ConfigurationError) as caught:
			home.set_staff_home_organisation_unit(user=PLAIN, organisation_unit=self.unit, expected_token="x", idempotency_key=_key())
		self.assertEqual(caught.exception.code, "CFG_HOME_UNIT_INVALID")
		self.assertIsNone(frappe.db.get_value("User", STAFF, home.FIELD))
		self.assertEqual(self.events, [])

	def test_replay_conflict_stale_token_and_no_op(self):
		key = _key()
		original_token = self._token()
		first = self._set(self.unit, key=key, token=original_token)
		again = home.set_staff_home_organisation_unit(user=STAFF, organisation_unit=self.unit, expected_token=original_token, idempotency_key=key)
		self.assertEqual(again, first)  # a replay returns the original result
		self.assertEqual(len(self.events), 1)
		with self.assertRaises(ConfigurationError) as caught:  # same key, different content
			home.set_staff_home_organisation_unit(user=STAFF, organisation_unit=self.other, expected_token=original_token, idempotency_key=key)
		self.assertEqual(caught.exception.code, "CFG_IDEMPOTENCY_CONFLICT")
		with self.assertRaises(ConfigurationError) as caught:  # a stale token fails atomically
			self._set(self.other, token="1999-01-01 00:00:00")
		self.assertEqual(caught.exception.code, "CFG_VERSION_CONFLICT")
		self.assertEqual(frappe.db.get_value("User", STAFF, home.FIELD), self.unit)
		audits = frappe.db.count("Audit Event", {"action": "set_staff_home_organisation_unit", "document_name": STAFF})
		unchanged = self._set(self.unit)  # an unchanged value is a no-op: nothing appended, nothing published
		self.assertTrue(unchanged["ok"] and not unchanged["changed"], unchanged)
		self.assertEqual(frappe.db.count("Audit Event", {"action": "set_staff_home_organisation_unit", "document_name": STAFF}), audits)
		self.assertEqual(len(self.events), 1)

	# CFG19-AC-003 — one audit event and one published change.
	def test_each_change_appends_one_audit_event_and_publishes_one_event(self):
		started = frappe.db.count("Audit Event", {"action": "set_staff_home_organisation_unit", "document_name": STAFF})
		self._set(self.unit)
		self._set(self.other)
		self.assertEqual(frappe.db.count("Audit Event", {"action": "set_staff_home_organisation_unit", "document_name": STAFF}) - started, 2)
		self.assertEqual(len(self.events), 2)
		last = self.events[-1]
		self.assertEqual((last["user"], last["before"], last["after"]), (STAFF, self.unit, self.other))
		self.assertEqual(last["actor"], "Administrator")
		self.assertTrue(last["instant"] and last["command_id"])

	# CFG19-AC-004 — contracted reads only; Not recorded is derived on the server.
	def test_the_setup_register_lists_staff_and_filters_not_recorded(self):
		self._set(self.unit)
		everyone = home.list_staff_home_units()
		rows = {r["user"]: r for r in everyone["rows"]}
		self.assertEqual(rows[STAFF]["organisation_unit"], self.unit)
		self.assertEqual(rows[PLAIN]["state"], "Not recorded")
		self.assertNotIn("Administrator", rows)
		self.assertNotIn("Guest", rows)
		self.assertTrue(set(rows[STAFF]) >= {"user", "full_name", "state", "organisation_unit", "unit_name", "unit_status", "token"})
		self.assertFalse(set(rows[STAFF]) & {"business_role", "responsibility", "scope", "roles"})
		missing = home.list_staff_home_units(not_recorded=True)
		self.assertIn(PLAIN, [r["user"] for r in missing["rows"]])
		self.assertNotIn(STAFF, [r["user"] for r in missing["rows"]])
		found = home.list_staff_home_units(search="pw.home.staff")
		self.assertEqual([r["user"] for r in found["rows"]], [STAFF])

	def test_the_setup_register_is_for_setup_administrators(self):
		frappe.set_user(PLAIN)
		with self.assertRaises(ConfigurationError) as caught:
			home.list_staff_home_units()
		self.assertEqual(caught.exception.code, "CFG_AUTHORITY_REQUIRED")

	# AUTH-AC-048 — an inactive unit stays on the person and shows Inactive.
	def test_a_unit_that_becomes_inactive_stays_on_the_person(self):
		self._set(self.other)
		frappe.db.set_value("Organisation Unit", self.other, "status", "Inactive")
		self.addCleanup(lambda: (frappe.db.set_value("Organisation Unit", self.other, "status", "Active"), frappe.db.commit()))
		read = home.get_staff_home_organisation_unit(STAFF)
		self.assertEqual((read["state"], read["organisation_unit"], read["unit_status"]), ("Recorded", self.other, "Inactive"))
		self.assertTrue(read["unit_name"])

	# CFG19-AC-005 / AUTH-AC-047 — no authority effect.
	def test_a_home_unit_changes_no_responsibility(self):
		before = frappe.db.count("User Responsibility Assignment", {"user": STAFF})
		roles_before = sorted(frappe.get_roles(STAFF))
		self._set(self.unit)
		self._set("")
		self.assertEqual(frappe.db.count("User Responsibility Assignment", {"user": STAFF}), before)
		self.assertEqual(sorted(frappe.get_roles(STAFF)), roles_before)
