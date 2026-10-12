// Structural fidelity for the Bid Evaluation screens against their boards
// (EVL-CHG-001 v0.4, `15_bid_evaluation/design/Bid Evaluation Artboards.dc.html`).
// Each board is built by the live screen builders from the server's own
// answers for its state and viewer — captured from the browser world by
// `bid_evaluation.seeds.playwright_ui_fixtures.capture`, never written by hand
// — mounted in `EvlBoard.vue` and compared container for container with the
// board rendered from the design tool's own template. Registered departures
// are the only allowed differences.
import { afterEach, beforeAll, describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import { nextTick } from "vue";

import { bidEvaluationSkeleton } from "../../../../../tests/ui/fidelity/board.js";
import { compareSkeletons, formatMismatch, skeletonOf } from "../../../../../tests/ui/fidelity/skeleton.js";
import { COVERED, DEPARTURES } from "../../../../../tests/ui/fidelity/departures/bid-evaluation.js";

import EvlBoard from "./board/EvlBoard.vue";
import { build, dialogFor, record } from "./screens/index.js";
import { peopleOf, staleBoard } from "./screens/common.js";
import { workspaceBoard } from "./screens/workspace.js";
import { supplierBoard } from "./portal/supplier.js";

const FIXTURES = import.meta.glob("./fixtures/*.json", { eager: true, import: "default" });
export const USERS = {
	ao: "pw.tnd.ao@example.test", hop: "pw.req.hopf@example.test", secretary: "pw.tnd.officer@example.test", chair: "pw.evl.chair@example.test",
	member: "pw.evl.member@example.test", member_2: "pw.evl.member2@example.test", auditor: "pw.req.auditor@example.test", admin: "Administrator",
	supplier: "supplier",
};

export function world(stage, viewer) {
	const all = FIXTURES[`./fixtures/${stage}.json`];
	if (!all) throw new Error(`no captured world for ${stage}; run capture`);
	const answer = all[USERS[viewer]];
	if (!answer) throw new Error(`${viewer} cannot read the ${stage} world`);
	// a read identical to another reader's is stored once (capture's {"$same_as": reader})
	const resolved = Object.fromEntries(Object.entries(answer).map(([part, value]) => [part, value && value.$same_as ? all[value.$same_as][part] : value]));
	return JSON.parse(JSON.stringify(resolved));
}

// board, captured stage, viewer, route (sub, id), form values the viewer set,
// dialog opened, and what else the page holds (a refusal's field errors, a
// stale record, an unconfirmed signature). "@x" in a route is a captured id.
export const SCREENS = [
	["D02-A", "prepared", "ao"],
	["D02-DELEGATE", "appointed", "hop", ["delegate"]],
	["D02-D", "assigned", "chair", ["declaration"], { choice: "No conflict to declare" }],
	["D02-CONFLICT", "assigned", "chair", ["declaration"], { choice: "Declare a conflict" }],
	["D02-REPLACE", "conflict", "ao", ["replace"]],
	["D02-INELIGIBLE", "conflict", "ao", ["replace"], {}, "", { errors: { incoming: "This person cannot serve on this evaluation committee.",
		incoming_detail: "The person has an unresolved declared conflict for this tender." } }],
	["D02-INTAKE-FIRST", "intake-first", "ao"],
	["D02-DECLARE-FIRST", "declare-first", "member"],
	["D02-UNABLE", "declared", "member", ["unable"]],
	["D02-NO-BIDS", "no-bids", "chair"],
	["S-LOADING", "prepared", "chair", [], {}, "", { state: "loading" }],
	["S-ERROR", "prepared", "chair", [], {}, "", { state: "failure" }],
	["S-NOT-FOUND", "prepared", "chair", [], {}, "", { state: "not-found" }],
	["S-OPENING-AWAITED", "declared", "chair"],
	["S-STALE-RECORD", "resolved", "secretary", ["report"], {}, "", { stale: true }],
	["S-STALE-REPORT", "resigning", "member", ["report", "@previous-report"]],
	["S-UNCONFIRMED", "signing", "member", ["report"], {}, "", { unconfirmed: true }],
	["D03", "concern", "chair"],
	["D03-READY", "resolved", "chair"],
	["D04", "reviewing", "member", ["bid", "@bid"]],
	["D04-AUTO", "reviewing", "member", ["bid", "@bid"], { show: "Automatic checks" }],
	["D04-CONCERN", "reviewing", "member", ["bid", "@bid"], {}, "concern"],
	["D04-FAIL", "failed", "member", ["bid", "@bid"], { show: "All checks" }],
	["D05-START", "discussion", "chair"],
	["D05-JOIN", "discussion", "member"],
	["D05", "joined", "secretary"],
	["D05-ABSENT", "member-left", "secretary"],
	["D05-ABSENT-CHAIR", "member-left", "chair"],
	["D05-ABSENT-MEMBER", "member-left", "member_2"],
	["D05-CONCLUSION", "joined", "chair", [""], { decision: "conclusion", result: "Meets" }],
	["D05-CONCLUSION-Q", "joined", "chair", [""], { decision: "conclusion", result: "Needs review" }],
	["D05-CHAIR", "noted", "chair"],
	["D05-MEMBER", "authorised", "member"],
	["D05-DISAGREE", "authorised", "member", [""], {}, "disagree"],
	["D05-RECORD", "resolved", "secretary", ["record"]],
	["D05-RECORD-MEMBER", "resolved", "chair", ["record"]],
	["D05-RECORD-AUDITOR", "resolved", "auditor", ["record"]],
	["D06-SEND", "authorised", "secretary", ["clarification", "@clarification"]],
	["D06-DELIVERY", "notice-failed", "secretary", ["clarification", "@clarification"]],
	["D06-WITHDRAW", "replacement", "secretary", ["clarification", "@first-clarification"]],
	["D06-WITHDRAW-DLG", "replacement", "secretary", ["clarification", "@first-clarification"], {}, "withdraw"],
	["D06-OUTCOME", "outcome", "chair"],
	["D06-NO-REPLY", "no-reply", "chair"],
	["D06-LATE-REVIEW", "late-reply", "chair", [""], { disposition: "Not considered" }],
	["D06-CHANGED-OFFER", "outcome", "chair", [""], { disposition: "Excluded change" }],
	["D07-DRAFT", "resolved", "secretary", ["report"]],
	["D07-PREVIEW", "resolved", "secretary", ["report", "preview"]],
	["D07-INCOMPLETE", "reviewing", "secretary", ["report"]],
	["D07-NO-RESPONSIVE", "failed-report", "secretary", ["report"]],
	["D07-NO-AGREEMENT", "no-agreement", "secretary", ["report"]],
	["D07-OVERDUE", "overdue", "chair", ["report"]],
	["D07-OVERDUE-SEC", "overdue", "secretary", ["report"]],
	["D07-EXPIRED", "expired", "secretary", ["report"]],
	["D07-SIGN", "signing", "member", ["report"]],
	["D07-CONCERN", "signing", "member", ["report"], {}, "concern"],
	["D07-REVISE", "signing", "secretary", ["report"]],
	["D07-REVISE-DLG", "signing", "secretary", ["report"], {}, "revise"],
	["D07-WAIT", "chair-signed", "chair", ["report"]],
	["D07-DELIVERY", "delivery-failed", "secretary", ["report"]],
	["D07-SENT", "report-sent", "chair", ["report"]],
	["D07-HOP", "report-sent", "hop", ["report"]],
	["D07-HOP-RETURN", "report-sent", "hop", ["report"], {}, "return"],
	["D07-RETURNED", "returned", "secretary", ["report"]],
	["D07-DECISION-UNKNOWN", "decision-unknown", "hop", ["report"]],
	["D07-DECISION-UNKNOWN-CHAIR", "decision-unknown", "chair", ["report"]],
	["S-AUDITOR", "report-sent", "auditor", ["report"]],
	["D08-SOURCE", "source-failed", "secretary"],
	["D08-VERIFY-PLAN", "joined", "chair", [""], { decision: "verification" }],
	["D08-DD", "planned", "member_2", ["verification"]],
	["D08-DD-FREEZE", "observed", "chair", ["verification"]],
	["D08-DD-SIGN", "dd-frozen", "member_2", ["verification"]],
	["D08-VERIFY-OUTCOME", "dd-signed", "chair", [""], { result: "Meets" }],
	["D08-VERIFY-NEG", "dd-signed", "chair", [""], { result: "Does not meet" }],
	["D08-SUPPLEMENT", "supplement", "chair", ["update", "@update"]],
	["D08-SUPPLEMENT-SENT", "supplement-sent", "chair", ["update", "@update"]],
	["D08-SUPPLEMENT-HOP", "supplement-sent", "hop", ["update", "@update"]],
	["D08-CORRECTION", "awarded", "chair", ["correction"]],
	["D08-CORRECTION-HOP", "corrected", "hop", ["correction"]],
	["D08-PAUSED", "paused", "chair"],
	["D08-CANCELLED", "cancelled", "chair"],
	["P-PREP", "paused-prep", "ao"],
	["P-SIGN", "paused-sign", "chair"],
	["C-PREP", "cancelled-prep", "ao"],
	["C-SIGN", "cancelled-sign", "chair"],
].map(([board, stage, viewer, route, form, dialog, page]) => ({ board, stage, viewer, route: route && route.length ? route : [""], form: form || {}, dialog: dialog || "", page: page || {} }));

// The workspace (D01 family), built from each viewer's captured ListEvaluationWork.
export const WORKSPACE = [
	["D01", "concern", "chair"],
	["D01-APPOINT", "prepared", "ao"],
].map(([board, stage, viewer, form]) => ({ board, stage, viewer, form: form || {} }));

export function boardFor({ stage, viewer, route, form, dialog, page }) {
	if (page.state) return { board: { ...record.states(page.state) }, form: {}, people: {} };
	const captured = world(stage, viewer);
	const data = captured.data;
	const clarifications = (data.work || {}).clarifications || [];
	const ids = {
		"@bid": captured.bid && captured.bid.bid,
		"@clarification": clarifications.slice(-1).map((c) => c.name)[0],
		"@first-clarification": clarifications.map((c) => c.name)[0],
		"@update": ((data.work || {}).updates || []).map((u) => u.name)[0],
		"@previous-report": captured.report_previous && captured.report_previous.report,
	};
	const [sub, ...rest] = route;
	const id = rest.map((x) => ids[x] || x).join("/");
	const report = rest[0] === "@previous-report" ? captured.report_previous : captured.report;
	const ctx = { data, sub: sub || "", id, user: USERS[viewer], form: { ...form }, errors: { members: {}, ...(page.errors || {}) }, bid: captured.bid, report,
		record: captured.record, candidates: captured.candidates, unconfirmed: !!page.unconfirmed, dialogArgs: dialog ? { name: dialog } : null };
	let board = build(ctx);
	if (page.stale) board = staleBoard(board);
	if (dialog) {
		const d = dialogFor(dialog, ctx);
		board.dlg = { ...d, sec: d.sec || [{ label: "Cancel", action: "close-dialog" }] };
	}
	return { board, form: ctx.form, people: peopleOf(data) };
}

async function settle() {
	for (let i = 0; i < 4; i += 1) await nextTick();
}

beforeAll(() => {
	globalThis.frappe.session = { user: "" };
	globalThis.frappe.set_route = () => {};
});
afterEach(() => {
	document.body.innerHTML = "";
});

describe.each(SCREENS)("$board — $viewer on the $stage world", (screen) => {
	it("is built out of the board's own elements", async () => {
		globalThis.frappe.session.user = USERS[screen.viewer];
		const { board, form, people } = boardFor(screen);
		const wrapper = mount(EvlBoard, { props: { board, form, people }, attachTo: document.body });
		await settle();
		const result = compareSkeletons(bidEvaluationSkeleton(screen.board), skeletonOf(wrapper.element), { departures: DEPARTURES[screen.board] || [] });
		const message = formatMismatch(`${screen.board} (${screen.stage}, ${screen.viewer})`, result);
		wrapper.unmount();
		expect(message, message).toBe("");
	}, 30_000);
});

describe.each(WORKSPACE)("$board — $viewer's workspace on the $stage world", (screen) => {
	it("is built out of the board's own elements", async () => {
		globalThis.frappe.session.user = USERS[screen.viewer];
		const form = { query: "", state: "", ...screen.form };
		const wrapper = mount(EvlBoard, { props: { board: workspaceBoard({ work: world(screen.stage, screen.viewer).work, form }), form }, attachTo: document.body });
		await settle();
		const result = compareSkeletons(bidEvaluationSkeleton(screen.board), skeletonOf(wrapper.element), { departures: DEPARTURES[screen.board] || [] });
		const message = formatMismatch(`${screen.board} (${screen.stage}, ${screen.viewer})`, result);
		wrapper.unmount();
		expect(message, message).toBe("");
	}, 30_000);
});

// The supplier's own request in the portal (390 px), from the supplier's captured reads.
export const SUPPLIER = [
	["D06-SUPPLIER", "sent"],
	["D06-RECEIVED", "replied"],
	["D06-LATE", "no-reply"],
	["D06-LATE-RECEIVED", "late-reply"],
	["D06-CLOSED", "withdrawn"],
	["D06-FINAL-CLOSED", "resolved"],
	["D06-FINAL-CLOSED-NR", "no-reply-closed"],
].map(([board, stage]) => ({ board, stage }));

describe.each(SUPPLIER)("$board — the supplier on the $stage world", (screen) => {
	it("is built out of the board's own elements", async () => {
		const own = world(screen.stage, "supplier").own[0];
		const form = { body: own.reply && own.reply.state === "Draft" ? own.reply.body : "", attachments: [] };
		const wrapper = mount(EvlBoard, { props: { board: supplierBoard(own, form), form }, attachTo: document.body });
		await settle();
		const result = compareSkeletons(bidEvaluationSkeleton(screen.board), skeletonOf(wrapper.element), { departures: DEPARTURES[screen.board] || [] });
		const message = formatMismatch(`${screen.board} (${screen.stage}, supplier)`, result);
		wrapper.unmount();
		expect(message, message).toBe("");
	}, 30_000);
});

describe("the COVERED claim", () => {
	it("lists exactly the boards this spec compares", () => {
		expect([...COVERED].sort()).toEqual([...SCREENS, ...WORKSPACE, ...SUPPLIER].map((s) => s.board).sort());
	});
});
