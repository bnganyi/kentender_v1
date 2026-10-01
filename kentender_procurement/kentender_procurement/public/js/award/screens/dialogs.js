// The Award dialogs (AWD-CHG-001 v0.4 §10.3 "Other required dialog text";
// boards X01–X11). Each names the command its primary button runs
// (`reconciliation/command_map.md`); Back only closes. No confirmation
// checkbox, no extra approval.
import { btn } from "../board/model.js";

const back = () => btn("Back", "close-dialog");

export const DIALOGS = {
	"return-report": () => ({ t: "Return report", f: [{ label: "Reason", area: true, name: "dlg_reason" }], a: [back(), btn("*Return report", "return-report")] }),
	"return-for-correction": () => ({ t: "Return for correction", f: [{ label: "Reason", area: true, name: "dlg_reason" }],
		a: [back(), btn("*Return for correction", "decide", { outcome: "Return for correction" })] }),
	"record-no-award": () => ({ t: "Record no award", f: [{ label: "Reason", area: true, name: "dlg_reason" }, { label: "Next action", name: "dlg_next_action" }],
		a: [back(), btn("*Record no award", "decide", { outcome: "No award" })] }),
	"correction-return": () => ({ t: "Return for correction", f: [{ label: "Reason", area: true, name: "dlg_reason" }],
		a: [back(), btn("*Return for correction", "correction", { outcome: "Return for correction" })] }),
	"correction-no-award": () => ({ t: "Record no award", f: [{ label: "Reason", area: true, name: "dlg_reason" }, { label: "Next action", name: "dlg_next_action" }],
		a: [back(), btn("*Record no award", "correction", { outcome: "Record no award" })] }),
	"record-next-action": (args) => ({ t: "Record next action", f: [{ label: "Reason", area: true, name: "dlg_reason" }, { label: "Next action", name: "dlg_next_action" }],
		a: [back(), btn("*Save", "disposition", { issue: args.issue })] }),
	"record-outcome": (args, d) => {
		const o = ((d && d.outstanding) || []).find((x) => x.issue === args.issue) || {};
		return { t: "Record outcome", f: [{ label: "Basis for hold", ro: o.basis }, { label: "Outcome", radio: o.outcomes || [], name: "dlg_outcome" },
			{ label: "Reason", area: true, name: "dlg_reason" }, { label: "Evidence", name: "dlg_evidence" }, { label: "Next action", name: "dlg_next_action" }],
			a: [back(), btn("*Save outcome", "disposition", { issue: args.issue })] };
	},
	"review-correction": (args, d) => {
		const o = ((d && d.outstanding) || []).find((x) => x.issue === args.issue) || {};
		return { t: "Review correction", f: [{ label: "Outcome", radio: o.outcomes || ["No material effect", "Request corrected evaluation", "Request decision review", "Further action required"],
			name: "dlg_outcome" }, { label: "Reason", area: true, name: "dlg_reason" }, { label: "Evidence", name: "dlg_evidence" }, { label: "Next action", name: "dlg_next_action" }],
			a: [back(), btn("*Save outcome", "disposition", { issue: args.issue })] };
	},
	"record-restriction": () => ({ t: "Record restriction", f: [{ label: "Basis for hold", radio: ["Authoritative order", "Reported challenge"], name: "dlg_basis" },
		{ label: "Source", name: "dlg_source" }, { label: "Received at", name: "dlg_received_at" }, { label: "Effective from", name: "dlg_effective_from" },
		{ label: "Scope", name: "dlg_scope" }, { label: "Evidence", name: "dlg_evidence" }, { label: "Reason", area: true, name: "dlg_reason" }],
		a: [back(), btn("*Save restriction", "record-restriction")] }),
	// supplier (portal)
	accept: (args) => ({ t: "Accept this award?", b: args.wording, a: [back(), btn("*Accept award", "respond", { response: "Accept" })] }),
	decline: () => ({ t: "Decline this award?", f: [{ label: "Reason", area: true, name: "dlg_reason" }], a: [back(), btn("!Decline award", "respond", { response: "Decline" })] }),
	"request-explanation": () => ({ t: "Request explanation", f: [{ label: "Your request", area: true, name: "dlg_request" }], a: [back(), btn("*Send request", "request-explanation")] }),
};

export function dialogFor(name, args, data) {
	const f = DIALOGS[name];
	return f ? f(args || {}, data) : null;
}
