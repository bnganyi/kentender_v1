# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""W2 — Workbench Active Plan Context + Gate.

Scope (Workbench Wiring Tracker, W2):
- Fetch `get_pp_active_plan_view_model` once per fresh Workbench mount.
- No active plan -> non-visual gate: alert + redirect to the Planning Hub
  (the Hub already owns the Create Plan / Activate Plan CTAs and design).
- Active plan -> populate the existing "Active Plan" KPI card already
  present in the pixel-perfect design (status badge, plan title, fiscal
  year) via plain text updates inside the design iframe's own document.
  No new DOM nodes are introduced anywhere.

This module only asserts the frontend wiring contract at the source level
(consistent with the rest of this router's test suite, which has no JS
runtime harness). The backend contract itself
(`get_pp_active_plan_view_model` / `get_active_plan_view_model`) is already
covered by `test_pp3_active_plan_view_model_p2_001.py`; here we additionally
pin the exact field names the JS depends on so a silent API contract change
is caught immediately. Playwright UX validation runs separately against
`kentender.midas.com`.
"""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from kentender_core.seeds import constants as C
from kentender_core.seeds._common import ensure_currency_kes
from kentender_procurement.procurement_planning.pp2_constants import PLAN_ACTIVE
from kentender_procurement.procurement_planning.services.active_plan_view_model import (
	get_active_plan_view_model,
)


def _router_path() -> Path:
	return Path(__file__).resolve().parents[2] / "public" / "js" / "pp2_planning_router.js"


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Plan"))


class TestPP4WorkbenchActivePlanContextW2Source(UnitTestCase):
	"""Source-level wiring assertions for pp2_planning_router.js."""

	def setUp(self) -> None:
		super().setUp()
		self.source = _router_path().read_text(encoding="utf-8", errors="replace")

	def _fn_block(self, signature: str) -> str:
		return self.source.split(signature, 1)[1].split("\n\t}\n", 1)[0]

	def test_fetch_uses_existing_active_plan_api_constant(self) -> None:
		fetch_fn = self._fn_block("function fetchAndApplyWorkbenchActivePlanContext(root) {")
		self.assertIn("method: ACTIVE_PLAN_API", fetch_fn)
		self.assertIn("has_active_plan", fetch_fn)
		self.assertIn("redirectWorkbenchToPlanningHubForNoActivePlan(payload)", fetch_fn)
		self.assertIn("withWorkbenchIframeDocument(root", fetch_fn)
		# Reuses the existing PP2/PP3 API path constant rather than duplicating it.
		self.assertIn(
			'"kentender_procurement.procurement_planning.api.active_plan.get_pp_active_plan_view_model"',
			self.source,
		)

	def test_no_active_plan_gate_alerts_and_redirects_to_hub(self) -> None:
		gate_fn = self._fn_block("function redirectWorkbenchToPlanningHubForNoActivePlan(payload) {")
		self.assertIn("frappe.show_alert", gate_fn)
		self.assertIn('indicator: "orange"', gate_fn)
		self.assertIn('window.location.href = "/desk/planning-hub"', gate_fn)

	def test_active_plan_card_updates_only_existing_kpi_card_fields(self) -> None:
		card_fn = self._fn_block("function applyWorkbenchActivePlanCard(doc, payload) {")
		# Selects the design's own pre-existing "Active Plan" KPI card by its
		# unique class pairing — no new data-testid / element is introduced.
		self.assertIn(".bg-primary-container.border-primary-container", card_fn)
		self.assertIn("data.status_label", card_fn)
		self.assertIn("data.plan_title", card_fn)
		self.assertIn("data.fiscal_year", card_fn)
		self.assertIn(".textContent", card_fn)

	def test_iframe_document_scoping_helper_does_not_touch_desk_root(self) -> None:
		scope_fn = self._fn_block("function withWorkbenchIframeDocument(root, callback) {")
		self.assertIn('data-testid="pp4-workbench-design-iframe"', scope_fn)
		self.assertIn("contentDocument", scope_fn)
		self.assertNotIn("root.innerHTML", scope_fn)

	def test_iframe_document_scoping_helper_rejects_transient_blank_document(self) -> None:
		"""Regression (W3): a freshly-created iframe's about:blank placeholder
		document also reports `readyState === "complete"` with an empty <body>.
		Any caller that invokes this helper synchronously (not from inside an
		async callback, e.g. queue-tab binding on mount) would otherwise race
		the real navigation and silently operate on the wrong document. The
		helper must require a rendered child before treating the document as
		loaded, and must still catch the real `load` event afterwards."""
		scope_fn = self._fn_block("function withWorkbenchIframeDocument(root, callback) {")
		self.assertIn("doc.body.firstElementChild", scope_fn)
		self.assertIn('addEventListener("load", tryInvoke', scope_fn)


class TestPP4WorkbenchActivePlanContextW2FieldContract(IntegrationTestCase):
	"""Pin the exact `get_active_plan_view_model` fields the JS reads from,
	so an unnoticed backend rename cannot silently break the W2 card/gate."""

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self._cleanup: list[str] = []
		if not _pp_ok():
			self._skip = True
			return
		self._skip = False
		ensure_currency_kes()

	def tearDown(self):
		if getattr(self, "_skip", True):
			return
		frappe.set_user("Administrator")
		for name in reversed(self._cleanup):
			if frappe.db.exists("Procurement Plan", name):
				frappe.delete_doc("Procurement Plan", name, force=True, ignore_permissions=True)
		frappe.db.commit()

	def _mk_active_plan(self, *, fiscal_year: int) -> str:
		plan = frappe.get_doc(
			{
				"doctype": "Procurement Plan",
				"plan_name": f"W2 workbench plan {frappe.generate_hash(length=5)}",
				"plan_code": f"PLAN-W2-{frappe.generate_hash()[:6].upper()}",
				"fiscal_year": fiscal_year,
				"procuring_entity": C.ENTITY_MOH,
				"currency": "KES",
				"status": PLAN_ACTIVE,
				"is_active": 1,
			}
		)
		plan.insert(ignore_permissions=True)
		self._cleanup.append(plan.name)
		return plan.name

	def test_gate_payload_exposes_message_used_by_alert(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning not installed")
		out = get_active_plan_view_model(actor="Administrator", fiscal_year=2099)
		self.assertTrue(out.get("ok"), msg=out)
		self.assertFalse(out.get("has_active_plan"))
		self.assertIsInstance(out.get("message"), str)
		self.assertTrue(str(out.get("message") or "").strip())

	def test_active_plan_payload_exposes_card_fields(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning not installed")
		self._mk_active_plan(fiscal_year=2077)
		frappe.db.commit()

		out = get_active_plan_view_model(actor="Administrator", fiscal_year=2077)
		self.assertTrue(out.get("ok"), msg=out)
		self.assertTrue(out.get("has_active_plan"))
		for field in ("status_label", "plan_title", "fiscal_year"):
			self.assertIn(field, out)
			self.assertTrue(str(out.get(field) or "").strip(), msg=f"{field} must be non-empty")
