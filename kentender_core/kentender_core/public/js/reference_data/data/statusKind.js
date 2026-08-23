// Maps the server's real status vocabulary (Procuring Entity, Financial Year,
// PE Fiscal Year Context, plus the readiness/action-needed labels) onto the design
// system's five-state kt-status semantic (see kt-status.css in the design pack):
// is-live (in force now), is-draft (authored, not submitted), is-pending (awaiting
// evaluation/action), is-attention (action needed), is-critical (stopped/removed).
const KIND_BY_STATUS = {
	Draft: "is-draft",
	Active: "is-live",
	Available: "is-live",
	Ready: "is-live",
	"Under Review": "is-pending",
	"Awaiting Approval": "is-pending",
	Scheduled: "is-pending",
	"Not assessed": "is-pending",
	"Configuration required": "is-attention",
	Suspended: "is-critical",
	Closed: "is-critical",
	Retired: "is-critical",
	Inactive: "is-critical",
};

export function statusKind(status) {
	return KIND_BY_STATUS[status] || "is-pending";
}
