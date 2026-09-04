import { ref } from "vue";
import { listAvailableFiscalYears } from "../../budget_funding/data/budgetApi.js";

// BUD-CHG-001 v1.3 Phase 7 — one site is one Procuring Entity: Budget has no
// PE+FY "working context" any more, only a local Fiscal Year filter (§10:
// "a changeable filter on the workspace. It is never a gate and never a
// context selector."). Replaces useWorkingContext.js/WorkingContextPicker.vue
// for every Budget screen.
//
// §12.1: "It never chooses the first Budget or the first year... remembered
// only with a visible reset, and is ignored when stale or invalid." So this
// never auto-picks list[0] — only a previously-selected year, read back from
// localStorage and re-validated against the live catalogue on every load,
// counts as "selected". Shared across screens (Workspace, and the pre-
// creation Register flow) via the same storage key, so navigating from one
// to the other carries the same selection with no query-string plumbing.
const STORAGE_KEY = "kt-budget-fiscal-year";

export function useFiscalYearFilter() {
	const loading = ref(true);
	const fiscalYears = ref([]);
	const selected = ref("");

	async function load() {
		loading.value = true;
		try {
			fiscalYears.value = (await listAvailableFiscalYears()) || [];
			const remembered = window.localStorage.getItem(STORAGE_KEY) || "";
			selected.value = fiscalYears.value.includes(remembered) ? remembered : "";
		} finally {
			loading.value = false;
		}
	}

	function select(fy) {
		selected.value = fy || "";
		try {
			if (fy) window.localStorage.setItem(STORAGE_KEY, fy);
			else window.localStorage.removeItem(STORAGE_KEY);
		} catch (e) {
			// Private-browsing/storage-blocked contexts: the in-memory selection
			// still works for this page load, it just doesn't persist.
		}
	}

	return { loading, fiscalYears, selected, load, select };
}
