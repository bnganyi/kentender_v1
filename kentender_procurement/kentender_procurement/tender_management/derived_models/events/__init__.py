# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Derived model audit/event helpers (DERIVED-1100)."""

from __future__ import annotations

from kentender_procurement.tender_management.derived_models.events.audit import (
	DERIVED_MODEL_ENTITY,
	DERIVED_MODEL_EVENT_ACTIONS,
	emit_derived_model_audit,
	emit_derived_model_audit_for_output,
	emit_derived_model_generation_failed,
	pack_manual_denial_event_code,
)
from kentender_procurement.tender_management.derived_models.events.codes import (
	ADDENDUM_DERIVED_MODELS_REGENERATED,
	CONTRACT_BINDING_VIOLATION_DENIED,
	DERIVED_MODEL_CONSUMED,
	DERIVED_MODEL_CONSUMPTION_DENIED,
	DERIVED_MODEL_GENERATED,
	DERIVED_MODEL_GENERATION_FAILED,
	DERIVED_MODEL_GENERATION_REQUESTED,
	DERIVED_MODEL_MARKED_STALE,
	DERIVED_MODEL_SUPERSEDED,
	MANUAL_EVALUATION_CRITERIA_DENIED,
	MANUAL_OPENING_EVALUATION_FIELD_DENIED,
	MANUAL_SUBMISSION_REQUIREMENT_DENIED,
)

__all__ = (
	"ADDENDUM_DERIVED_MODELS_REGENERATED",
	"CONTRACT_BINDING_VIOLATION_DENIED",
	"DERIVED_MODEL_CONSUMED",
	"DERIVED_MODEL_CONSUMPTION_DENIED",
	"DERIVED_MODEL_ENTITY",
	"DERIVED_MODEL_EVENT_ACTIONS",
	"DERIVED_MODEL_GENERATED",
	"DERIVED_MODEL_GENERATION_FAILED",
	"DERIVED_MODEL_GENERATION_REQUESTED",
	"DERIVED_MODEL_MARKED_STALE",
	"DERIVED_MODEL_SUPERSEDED",
	"MANUAL_EVALUATION_CRITERIA_DENIED",
	"MANUAL_OPENING_EVALUATION_FIELD_DENIED",
	"MANUAL_SUBMISSION_REQUIREMENT_DENIED",
	"emit_derived_model_audit",
	"emit_derived_model_audit_for_output",
	"emit_derived_model_generation_failed",
	"pack_manual_denial_event_code",
)
