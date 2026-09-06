// Shared frappe.call wrapper for the Strategy Vue-in-Desk data adapters.
// Verbatim copy of kentender_budget's / the NDS frappeCall.js (AGENTS.md
// §6.6 — each app keeps its own copy of this pure helper).
//
// frappe.call() returns the raw jqXHR on failure (see frappe/public/js/frappe/request.js —
// $.ajax(...).fail(...) rejects with the jqXHR itself, not an Error). Awaiting it and doing
// `e.message || String(e)` therefore always falls through to String(jqXHR), which stringifies
// to "[object Object]" — every server-side frappe.throw()/validation error surfaced this way
// instead of its real message. Extract the real message from the parsed response body instead.
export async function frappeCall(method, args) {
	try {
		// silent — request.js otherwise raises Frappe's own "Message" modal for
		// every _server_messages rejection, on top of the screen's inline error
		// summary: the same refusal rendered twice. An earlier version of this
		// file tried to suppress that per exception *type* (error_handlers keyed
		// by "ValidationError"/"PermissionError"), but Frappe's automatic field
		// validation raises specific subclasses — MandatoryError,
		// LinkValidationError, UniqueValidationError — whose exc_type never
		// matched the allowlist, so the raw framework dialog still popped for
		// every missing-mandatory-field or bad-Link refusal. `silent: true`
		// suppresses frappe's own dialog unconditionally, regardless of
		// exception type; the message itself still reaches the caller through
		// extractErrorMessage below.
		const response = await frappe.call({ method, args, freeze: false, silent: true });
		return response.message;
	} catch (xhr) {
		const err = new Error(extractErrorMessage(xhr));
		// frappe.PermissionError responds with HTTP 403 (frappe/exceptions.py) —
		// exposed so a caller can distinguish "forbidden" from any other
		// failure without re-parsing the raw jqXHR itself.
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
