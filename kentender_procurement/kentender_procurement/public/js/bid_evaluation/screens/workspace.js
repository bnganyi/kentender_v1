// The Bid evaluation workspace (EVL-CHG-001 v0.4 §9.2; boards D01, D01-EMPTY,
// D01-FILTERED, D01-APPOINT): the viewer's own
// evaluation tasks, then the register they may read (ListEvaluationWork), with
// a local search and state filter. No tracker or next step on the workspace.
// A viewer with no evaluation responsibility gets the shared access state (BidEvaluationWorkspace.vue), not a board.
import { em, fb, task, tb } from "../board/model.js";

export const STATES = ["All states", "Preparing", "Reviewing", "Signing", "Report sent", "No evaluation required", "Cancelled"];

export function workspaceBoard({ work, form, loading = false }) {
	const head = { title: "Bid evaluation", desc: "Review automatic checks, resolve questions and prepare the committee report." };
	if (loading || !work) return { ...head, blocks: [em("Loading evaluations…", null, "loader")] };
	const register = work.register || [];
	const titleOf = (ref) => (register.find((r) => r.tender === ref) || {}).title || ref;
	const stateOf = (ref) => (register.find((r) => r.tender === ref) || {}).state || "";
	const blocks = (work.tasks || []).map((t) => task(t.title, titleOf(t.reference), t.status === "Assigned" ? stateOf(t.reference) : t.status,
		{ label: t.action_label || "Open evaluation", action: "open", args: { route: t.route } }));
	blocks.push(fb([["Find a tender", form.query || "", { wide: true, ph: "Find a tender", name: "query" }],
		["State", form.state || "", { select: true, name: "state", options: STATES.map((s) => ({ value: s === "All states" ? "" : s, label: s })) }]], { title: "Evaluations", sec: true }));
	if (register.length) {
		blocks.push(tb(["Tender", "Title", "Work state", "Action"], register.map((r) => [r.tender, r.title, r.state,
			{ label: "View", action: "open", args: { route: ["tenders", r.tender, "evaluation"] }, testid: `evl-view-${r.tender}` }]), { testid: "evl-register", paged: "evl-register" }));
	} else if (form.query || form.state) {
		blocks.push({ ...em("No evaluations match your search.", "Clear search", "search"), btnAction: "clear" });
	} else {
		blocks.push(em("No evaluations are assigned to you.", null, "clipboard"));
	}
	return { ...head, blocks };
}
