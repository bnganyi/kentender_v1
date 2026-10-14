// Structural fidelity for the Contracts screens built in Phase 3 against their boards (CM-CHG-001 v0.8 section 10.3; plan Phase 3, tracker CM8-315):
// D-ERR (record load error) and D-DENIED (shared denial page). Each is built by the real page component from a stubbed read answer and compared container
// for container with the board rendered from the design tool's own template. Registered departures (`tests/ui/fidelity/departures/contracts.js`) are the
// only allowed differences. The page lands on the workspace; the boards are the states that replace its content.
import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import { mount, flushPromises } from "@vue/test-utils";
import { ref } from "vue";

import { cmSkeleton } from "../../../../../tests/ui/fidelity/board.js";
import { compareSkeletons, formatMismatch, skeletonOf } from "../../../../../tests/ui/fidelity/skeleton.js";
import { COVERED, DEPARTURES } from "../../../../../tests/ui/fidelity/departures/contracts.js";

const answer = { value: null };
vi.mock("./data/api.js", () => ({ getWorkspace: () => (answer.value instanceof Error ? Promise.reject(answer.value) : Promise.resolve(answer.value)) }));

import Contracts from "./Contracts.vue";
import StatePage from "./components/StatePage.vue";

// board -> how the built screen is produced. D-ERR is the page failing to load; D-DENIED is the contract-level denial, which has no route until the
// contract record exists (Phase 4), so the same state component is mounted in the page's own sheet with the board's own message and action.
const SCREENS = [
	{ board: "D-ERR", build: () => mount(Contracts, { attachTo: document.body, global: pageGlobals() }) , answer: new Error("down") },
	{ board: "D-DENIED", build: () => mount({ template: '<div class="kt-page"><StatePage tone="lock" message="You do not have access to this contract." :secondary="[\'Back to contracts\']" /></div>', components: { StatePage } }, { attachTo: document.body, global: pageGlobals() }) },
];

function pageGlobals() {
	return { config: { globalProperties: { __: (text) => text, frappe: globalThis.frappe } } };
}

beforeAll(() => {
	globalThis.__ = (text) => text;
	globalThis.frappe = { session: { user: "" }, set_route: () => {}, boot: { user: { roles: [] } } };
	globalThis.kentender_core = {
		industry: { mountPageRail: () => ({ update() {}, unmount() {} }) },
		desk_page: { useRoute: () => ({ route: ref(["contracts"]), epoch: ref(0), go() {}, isShown: ref(true) }) },
	};
});
afterEach(() => {
	document.body.innerHTML = "";
});

describe.each(SCREENS)("$board", (screen) => {
	it("is built out of the board's own elements", async () => {
		answer.value = screen.answer || null;
		const wrapper = screen.build();
		await flushPromises();
		const live = wrapper.element.classList.contains("kt-page") ? wrapper.element : wrapper.element.querySelector(".kt-page");
		const result = compareSkeletons(cmSkeleton(screen.board), skeletonOf(live), { departures: DEPARTURES[screen.board] || [] });
		const message = formatMismatch(screen.board, result);
		wrapper.unmount();
		expect(message, message).toBe("");
	}, 30_000);
});

describe("the COVERED claim", () => {
	it("lists exactly the boards this spec compares", () => {
		expect([...COVERED].sort()).toEqual(SCREENS.map((s) => s.board).sort());
	});
});
