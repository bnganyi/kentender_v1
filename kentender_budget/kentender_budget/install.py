# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Install hooks — BUD-CHG-001 v1.2. Mirrors kentender_strategy's install
posture: on the AUTH-ADR-001 native Role + User Permission engine, no
Capability Profile / Operational Scope Assignment / Workflow Routing Rule
bootstrap is needed, and Desk Page sync happens through hooks.page_js, not
a manual Page-fixture import loop. The legacy Page/Workspace fixture sync
this hook used to run was retired with the pre-v1.2 UI teardown.
"""

from __future__ import annotations


def ensure_database_guards() -> None:
	"""The database-level concurrency guards of BUD-BR-002 and AUD-BUD-004: one Active Budget Version per
	Budget, and one commitment per (contract, reservation). They were added by patches, and a fresh install
	marks every patch complete without running it, so a site installed after they landed had neither (RG-20).
	Both functions are idempotent and are also the patches' own bodies."""
	from kentender_budget.patches import (
		bud_chg_001_v1_3_phase4_active_version_unique_index as active_version_index,
		bud_chg_001_v1_12_commitment_contract_unique_per_reservation as commitment_key,
	)

	active_version_index.execute()
	commitment_key.execute()


def after_install():
	ensure_database_guards()


def after_migrate():
	from kentender_budget.services.budget_authorization import ensure_budget_governance_roles

	ensure_budget_governance_roles()
	ensure_database_guards()


def before_tests():
	from kentender_budget.services.budget_authorization import ensure_budget_governance_roles

	ensure_budget_governance_roles()
