// Maps the server's real audit action codes (kentender_core.services.reference_data_transitions,
// recorded verbatim in Audit Event.action) onto a readable label for the History/Governance
// history tables. Falls back to a humanized version of the raw code for anything not listed here,
// so a new action code never renders as a blank cell.
const LABEL_BY_ACTION = {
	"reference_data.pe.create_draft": "Created draft",
	"reference_data.pe.update_draft": "Draft updated",
	"reference_data.pe.activate": "Activated",
	"reference_data.pe.apply_amendment": "Amendment applied",
	"reference_data.pe.propose_amendment": "Proposed amendment",
	"reference_data.pe.suspend": "Suspended",
	"reference_data.pe.reinstate": "Reinstated",
	"reference_data.pe.retire": "Retired",

	"reference_data.fy.create_draft": "Created draft",
	"reference_data.fy.make_available": "Made available",
	"reference_data.fy.retire": "Retired",

	"reference_data.context.enable": "Enabled",
	"reference_data.context.activate": "Activated",
	"reference_data.context.suspend": "Suspended",
	"reference_data.context.reinstate": "Reinstated",
	"reference_data.context.close": "Closed",
	"reference_data.context.auto_close": "Closed (automatic)",
	"reference_data.context.reopen": "Reopened",
};

function humanize(action) {
	const tail = action.split(".").pop() || action;
	return tail.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());
}

export function actionLabel(action) {
	return LABEL_BY_ACTION[action] || humanize(action);
}
