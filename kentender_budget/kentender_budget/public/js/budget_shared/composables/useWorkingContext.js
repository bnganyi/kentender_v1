import { ref } from "vue";
import { getWorkingContext, selectWorkingContext } from "../../budget_funding/data/budgetApi.js";

// BUD-CHG-001 v1.2 Phase 8 — the shared PE/FY working-context selector.
// Wraps kentender_core.api.reference_data_api's get_working_context/
// select_working_context (kentender_core owns PE/Financial Year/PE Fiscal
// Year Context; Budget consumes it as a published service, same pattern as
// list_organisation_units/list_funding_sources). The resolved context is
// only a working-context preference, never an authorization grant —
// business actions stay gated by their own Role/capability checks
// server-side regardless of what's selected here.
export function useWorkingContext(module) {
	const loading = ref(true);
	const mode = ref("none"); // "unrestricted" | "single" | "multiple" | "none"
	const contexts = ref([]);
	const selected = ref(null);
	const selectionRequired = ref(false);

	function apply(result) {
		mode.value = result.mode;
		contexts.value = result.contexts || [];
		selected.value = result.selected || null;
		selectionRequired.value = result.selection_required;
	}

	async function refresh(requestedContext) {
		loading.value = true;
		try {
			apply(await getWorkingContext(module, requestedContext));
		} finally {
			loading.value = false;
		}
	}

	async function select(contextId) {
		selected.value = await selectWorkingContext(module, contextId);
		selectionRequired.value = false;
	}

	return { loading, mode, contexts, selected, selectionRequired, refresh, select };
}
