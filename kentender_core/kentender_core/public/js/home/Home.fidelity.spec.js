// Structural fidelity for the Home page against its sixteen boards (HOME-CHG-001 v0.6 §10B, design/Home/Home.dc.html).
// No browser, no site: each board is mounted on the payload that board draws (fixtures/boards.js) and compared with
// the board's markup, read through tests/ui/fidelity/board.js, in two ways:
//   1. the container skeleton (header, summary columns, regions, the rail, headings, module chips, the design
//      system's spot and status, and each button with its variant), and
//   2. the ordered landmark texts (headings, summary columns, buttons, links).
// Registered departures (tests/ui/fidelity/departures/home.js) are the only allowed differences; a stale entry fails.
import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("./data/homeApi.js", () => ({ homeApi: { load: vi.fn() } }));

import { homeBoardIds, homeScope, homeSkeleton, homeSkeletonOf, landmarkTexts } from "../../../../../tests/ui/fidelity/board.js";
import { compareSkeletons, formatMismatch } from "../../../../../tests/ui/fidelity/skeleton.js";
import { COVERED, DEPARTURES } from "../../../../../tests/ui/fidelity/departures/home.js";
import Home from "./Home.vue";
import { homeApi } from "./data/homeApi.js";
import { BOARD_STATES } from "./fixtures/boards.js";

const mounted = [];
async function mountBoard(board) {
	const state = BOARD_STATES[board]();
	if (state.pending) homeApi.load.mockReturnValue(new Promise(() => {}));
	else homeApi.load.mockResolvedValue(JSON.parse(JSON.stringify(state.payload)));
	const wrapper = mount(Home, { attachTo: document.body, global: { mocks: { __: globalThis.__, frappe: globalThis.frappe } } });
	mounted.push(wrapper);
	await flushPromises();
	return wrapper.element.querySelector("main");
}

beforeEach(() => {
	document.body.innerHTML = "";
	vi.clearAllMocks();
	globalThis.__homeEpoch.value = 0;
});
afterEach(() => {
	while (mounted.length) mounted.pop().unmount();
});

// The board's ordered landmark texts must all appear, in order, among the page's. A page text no board text accounts
// for must be registered by its text; a board text the page does not draw, as `omitsText`.
function compareTexts(board, built, departures) {
	const allowedExtra = new Set(departures.map((d) => d.text).filter(Boolean));
	const allowedMissing = new Set(departures.flatMap((d) => d.omitsText || []));
	const missing = [];
	const consumed = new Set();
	let cursor = 0;
	for (const wanted of board) {
		let found = -1;
		for (let i = cursor; i < built.length; i += 1) {
			if (built[i].text === wanted.text) {
				found = i;
				break;
			}
		}
		if (found === -1) {
			if (!allowedMissing.has(wanted.text)) missing.push(wanted);
			continue;
		}
		consumed.add(found);
		cursor = found + 1;
	}
	return { missing, extra: built.filter((item, i) => !consumed.has(i) && !allowedExtra.has(item.text)) };
}

function formatTexts(label, { missing, extra }) {
	const lines = [];
	if (missing.length) {
		lines.push(`${label}: ${missing.length} landmark text(s) the board draws are not in the page, or are out of order.`);
		for (const m of missing) lines.push(`  MISSING: <${m.tag}> "${m.text}"`);
	}
	if (extra.length) {
		lines.push(`${label}: ${extra.length} landmark text(s) the board does not draw are in the page and unregistered.`);
		for (const e of extra) lines.push(`  UNREGISTERED: <${e.tag}> "${e.text}"`);
	}
	return lines.join("\n");
}

const departuresFor = (board) => DEPARTURES[board] || [];

function compareBoard(board, root, departures = departuresFor(board)) {
	const skeleton = compareSkeletons(homeSkeleton(board), homeSkeletonOf(root), { departures: departures.filter((d) => d.path || d.testid || d.replaces || d.omits) });
	const texts = compareTexts(landmarkTexts(homeScope(board)), landmarkTexts(root), departures);
	return { skeleton, texts };
}

const messageOf = (board, { skeleton, texts }) => [formatMismatch(`${board} skeleton`, skeleton), formatTexts(`${board} text`, texts)].filter(Boolean).join("\n");

// The sixteen boards, by name (tests/ui/fidelity/covered.spec.js checks that every COVERED board is named here).
const BOARDS = [
	"HOME-DES-21", "HOME-DES-21N", "HOME-DES-29", "HOME-DES-22", "HOME-DES-23", "HOME-DES-24", "HOME-DES-25", "HOME-DES-26",
	"HOME-DES-26B", "HOME-DES-27", "HOME-DES-28A", "HOME-DES-28B", "HOME-DES-28C", "HOME-DES-28D", "HOME-DES-28E", "HOME-DES-28F",
];

describe("the boards", () => {
	it("are the sixteen the page compares, no more and no fewer", () => {
		expect(BOARDS).toEqual(COVERED);
		expect(homeBoardIds()).toEqual(BOARDS);
		expect(Object.keys(BOARD_STATES)).toEqual(COVERED);
	});
});

describe.each(COVERED)("%s", (board) => {
	it("is built out of the board's own containers, in its own order, with its own landmark texts", async () => {
		const root = await mountBoard(board);
		const message = messageOf(board, compareBoard(board, root));
		expect(message, message).toBe("");
	}, 30_000);

	it("carries no registered departure that the comparison no longer needs", async () => {
		const departures = departuresFor(board);
		if (!departures.length) return;
		const root = await mountBoard(board);
		const stale = [];
		departures.forEach((entry, index) => {
			const without = compareBoard(board, root, departures.filter((_, i) => i !== index));
			const need = without.skeleton.missing.length + without.skeleton.extra.length + without.texts.missing.length + without.texts.extra.length;
			if (need === 0) stale.push(entry.path || entry.text || (entry.omits || entry.omitsText || []).join(","));
		});
		expect(stale, `stale departures for ${board}`).toEqual([]);
	}, 30_000);
});

describe("the departures registry", () => {
	it("gives every entry a reason and an authority, and names only boards this spec compares", () => {
		for (const [board, entries] of Object.entries(DEPARTURES)) {
			expect(COVERED, `${board} is not in COVERED`).toContain(board);
			expect(entries.length).toBeGreaterThan(0);
			for (const entry of entries) {
				expect(entry.reason, `${board}: an entry has no reason`).toBeTruthy();
				expect(entry.authority, `${board}: an entry has no authority`).toBeTruthy();
			}
		}
	});
});
