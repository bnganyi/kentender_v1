# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-UI-01 Portfolio service contract tests."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt

from kentender_budget.seeds.moh_mvp_v1_portfolio import upsert_moh_mvp_v1_portfolio
from kentender_budget.services.budget_contracts import (
	format_kes_compact,
	get_budget_portfolio,
	list_budgets,
)
from kentender_budget.services.budget_permissions import ensure_budget_roles


class TestBudgetPortfolioUi01(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_budget_roles()
		cls.seed = upsert_moh_mvp_v1_portfolio()

	def test_portfolio_strip_counts_shape(self):
		pf = get_budget_portfolio(procuring_entity=self.seed["procuring_entity"])
		counts = pf["counts"]
		for key in ("active", "awaiting_review", "returned", "funding_exceptions"):
			self.assertIn(key, counts)
			self.assertIsInstance(counts[key], int)
		self.assertGreaterEqual(counts["active"], 1)
		self.assertGreaterEqual(counts["awaiting_review"], 1)
		self.assertGreaterEqual(counts["funding_exceptions"], 1)
		self.assertTrue(pf.get("capabilities", {}).get("register_budget"))

	def test_list_includes_stitch_fixture_rows(self):
		rows = list_budgets(procuring_entity=self.seed["procuring_entity"])
		by_code = {r["code"]: r for r in rows}
		self.assertIn("MOH-BUD-2027-2028", by_code)
		active = by_code["MOH-BUD-2027-2028"]
		self.assertEqual(active["status"], "Active")
		self.assertEqual(active["approved_display"], "KES 560M")
		self.assertEqual(active["available_display"], "KES 105M")
		self.assertIn("stale", (active.get("attention") or "").lower())
		self.assertEqual(active["action"], "open")

		submitted = by_code["MOH-BUD-0002"]
		self.assertEqual(submitted["status"], "Submitted")
		self.assertEqual(submitted["status_label"], "Under review")
		self.assertEqual(submitted["available_display"], "Not active")
		self.assertEqual(submitted["action"], "review")

		closed = by_code["MOH-BUD-2026-2027"]
		self.assertEqual(closed["status"], "Closed")
		self.assertEqual(closed["action"], "view")
		# Stitch Closed Available is KES 0 (not "Not active" — that is for Submitted).
		self.assertEqual(closed["available_display"], "KES 0")
		self.assertTrue(closed.get("action_muted"))

	def test_list_filters_search_and_status(self):
		rows = list_budgets(
			procuring_entity=self.seed["procuring_entity"],
			search="MOH-BUD-2027-2028",
			status="Active",
		)
		self.assertTrue(rows)
		self.assertTrue(all(r["status"] == "Active" for r in rows))
		self.assertTrue(any(r["code"] == "MOH-BUD-2027-2028" for r in rows))

		under = list_budgets(
			procuring_entity=self.seed["procuring_entity"],
			status="Under review",
		)
		self.assertTrue(under)
		self.assertTrue(all(r["status"] == "Submitted" for r in under))

		empty = list_budgets(
			procuring_entity=self.seed["procuring_entity"],
			search="NO-SUCH-BUDGET-ZZZ",
		)
		self.assertEqual(empty, [])

	def test_entity_scope_excludes_other_pe(self):
		# Admin may query a non-existent PE and get empty; cross-entity for scoped users is denied.
		rows = list_budgets(procuring_entity="__no_such_pe__")
		self.assertEqual(rows, [])

	def test_viewer_hides_draft_and_returned(self):
		from kentender_budget.services import budget_permissions as perms

		self.assertEqual(
			set(perms.visible_statuses_for_roles({perms.ROLE_VIEWER})),
			{"Active", "Submitted", "Closed", "Cancelled"},
		)
		self.assertIsNone(
			perms.visible_statuses_for_roles({perms.ROLE_VIEWER, perms.ROLE_OFFICER})
		)
		self.assertIsNone(perms.visible_statuses_for_roles({"System Manager"}))

	def test_register_capability_officer_only(self):
		from kentender_budget.services import budget_permissions as perms

		self.assertTrue(perms.can_register_budget_for_roles({perms.ROLE_OFFICER}))
		self.assertFalse(perms.can_register_budget_for_roles({perms.ROLE_AUTHORITY}))
		self.assertFalse(perms.can_register_budget_for_roles({perms.ROLE_VIEWER}))
		self.assertTrue(perms.can_register_budget_for_roles({perms.ROLE_OFFICER, "System Manager"}))

	def test_cross_entity_denied_for_scoped_user(self):
		from kentender_budget.services import budget_contracts as contracts
		from kentender_budget.services import budget_permissions as perms

		# resolve_scoped_entity rejects foreign PE for non-admin roles.
		with self.assertRaises(frappe.PermissionError):
			contracts.resolve_scoped_entity(
				requested="OTHER-PE",
				user_entity="PE-MOH",
				roles={perms.ROLE_OFFICER},
			)
		self.assertEqual(
			contracts.resolve_scoped_entity(
				requested=None,
				user_entity="PE-MOH",
				roles={perms.ROLE_OFFICER},
			),
			"PE-MOH",
		)

	def test_format_kes_compact(self):
		self.assertEqual(format_kes_compact(560_000_000), "KES 560M")
		self.assertEqual(format_kes_compact(105_000_000), "KES 105M")
		self.assertEqual(format_kes_compact(100_000), "KES 100,000")
		self.assertEqual(format_kes_compact(0), "KES 0")

	def test_draft_without_lines_shows_registered_approved_total(self):
		"""Register saves external_approved_total; portfolio must not show KES 0 from empty lines."""
		from kentender_budget.services.budget_contracts import register_budget

		pe = self.seed["procuring_entity"]
		# Clean any leftover Draft for this high FY.
		for name in frappe.get_all(
			"Budget",
			filters={
				"procuring_entity": pe,
				"fiscal_period": "2044/45",
				"status": ["in", ["Draft", "Submitted", "Returned", "Active"]],
			},
			pluck="name",
		):
			frappe.delete_doc("Budget", name, force=True, ignore_permissions=True)

		ensure_budget_roles()
		email = "bud.officer.port.appr@example.com"
		if not frappe.db.exists("User", email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": "BudPortAppr",
					"send_welcome_email": 0,
					"user_type": "System User",
				}
			)
			user.insert(ignore_permissions=True)
		user = frappe.get_doc("User", email)
		user.add_roles("Budget Officer")
		frappe.db.delete("User Permission", {"user": email, "allow": "Procuring Entity"})
		frappe.get_doc(
			{
				"doctype": "User Permission",
				"user": email,
				"allow": "Procuring Entity",
				"for_value": pe,
				"is_default": 1,
			}
		).insert(ignore_permissions=True)

		frappe.set_user(email)
		result = register_budget(
			{
				"title": "Portfolio approved display FY 2044/45",
				"fiscal_period": "2044/45",
				"currency": "KES",
				"budget_owner": "Director, Finance and Accounts",
				"authoritative_reference": "MOH-FIN-BUD-PORT-APPR-2044",
				"approval_date": "2044-06-15",
				"external_approved_total": "100000",
				"approval_evidence": "",
			}
		)
		self.assertTrue(result.get("ok"), result)
		budget_id = result["budget"]["id"]
		self.addCleanup(
			lambda: frappe.delete_doc("Budget", budget_id, force=True, ignore_permissions=True)
			if frappe.db.exists("Budget", budget_id)
			else None
		)
		self.assertFalse(frappe.db.exists("Budget Line", {"budget": budget_id}))

		frappe.set_user("Administrator")
		rows = list_budgets(procuring_entity=pe, search="Portfolio approved display")
		self.assertTrue(rows)
		row = rows[0]
		self.assertEqual(flt(row["approved_amount"]), 100_000)
		self.assertEqual(row["approved_display"], "KES 100,000")
		self.assertEqual(row["available_display"], "Not active")
