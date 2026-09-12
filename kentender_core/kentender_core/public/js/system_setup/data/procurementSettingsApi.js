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
	setReminderThresholdDays: (days) =>
		frappeCall(PREFIX + "set_reminder_threshold_days", { days, idempotency_key: newIdempotencyKey("rem") }),
};
