# Copyright (c) 2026, KenTender and contributors
"""Log STD Module POC retirement — no DocType or data deletion."""

from __future__ import annotations

import frappe


def execute() -> None:
	frappe.logger("kentender_procurement").info(
		"STD Module POC retired (2026-07). Active UI/API archived under "
		"apps/kentender_v1/archive/std-module-poc-retired-2026-07/. "
		"Database rows preserved; placeholder page: std-module-retired."
	)
