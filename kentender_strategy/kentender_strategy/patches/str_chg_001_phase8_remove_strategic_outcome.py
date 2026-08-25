# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 v1.4 Phase 8 — remove Strategic Outcome from the Strategy Node
hierarchy (v1.4 §18.1).

Any Performance Indicator currently attached to a Strategic Outcome is
reattached to that Outcome's direct parent Strategic Objective, then the
Outcome is deleted. Fails loudly — does not guess another Objective — if an
Outcome's parent is not exactly one Strategic Objective, or if a reattached
Indicator would cross a plan version boundary.
"""

from __future__ import annotations

import frappe


def execute() -> None:
	outcomes = frappe.get_all(
		"Strategy Node",
		filters={"node_type": "Strategic Outcome"},
		fields=["name", "parent_node_id"],
	)

	for outcome in outcomes:
		parent = None
		if outcome.parent_node_id:
			parent = frappe.db.get_value(
				"Strategy Node",
				outcome.parent_node_id,
				["name", "node_type", "plan_version_id"],
				as_dict=True,
			)
		if not parent or parent.node_type != "Strategic Objective":
			frappe.throw(
				f"Strategic Outcome {outcome.name}'s parent is not exactly one "
				"Strategic Objective — aborting Phase 8 migration"
			)

		indicators = frappe.get_all(
			"Performance Indicator",
			filters={"measures_node_id": outcome.name},
			fields=["name", "plan_version_id"],
		)
		for indicator in indicators:
			if indicator.plan_version_id != parent.plan_version_id:
				frappe.throw(
					f"Performance Indicator {indicator.name} measuring Outcome "
					f"{outcome.name} crosses a plan version boundary from its "
					"parent Strategic Objective — aborting Phase 8 migration"
				)
			frappe.db.set_value(
				"Performance Indicator", indicator.name, "measures_node_id", parent.name
			)

		frappe.delete_doc("Strategy Node", outcome.name, force=1, ignore_permissions=True)

	frappe.db.commit()
