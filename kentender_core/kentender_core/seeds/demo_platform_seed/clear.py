# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Purge conflicting demo/test stacks before demo platform load."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_core.seeds.demo_platform_seed.constants import DEMO_PREFIX
from kentender_core.seeds.stable_platform_seed.clear import clear_stable_platform_seed


def _delete_by_ref_prefix(doctype: str, field: str, prefix: str) -> int:
	if not frappe.db.exists("DocType", doctype):
		return 0
	names = frappe.get_all(doctype, filters={field: ("like", f"{prefix}%")}, pluck="name")
	for name in names:
		frappe.delete_doc(doctype, name, force=True, ignore_permissions=True, delete_permanently=True)
	return len(names)


def clear_demo_prefixed_rows() -> dict[str, int]:
	"""Remove prior DEMO-MOH-2026-* rows."""
	counts: dict[str, int] = {}
	for dt, field in (
		("Electronic Bid Submission", "configuration_ref"),
		("IT Bid Opening Record", "publication"),
		("IT Tender Publication Record", "configuration_ref"),
		("Confirmed Tender Document Package", "configuration_ref"),
		("Tender Configuration", "configuration_ref"),
		("Procurement Package", "package_code"),
		("Demand", "demand_id"),
	):
		# Opening record keyed by publication name — clear via pubs above
		if dt == "IT Bid Opening Record":
			continue
		counts[dt] = _delete_by_ref_prefix(dt, field, DEMO_PREFIX)
	# Opening records left dangling
	if frappe.db.exists("DocType", "IT Bid Opening Record"):
		orphans = frappe.get_all("IT Bid Opening Record", pluck="name")
		for name in orphans:
			pub = frappe.db.get_value("IT Bid Opening Record", name, "publication")
			if not pub or not frappe.db.exists("IT Tender Publication Record", pub):
				frappe.delete_doc(
					"IT Bid Opening Record", name, force=True, ignore_permissions=True
				)
	return counts


def clear_cfg_noise() -> dict[str, Any]:
	"""Clear known CFG/pub demo stacks that fight the linked demo narrative."""
	out: dict[str, Any] = {}
	try:
		from kentender_procurement.tender_configurations.seed.ui00_seed import clear_ui00_seed

		clear_ui00_seed()
		out["ui00"] = True
	except Exception as exc:  # noqa: BLE001 — seed orchestrator must continue
		out["ui00"] = str(exc)
	try:
		from kentender_procurement.tender_configurations.seed.ui01_mockup_seed import (
			clear_ui01_mockup_seed,
		)

		clear_ui01_mockup_seed()
		out["ui01"] = True
	except Exception as exc:  # noqa: BLE001
		out["ui01"] = str(exc)

	# Journey / lean / e1 / mock prefixes
	for prefix in (
		"TCFG-SEED",
		"TCFG-MOCK",
		"TCFG-LEAN",
		"TCFG-E1",
		"TCFG-PP",
		"TCFG-JOURNEY",
		"BWMF-CAL",
		"DIA-MOH-2026-",
	):
		key = prefix.rstrip("%").rstrip("-")
		out[key] = {
			"configs": _delete_by_ref_prefix("Tender Configuration", "configuration_ref", prefix),
			"packages": _delete_by_ref_prefix("Procurement Package", "package_code", prefix),
			"pubs": _delete_by_ref_prefix(
				"IT Tender Publication Record", "configuration_ref", prefix
			),
			"demands": _delete_by_ref_prefix("Demand", "demand_id", prefix)
			if prefix.startswith("DIA")
			else 0,
		}
	return out


def clear_demo_platform(*, clear_stable: bool = True, clear_it_std: bool = False) -> dict[str, Any]:
	"""Full purge for demo platform reset (does not remove ACTIVE IT STD by default)."""
	frappe.set_user("Administrator")
	result: dict[str, Any] = {
		"demo_prefixed": clear_demo_prefixed_rows(),
		"cfg_noise": clear_cfg_noise(),
	}
	if clear_stable:
		result["stable"] = clear_stable_platform_seed(
			purge_non_master=True,
			clear_it_std=clear_it_std,
			skip_guard=False,
		)
	frappe.db.commit()
	return result
