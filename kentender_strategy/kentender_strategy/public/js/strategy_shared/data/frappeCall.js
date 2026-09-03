// Shared frappe.call wrapper for the Strategy Vue-in-Desk data adapters.
//
// frappe.call() returns the raw jqXHR on failure (see frappe/public/js/frappe/request.js —
// $.ajax(...).fail(...) rejects with the jqXHR itself, not an Error). Awaiting it and doing
// `e.message || String(e)` therefore always falls through to String(jqXHR), which stringifies
// to "[object Object]" — every server-side frappe.throw()/validation error surfaced this way
// instead of its real message. Extract the real message from the parsed response body instead.
// Frappe pops its own msgprint dialog for any server exception carrying
// _server_messages — so a refusal surfaced twice: once as a raw framework
// dialog titled with the internal error code (AUTH_ROLE_REQUIRED), and again
// as the screen's own inline message. request.js skips its dialog whenever a
// per-call error_handlers entry matches the exception type, so registering
// no-op handlers for the refusal types leaves exactly one, in-app message.
const SILENCED_EXC_TYPES = ["PermissionError", "ValidationError"];
const noopHandlers = Object.fromEntries(SILENCED_EXC_TYPES.map((t) => [t, () => {}]));

export async function frappeCall(method, args) {
	try {
		const response = await frappe.call({
			method,
			args,
			freeze: false,
			error_handlers: noopHandlers,
		});
		return response.message;
	} catch (xhr) {
		throw new Error(extractErrorMessage(xhr));
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
