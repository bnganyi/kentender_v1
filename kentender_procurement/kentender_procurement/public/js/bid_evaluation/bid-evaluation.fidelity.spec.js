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
import { build, dialogFor } from "./screens/index.js";
import { peopleOf } from "./screens/common.js";

const FIXTURES = import.meta.glob("./fixtures/*.json", { eager: true, import: "default" });
export const USERS = {
	ao: "pw.tnd.ao@example.test", hop: "pw.req.hopf@example.test", secretary: "pw.tnd.officer@example.test", chair: "pw.evl.chair@example.test",
	member: "pw.evl.member@example.test", member_2: "pw.evl.member2@example.test", auditor: "pw.req.auditor@example.test", admin: "Administrator",
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

// board, captured stage, viewer, route (sub, id), form values the viewer set, dialog opened
export const SCREENS = [
	["D02-A", "prepared", "ao"],
	["D02-S", "appointed", "hop"],
	["D02-D", "assigned", "chair", ["declaration"], { choice: "No conflict to declare" }],
	["D02-CONFLICT", "assigned", "chair", ["declaration"], { choice: "Declare a conflict" }],
	["D02-REPLACE", "conflict", "ao", ["replace"]],
	["D02-INTAKE-FIRST", "intake-first", "ao"],
	["D02-INTAKE-FIRST-HOP", "intake-first", "hop"],
	["D02-UNABLE", "declared", "member", ["unable"]],
	["D02-NO-BIDS", "no-bids", "chair"],
	["S-OPENING-AWAITED", "declared", "chair"],
	["D03", "concern", "chair"],
	["D03-READY", "resolved", "chair"],
	["D04", "reviewing", "member", ["bid", "@bid"]],
	["D04-AUTO", "reviewing", "member", ["bid", "@bid"], { show: "Automatic checks" }],
	["D04-CONCERN", "reviewing", "member", ["bid", "@bid"], {}, "concern"],
	["D04-FAIL", "failed", "member", ["bid", "@bid"], { show: "All checks" }],
	["D05-START", "discussion", "chair"],
	["D05-JOIN", "discussion", "member"],
	["D05", "joined", "secretary"],
	["D05-CONCLUSION", "joined", "chair", [""], { decision: "conclusion", result: "Meets" }],
	["D05-CHAIR", "noted", "chair"],
	["D05-MEMBER", "authorised", "member"],
	["D05-DISAGREE", "authorised", "member", [""], {}, "disagree"],
	["D05-RECORD", "resolved", "secretary", ["record"]],
	["D05-RECORD-MEMBER", "resolved", "chair", ["record"]],
	["D05-RECORD-AUDITOR", "resolved", "auditor", ["record"]],
	["D06-SEND", "authorised", "secretary", ["clarification", "@clarification"]],
	["D06-OUTCOME", "outcome", "chair"],
	["D07-DRAFT", "resolved", "secretary", ["report"]],
	["D07-PREVIEW", "resolved", "secretary", ["report", "preview"]],
	["D07-SIGN", "signing", "member", ["report"]],
	["D07-CONCERN", "signing", "member", ["report"], {}, "concern"],
	["D07-REVISE", "signing", "secretary", ["report"]],
	["D07-REVISE-DLG", "signing", "secretary", ["report"], {}, "revise"],
	["D07-WAIT", "chair-signed", "chair", ["report"]],
	["D07-SENT", "report-sent", "chair", ["report"]],
	["D07-HOP", "report-sent", "hop", ["report"]],
	["D07-HOP-RETURN", "report-sent", "hop", ["report"], {}, "return"],
	["S-AUDITOR", "report-sent", "auditor", ["report"]],
	["D08-PAUSED", "paused", "chair"],
	["D08-CANCELLED", "cancelled", "chair"],
].map(([board, stage, viewer, route, form, dialog]) => ({ board, stage, viewer, route: route || [""], form: form || {}, dialog: dialog || "" }));

export function boardFor({ stage, viewer, route, form, dialog }) {
	const captured = world(stage, viewer);
	const data = captured.data;
	const ids = { "@bid": captured.bid && captured.bid.bid, "@clarification": ((data.work || {}).clarifications || []).slice(-1).map((c) => c.name)[0] };
	const [sub, ...rest] = route;
	const id = rest.map((x) => ids[x] || x).join("/");
	const ctx = { data, sub: sub || "", id, user: USERS[viewer], form: { ...form }, errors: { members: {} }, bid: captured.bid, report: captured.report,
		record: captured.record, candidates: captured.candidates, unconfirmed: false, dialogArgs: dialog ? { name: dialog } : null };
	const board = build(ctx);
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

describe("the COVERED claim", () => {
	it("lists exactly the boards this spec compares", () => {
		expect([...COVERED].sort()).toEqual(SCREENS.map((s) => s.board).sort());
	});
});
