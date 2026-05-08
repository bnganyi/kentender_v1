# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD Governance Desk navigation (STD-GOV-NAV-AC-001…008)."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

WS_NAME = "Governance & Configuration"
EXPECTED_SHORTCUTS: tuple[str, ...] = (
	"Official STD Library — Catalogue",
	"Import Official STD Package",
	"Pending Validation",
	"Pending Approval",
	"Active STD Templates",
	"Superseded / Retired / Archived",
	"STD Template Usage",
	"STD Governance Audit",
	"STD Package Inspector",
)


class TestStdGovernanceWorkspaceNav(IntegrationTestCase):
	def test_std_gov_nav_ac001_ac006_workspace_and_shortcuts(self) -> None:
		"""AC-001, AC-002…AC-006: workspace exists with catalogue, import, queues, active, historical, usage, audit, inspector."""
		self.assertTrue(frappe.db.exists("Workspace", WS_NAME))
		ws = frappe.get_doc("Workspace", WS_NAME)
		labels = [s.label for s in (ws.shortcuts or [])]
		for exp in EXPECTED_SHORTCUTS:
			self.assertIn(exp, labels, msg=f"missing shortcut {exp}")
		content = (ws.content or "").replace("\\u2014", "\u2014")
		self.assertIn("Official STD Library", content)
		self.assertIn(
			"Manage official standard tender documents available for tender preparation",
			content,
		)
		self.assertIn("PDF or Word files alone do not create a working STD", content)
		self.assertIn("source evidence", content)
		self.assertIn("reviewed JSON/YAML", content)
		self.assertIn("Run Governance Validation", content)
		self.assertIn("Package validation", content)
		self.assertIn("not raw engine traces", content)
		self.assertIn("recombined tender bundle", content)
		self.assertIn("STD-LIB-0300", content)
		self.assertIn("STD-LIB-0310", content)
		self.assertIn("STD-LIB-0250", content)
		self.assertIn("Advanced Technical View", content)
		self.assertIn("not the default path", content)
		self.assertIn("Submission Requirements (DSM)", content)
		self.assertIn("Opening Register (DOM)", content)
		self.assertIn("Evaluation Rules (DEM)", content)
		self.assertIn("Contract Carry-Forward (DCM)", content)
		self.assertIn("STD-LIB-0340", content)
		self.assertIn("STD-LIB-0341", content)
		self.assertIn("STD Instances", content)
		self.assertIn("not the primary task", content)
		self.assertIn("STD Template Usage shortcut", content)
		self.assertIn("read-only references", content)
		self.assertIn("STD-LIB-0320", content)
		self.assertIn("Frappe Desk", content)
		self.assertIn("kentender_procurement", content)
		self.assertIn("separate single-page application", content)
		self.assertIn("explicit programme sign-off", content)
		self.assertIn("ISSUES_LOG", content)
		self.assertIn("whitelisted server methods", content)
		self.assertIn("ROLE_STD_ADMIN", content)
		self.assertIn("STD Template Administrator", content)
		self.assertIn("STD Template Importer", content)
		self.assertIn("STD Template Activator", content)
		self.assertIn("DocPerm", content)
		self.assertIn("Workstream 1", content)
		by_label = {s.label: s for s in (ws.shortcuts or [])}
		self.assertEqual(by_label["Import Official STD Package"].type, "DocType")
		self.assertEqual(by_label["Import Official STD Package"].link_to, "STD Template")
		self.assertEqual(by_label["Import Official STD Package"].doc_view, "New")
		self.assertIn("Pending Validation", by_label)
		self.assertIn("lifecycle_status", (by_label["Pending Validation"].stats_filter or ""))
		self.assertIn("Submitted for Approval", (by_label["Pending Approval"].stats_filter or ""))
		self.assertIn("Active", (by_label["Active STD Templates"].stats_filter or ""))
		self.assertIn("Superseded", (by_label["Superseded / Retired / Archived"].stats_filter or ""))
		self.assertEqual(by_label["STD Template Usage"].link_to, "STD Template Usage")
		self.assertEqual(by_label["STD Governance Audit"].link_to, "STD Template Lifecycle Event")
		self.assertIn(
			"KE-PPRA-WORKS-BLDG-2022-04-POC", (by_label["STD Package Inspector"].stats_filter or "")
		)

	def test_std_gov_nav_ac008_no_procurement_officer_on_workspace(self) -> None:
		"""AC-008: Procurement Officer is not in workspace Has Role (visibility for plain PO)."""
		ws = frappe.get_doc("Workspace", WS_NAME)
		roles = {r.role for r in (ws.roles or [])}
		self.assertNotIn("Procurement Officer", roles)
		# If a user has only roles from the workspace list, they can see it; PO is excluded.
		ws_roles = roles - {"Administrator", "System Manager"}
		self.assertTrue(ws_roles)  # at least one governance role row

	def test_std_gov_nav_reviewer_in_workspace_roles(self) -> None:
		"""AC-005: Approver / Reviewer roles are listed on the workspace (Desk visibility)."""
		ws = frappe.get_doc("Workspace", WS_NAME)
		r = {row.role for row in (ws.roles or [])}
		self.assertIn("STD Template Reviewer", r)
		self.assertIn("STD Template Approver", r)

	def test_std_gov_nav_ac007_auditor_in_workspace_roles(self) -> None:
		"""AC-007: Auditor is on the workspace (Usage + Audit shortcuts are role-gated at DocType level)."""
		ws = frappe.get_doc("Workspace", WS_NAME)
		r = {row.role for row in (ws.roles or [])}
		self.assertIn("STD Template Auditor", r)
