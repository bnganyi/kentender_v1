// Thin wrappers over kentender_core.api.responsibility_api. Every rule the
// dialog shows — required fields, exact scope, descendant counts, exclusive
// office conflicts and the human summary — is computed by the server's
// preview, never here. There is no Procuring Entity parameter anywhere: one
// site is one PE (AUTH-ADR-001 v1.6).
import { frappeCall } from "../../kt_admin_shared/data/frappeCall.js";

const PREFIX = "kentender_core.api.responsibility_api.";

export const responsibilityApi = {
	listRows: (filters) => frappeCall(PREFIX + "list_user_responsibilities", filters),
	formOptions: () => frappeCall(PREFIX + "assignment_form_options", {}),
	searchUsers: (query) => frappeCall(PREFIX + "search_users", { query: query || null }),
	preview: (payload) => frappeCall(PREFIX + "preview_responsibility_assignment", payload),
	assign: (payload) => frappeCall(PREFIX + "grant_responsibility", payload),
	detail: (assignment) => frappeCall(PREFIX + "get_responsibility_assignment", { assignment }),
	revoke: (assignment, reason, expectedVersion) =>
		frappeCall(PREFIX + "revoke_responsibility", {
			assignment,
			reason,
			expected_version: expectedVersion || null,
		}),
};
