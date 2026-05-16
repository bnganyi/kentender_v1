# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R2-004 — WORKS master strategy seed (spec §8). Public ``bench execute`` entry.

Run::

	bench --site kentender.midas.com execute \\
	  kentender_strategy.seeds.seed_works_master_strategy_hierarchy.run

To attach **your** Desk user to the seeded procuring entity (so Strategy lists and the
workspace landing API return rows), pass ``sync_scope_user_email``::

	bench --site kentender.midas.com execute \\
	  kentender_strategy.seeds.seed_works_master_strategy_hierarchy.run \\
	  --kwargs '{"sync_scope_user_email": "strategy.manager@example.com"}'

Prerequisite: **Procuring Entity** ``PE-MOH`` or ``MOH`` (LV-R2-001-03).
"""

from __future__ import annotations

from typing import Any

from kentender_core.seeds._common import ensure_user_permission
from kentender_strategy.seeds.works_master_strategy_hierarchy import (
	desk_visibility,
	upsert_works_master_strategy_hierarchy,
)


def run(sync_scope_user_email: str | None = None) -> dict[str, Any]:
	"""Upsert STRAT / PROG / OBJ / TGT per WORKS master seed spec §8.

	:param sync_scope_user_email: If set, ensure a User Permission (Procuring Entity) for this user
		on the procuring entity used by the seeded plan (dev/UAT convenience for Desk visibility).
	"""
	out: dict[str, Any] = upsert_works_master_strategy_hierarchy()
	if out.get("ok") and out.get("procuring_entity"):
		out["desk_visibility"] = desk_visibility(str(out["procuring_entity"]))
	if out.get("ok") and sync_scope_user_email and str(sync_scope_user_email).strip():
		email = str(sync_scope_user_email).strip()
		ensure_user_permission(email, str(out["procuring_entity"]))
		out["user_permission_synced_for"] = email
	return out
