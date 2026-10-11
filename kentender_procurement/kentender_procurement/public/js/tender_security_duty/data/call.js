// frappe.call wrapper for the tender-security intake page — a copy of
// tnd_shared/frappeCall.js (AGENTS.md §6.6: each module keeps its own copy of
// a pure helper) that can send GET, since Bid Submission's reads accept GET
// only. The server's error code (`kt_error_code`) travels on the error.
export async function frappeCall(method, args, type = "POST") {
	try {
		// silent — request.js otherwise raises Frappe's own "Message" modal for
		// every rejection, on top of the screen's inline error summary
		// (AGENTS.md §6.10): the same refusal rendered twice.
		const response = await frappe.call({ method, args, type, freeze: false, silent: true });
		return response.message;
	} catch (xhr) {
		const data = (xhr && xhr.responseJSON) || {};
		const err = new Error(data.kt_error_message || extractErrorMessage(xhr));
		err.httpStatus = xhr && xhr.status;
		err.code = data.kt_error_code || "";
		err.detail = data.kt_error_detail || {};
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
