# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""KT-ACCESS-REV-001 AR-09 / AR-10 — the Technical Operator is a technical reader.

KT-STD-001 v1.25 §8.3 (Project Owner, 4 October 2026: "Technical Operator has
site-wide read-only access"): the Technical Operator reads every business
surface site-wide, with no business action. That follows the in-force
*assignment*, not the System Manager role, so reading no longer carries setup
and responsibility-administration power with it (the Owner accepted separating
the two). The other technical-holder responsibilities (Release Operator,
Evaluation Technical Support) are not readers.
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services import responsibility_administration as administration
from kentender_core.services.authorization import PURPOSE_COMMAND, PURPOSE_READ, authorise_record, is_technical
from kentender_core.tests import v16_fixtures as fx
from kentender_core.tests.responsibility_test_cleanup import purge

NS = "KT_TEST_TECHOP"


def _grant(user, role, **kwargs):
	return administration.grant(user=user, business_role=role, organisation_unit="", fixture_namespace=NS, **kwargs)


class TestTechnicalOperatorReader(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.addClassCleanup(purge)
		fx.ensure_site_configured()
		frappe.db.commit()

	def test_an_in_force_operator_assignment_is_a_technical_reader_without_system_manager(self):
		operator = fx.user("techop.reader")
		_grant(operator, "Technical Operator")
		frappe.local.role_permissions = {}
		self.assertNotIn("System Manager", frappe.get_roles(operator))
		self.assertTrue(is_technical(operator))

	def test_it_reads_a_business_responsibility_site_wide_but_exercises_none(self):
		operator = fx.user("techop.business")
		_grant(operator, "Technical Operator")
		read = authorise_record(user=operator, business_role="Accounting Officer", purpose=PURPOSE_READ)
		self.assertTrue(read.allowed and read.technical_read)
		command = authorise_record(user=operator, business_role="Accounting Officer", purpose=PURPOSE_COMMAND)
		self.assertFalse(command.allowed)

	def test_a_scheduled_expired_or_revoked_assignment_is_not_a_technical_reader(self):
		scheduled = fx.user("techop.scheduled")
		_grant(scheduled, "Technical Operator", effective_from="2097-01-01 00:00:00", effective_to="2098-01-01 00:00:00")
		self.assertFalse(is_technical(scheduled))

		revoked = fx.user("techop.revoked")
		granted = _grant(revoked, "Technical Operator")["assignment"]
		self.assertTrue(is_technical(revoked))
		administration.revoke(granted, reason="Technical reader test: the assignment ends.")
		frappe.local.role_permissions = {}
		self.assertFalse(is_technical(revoked))

		expired = fx.user("techop.expired")
		granted = _grant(expired, "Technical Operator", effective_from="2020-01-01 00:00:00", effective_to="2097-01-01 00:00:00")["assignment"]
		frappe.db.set_value("User Responsibility Assignment", granted, "effective_to", "2020-06-30 23:59:59", update_modified=False)
		# the Role lingers until the reconciliation; the in-force assignment decides
		self.assertIn("Technical Operator", frappe.get_roles(expired))
		self.assertFalse(is_technical(expired))

	def test_the_other_technical_holder_responsibilities_are_not_readers(self):
		for role in ("Release Operator", "Evaluation Technical Support"):
			user = fx.user("techop." + role.split()[0].lower())
			_grant(user, role)
			self.assertFalse(is_technical(user), role)

	def test_a_person_with_a_business_responsibility_only_is_not_a_technical_reader(self):
		user = fx.user("techop.business.only")
		_grant(user, "Strategy Approver")
		self.assertFalse(is_technical(user))


class TestTechnicalSearchOnlyNamesWhatMayBeOpened(IntegrationTestCase):
	"""KT-ACCESS-REV-001 AR-13 — `frappe.get_all` ignores permissions, so the search asks the technical policy."""

	def test_a_doctype_with_no_technical_read_row_is_never_named(self):
		from kentender_core.services import technical_search

		# Bid Receipt carries no System Manager row: a result for it would lead to a refused form
		self.assertFalse(technical_search.may_open("Bid Receipt", "any", "Administrator"))

	def test_a_sealed_bid_record_is_never_named_even_though_the_role_reads_the_doctype(self):
		from unittest import mock

		from kentender_core.services import technical_search

		shell = frappe.new_doc("Bid Workspace")
		shell.name = "BID-PROBE"
		with mock.patch.object(technical_search.frappe, "get_doc", return_value=shell):
			self.assertFalse(technical_search.may_open("Bid Workspace", "BID-PROBE", "Administrator"))

	def test_an_ordinary_record_with_the_technical_row_is_named(self):
		from kentender_core.services import technical_search

		self.assertTrue(technical_search.may_open("Funding Source", "any", "Administrator"))
