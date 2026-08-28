// Classifies a rejected referenceDataApi call (see referenceDataApi.js's call(),
// which rejects with {code, message} instead of letting Frappe's default popup
// handle it) into either an inline field error or a themed banner message, so
// screens never fall back to frappe.throw's generic modal dialog.
//
// fieldMap maps a server error `title` (e.g. "PE_CODE_DUPLICATE") onto the local
// form field it belongs to. Errors with no title, or a title not in fieldMap,
// are treated as page-level and returned as `banner` instead.
export function classifyApiError(err, fieldMap = {}) {
	const message = (err && err.message) || __("Something went wrong. Please try again.");
	const field = err && err.code ? fieldMap[err.code] : null;
	if (field) {
		return { field, message, banner: null };
	}
	return { field: null, message: null, banner: message };
}
