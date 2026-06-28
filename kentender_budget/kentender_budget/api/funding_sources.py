# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""Funding Source distribution endpoint.

Returns portfolio-wide allocation totals grouped by funding source type,
with percentage share for each bucket.
"""
from __future__ import annotations

import frappe


@frappe.whitelist()
def get_funding_source_distribution() -> dict:
	"""Return allocation breakdown by funding source type.

	Response shape::

	    {
	      "total": 70_000_000.0,
	      "segments": [
	        {"source_type": "Exchequer", "total": 49_000_000.0, "pct": 70.0},
	        {"source_type": "Donor",     "total": 14_000_000.0, "pct": 20.0},
	        ...
	      ]
	    }

	Only active Budget Lines (``is_active = 1``) are included.  Lines with no
	``funding_source`` are bucketed as ``"Unclassified"``.
	"""
	rows = frappe.db.sql(
		"""
		SELECT
		    COALESCE(fs.source_type, 'Unclassified') AS source_type,
		    SUM(bl.amount_allocated)                  AS total
		FROM      `tabBudget Line`    bl
		LEFT JOIN `tabFunding Source` fs ON fs.name = bl.funding_source
		WHERE bl.is_active = 1
		GROUP BY COALESCE(fs.source_type, 'Unclassified')
		ORDER BY total DESC
		""",
		as_dict=True,
	)

	grand_total = sum(float(r["total"] or 0) for r in rows)

	segments = []
	for r in rows:
		amount = float(r["total"] or 0)
		pct = round((amount / grand_total) * 100, 1) if grand_total else 0.0
		segments.append({
			"source_type": r["source_type"] or "Unclassified",
			"total": amount,
			"pct": pct,
		})

	# Normalise rounding so percentages always sum to exactly 100.0
	if segments and grand_total:
		diff = round(100.0 - sum(s["pct"] for s in segments), 1)
		if diff:
			segments[0]["pct"] = round(segments[0]["pct"] + diff, 1)

	return {"total": grand_total, "segments": segments}
