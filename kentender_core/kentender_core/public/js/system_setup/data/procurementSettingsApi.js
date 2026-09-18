// PLN-CHG-001 v1.18 §10.11 (C03/C04) — thin wrappers over
// kentender_core.api.procurement_settings_api. Every rule (authority,
// validation, version supersession, immutability once referenced, audit) is
// applied server-side; this module only shapes calls.
import { frappeCall } from "../../kt_admin_shared/data/frappeCall.js";

const PREFIX = "kentender_core.api.procurement_settings_api.";

function newIdempotencyKey(prefix) {
	return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

export const procurementSettingsApi = {
	get: () => frappeCall(PREFIX + "get_procurement_settings", {}),
	addFundingSource: (label) =>
		frappeCall(PREFIX + "add_funding_source", { label, idempotency_key: newIdempotencyKey("fs") }),
	updateFundingSource: (name, { label, enabled }, expectedVersion) =>
		frappeCall(PREFIX + "update_funding_source", {
			name,
			label: label || null,
			enabled: enabled === undefined || enabled === null ? null : enabled ? 1 : 0,
			expected_version: expectedVersion || null,
		}),
	// Only offered in the UI for a source nothing references yet (row.referenced
	// === false); the server refuses a referenced one with CFG_CATALOGUE_IN_USE
	// regardless, so this is never authority, only a shortcut for the common case.
	deleteFundingSource: (name) => frappeCall(PREFIX + "delete_funding_source", { name }),
	getMethodProfile: (name) => frappeCall(PREFIX + "get_method_profile", { name }),
	registerMethodProfileVersion: (payload) =>
		frappeCall(PREFIX + "register_method_profile_version", {
			...payload,
			conditions: JSON.stringify(payload.conditions || []),
			idempotency_key: newIdempotencyKey("mpr"),
		}),
	getScheduleProfile: (name) => frappeCall(PREFIX + "get_schedule_profile", { name }),
	registerScheduleProfileVersion: (payload) =>
		frappeCall(PREFIX + "register_schedule_profile_version", {
			...payload,
			milestones: JSON.stringify(payload.milestones || []),
			idempotency_key: newIdempotencyKey("spr"),
		}),
	getRegulatoryReferenceVersion: (name) =>
		frappeCall(PREFIX + "get_regulatory_reference_version", { name }),
	listRegulatoryReferenceVersions: (referenceSet) =>
		frappeCall(PREFIX + "list_regulatory_reference_versions", { reference_set: referenceSet }),
	// §7.3 is two commands on purpose: the set can exist with no version, and
	// the editor recovers from a failure between them.
	createRegulatoryReference: ({ reference_key, reference_kind, display_name }) =>
		frappeCall(PREFIX + "create_regulatory_reference", {
			reference_key,
			reference_kind,
			display_name: display_name || null,
			idempotency_key: newIdempotencyKey("ref"),
		}),
	saveRegulatoryReferenceVersion: (payload) =>
		frappeCall(PREFIX + "save_regulatory_reference_version", {
			...payload,
			payload: JSON.stringify(payload.payload || {}),
			applicability_entity_types: JSON.stringify(payload.applicability_entity_types || []),
			applicability_categories: JSON.stringify(payload.applicability_categories || []),
			supersedes_version_ids: JSON.stringify(payload.supersedes_version_ids || []),
			idempotency_key: newIdempotencyKey("refv"),
		}),
	renameRegulatoryReference: (referenceSet, displayName, expectedVersion) =>
		frappeCall(PREFIX + "rename_regulatory_reference", {
			reference_set: referenceSet,
			display_name: displayName,
			expected_version: expectedVersion || null,
		}),
	recordReferenceVerification: (payload) =>
		frappeCall(PREFIX + "record_reference_verification", {
			...payload,
			idempotency_key: newIdempotencyKey("verify"),
		}),
	listVerificationHistory: (targetDoctype, targetName) =>
		frappeCall(PREFIX + "list_verification_history", {
			target_doctype: targetDoctype,
			target_name: targetName,
		}),
	getBusinessDayCalendar: (name) => frappeCall(PREFIX + "get_business_day_calendar", { name }),
	registerBusinessDayCalendarVersion: (payload) =>
		frappeCall(PREFIX + "register_business_day_calendar_version", {
			...payload,
			weekend_days: JSON.stringify(payload.weekend_days || []),
			holidays: JSON.stringify(payload.holidays || []),
			idempotency_key: newIdempotencyKey("cal"),
		}),
	setReminderThresholdDays: (days) =>
		frappeCall(PREFIX + "set_reminder_threshold_days", { days, idempotency_key: newIdempotencyKey("rem") }),
};
