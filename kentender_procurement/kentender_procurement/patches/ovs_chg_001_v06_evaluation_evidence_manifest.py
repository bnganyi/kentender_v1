# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Give every report version delivered before 4 October 2026 an evidence
manifest (OVS-CHG-001 v0.6 §7; plan D16; owner approval 4 Oct 2026,
"OVS6-0213: Yes").

A version delivered before manifests existed names no evaluated bid version
and no submitted document. This rebuilds the manifest from the case's
insert-only rows as they stood when the version was frozen, and labels it
"Reconstructed after delivery" so it is never mistaken for one written at
signing. A version that already has a manifest is left alone, so the patch is
safe to run again. A package that cannot be read now leaves that version
without a manifest (its bid-level read stays Not found) and is logged; the
patch never fails the migration."""

from __future__ import annotations

import frappe


def execute():
	if not frappe.db.exists("DocType", "Evaluation Report Delivery") or not frappe.db.has_column("Evaluation Report Version", "evidence_manifest_json"):
		return
	from kentender_procurement.bid_evaluation.services import evidence_manifest

	done = skipped = 0
	for name in sorted(set(frappe.get_all("Evaluation Report Delivery", filters={"status": "Delivered"}, pluck="report_version"))):
		try:
			if evidence_manifest.backfill(name):
				done += 1
		except Exception:
			skipped += 1
			frappe.log_error(title=f"OVS evidence manifest backfill skipped {name}")
	frappe.db.commit()
	if done or skipped:
		print(f"OVS evidence manifest backfill: {done} written, {skipped} skipped")
