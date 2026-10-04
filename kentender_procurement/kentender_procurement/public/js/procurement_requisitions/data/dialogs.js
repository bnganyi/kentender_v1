// Governed reason dialogs drawn on the board, stated once so every screen
// that offers the action uses the board's exact wording (REQ-DES-06/07/08/10).
export const PLANNING_CORRECTION = {
	title: "Request a Planning correction?",
	reasonLabel: "What is wrong in the approved plan? (required, 20–1,000 characters)",
	confirmLabel: "Send correction request",
	notice: "This requisition will be preserved and stopped. It will not reopen automatically after Planning responds.",
	noticeTone: "warning",
	rows: 3,
	testid: "req-planning-dialog",
};

export const WITHDRAW = {
	title: "Withdraw this requisition?",
	confirmLabel: "Withdraw requisition",
	placeholder: "State why this requisition is being withdrawn",
	notice: "The requisition will close without using approved-plan amounts or reserving funding.",
	noticeTone: "warning",
	danger: true,
	testid: "req-withdraw-dialog",
};
