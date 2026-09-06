// Shared frappe.call wrapper for the AUTH-ADR-001 v1.3 §12 administration
// surfaces (Organisation structure, User responsibilities). Same helper the
// Departmental Needs and Budget adapters use — a pure function with no Vue or
// component identity crosses a bundle boundary safely (AGENTS.md §6.6), unlike
// a page-level component object, so both bundles here import this one copy.
//
// frappe.call() returns the raw jqXHR on failure (see frappe/public/js/frappe/request.js —
// $.ajax(...).fail(...) rejects with the jqXHR itself, not an Error). Awaiting it and doing
// `e.message || String(e)` therefore always falls through to String(jqXHR), which stringifies
// to "[object Object]" — every server-side frappe.throw()/validation error surfaced this way
// instead of its real message. Extract the real message from the parsed response body instead.
export async function frappeCall(method, args) {
	try {
		// silent — request.js otherwise raises Frappe's own "Message" modal for
		// every _server_messages rejection, on top of the screen's inline
		// error summary (§12.6): the same refusal rendered twice. The message
		// itself still reaches the caller through extractErrorMessage below.
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
