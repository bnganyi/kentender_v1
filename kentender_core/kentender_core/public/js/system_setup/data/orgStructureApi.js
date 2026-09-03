// Thin wrappers over kentender_core.api.organisation_structure_api. No
// business logic here — every guard (administrator, root, parent, sibling
// uniqueness, concurrency) lives server-side; this module only shapes calls.
// There is no Procuring Entity parameter: one site is one PE.
import { frappeCall } from "../../kt_admin_shared/data/frappeCall.js";

const PREFIX = "kentender_core.api.organisation_structure_api.";

function newIdempotencyKey() {
	return `ou-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

export const orgStructureApi = {
	getStructure: (selected) =>
		frappeCall(PREFIX + "get_organisation_structure", { selected: selected || null }),
	getUnit: (unitId) => frappeCall(PREFIX + "get_unit_detail", { unit_id: unitId }),
	addUnit: (parentId, name) =>
		frappeCall(PREFIX + "add_organisation_unit", {
			parent_id: parentId || null,
			name,
			idempotency_key: newIdempotencyKey(),
		}),
	renameUnit: (unitId, name, expectedVersion) =>
		frappeCall(PREFIX + "rename_organisation_unit", {
			unit_id: unitId,
			name,
			expected_version: expectedVersion || null,
		}),
	setActive: (unitId, active, expectedVersion) =>
		frappeCall(PREFIX + "set_organisation_unit_active", {
			unit_id: unitId,
			active: active ? 1 : 0,
			expected_version: expectedVersion || null,
		}),
};
