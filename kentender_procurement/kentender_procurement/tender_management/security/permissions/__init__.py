# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Canonical permission catalogue and role alignment (SEC-0100 / SEC-0110)."""

from __future__ import annotations

from kentender_procurement.tender_management.security.permissions.catalog import (
	CANONICAL_PERMISSION_IDS,
	canonical_permission_definitions,
)
from kentender_procurement.tender_management.security.permissions.seed_catalog import (
	run as seed_security_permission_catalog,
	upsert_all_permissions,
)
from kentender_procurement.tender_management.security.permissions.role_matrix import (
	CANONICAL_ROLE_CODES,
	ROLE_MATRIX,
)
from kentender_procurement.tender_management.security.permissions.role_permission import (
	RolePermissionService,
)
from kentender_procurement.tender_management.security.permissions.seed_role_matrix import (
	run as seed_security_role_matrix,
	upsert_role_matrix,
)
from kentender_procurement.tender_management.security.permissions.seed_security_fixtures_0700 import (
	fixture_users,
	negative_access_cases,
	run as seed_security_fixtures_0700,
	upsert_security_seed_fixtures,
)
from kentender_procurement.tender_management.security.permissions.service import (
	PermissionService,
)

__all__ = (
	"CANONICAL_PERMISSION_IDS",
	"CANONICAL_ROLE_CODES",
	"ROLE_MATRIX",
	"PermissionService",
	"RolePermissionService",
	"canonical_permission_definitions",
	"seed_security_permission_catalog",
	"seed_security_role_matrix",
	"seed_security_fixtures_0700",
	"upsert_all_permissions",
	"upsert_role_matrix",
	"upsert_security_seed_fixtures",
	"fixture_users",
	"negative_access_cases",
)
