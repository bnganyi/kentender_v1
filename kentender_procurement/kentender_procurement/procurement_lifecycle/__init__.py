# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Procurement lifecycle domain primitives (journey / handoff navigation layer — ADR-PLC-002)."""

from kentender_procurement.procurement_lifecycle.journey_status_category import (
	JOURNEY_STATUS_CATEGORY_VALUES,
	ProcurementJourneyStatusCategory,
	is_valid_journey_status_category,
)
from kentender_procurement.procurement_lifecycle.constants import (
	JOURNEY_STEP_CONFIG,
	JOURNEY_STEP_CONFIG_VERSION,
	JOURNEY_STEP_KEYS_IN_ORDER,
	JourneyStepConfig,
	get_journey_step_config,
	iter_journey_step_configs,
)
from kentender_procurement.procurement_lifecycle.journey_status_mapping import (
	map_raw_to_journey_status_category,
)
from kentender_procurement.procurement_lifecycle.evidence_links import (
	EVIDENCE_LINKS_JSON_STORAGE_DECISION,
	EVIDENCE_LINKS_MAX_LINKS,
	EVIDENCE_LINKS_MAX_SERIALIZED_BYTES,
	EVIDENCE_LINK_FIELD_MAX_CHARS,
	EVIDENCE_LINK_REQUIRED_KEYS,
	EVIDENCE_LINK_VISIBILITY_VALUES,
	parse_validate_and_normalize_evidence_links,
)
from kentender_procurement.procurement_lifecycle.technical_refs import (
	TECHNICAL_REFS_JSON_MAX_SERIALIZED_BYTES,
	parse_validate_technical_refs_json,
)
from kentender_procurement.procurement_lifecycle.handoff_card_transitions import (
	ALLOWED_HANDOFF_STATUS_TRANSITIONS,
	HandoffCardStatus,
	allowed_next_handoff_statuses,
	assert_transition_graph_well_formed,
	assert_valid_handoff_status_transition,
	can_handoff_status_transition,
)
from kentender_procurement.procurement_lifecycle.handoff_card_status import (
	HANDOFF_CARD_STATUS_OPTIONS,
	HANDOFF_CARD_STATUS_VALUES,
	is_valid_handoff_card_status,
)
from kentender_procurement.procurement_lifecycle.works_seed_step_contract import (
	WORKS_SEED_TENDER_PUBLISHED_STEP_KEYS_IN_ORDER,
)
from kentender_procurement.procurement_lifecycle.journey_object_lookup import (
	JOURNEY_OBJECT_LOOKUP_REF_FIELDS,
	get_procurement_journey_by_object,
	journey_lookup_sql_explanation,
	ref_field_for_object_type,
	resolve_journey_code_for_object,
)
from kentender_procurement.procurement_lifecycle.source_module_authority import (
	AUTHORITATIVE_SOURCE_DOCTYPES,
	handoff_fields_for_stale_mark,
	recommend_handoff_stale_for_source_fingerprint_drift,
)

__all__ = [
	"ALLOWED_HANDOFF_STATUS_TRANSITIONS",
	"AUTHORITATIVE_SOURCE_DOCTYPES",
	"TECHNICAL_REFS_JSON_MAX_SERIALIZED_BYTES",
	"EVIDENCE_LINKS_JSON_STORAGE_DECISION",
	"EVIDENCE_LINKS_MAX_LINKS",
	"EVIDENCE_LINKS_MAX_SERIALIZED_BYTES",
	"EVIDENCE_LINK_FIELD_MAX_CHARS",
	"EVIDENCE_LINK_REQUIRED_KEYS",
	"EVIDENCE_LINK_VISIBILITY_VALUES",
	"HANDOFF_CARD_STATUS_OPTIONS",
	"HANDOFF_CARD_STATUS_VALUES",
	"HandoffCardStatus",
	"JOURNEY_STATUS_CATEGORY_VALUES",
	"JOURNEY_STEP_CONFIG",
	"JOURNEY_STEP_CONFIG_VERSION",
	"JOURNEY_OBJECT_LOOKUP_REF_FIELDS",
	"JOURNEY_STEP_KEYS_IN_ORDER",
	"JourneyStepConfig",
	"ProcurementJourneyStatusCategory",
	"WORKS_SEED_TENDER_PUBLISHED_STEP_KEYS_IN_ORDER",
	"allowed_next_handoff_statuses",
	"assert_transition_graph_well_formed",
	"assert_valid_handoff_status_transition",
	"can_handoff_status_transition",
	"get_journey_step_config",
	"get_procurement_journey_by_object",
	"handoff_fields_for_stale_mark",
	"journey_lookup_sql_explanation",
	"is_valid_handoff_card_status",
	"is_valid_journey_status_category",
	"iter_journey_step_configs",
	"map_raw_to_journey_status_category",
	"parse_validate_and_normalize_evidence_links",
	"parse_validate_technical_refs_json",
	"ref_field_for_object_type",
	"recommend_handoff_stale_for_source_fingerprint_drift",
	"resolve_journey_code_for_object",
]
