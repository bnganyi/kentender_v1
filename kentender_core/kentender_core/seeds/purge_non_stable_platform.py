# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Purge dev/UAT rows outside the stable platform seed registry (Works + IT).

Usage::

    bench --site kentender.midas.com execute kentender_core.seeds.purge_non_stable_platform.run

Dry run::

    bench --site kentender.midas.com execute kentender_core.seeds.purge_non_stable_platform.run \\
        --kwargs '{"dry_run": true}'
"""

from __future__ import annotations

import json

import frappe

from kentender_core.seeds.stable_platform_seed.purge import purge_non_stable_platform_seed


def run(**kwargs: object) -> None:
	dry_run = bool(kwargs.get("dry_run", False))
	result = purge_non_stable_platform_seed(dry_run=dry_run)
	frappe.db.commit()
	print(json.dumps(result, indent=2, default=str))
