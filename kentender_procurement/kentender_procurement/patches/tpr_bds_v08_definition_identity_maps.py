# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 plan D3 (Tenders tracker TND12-B02): backfill the stored
identity map of every successor Tender Bid Definition frozen before
`store()` began writing it.

The map is recomputed exactly as `issue_addendum` computes it: the bound
release's own addendum-identity rules over the stored predecessor and
successor definitions (STD `classify` / `incomplete_required`). The
predecessor is the definition that was bidder-current when the addendum was
issued — the highest earlier version that has been Effective. The written
values are derived data on an immutable row, so this one-time backfill
writes them directly; nothing else about the row changes.
"""

from __future__ import annotations

import json

import frappe


def execute() -> None:
	frappe.reload_doc("tenders", "doctype", "tender_bid_definition")
	from kentender_procurement.std_templates.compiler import addenda as std_addenda
	from kentender_procurement.std_templates.services import runtime as std_runtime
	from kentender_procurement.tenders.services import digest

	rows = frappe.get_all(
		"Tender Bid Definition", filters={"addendum": ("is", "set")},
		fields=["name", "tender", "definition_version", "definition_json", "identity_map_json"], order_by="tender asc, definition_version asc", limit_page_length=0,
	)
	for row in rows:
		if row.identity_map_json:
			continue
		prior = frappe.get_all(
			"Tender Bid Definition", filters={"tender": row.tender, "definition_version": ("<", row.definition_version), "status": ("in", ("Effective", "Superseded"))},
			fields=["name", "definition_json"], order_by="definition_version desc", limit=1,
		)
		if not prior:
			continue
		successor = json.loads(row.definition_json or "{}")
		release = std_runtime.release_doc(successor["template_release_id"])
		classifications = std_addenda.classify(json.loads(prior[0].definition_json or "{}"), successor, std_runtime.installed_assets(release).addendum_rules)
		identity_map = {"classifications": classifications, "fresh_required": std_addenda.incomplete_required(successor, classifications)}
		frappe.db.set_value(
			"Tender Bid Definition", row.name,
			{"predecessor_bid_definition": prior[0].name, "identity_map_json": digest.canonical_json(identity_map), "identity_map_digest": digest.sha256_hex(identity_map)},
			update_modified=False,
		)
