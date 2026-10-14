// The Contracts page's reads. Server output is authoritative for data and for what the viewer may do (AGENTS.md §6.2); this adapter only transports it.
export function getWorkspace({ page = 1, pageSize = 20 } = {}) {
	return frappe
		.call({ method: "kentender_contracts.api.workspace.get_contract_workspace", args: { page, page_size: pageSize }, freeze: false })
		.then((response) => response.message);
}
