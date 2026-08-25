# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Install hooks — Budget Management workspace + Desk pages after migrate."""

from __future__ import annotations

import os

import frappe
from frappe.modules.import_file import import_file_by_path

_PAGES = (
	"budget_funding",
	"budget_register",
	"budget_funding_performance",
	"budget_overview",
	"budget_lines",
	"budget_funding_activity",
	"budget_revisions",
	"budget_revision_create",
	"budget_revision_review",
	"budget_downstream",
	"budget_review",
	"budget_audit",
)


def _sync_pages() -> None:
	base = os.path.join(frappe.get_app_path("kentender_budget"), "kentender_budget", "page")
	for folder in _PAGES:
		path = os.path.join(base, folder, f"{folder}.json")
		if os.path.exists(path):
			import_file_by_path(path, force=True)


def after_migrate():
	"""Ensure Budget Desk pages + Procurement rail Workspace resolve after migrate."""
	_sync_pages()

	try:
		from kentender_budget.seeds.budget_role_users import upsert_budget_role_users

		upsert_budget_role_users()
		from kentender_budget.seeds.budget_authorization_seed import upsert_budget_authorization

		upsert_budget_authorization()
	except Exception:
		frappe.log_error(title="BUD-SUP-002 budget role users seed failed")

	path = os.path.join(
		frappe.get_app_path("kentender_budget"),
		"kentender_budget",
		"workspace",
		"budget_management",
		"budget_management.json",
	)
	if os.path.exists(path):
		import_file_by_path(path, force=True)

	from kentender_budget.services.budget_workspace import ensure_budget_workspace

	ensure_budget_workspace()


def before_tests():
	from kentender_budget.seeds.budget_authorization_seed import (
		upsert_budget_authorization,
		upsert_budget_test_authorization,
	)

	upsert_budget_authorization()
	upsert_budget_test_authorization()
