# Copyright (c) 2026, Midas and contributors
# License: MIT. See LICENSE

import os

import frappe
from frappe.modules.import_file import import_file_by_path


def after_migrate():
	"""Sync Budget Management Desk assets from module JSON (workspace, sidebar, desktop icon)."""
	_sync_budget_management_workspace()
	_sync_budget_workspace_sidebar()
	_sync_budget_desktop_icon()


def _sync_budget_management_workspace():
	path = os.path.join(
		frappe.get_app_path("kentender_budget"),
		"kentender_budget",
		"workspace",
		"budget_management",
		"budget_management.json",
	)
	if os.path.exists(path):
		import_file_by_path(path, force=True)


def _sync_budget_workspace_sidebar():
	path = os.path.join(
		frappe.get_app_path("kentender_budget"),
		"kentender_budget",
		"workspace_sidebar",
		"budget.json",
	)
	if os.path.exists(path):
		import_file_by_path(path, force=True)


def _sync_budget_desktop_icon():
	path = os.path.join(
		frappe.get_app_path("kentender_budget"),
		"kentender_budget",
		"desktop_icon",
		"budget.json",
	)
	if os.path.exists(path):
		import_file_by_path(path, force=True)
