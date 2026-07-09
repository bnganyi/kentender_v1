# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Seed read-only STD Usage Binding rows from tender_binding_smoke_tests.json."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.std_engine.package_import.record_mapper import (
	PackageContext,
	map_usage_binding_record,
)


def seed_usage_bindings_from_smoke_tests(
	ctx: PackageContext,
	smoke_payload: dict[str, Any] | None,
	stats: dict[str, int],
) -> None:
	records = (smoke_payload or {}).get("records") or []
	committed = 0
	for record in records:
		doc_dict = map_usage_binding_record(record, ctx)
		binding_key = doc_dict["binding_key"]
		if frappe.db.exists("STD Usage Binding", binding_key):
			continue
		frappe.get_doc(doc_dict).insert(ignore_permissions=True)
		committed += 1
	stats["usageBindings"] = committed
