# Copyright (c) 2026, KenTender and contributors
"""Shared fixture helpers for the STR-CHG-001 suites.

STR-BR-010 / §12.3: a Fiscal Year target must fall within its plan period,
so a suite whose fixture plans live in the far future (2040–2045, chosen so
they never overlap the canonical §14.3 plan's 2023–2028 authority) needs a
Fiscal Year in that window. ERPNext Fiscal Year rows carry only a date
range; one shared, idempotently-created year is harmless to leave behind
and is deliberately not deleted (a parallel suite may be using it).
"""

from __future__ import annotations

import frappe


def ensure_fiscal_year(start_year: int) -> str:
	name = f"{start_year}-{start_year + 1}"
	if not frappe.db.exists("Fiscal Year", name):
		frappe.get_doc(
			{
				"doctype": "Fiscal Year",
				"year": name,
				"year_start_date": f"{start_year}-07-01",
				"year_end_date": f"{start_year + 1}-06-30",
			}
		).insert(ignore_permissions=True)
	return name


def pin_review_date(testcase, date: str = "2099-12-31") -> None:
	"""v1.8 §5.1 — approval is permitted only when the version can become
	effective immediately, judged against the site date. Fixture plans live
	far in the future so they never overlap the canonical §14.3 plan, so a
	suite that approves them pins the review instant the way §14.4 pins its
	own clocks. Restored automatically at the end of the test."""
	from unittest.mock import patch

	patcher = patch(
		"kentender_strategy.services.strategy_readiness.today",
		return_value=frappe.utils.getdate(date),
	)
	patcher.start()
	testcase.addCleanup(patcher.stop)


def purge_record(doctype: str, name: str) -> None:
	"""Test clean-up delete. Strategy records and the records other apps guard
	with the command-only write guard (a User Responsibility Assignment, an Audit
	Event) are deleted through the guard's maintenance path, never a standing
	exemption; anything else is deleted as before."""
	from contextlib import nullcontext

	from kentender_core.services.command_write_guard import maintenance_write

	if not frappe.db.exists(doctype, name):
		return
	family = getattr(frappe.get_doc(doctype, name), "command_write_family", "")
	with maintenance_write(family, reason="Strategy test clean-up") if family else nullcontext():
		frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)


def open_strategy_write_window(testcase) -> None:
	"""Legacy suites build their fixtures with direct inserts. They run inside the
	guard's maintenance window for the whole test (closed after tearDown), which
	is a test-site-only path, never a standing exemption. Suites that prove the
	guard itself (test_str_aud_remediation) do not use it."""
	from kentender_core.services.command_write_guard import maintenance_write

	window = maintenance_write("Strategy", reason="Strategy test fixtures")
	window.__enter__()
	testcase.addCleanup(window.__exit__, None, None, None)
