// Thin frappe.call wrappers over kentender_core.api.reference_data_api. No business
// logic here — every guard (permission, state, SoD, idempotency) lives server-side;
// this module only shapes requests/responses for the composables.

const METHOD_PREFIX = "kentender_core.api.reference_data_api.";

// Parses Frappe's raw error payload (from frappe.call's error callback) into
// {code, message}, where `code` is the server's frappe.throw(..., title=...)
// value when set. `silent:true` below stops frappe.call's default behaviour of
// popping its own generic error dialog — screens handle {code, message} themselves.
function parseServerError(r) {
	let messages = [];
	try {
		if (r && r._server_messages) {
			messages = JSON.parse(r._server_messages).map((m) => (typeof m === "string" ? JSON.parse(m) : m));
		}
	} catch (e) {
		/* fall through to the generic message below */
	}
	const first = messages[0] || {};
	return {
		code: first.title || (r && r.exc_type) || null,
		message: first.message || __("Something went wrong. Please try again."),
		excType: (r && r.exc_type) || null,
	};
}

function call(method, args) {
	return new Promise((resolve, reject) => {
		frappe.call({
			method: METHOD_PREFIX + method,
			args,
			silent: true,
			callback: (r) => resolve(r.message),
			error: (r) => reject(parseServerError(r)),
		});
	});
}

function newIdempotencyKey() {
	return `rd-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

export const referenceDataApi = {
	listPeTypes: () => call("list_pe_types", {}),

	// --- Procuring Entity ---
	listProcuringEntities: (params = {}) => call("list_procuring_entities", params),
	getProcuringEntity: (peId) => call("get_procuring_entity", { pe_id: peId }),
	createPe: (payload) => call("create_or_revise_pe", { payload }),
	updatePeDraft: (peId, payload) => call("update_pe_draft", { pe_id: peId, payload }),
	proposePeAmendment: (peId, changeReason) =>
		call("create_or_revise_pe", { pe_id: peId, change_reason: changeReason }),
	decidePeChange: (peId, action, extra = {}) =>
		call("decide_pe_change", { pe_id: peId, action, idempotency_key: newIdempotencyKey(), ...extra }),

	// --- Financial Year ---
	listFinancialYears: (params = {}) => call("list_financial_years", params),
	getFinancialYear: (financialYearId) => call("get_financial_year", { financial_year_id: financialYearId }),
	createFinancialYear: (startYear) => call("create_financial_year", { start_year: startYear }),
	makeFinancialYearAvailable: (financialYearId) =>
		call("make_financial_year_available", { financial_year_id: financialYearId, idempotency_key: newIdempotencyKey() }),
	retireFinancialYear: (financialYearId) =>
		call("retire_financial_year", { financial_year_id: financialYearId, idempotency_key: newIdempotencyKey() }),

	// --- PE Fiscal Year Context ---
	listPeFyContexts: (params = {}) => call("list_pe_fy_contexts", params),
	getPeFyContext: (contextId) => call("get_pe_fy_context", { context_id: contextId }),
	enablePeFyContext: (procuringEntity, financialYear, activeFrom, activeTo) =>
		call("enable_pe_fy_context", {
			procuring_entity: procuringEntity,
			financial_year: financialYear,
			active_from: activeFrom,
			active_to: activeTo,
			idempotency_key: newIdempotencyKey(),
		}),
	decidePeFyContext: (contextId, action, expectedVersion, extra = {}) =>
		call("decide_pe_fy_context", {
			context_id: contextId,
			action,
			idempotency_key: newIdempotencyKey(),
			expected_version: expectedVersion,
			...extra,
		}),
};
