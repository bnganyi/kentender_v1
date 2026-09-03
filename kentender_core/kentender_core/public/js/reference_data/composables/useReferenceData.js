import { reactive, toRefs } from "vue";
import { referenceDataApi as api } from "../data/referenceDataApi.js";

// Classifies a referenceDataApi rejection ({code, message, excType} — see
// referenceDataApi.js's call()) into the two error states the register screens
// distinguish (§12.9): "forbidden" (PermissionError) vs "server" (anything else).
function classifyError(err) {
	if (err && err.excType === "PermissionError") {
		return { type: "forbidden", message: __("You do not have access to maintain reference data.") };
	}
	return { type: "server", message: __("Reference data could not be loaded.") };
}

export function useReferenceData() {
	const state = reactive({
		peTypes: [],
		pe: { rows: [], count: 0, loading: false, error: null },
		fy: { rows: [], count: 0, loading: false, error: null },
		context: { rows: [], count: 0, loading: false, error: null },
	});

	async function loadPeTypes() {
		try {
			const res = await api.listPeTypes();
			state.peTypes = res.rows || [];
		} catch (e) {
			// Non-fatal — only affects the New PE type dropdown, not the register itself.
			state.peTypes = [];
		}
	}

	// `quiet` refetches in place. RegisterStates swaps the whole table for a
	// skeleton while `loading` is true, so a refresh triggered by returning to
	// the register (rather than a genuine first load) would flash the rows away
	// and back. Quiet keeps them mounted until the new ones land.
	async function refreshPe(filters = {}, { quiet = false } = {}) {
		if (!quiet) state.pe.loading = true;
		state.pe.error = null;
		try {
			const res = await api.listProcuringEntities(filters);
			state.pe.rows = res.rows || [];
			state.pe.count = res.count || 0;
		} catch (e) {
			state.pe.error = classifyError(e);
		} finally {
			state.pe.loading = false;
		}
	}

	async function refreshFy(filters = {}, { quiet = false } = {}) {
		if (!quiet) state.fy.loading = true;
		state.fy.error = null;
		try {
			const res = await api.listFinancialYears(filters);
			state.fy.rows = res.rows || [];
			state.fy.count = res.count || 0;
		} catch (e) {
			state.fy.error = classifyError(e);
		} finally {
			state.fy.loading = false;
		}
	}

	async function refreshContext(filters = {}, { quiet = false } = {}) {
		if (!quiet) state.context.loading = true;
		state.context.error = null;
		try {
			const res = await api.listPeFyContexts(filters);
			state.context.rows = res.rows || [];
			state.context.count = res.count || 0;
		} catch (e) {
			state.context.error = classifyError(e);
		} finally {
			state.context.loading = false;
		}
	}

	async function refreshAll(opts = {}) {
		await Promise.all([
			loadPeTypes(),
			refreshPe({}, opts),
			refreshFy({}, opts),
			refreshContext({}, opts),
		]);
	}

	return { ...toRefs(state), refreshPe, refreshFy, refreshContext, refreshAll, loadPeTypes, classifyError };
}
