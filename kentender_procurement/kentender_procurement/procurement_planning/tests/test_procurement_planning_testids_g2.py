# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Phase G2 — Verify stable Procurement Planning ``data-testid`` hooks in desk JS.

8. Smoke Test Contracts §6 — fast regression that UI assets still expose the hooks
E2E and Playwright use. Dynamic ids (e.g. ``pp-row-``) are covered by pattern checks.
"""

from __future__ import annotations

from pathlib import Path

from frappe.tests import UnitTestCase


def _pkg_root() -> Path:
	""".../kentender_procurement (inner — contains ``public/`` and ``procurement_planning/``)."""
	return Path(__file__).resolve().parents[2]


def _app_public(*parts: str) -> Path:
	return _pkg_root().joinpath("public", *parts)


# KPI testids are emitted from ``api/landing.py``; keep them in sync (§6).
KPI_TESTIDS = (
	"pp-kpi-total-packages",
	"pp-kpi-total-value",
	"pp-kpi-approved-packages",
	"pp-kpi-ready-for-tender",
	"pp-kpi-high-risk",
)

REQUIRED_STABLE = (
	"pp-landing-page",
	"pp-page-title",
	"pp-current-plan-bar",
	"pp-plan-summary-belt",
	"pp-plan-summary-label",
	"pp-package-work",
	"pp-package-work-label",
	"pp-plan-actions",
	"pp-kpi-currency-context",
	"pp-control-bar",
	"pp-tab-my-work",
	"pp-tab-all",
	"pp-tab-approved",
	"pp-tab-ready",
	"pp-package-search",
	"pp-package-list",
	"pp-detail-panel",
	"pp-header-cta",
	"pp-new-plan-button",
	"pp-new-package-button",
	"pp-template-selector",
	"pp-template-preview",
	"pp-template-apply",
	"pp-action-apply-template",
	"pp-action-approve",
	"pp-action-submit",
	"pp-action-mark-ready",
	"pp-action-complete-package",
	"pp-action-release-to-tender",
	"pp-detail-release-blocked-hint",
	"pp-action-return",
	"pp-action-reject",
	"pp-action-edit",
	"pp-action-add-demand-lines",
	"pp-action-remove-demand-line",
	"pp-demand-lines-empty",
	"pp-demand-lines-empty-add",
	"pp-detail-title",
	"pp-detail-plan-status",
	"pp-detail-package-status",
	"pp-detail-template",
	"pp-detail-method",
	"pp-detail-section-definition",
	"pp-detail-estimated-value",
	"pp-detail-demand-lines",
	"pp-detail-workflow",
	"pp-detail-risk-profile",
	"pp-detail-kpi-profile",
	"pp-detail-decision-criteria",
	"pp-detail-vendor-management",
	"pp-builder-page",
	"pp-builder-section-demand-lines",
	"pp-builder-save",
	"pp-builder-submit",
	"pp-landing-blocked",
)


class TestProcurementPlanningTestIdsG2(UnitTestCase):
	def test_g2_required_testids_in_workspace_and_builder_js(self) -> None:
		js_paths = [
			_js("js", "procurement_planning_workspace.js"),
			_js("js", "procurement_package.js"),
			_js("js", "pp_template_selector.js"),
		]
		merged = ""
		for p in js_paths:
			if not p.exists():
				raise self.failureException(f"missing {p}")
			merged += p.read_text(encoding="utf-8", errors="replace")
		for tid in REQUIRED_STABLE:
			# In-template `data-testid="…"`, DOM setters, jQuery `.attr(...)`, or explicit constants.
			if f'data-testid="{tid}"' in merged or f'setAttribute("data-testid", "{tid}")' in merged:
				continue
			if f"setAttribute('data-testid', '{tid}')" in merged:
				continue
			if f'.attr("data-testid", "{tid}")' in merged:
				continue
			if f'"{tid}"' in merged:
				continue
			self.fail(f"Missing data-testid hook {tid!r} (8. §6, G2).")
		landing = _pkg_root() / "procurement_planning" / "api" / "landing.py"
		landing_text = landing.read_text(encoding="utf-8", errors="replace")
		for tid in KPI_TESTIDS:
			self.assertIn(f'"{tid}"', landing_text, f"KPI testid {tid!r} missing in landing API (G2).")
		# dynamic row + queue
		self.assertIn("pp-row-", merged)
		self.assertIn("pp-queue-", merged)


def _js(*p: str) -> Path:
	return _app_public(*p)
