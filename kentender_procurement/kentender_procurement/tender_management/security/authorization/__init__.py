# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Authorization decision engine, scope, state, negative rules, denial codes (SEC-0200–SEC-0330)."""

from __future__ import annotations

from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	ACTION_AUTHORIZATION_REGISTRY,
	ActionAuthorizationSpec,
	registered_action_codes,
	spec_for_action,
	tm2_doc9_section_74_action_codes,
)
from kentender_procurement.tender_management.security.authorization.decision_engine import (
	AuthorizationDecisionEngine,
	AuthorizationEvaluationAllowed,
	AuthorizationEvaluationDenied,
)
from kentender_procurement.tender_management.security.authorization.object_scope import (
	ObjectScopeOutcome,
	ObjectScopeService,
)
from kentender_procurement.tender_management.security.authorization.state_authorization import (
	StateAuthorizationOutcome,
	StateAuthorizationService,
)
from kentender_procurement.tender_management.security.authorization.negative_permissions import (
	NegativePermissionOutcome,
	NegativePermissionService,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import (
	DenialCode,
	EXTENSION_DENIAL_CODES,
	PACK_SEC_0200_CODES,
	PACK_TM2_DOC9_SECTION_75_DENIAL_CODES,
	StandardDenialPayload,
	all_denial_code_values,
	build_denial,
	is_known_denial_code,
)

__all__ = (
	"ACTION_AUTHORIZATION_REGISTRY",
	"ActionAuthorizationSpec",
	"AuthorizationDecisionEngine",
	"AuthorizationEvaluationAllowed",
	"AuthorizationEvaluationDenied",
	"ObjectScopeOutcome",
	"ObjectScopeService",
	"StateAuthorizationOutcome",
	"StateAuthorizationService",
	"NegativePermissionOutcome",
	"NegativePermissionService",
	"DenialCode",
	"EXTENSION_DENIAL_CODES",
	"PACK_SEC_0200_CODES",
	"PACK_TM2_DOC9_SECTION_75_DENIAL_CODES",
	"StandardDenialPayload",
	"all_denial_code_values",
	"build_denial",
	"is_known_denial_code",
	"registered_action_codes",
	"spec_for_action",
	"tm2_doc9_section_74_action_codes",
)
