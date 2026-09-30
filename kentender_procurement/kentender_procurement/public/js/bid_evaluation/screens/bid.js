// Requirement review (EVL-CHG-001 v0.4 §9.5; boards D04, D04-AUTO, D04-FAIL,
// D04-CONCERN, D08-RULE). One opened bid: its requirements, the automatic
// results, the submitted evidence, and this member's finding. The Show filter
// is a local display control; it changes nothing on the server.
import { ds, ev, fi, kv, n, sg, tb } from "../board/model.js";
import { cmd, dialog, guidance, money } from "./common.js";

// A requirement name inside a sentence; a code keeps its capitals (as the server's headlines do).
const inSentence = (label) => {
	const first = String(label || "").split(" ")[0];
	return first.length > 1 && first === first.toUpperCase() ? label : String(label || "").charAt(0).toLowerCase() + String(label || "").slice(1);
};

export const FILTERS = ["All checks", "Needs review", "Does not meet", "Meets", "Not applicable", "Automatic checks"];

function visible(requirements, show) {
	if (show === "Automatic checks") return requirements.filter((r) => r.automatic && !r.evidence_pending);
	if (show === "All checks") return requirements;
	return requirements.filter((r) => r.result === show);
}

function required(r) {
	return r.checks.map((c) => c.required).filter(Boolean).join("; ");
}

function offered(r) {
	return [...new Set(r.checks.filter((c) => c.field !== "compliance").map((c) => c.offered).filter(Boolean))].join("; ");
}

export function defaultFilter(bid) {
	const reqs = bid.requirements || [];
	if (reqs.some((r) => r.result === "Needs review")) return "Needs review";
	if (reqs.some((r) => r.result === "Does not meet")) return "All checks";
	return "Automatic checks";
}

export function selectedRequirement(bid, form) {
	const reqs = bid.requirements || [];
	return reqs.find((r) => r.requirement_key === form.requirement_key) || reqs.find((r) => r.evidence_pending) || reqs.find((r) => r.result === "Needs review") || null;
}

export function bidScreen(ctx) {
	const { data, bid, form } = ctx;
	if (!bid) return { title: "", blocks: [] };
	const show = form.show || defaultFilter(bid);
	const shown = visible(bid.requirements || [], show);
	const target = selectedRequirement(bid, form);
	// the finding form belongs to the review list (board D04); the automatic
	// checks and the all-checks views are read-only (D04-AUTO, D04-FAIL)
	const reviewing = !!target && show === "Needs review" && data.viewer.eligible && !data.viewer.secretary;
	const rows = shown.map((r) => [r.label, required(r), offered(r), r.result, r.reason || (r.checks[0] || {}).reason || ""]);
	const ruleIssue = shown.some((r) => /rule is unavailable/i.test(r.reason || ""));
	const blocks = [];
	if (ruleIssue) blocks.push(n("warning", "This requirement needs review because its evaluation rule is unavailable."));
	blocks.push({ k: "filter", cells: [["Show", show, { select: true, name: "show", options: FILTERS.map((x) => ({ value: x, label: x })) }]] });
	blocks.push(tb(["Requirement", "Required", "Offered", "Result", "Reason"], rows, { testid: "evl-requirements",
		caption: show === "Automatic checks" ? "These results compare the submitted values. Supporting evidence is reviewed separately." : "" }));
	const evidence = (reviewing ? target.evidence : shown.flatMap((r) => r.evidence)).filter((e, i, all) => all.findIndex((x) => x.digest === e.digest) === i);
	if (evidence.length) blocks.push(ev(evidence.map((e) => ({ label: e.name, action: "evidence", args: { digest: e.digest } }))));
	if (bid.responsiveness === "Not responsive") {
		const row = ((data.comparison || {}).rows || []).find((x) => x.bid === bid.bid) || {};
		blocks.push(tb(["Submitted total", "Evaluated total", "Position"], [[money(row.currency, row.submitted_total), row.evaluated_total || "", String(row.position || "")]],
			{ title: "Financial assessment", sec: true, caption: "The submitted total is shown as a source fact." }));
	}
	let pri = null;
	const sec = [];
	if (reviewing) {
		blocks.push(sg("Your finding", ["Meets", "Does not meet", "Needs review"], -1, { name: "result" }),
			fi("Reason", "", { area: true, req: true, rows: 2, name: "reason" }));
		if (target.history.length) blocks.push(ds("Finding history", target.history.map((h) => `${h.kind}: ${h.result || ""} — ${h.reason} (${h.author_name}, ${h.at})`)));
		else blocks.push(ds("Finding history", target.checks.map((c) => `Automatic check: ${c.reason}`)));
		pri = cmd("Save finding", "record_finding", { values: { bid: bid.bid, requirement_key: target.requirement_key, evidence_reference: (target.evidence[0] || {}).name || "" },
			fields: ["result", "reason"] });
		sec.push(dialog("Raise concern", "concern"));
	} else if (data.viewer.eligible && !data.viewer.secretary) {
		pri = ruleIssue && data.viewer.chair ? dialog("Report issue", "issue") : dialog("Raise concern", "concern");
		if (ruleIssue && data.viewer.chair) sec.push({ label: "View report", action: "nav", args: { to: ["report"] } });
	}
	const headline = reviewing ? `Review the evidence for the ${inSentence(target.label)}.` : "Review the results and raise a concern if needed.";
	return {
		title: bid.bidder, desc: "Compare the offered response with the published requirement.", back: "Back to evaluation", backAction: "back-to-record",
		guidance: guidance(data, { headline: data.viewer.eligible && !data.viewer.secretary ? headline : (data.guidance || {}).headline }), blocks, pri, sec,
	};
}

export function concernDialog(ctx) {
	const { bid, form } = ctx;
	const target = selectedRequirement(bid, form) || (bid.requirements || [])[0] || {};
	return {
		t: "Raise an evaluation concern",
		blocks: [kv([["Requirement", `${target.label} — ${required(target)}`]]), fi("Reason", "", { area: true, req: true, rows: 3, name: "concern_reason" })],
		pri: cmd("Record concern", "raise_concern", { values: { bid: bid.bid, requirement_key: target.requirement_key }, fields: [["reason", "concern_reason"]], close: true }),
	};
}

export function issueDialog(ctx) {
	const { bid } = ctx;
	const target = (bid.requirements || []).find((r) => /rule is unavailable/i.test(r.reason || "")) || {};
	return {
		t: "Report an evaluation issue",
		blocks: [kv([["Requirement", target.label || ""]]), fi("What is wrong?", "The automatic comparison rule is unavailable.", { area: true, req: true, rows: 3, name: "issue_description" })],
		cons: "Technical support will be assigned. No bid content is shared in the support notice.",
		pri: cmd("Submit issue", "report_issue", { values: { bid: bid.bid, requirement_key: target.requirement_key }, fields: [["description", "issue_description"]], close: true }),
	};
}
