// The Contracts page's reads and its one command call. Server output is authoritative for data and for what the viewer may do (AGENTS.md §6.2); this adapter only transports it.
// `silent: true` keeps Frappe's own "Message" dialog from appearing for a refusal: a refusal comes back as data and the screen draws it beside the thing it concerns (AGENTS.md §6.10).
const BASE = "kentender_contracts.api";

// The Desk page calls through `frappe.call`; the supplier portal sets its own transport (`portal.call`) before it mounts, because a Website page has no `frappe.call` that stays quiet.
let transport = (method, args, options) => frappe.call({ method, args, type: (options && options.type) || "POST", freeze: false, silent: true }).then((response) => response.message);

export function useTransport(fn) {
	transport = fn;
}

function call(method, args, options) {
	return transport(method, args, options);
}

export function getWorkspace({ page = 1, pageSize = 10, view = "", search = "", status = "", source = "" } = {}) {
	return call(`${BASE}.workspace.get_contract_workspace`, { page, page_size: pageSize, view, search, status, source });
}

export function getBoard({ contract, tab = "", subject = [] }) {
	return call(`${BASE}.contract.get_contract_board`, { contract, tab, subject: JSON.stringify(subject) });
}

export function runCommand({ command, contract, expectedVersion, key, args = {}, values = {} }) {
	return call(`${BASE}.contract.run_contract_command`, {
		command,
		contract,
		expected_version: expectedVersion,
		idempotency_key: key,
		args: JSON.stringify(args),
		values: JSON.stringify(values),
	}, { type: "POST" });
}
