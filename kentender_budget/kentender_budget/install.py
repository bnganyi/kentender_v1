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


def after_migrate():
	from kentender_budget.services.budget_authorization import ensure_budget_governance_roles

	ensure_budget_governance_roles()


def before_tests():
	from kentender_budget.services.budget_authorization import ensure_budget_governance_roles

	ensure_budget_governance_roles()
