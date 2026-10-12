# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 Phase 1: the legacy bid-submission surfaces are retired.

Guards the removal register in `docs/mvp-1-r1/12_bid_submission/reconciliation/
legacy_inventory.md` (plan BDS-CHG-001 v0.8 Phase 1, owner decision OD-F; spec
BDS01-IMP-090, BDS07-IMP-010): no retired route, page, asset, service, test,
seed, make target or DocType survives, and no remaining module imports one.
The retirement patch itself is the only code allowed to name the retired
DocTypes. The module that carried the bid slice has since been retired whole
(see `kentender_procurement/tests/test_retired_tender_configurations_gone.py`).
"""

from __future__ import annotations

import json
import os
import re

import frappe
from frappe.tests import IntegrationTestCase

APP_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # kentender_procurement/kentender_procurement
REPO_DIR = os.path.dirname(os.path.dirname(APP_DIR))  # apps/kentender_v1

RETIRED_DOCTYPES = ("Electronic Bid Submission", "IT Bid Opening Record", "Electronic Bid Audit Event")
RETIRED_PAGES = ("bid-submissions", "it-electronic-bidder-workspace", "published-tender-overview")

RETIRED_PATHS = (
	"www/tenders",
	"www/supplier",
	"kentender_procurement/page/bid_submissions",
	"kentender_procurement/page/published_tender_overview",
	"page/it_electronic_bidder_workspace",
	"public/js/electronic_bid",
	"templates/includes/kt_bidder_portal_nav.html",
	"templates/includes/kt_bidder_workspace_sidebar.html",
	"templates/includes/qualification",
	"templates/includes/technical_proposal",
	"bid_submission_opening",
	*(f"public/js/{name}.js" for name in (
		"bid_submissions_page", "it_electronic_bidder_workspace_page", "published_tender_overview_page",
		"kt_bidder_countdown", "final_submission_web", "price_schedule_web", "published_tender_overview_web",
		"qualification_and_capability_web", "requirement_matrix_web", "technical_proposal_web",
		"tender_documents_addenda_web", "requirements_compliance_review",
	)),
	*(f"public/css/{name}.css" for name in (
		"bid_submissions_page", "bidder_portal_forms", "confidential_business_questionnaire_web",
		"documents_addenda_web", "final_submission_web", "form_of_tender_web", "preliminary_requirements_web",
		"price_schedule_web", "qualification_and_capability_web", "requirement_matrix_web",
		"statutory_declarations_web", "submission_checklist_web", "technical_proposal_web", "tender_security_web",
	)),
)
RETIRED_REPO_PATHS = ("tests/ui/smoke/bid-submissions", "tests/ui/smoke/bidder-workspace")
RETIRED_MAKE_TARGETS = (
	"bid-submissions-domain-gate", "ui-bid-submissions-gate", "bw-domain-gate", "bw-a0-domain-gate",
	"ui-bidder-a0-gate", "ui-bidder-a1-gate", "bw-a2-domain-gate", "ui-bidder-a2-gate", "bw-a3-domain-gate",
	"ui-bidder-a3-gate", "bw-x100-domain-gate", "bw-s300-domain-gate", "ui-bidder-s300-cbq-gate",
	"bw-fot-domain-gate", "ui-bidder-fot-gate", "bw-statutory-domain-gate", "ui-bidder-statutory-gate",
	"bw-tender-security-domain-gate", "ui-bidder-tender-security-gate", "bw-preliminary-domain-gate",
	"ui-bidder-preliminary-gate", "bw-qualification-domain-gate", "ui-bidder-qualification-gate",
	"bw-technical-proposal-domain-gate", "ui-bidder-technical-proposal-gate",
	"bw-requirements-compliance-domain-gate", "ui-bidder-requirements-compliance-gate",
	"bw-price-schedule-domain-gate", "ui-bidder-price-schedule-gate", "bw-final-submission-domain-gate",
	"bw-final-submission-stitch-contract-gate", "ui-bidder-final-submission-gate", "bw-a4-domain-gate",
	"ui-bidder-a4-gate", "seed-demand-to-bidder-journey",
)
PATCH_MODULE = "kentender_procurement/patches/bds_chg_001_v08_retire_bid_slice.py"

SCAN_ROOTS = ("kentender_core", "kentender_strategy", "kentender_budget", "kentender_procurement", "kentender_suppliers")
SKIP_DIRS = {"__pycache__", "node_modules", "archive", "retired", "dist"}


def _py_files():
	for app in SCAN_ROOTS:
		base = os.path.join(REPO_DIR, app)
		for dirpath, dirnames, filenames in os.walk(base):
			dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
			for name in filenames:
				if name.endswith(".py"):
					yield os.path.join(dirpath, name)


class TestLegacyBidSliceRetired(IntegrationTestCase):
	def test_no_retired_file_or_folder_survives(self):
		present = [p for p in RETIRED_PATHS if os.path.exists(os.path.join(APP_DIR, p))]
		present += [p for p in RETIRED_REPO_PATHS if os.path.exists(os.path.join(REPO_DIR, p))]
		self.assertEqual(present, [])

	def test_hooks_carry_no_legacy_bid_route_page_or_global_script(self):
		from kentender_procurement import hooks

		legacy_routes = [
			r for r in hooks.website_route_rules
			if r["from_route"].startswith(("/tenders/<publication_ref>", "/supplier/tenders"))
		]
		self.assertEqual(legacy_routes, [])
		self.assertFalse([s for s in hooks.app_include_js if "bidder_workspace_renderer" in s])
		self.assertFalse([p for p in RETIRED_PAGES if p in hooks.page_js])

	def test_only_the_retirement_patch_names_the_retired_doctypes(self):
		pattern = re.compile("|".join(re.escape(d) for d in RETIRED_DOCTYPES))
		offenders = []
		for path in _py_files():
			rel = os.path.relpath(path, REPO_DIR)
			if rel.endswith(PATCH_MODULE) or rel.endswith("bid_submission/tests/test_legacy_retirement.py"):
				continue
			if pattern.search(open(path, encoding="utf-8").read()):
				offenders.append(rel)
		self.assertEqual(offenders, [])

	def test_no_code_reads_a_retired_asset_or_page_path(self):
		# Static layout guards read retired files by path, which an import scan
		# cannot see (found 26 Sep 2026: six bidder layout tests did this).
		basenames = [os.path.basename(p) for p in RETIRED_PATHS if p.startswith(("public/js/", "public/css/"))]
		pattern = re.compile("|".join(re.escape(b) for b in basenames) + r"|www/tenders|www/supplier|\"www\" / \"tenders\"")
		offenders = []
		for app in SCAN_ROOTS:
			base = os.path.join(REPO_DIR, app)
			for dirpath, dirnames, filenames in os.walk(base):
				dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
				for name in filenames:
					if not name.endswith((".py", ".js", ".vue", ".ts", ".html")):
						continue
					path = os.path.join(dirpath, name)
					rel = os.path.relpath(path, REPO_DIR)
					if rel.endswith("bid_submission/tests/test_legacy_retirement.py"):
						continue
					if pattern.search(open(path, encoding="utf-8", errors="ignore").read()):
						offenders.append(rel)
		self.assertEqual(offenders, [])

	def test_retired_doctypes_pages_and_tables_are_gone_from_the_site(self):
		for doctype in RETIRED_DOCTYPES:
			self.assertFalse(frappe.db.exists("DocType", doctype), doctype)
			self.assertFalse(frappe.db.table_exists(doctype), doctype)
		for page in RETIRED_PAGES:
			self.assertFalse(frappe.db.exists("Page", page), page)

	def test_navigation_and_make_targets_no_longer_point_at_the_legacy_bid_screens(self):
		sidebar = json.load(open(os.path.join(APP_DIR, "workspace_sidebar", "procurement.json"), encoding="utf-8"))
		self.assertNotIn("bid-submissions", json.dumps(sidebar))
		makefile = open(os.path.join(REPO_DIR, "Makefile"), encoding="utf-8").read()
		left = [t for t in RETIRED_MAKE_TARGETS if re.search(rf"^{re.escape(t)}:", makefile, re.M)]
		self.assertEqual(left, [])
		registry = open(os.path.join(REPO_DIR, "kentender_core", "kentender_core", "public", "js", "kt_cl_surface_registry.js"), encoding="utf-8").read()
		self.assertNotIn("published-tender-overview", registry)
