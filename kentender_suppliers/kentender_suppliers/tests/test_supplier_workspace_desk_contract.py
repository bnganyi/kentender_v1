# Copyright (c) 2026, KenTender and contributors
# License: MIT. See license.txt

"""Desk-side contracts for Supplier Management workspace (mount + roles)."""

from __future__ import annotations

import json
from pathlib import Path

from frappe.tests import IntegrationTestCase


def _workspace_json_path() -> Path:
	return (
		Path(__file__).resolve().parents[1]
		/ "supplier_management"
		/ "workspace"
		/ "ktsm_supplier_registry"
		/ "ktsm_supplier_registry.json"
	)


class TestSupplierWorkspaceDeskContract(IntegrationTestCase):
	def test_supplier_workspace_roles_include_procurement_personas(self):
		data = json.loads(_workspace_json_path().read_text(encoding="utf-8"))
		roles = {r["role"] for r in (data.get("roles") or [])}
		for required in (
			"Procurement Officer",
			"Planning Authority",
			"Procurement Planner",
		):
			self.assertIn(required, roles, f"Workspace must include {required} for desk access parity")

	def test_supplier_workspace_paragraph_does_not_embed_div_mount(self):
		"""EditorJS paragraph sanitizer allows only br,b,i,a,span — raw div mounts never reach the DOM."""
		data = json.loads(_workspace_json_path().read_text(encoding="utf-8"))
		raw = data.get("content") or ""
		self.assertNotIn("<div", raw.lower(), "Paragraph content must not rely on stripped div mounts")
