// Shared frappe.call wrapper for the Budget Vue-in-Desk data adapters.
// Verbatim copy of kentender_strategy's frappeCall.js (AGENTS.md §6.6 — a
// page-level component object can't cross a bundle boundary, but a pure
// helper with no Vue/component identity carries no such restriction; each
// app keeps its own copy rather than importing across app boundaries).
//
// frappe.call() returns the raw jqXHR on failure (see frappe/public/js/frappe/request.js —
// $.ajax(...).fail(...) rejects with the jqXHR itself, not an Error). Awaiting it and doing
// `e.message || String(e)` therefore always falls through to String(jqXHR), which stringifies
// to "[object Object]" — every server-side frappe.throw()/validation error surfaced this way
// instead of its real message. Extract the real message from the parsed response body instead.
export async function frappeCall(method, args) {
	try {
		// silent — request.js otherwise raises Frappe's own "Message" modal for
		// every _server_messages rejection, on top of the screen's own inline
		// error rendering: the same refusal shown twice. The message itself
		// still reaches the caller through extractErrorMessage below. Keep this
		// in sync with the other apps' copies of this helper (kt_admin_shared,
		// nds_shared, pln_shared, strategy_shared all already set this).
		const response = await frappe.call({ method, args, freeze: false, silent: true });
		return response.message;
	} catch (xhr) {
		const err = new Error(extractErrorMessage(xhr));
		// frappe.PermissionError responds with HTTP 403 (frappe/exceptions.py) —
		// exposed so a caller can distinguish "forbidden" from any other
		// failure (e.g. to pick the Forbidden vs Server-error empty state)
		// without re-parsing the raw jqXHR itself.
		err.httpStatus = xhr && xhr.status;
		throw err;
	}
}

function extractErrorMessage(xhr) {
	const data = xhr && xhr.responseJSON;
	if (data && data._server_messages) {
		try {
			const messages = JSON.parse(data._server_messages)
				.map((m) => {
					try {
						return JSON.parse(m).message || m;
					} catch (e) {
						return m;
					}
				})
				.filter(Boolean);
			if (messages.length) return messages.join(" ");
		} catch (e) {
			// fall through to exception/statusText below
		}
	}
	if (data && data.exception) {
		const parts = String(data.exception).split(": ");
		return parts.length > 1 ? parts.slice(1).join(": ") : parts[0];
	}
	if (xhr && xhr.statusText && xhr.statusText !== "error") return xhr.statusText;
	return __("Something went wrong. Please try again.");
}
