# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Load demo platform seed (PE cleanup → purge → stable → actionable)."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_core.seeds.demo_platform_seed.actionable import seed_actionable_stages
from kentender_core.seeds.demo_platform_seed.clear import clear_demo_platform
from kentender_core.seeds.demo_platform_seed.constants import (
	DEFAULT_PLANNING_CHECKPOINT,
	PACK_NAME,
	PACK_TITLE,
)
from kentender_core.seeds.demo_platform_seed.pe_cleanup import cleanup_procuring_entities
from kentender_core.seeds.stable_platform_seed.load import load_stable_platform_seed
from kentender_core.seeds.stable_platform_seed.validate import validate_stable_platform_seed


def load_demo_platform_seed(
	*,
	reset: bool = True,
	planning_checkpoint: str = DEFAULT_PLANNING_CHECKPOINT,
	import_it_std: bool = True,
) -> dict[str, Any]:
	"""Full demo platform load. Prefer reset=True for a clean demo site."""
	frappe.set_user("Administrator")
	result: dict[str, Any] = {
		"pack": PACK_NAME,
		"title": PACK_TITLE,
		"ok": False,
	}

	# PE cleanup first so preferred entities exist even if later steps fail mid-way
	result["pe_cleanup"] = cleanup_procuring_entities()

	if reset:
		result["cleared"] = clear_demo_platform(clear_stable=True, clear_it_std=False)
		# Re-ensure PEs after purge (stable clear may remove departments but not PE-MOH)
		result["pe_cleanup_post_clear"] = cleanup_procuring_entities()

	stable = load_stable_platform_seed(
		reset=False,
		planning_checkpoint=planning_checkpoint,
		import_it_std=import_it_std,
		include_it_supplement=True,
		purge_non_master=False,
	)
	result["stable"] = stable
	if not stable.get("ok"):
		result["message"] = "Stable platform load failed."
		frappe.db.commit()
		return result

	result["stable_validation"] = validate_stable_platform_seed(
		planning_checkpoint=planning_checkpoint,
		expect_it_std=import_it_std,
		expect_it_supplement=True,
	)

	try:
		from kentender_procurement.tender_configurations.electronic_std_templates.validator import (
			load_ppra_it_std_v1_approval,
		)

		approval = load_ppra_it_std_v1_approval()
		result["electronic_std_template"] = {
			"status": (approval or {}).get("status"),
			"template_id": (approval or {}).get("template_id"),
		}
	except Exception as exc:  # noqa: BLE001
		result["electronic_std_template"] = {"error": str(exc)}

	result["actionable"] = seed_actionable_stages()
	# Final PE pass: rehome lean/journey PE codes that actionable might not create
	result["pe_cleanup_final"] = cleanup_procuring_entities()

	from kentender_core.seeds.demo_platform_seed.validate import validate_demo_platform_seed

	result["validation"] = validate_demo_platform_seed()
	result["ok"] = bool(result["validation"].get("ok"))
	frappe.db.commit()
	return result
