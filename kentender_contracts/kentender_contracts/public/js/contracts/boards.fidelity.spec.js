// Structural fidelity of the Contract Management screens against their boards (CM-CHG-001 v0.8 section 10.3; plan Phase 4, gate CM-G04). Each fixture in `fixtures/` is a board the server built
// for a real person at a real step of the ordinary thread (`tests/test_cm_boards.py`, `CM_CAPTURE_BOARDS=1`). The real component draws it, and its landmarks (page, tabs, next step, regions, fact
// rows, tables, fields, disclosures, notices, dialogs) are compared container for container with the board rendered from the design tool's own template. Registered departures
// (`tests/ui/fidelity/departures/contracts.js`) are the only allowed differences; an unregistered addition fails and so does a stale entry.
import { afterEach, beforeAll, describe, expect, it } from "vitest";
import { mount, flushPromises } from "@vue/test-utils";

import { cmDialogSkeleton, cmSkeleton } from "../../../../../tests/ui/fidelity/board.js";
import { compareSkeletons, formatMismatch, skeletonOf } from "../../../../../tests/ui/fidelity/skeleton.js";
import { DEPARTURES } from "../../../../../tests/ui/fidelity/departures/contracts.js";
import { BOARD_PAGES, BOARD_DIALOGS, BOARD_STATES, LIST_PAGES } from "../../../../../tests/ui/fidelity/departures/contracts.js";

import CmBoard from "./components/CmBoard.vue";
import BoardList from "./components/BoardList.vue";

const fixtures = import.meta.glob("./fixtures/*.json", { eager: true, import: "default" });
const board = (name) => {
	const found = fixtures[`./fixtures/${name}.json`];
	if (!found) throw new Error(`no captured fixture for ${name}: run tests/test_cm_boards.py with CM_CAPTURE_BOARDS=1`);
	return JSON.parse(JSON.stringify(found));
};

beforeAll(() => {
	globalThis.__ = (text) => text;
	globalThis.frappe = { session: { user: "" }, set_route: () => {}, boot: { user: { roles: [] } } };
	globalThis.kentender_core = { industry: {} };
});
afterEach(() => {
	document.body.innerHTML = "";
});

function draw(fixture) {
	return mount(CmBoard, { props: { board: board(fixture) }, attachTo: document.body, global: { config: { globalProperties: { __: (t) => t, frappe: globalThis.frappe } } } });
}

describe.each(BOARD_PAGES)("$fixture is $board", ({ fixture, board: id }) => {
	it("is built out of the board's own containers", async () => {
		const wrapper = draw(fixture);
		await flushPromises();
		const live = wrapper.element.classList.contains("kt-page") ? wrapper.element : wrapper.element.querySelector(".kt-page");
		const result = compareSkeletons(cmSkeleton(id), skeletonOf(live), { departures: DEPARTURES[id] || [] });
		const message = formatMismatch(id, result);
		wrapper.unmount();
		expect(message, message).toBe("");
	}, 30_000);
});

describe.each(LIST_PAGES)("$fixture is $board (the list)", ({ fixture, board: id }) => {
	it("is built out of the board's own containers", async () => {
		const wrapper = mount(BoardList, { props: { board: board(fixture) }, attachTo: document.body, global: { config: { globalProperties: { __: (t) => t } } } });
		await flushPromises();
		const result = compareSkeletons(cmSkeleton(id), skeletonOf(wrapper.element), { departures: DEPARTURES[id] || [] });
		const message = formatMismatch(id, result);
		wrapper.unmount();
		expect(message, message).toBe("");
	}, 30_000);
});

describe.each(BOARD_STATES)("$fixture with choice $choose is $board", ({ fixture, board: id, radio: group, choose, shows }) => {
	it("is built out of the board's own containers once the choice is made", async () => {
		const wrapper = draw(fixture);
		await flushPromises();
		expect(wrapper.element.querySelectorAll("textarea").length, "nothing is revealed before the choice").toBe(0);
		const radio = wrapper.element.querySelectorAll(`[data-testid="cm-input-${group}"] input[type="radio"]`)[choose];
		expect(radio, `option ${choose} of ${group} on ${fixture}`).toBeTruthy();
		radio.checked = true;
		radio.dispatchEvent(new Event("change", { bubbles: true }));
		await flushPromises();
		expect(wrapper.element.querySelectorAll("textarea").length, "the choice reveals the description").toBe(shows.textareas);
		expect(wrapper.element.textContent).toContain(shows.text);
		const live = wrapper.element.classList.contains("kt-page") ? wrapper.element : wrapper.element.querySelector(".kt-page");
		const result = compareSkeletons(cmSkeleton(id), skeletonOf(live), { departures: DEPARTURES[id] || [] });
		const message = formatMismatch(id, result);
		wrapper.unmount();
		expect(message, message).toBe("");
	}, 30_000);
});

describe.each(BOARD_DIALOGS)("$fixture opens $board", ({ fixture, action, board: id }) => {
	it("draws the dialog the board draws", async () => {
		const wrapper = draw(fixture);
		await flushPromises();
		const labels = [...wrapper.element.querySelectorAll("button")];
		const button = labels.find((b) => b.textContent.trim() === action);
		expect(button, `${action} is a button on ${fixture}`).toBeTruthy();
		button.click();
		await flushPromises();
		const dialog = wrapper.element.querySelector(".dialog");
		expect(dialog, `${action} opens a dialog`).toBeTruthy();
		const result = compareSkeletons(cmDialogSkeleton(id), skeletonOf(dialog), { departures: DEPARTURES[id] || [] });
		const message = formatMismatch(id, result);
		wrapper.unmount();
		expect(message, message).toBe("");
	}, 30_000);
});

import { COVERED } from "../../../../../tests/ui/fidelity/departures/contracts.js";

describe("the COVERED claim", () => {
	it("lists exactly the boards the two specs compare: the shared pages, the record screens and their dialogs", () => {
		const claimed = new Set(["D-ERR", "D-DENIED", ...LIST_PAGES.map((p) => p.board), ...BOARD_PAGES.map((p) => p.board), ...BOARD_STATES.map((p) => p.board), ...BOARD_DIALOGS.map((d) => d.board)]);
		expect([...COVERED].sort()).toEqual([...claimed].sort());
	});
});
