// Structural fidelity for the Bid Opening screens against their boards
// (BOP-CHG-001 v0.10, `14_bid_opening/design/Bid Opening Artboards v0.9.2.dc.html`).
// Each board is mounted with the server's own answer for its state and viewer
// — captured from the browser world by
// `bid_opening.seeds.playwright_ui_fixtures.capture`, never written by hand —
// and compared container for container. Local modes (a form the viewer opens)
// are reached by clicking, as a person would. Registered departures are the
// only allowed differences.
import { afterEach, beforeAll, describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import { nextTick } from "vue";

import { bidOpeningSkeleton } from "../../../../../tests/ui/fidelity/board.js";
import { compareSkeletons, formatMismatch, skeletonOf } from "../../../../../tests/ui/fidelity/skeleton.js";
import { COVERED, DEPARTURES } from "../../../../../tests/ui/fidelity/departures/bid-opening.js";

import CompletedScreen from "./screens/CompletedScreen.vue";
import OpenBidsScreen from "./screens/OpenBidsScreen.vue";
import PrepareScreen from "./screens/PrepareScreen.vue";
import RecordScreen from "./screens/RecordScreen.vue";

const FIXTURES = import.meta.glob("./fixtures/*.json", { eager: true, import: "default" });
const USERS = { ao: "pw.tnd.ao@example.test", chair: "pw.req.hopf@example.test", member: "pw.tnd.officer@example.test", independent: "pw.bop.independent@example.test", auditor: "pw.req.auditor@example.test", admin: "Administrator" };

export function world(stage, viewer) {
	const all = FIXTURES[`./fixtures/${stage}.json`];
	if (!all) throw new Error(`no captured world for ${stage}; run capture`);
	const data = all[viewer];
	if (!data) throw new Error(`${viewer} cannot read the ${stage} world`);
	return JSON.parse(JSON.stringify(data));
}

async function settle() {
	for (let i = 0; i < 4; i += 1) await nextTick();
}
const click = (testid) => async (wrapper) => {
	await wrapper.find(`[data-testid="${testid}"]`).trigger("click");
	await settle();
};
async function addMember(wrapper, user, role) {
	await wrapper.find('[data-testid="bop-add-member"]').trigger("click");
	await settle();
	await wrapper.find('[data-testid="bop-add-member-person"]').setValue(user);
	await wrapper.find('[data-testid="bop-add-member-role"]').setValue(role);
	await wrapper.find('[data-testid="bop-add-member-confirm"]').trigger("click");
	await settle();
}

const REFUSAL = {
	ok: false,
	code: "BOP_INDEPENDENT_MEMBER_REQUIRED",
	guard: { reason_code: "BOP_INDEPENDENT_MEMBER_REQUIRED", headline: "The opening committee needs an independent third member", message: "Appoint a committee member who was not involved in processing this Tender and will not evaluate it.", fixes: [{ fix_id: "add_member", label: "Add an independent third member", kind: "focus", primary: true }] },
};

// board, component, captured stage, viewer, extra props, what the viewer does first
const SCREENS = [
	["a1", PrepareScreen, "prepared", "ao", {}, async (w) => {
		await addMember(w, USERS.chair, "Chair and recorder");
		await addMember(w, USERS.member, "Member");
		await addMember(w, USERS.independent, "Independent member");
	}],
	["a2", PrepareScreen, "prepared", "ao", {}, async (w) => {
		await addMember(w, USERS.chair, "Chair and recorder");
		await addMember(w, USERS.member, "Member");
		await w.setProps({ refusal: REFUSAL }); // what Appoint committee returned
		await settle();
	}],
	["a3", PrepareScreen, "appointed", "ao"],
	["a4", PrepareScreen, "appointed", "ao", {}, click("bop-open-arrangements")],
	["a5", PrepareScreen, "published", "ao"],
	["c1", OpenBidsScreen, "joined", "chair"],
	["c2", OpenBidsScreen, "missing", "chair"],
	["c2b", OpenBidsScreen, "access", "chair"],
	["c2c", OpenBidsScreen, "not-available", "chair"],
	["c2d", OpenBidsScreen, "notify-failed", "chair"],
	["c3", OpenBidsScreen, "ready", "chair"],
	["c4", OpenBidsScreen, "started", "chair"],
	["c5", OpenBidsScreen, "opened", "member"],
	["c6", OpenBidsScreen, "opened", "chair"],
	["c7", OpenBidsScreen, "read-out", "chair", {}, click("bop-open-request")],
	["c8", OpenBidsScreen, "answered", "independent", {}, click("bop-open-account")],
	["c8b", OpenBidsScreen, "account", "chair"],
	["c13", OpenBidsScreen, "answered", "chair", {}, click("bop-open-comment")],
	["c13b", OpenBidsScreen, "commented", "chair"],
	["c9", OpenBidsScreen, "answered", "chair"],
	["c10", OpenBidsScreen, "member-left", "chair"],
	["c11", OpenBidsScreen, "unreadable", "chair"],
	["c11b", OpenBidsScreen, "resolved", "chair"],
	["c11c", OpenBidsScreen, "unresolved", "chair"],
	["c11e", OpenBidsScreen, "unresolved", "ao"],
	["c11d", OpenBidsScreen, "mismatch", "chair"],
	["c12", OpenBidsScreen, "cancelled", "chair"],
	["z1", OpenBidsScreen, "empty-started", "chair"],
	["n1", OpenBidsScreen, "not-held-due", "ao"],
	["n2", OpenBidsScreen, "not-held", "ao"],
	["r1", RecordScreen, "ended", "chair"],
	["r2", RecordScreen, "ended", "chair", {}, click("bop-prepare-record")],
	["r3", RecordScreen, "member-signed", "independent"],
	["r4", RecordScreen, "member-signed", "member"],
	["r5", RecordScreen, "changed", "member"],
	["r6", CompletedScreen, "complete", "chair"],
	["h1", CompletedScreen, "complete", "auditor"],
	["h2", CompletedScreen, "empty-complete", "chair"],
	["h3", CompletedScreen, "complete", "admin"],
	["h4", CompletedScreen, "complete", "chair", { sub: "correct" }],
	["h5", CompletedScreen, "corrected", "chair"],
].map(([board, component, stage, viewer, props, before]) => ({ board, name: component.__name || "Screen", component, stage, viewer, props: props || {}, before }));

beforeAll(() => {
	globalThis.frappe.session = { user: "" };
	globalThis.frappe.set_route = () => {};
});
afterEach(() => {
	document.body.innerHTML = "";
});

describe.each(SCREENS)("$board — $name as $viewer on the $stage world", ({ board, component, stage, viewer, props, before }) => {
	it("is built out of the board's own elements", async () => {
		globalThis.frappe.session.user = USERS[viewer];
		const wrapper = mount(component, { props: { data: world(stage, viewer), ...props }, attachTo: document.body });
		await settle();
		if (before) await before(wrapper);
		const result = compareSkeletons(bidOpeningSkeleton(board), skeletonOf(wrapper.element), { departures: DEPARTURES[board] || [] });
		const message = formatMismatch(`${board} (${stage}, ${viewer})`, result);
		wrapper.unmount();
		expect(message, message).toBe("");
	}, 30_000);
});

describe("the COVERED claim", () => {
	it("lists exactly the boards this spec compares", () => {
		expect([...COVERED].sort()).toEqual(SCREENS.map((s) => s.board).sort());
	});
});
