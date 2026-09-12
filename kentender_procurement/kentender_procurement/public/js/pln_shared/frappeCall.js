// Shared frappe.call wrapper for the Departmental Needs data adapter.
// Verbatim copy of kentender_budget's frappeCall.js (AGENTS.md §6.6 — a
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
	// `silent` only suppresses the `_server_messages` dialog (see request.js's
	// own cleanup()); request.js raises a *separate*, hardcoded dialog for
	// 401/403/404/413/508 unconditionally (its own `statusCode` map, fired
	// synchronously inside .fail(), before this function ever regains
	// control) — a masked "not found" read popped Frappe's raw "Not found"
	// modal on top of this screen's own calm inline state (reported live
	// 2026-09-11). Reacting after the fact (hide_msgprint in the catch) loses
	// a real race: Bootstrap's own modal("show"), triggered inside that same
	// .fail() handler, stages its "show" class through its own transition
	// queue, and a hide issued in the same tick can be overtaken by it — the
	// dialog stays up, inert, blocking every click behind it. Muting
	// frappe.msgprint for the life of this one call prevents the framework
	// from ever creating that dialog, so there is nothing left to race.
	// This also mutes any unrelated frappe.msgprint truly concurrent with
	// this specific request — the same accepted tradeoff `silent: true`
	// already makes for `_server_messages`, just extended to cover the
	// status-code dialogs silent doesn't reach.
	const originalMsgprint = frappe.msgprint;
	frappe.msgprint = () => {};
	try {
		const response = await frappe.call({ method, args, freeze: false, silent: true });
		return response.message;
	} catch (xhr) {
		const err = new Error(extractErrorMessage(xhr));
		// frappe.PermissionError responds with HTTP 403, DoesNotExistError
		// with 404 (frappe/exceptions.py) — exposed so a caller can
		// distinguish "forbidden"/"masked as not found" from any other
		// failure without re-parsing the raw jqXHR itself.
		err.httpStatus = xhr && xhr.status;
		throw err;
	} finally {
		frappe.msgprint = originalMsgprint;
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
