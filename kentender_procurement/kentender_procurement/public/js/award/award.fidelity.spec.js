// Structural fidelity for the Award screens against their 47 boards
// (AWD-CHG-001 v0.4, `16_award/design/Award Artboards.dc.html`). Each board is
// built by the live screen builders from the server's own answers for its
// stage and viewer — captured from the synthetic Award worlds by
// `award.seeds.playwright_ui_fixtures.capture_all`, never written by hand —
// mounted in `AwdBoard.vue` and compared container for container with the
// board rendered from the design tool's own template. Registered departures
// are the only allowed differences.
import { afterEach, beforeAll, describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import { nextTick } from "vue";

import { awardBoardIds, awardDialogSkeleton, awardKit, awardSkeleton } from "../../../../../tests/ui/fidelity/board.js";
import { compareSkeletons, formatMismatch, skeletonOf } from "../../../../../tests/ui/fidelity/skeleton.js";
import { COVERED, DEPARTURES } from "../../../../../tests/ui/fidelity/departures/award.js";

import AwdBoard from "./board/AwdBoard.vue";
import { recordBoard, technicalBoard } from "./screens/record.js";
import { workspaceBoard } from "./screens/workspace.js";
import { dialogFor } from "./screens/dialogs.js";
import { supplierBoard } from "./portal/supplier.js";

const FIXTURES = import.meta.glob("./fixtures/*.json", { eager: true, import: "default" });

function world(stage) {
	const all = FIXTURES[`./fixtures/${stage}.json`];
	if (!all) throw new Error(`no captured world for ${stage}; run capture_all`);
	return JSON.parse(JSON.stringify(all));
}

// board, stage, viewer, extra ({ route, dialog, org, workspace })
export const SCREENS = [
	["D01", "received", "hop", { workspace: true }],
	["D01e", "accepted", "hop", { workspace: true }],
	["D02", "received", "hop"],
	["D03", "signed", "ao"],
	["D04", "notified", "mary", { org: "Afya Digital Supplies Limited" }],
	["D05", "accepted", "hop"],
	["D06", "delivered", "hop"],
	["D07", "request", "hop"],
	["D07c", "request-closed", "hop", { route: ["requests", "@request"] }],
	["V01", "returned", "hop"],
	["V02", "source-incomplete", "hop"],
	["V03", "expired", "hop"],
	["V04", "no-award", "hop"],
	["V05", "notice-failed", "hop"],
	["V06", "declined", "hop"],
	["V07", "no-response", "hop"],
	["V08", "order-hold", "hop"],
	["V09", "post-decision-correction", "hop"],
	["V10", "receiver-down", "hop"],
	["V11", "cancelled", "hop"],
	["V12", "signing-unavailable", "hop"],
	["V13", "notified", "david", { org: "Afya Digital Supplies Limited" }],
	["V14", "unsuccessful", "mary", { org: "Afya Digital Supplies Limited" }],
	["V15", "rules-unverified", "hop"],
	["V15s", "status-unknown", "hop"],
	["V16", "technical", "daniel"],
	["V17", "correction-decision", "ao"],
	["V18", "tie", "hop"],
	["V19", "correction-authorised", "hop"],
	["V20", "corrected-report", "hop"],
	["V21", "closed-correction", "hop"],
	["V22", "late-response", "mary", { org: "Afya Digital Supplies Limited" }],
	["V23", "corrected-opinion", "ao"],
	["V23p", "corrected-opinion-positive", "ao"],
	["V24", "revised-held", "hop"],
	["V25", "revised-ready", "ao"],
	["X01", "notified", "mary", { org: "Afya Digital Supplies Limited", dialog: "accept" }],
	["X02", "notified", "mary", { org: "Afya Digital Supplies Limited", dialog: "decline" }],
	["X03", "received", "hop", { dialog: "record-restriction" }],
	["X04", "order-hold", "hop", { dialog: "record-outcome", issue: "Review/order" }],
	["X05", "challenge-hold", "hop", { dialog: "record-outcome", issue: "Review/order" }],
	["X06", "post-decision-correction", "hop", { dialog: "review-correction", issue: "Source correction" }],
	["X07", "received", "hop", { dialog: "return-report" }],
	["X08", "signed", "ao", { dialog: "return-for-correction" }],
	["X09", "signed", "ao", { dialog: "record-no-award" }],
	["X10", "declined", "hop", { dialog: "record-next-action", issue: "Supplier response" }],
	["X11", "notified", "mary", { org: "Afya Digital Supplies Limited", dialog: "request-explanation" }],
].map(([board, stage, viewer, extra]) => ({ board, stage, viewer, ...(extra || {}) }));

function boardFor(s) {
	const w = world(s.stage);
	if (s.workspace) return workspaceBoard(w[s.viewer].workspace);
	if (s.org) {
		const views = w[s.viewer] || {};
		const n = Object.values(views).find((v) => v.organisation_name === s.org);
		if (!n) throw new Error(`${s.viewer} has no notice in ${s.stage}`);
		let b = supplierBoard(n);
		if (s.dialog) b = { ...b, dlg: dialogFor(s.dialog, { wording: n.accept_wording }, n) };
		return b;
	}
	const d = w[s.viewer].record;
	if (d.technical) return technicalBoard(d);
	const ids = { "@request": (d.correspondence || []).map((c) => c.request)[0] };
	const [sub, ...rest] = s.route || [];
	let b = recordBoard(d, { sub: sub || "", id: rest.map((x) => ids[x] || x).join("/") });
	if (s.dialog) {
		const issue = s.issue ? ((d.outstanding || []).find((o) => o.type === s.issue) || {}).issue : undefined;
		b = { ...b, dlg: dialogFor(s.dialog, { issue }, d) };
	}
	return b;
}

async function settle() {
	for (let i = 0; i < 4; i += 1) await nextTick();
}

function oracle(id, dialogOnly) {
	return dialogOnly ? awardDialogSkeleton(id) : awardSkeleton(id);
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
		const board = boardFor(screen);
		const wrapper = mount(AwdBoard, { props: { board, form: {} }, attachTo: document.body });
		await settle();
		const dialogOnly = screen.board.startsWith("X");
		const live = dialogOnly ? wrapper.element.querySelector(".kt-dialog") : wrapper.element;
		const result = compareSkeletons(oracle(screen.board, dialogOnly), skeletonOf(live), { departures: DEPARTURES[screen.board] || [] });
		const message = formatMismatch(`${screen.board} (${screen.stage}, ${screen.viewer})`, result);
		wrapper.unmount();
		expect(message, message).toBe("");
	}, 30_000);
});

describe("the COVERED claim", () => {
	it("lists exactly the boards this spec compares, and every board is compared", () => {
		expect([...COVERED].sort()).toEqual(SCREENS.map((s) => s.board).sort());
		expect([...awardBoardIds()].sort()).toEqual([...COVERED].sort());
		expect(awardKit().BOARDS.length).toBe(47);
	});
});
