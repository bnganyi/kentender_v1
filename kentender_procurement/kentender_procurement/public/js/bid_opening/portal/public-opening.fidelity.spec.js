// Structural fidelity for the public opening page (BOP-CHG-001 v0.10 §10.5,
// boards p0–p6) against the Bid Opening board pack. Each board is mounted with
// the public answer captured from the browser world for its stage and visitor
// (`playwright_ui_fixtures.capture_public`), inside a stand-in of the portal
// runtime the page is given in the browser.
import { afterEach, describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import { nextTick, ref } from "vue";

import { bidOpeningSkeleton } from "../../../../../../tests/ui/fidelity/board.js";
import { compareSkeletons, formatMismatch, skeletonOf } from "../../../../../../tests/ui/fidelity/skeleton.js";
import { PUBLIC_COVERED, PUBLIC_DEPARTURES } from "../../../../../../tests/ui/fidelity/departures/bid-opening.js";

import PublicOpeningScreen from "./PublicOpeningScreen.vue";

const FIXTURES = import.meta.glob("../fixtures/public-*.json", { eager: true, import: "default" });
const VISITORS = { guest: "Guest", observer: "pw.bop.observer@example.test", supplier: "bids@afya-test.example" };

function view(stage, visitor) {
	const all = FIXTURES[`../fixtures/public-${stage}.json`];
	if (!all) throw new Error(`no captured public world for ${stage}; run capture`);
	const data = Object.entries(all).find(([user]) => user === VISITORS[visitor] || (visitor === "supplier" && !["Guest", VISITORS.observer].includes(user)));
	if (!data) throw new Error(`${visitor} has no captured view of ${stage}`);
	return JSON.parse(JSON.stringify(data[1]));
}

const portal = {
	useRoute: () => ({ epoch: ref(0), route: ref({ path: "", segments: [] }) }),
	createSequenceGuard: () => ({ next: () => 1, isCurrent: () => true }),
	createCommandRunner: () => ({ pending: ref(false), run: () => Promise.resolve(null) }),
	call: () => Promise.resolve(null),
	setTitle: () => {},
};

// board, captured stage, visitor
const BOARDS = [
	["p0", "prepared", "guest"],
	["p1a", "published", "guest"],
	["p1", "joined", "observer"],
	["p2", "answered", "observer"],
	["p3", "complete", "supplier"],
	["p4", "complete-preparing", "supplier"],
	["p5", "complete-requested", "supplier"],
	["p6", "complete", "observer"],
];

afterEach(() => {
	document.body.innerHTML = "";
});

describe.each(BOARDS)("%s — the public page on the %s world for a %s", (board, stage, visitor) => {
	it("is built out of the board's own elements", async () => {
		const wrapper = mount(PublicOpeningScreen, { props: { reference: "TND-MOH-2099-001", initial: view(stage, visitor) }, global: { provide: { portal } }, attachTo: document.body });
		for (let i = 0; i < 3; i += 1) await nextTick();
		const result = compareSkeletons(bidOpeningSkeleton(board), skeletonOf(wrapper.element), { departures: PUBLIC_DEPARTURES[board] || [] });
		const message = formatMismatch(`${board} (${stage}, ${visitor})`, result);
		wrapper.unmount();
		expect(message, message).toBe("");
	}, 30_000);
});

describe("the public COVERED claim", () => {
	it("lists exactly the boards this spec compares", () => {
		expect([...PUBLIC_COVERED].sort()).toEqual(BOARDS.map((b) => b[0]).sort());
	});
});
