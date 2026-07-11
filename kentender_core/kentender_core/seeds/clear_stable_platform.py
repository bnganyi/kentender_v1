# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Clear stable platform seed without reloading.

Usage::

    bench --site kentender.midas.com execute kentender_core.seeds.clear_stable_platform.run

    bench --site kentender.midas.com execute kentender_core.seeds.clear_stable_platform.run \\
        --kwargs '{"purge_non_master": false, "clear_it_std": false}'
"""

from __future__ import annotations

import json

import frappe

from kentender_core.seeds.stable_platform_seed.clear import clear_stable_platform_seed


def run(**kwargs: object) -> None:
	purge_non_master = bool(kwargs.get("purge_non_master", True))
	clear_it_std = bool(kwargs.get("clear_it_std", True))
	result = clear_stable_platform_seed(
		purge_non_master=purge_non_master,
		clear_it_std=clear_it_std,
		skip_guard=bool(frappe.in_test),
	)
	frappe.db.commit()
	print(json.dumps(result, indent=2, default=str))
