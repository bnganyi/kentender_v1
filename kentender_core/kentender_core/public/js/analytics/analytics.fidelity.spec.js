// Structural fidelity for the Analytics page against its boards (ANL-CHG-001 v0.8 §10A, design/Analytics/*.dc.html).
// No browser, no site: each board is mounted from the server's own answer for it, the golden payloads in
// fixtures/ANL-DES-*.json (written by tests/analytics_goldens.write_all from the real service, never by hand), and
// compared with the board's markup, read through tests/ui/fidelity/board.js, in two ways:
//   1. the container skeleton (what the page is built out of, and how it nests), and
//   2. the ordered landmark texts (headings, labels, tabs, table headings, buttons, links, column headings).
// Registered departures (tests/ui/fidelity/departures/analytics.js) are the only allowed differences; a stale entry fails.
import { flushPromises, mount } from "@vue/test-utils";
import { ref } from "vue";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("./data/analyticsApi.js", () => ({ analyticsApi: { load: vi.fn(), access: vi.fn() } }));

import { analyticsBoardIds, analyticsScope, analyticsSkeleton, landmarkTexts } from "../../../../../tests/ui/fidelity/board.js";
import { compareSkeletons, formatMismatch, skeletonOf } from "../../../../../tests/ui/fidelity/skeleton.js";
import { COVERED, DEPARTURES } from "../../../../../tests/ui/fidelity/departures/analytics.js";
import Analytics from "./Analytics.vue";
import { analyticsApi } from "./data/analyticsApi.js";

const FIXTURES = import.meta.glob("./fixtures/ANL-DES-*.json", { eager: true, import: "default" });
const payload = (id) => {
	const found = FIXTURES[`./fixtures/ANL-DES-${id}.json`];
	if (!found) throw new Error(`no golden payload for ANL-DES-${id}; run analytics_goldens.write_all`);
	return JSON.parse(JSON.stringify(found));
};

// board, the golden payload that is its captured server answer, and how the page is put in the board's state.
//   21X   the Overview payload with the definitions opened (the board draws it expanded)
//   31G   the loading state: the page mounted while its one read is still pending (the board draws no data)
//   every other board has its own golden payload, which also gives its route.
export const SCREENS = [
	{ board: "ANL-DES-21", golden: "21" },
	{ board: "ANL-DES-21X", golden: "21", open: true },
	{ board: "ANL-DES-22", golden: "22" },
	{ board: "ANL-DES-23", golden: "23" },
	{ board: "ANL-DES-24", golden: "24" },
	{ board: "ANL-DES-25", golden: "25" },
	{ board: "ANL-DES-26", golden: "26" },
	{ board: "ANL-DES-27", golden: "27" },
	{ board: "ANL-DES-28", golden: "28" },
	{ board: "ANL-DES-29", golden: "29" },
	{ board: "ANL-DES-29F", golden: "29F" },
	{ board: "ANL-DES-30", golden: "30" },
	{ board: "ANL-DES-30B", golden: "30B" },
	{ board: "ANL-DES-31A", golden: "31A" },
	{ board: "ANL-DES-31B", golden: "31B" },
	{ board: "ANL-DES-31C", golden: "31C" },
	{ board: "ANL-DES-31D", golden: "31D" },
	{ board: "ANL-DES-31E", golden: "31E" },
	{ board: "ANL-DES-31F", golden: "31F" },
	{ board: "ANL-DES-31G", golden: null, pending: true },
	{ board: "ANL-DES-31H", golden: "31H" },
	{ board: "ANL-DES-31J", golden: "31J" },
];

const routeRef = ref(["analytics"]);
function installGlobals() {
	routeRef.value = ["analytics"];
	globalThis.kentender_core = {
		desk_page: {
			useRoute: () => ({ route: routeRef, epoch: ref(0), go() {}, isShown: () => true }),
			createSequenceGuard() {
				let token = 0;
				return { next: () => ++token, isCurrent: (c) => c === token };
			},
			createScreenCache() {
				const store = new Map();
				return { get: (k) => store.get(k), has: (k) => store.has(k), set: (k, v) => store.set(k, v), remove: (k) => store.delete(k), clear: () => store.clear() };
			},
		},
	};
	globalThis.frappe.set_route = vi.fn();
	globalThis.frappe.router = { route: vi.fn() };
}
function urlOf(data) {
	const f = data.filters;
	const q = new URLSearchParams();
	if (f.fy) q.set("fy", f.fy);
	if (f.dept) q.set("dept", f.dept);
	if (f.state) q.set("state", f.state);
	return "/desk/analytics" + (data.tab && data.tab !== "overview" ? "/" + data.tab : "") + (q.toString() ? "?" + q : "");
}

async function mountBoard(screen) {
	if (screen.pending) {
		window.history.pushState(null, "", "/desk/analytics");
		analyticsApi.load.mockReturnValue(new Promise(() => {}));
	} else {
		const data = payload(screen.golden);
		window.history.pushState(null, "", urlOf(data));
		analyticsApi.load.mockResolvedValue(data);
	}
	const wrapper = mount(Analytics, { attachTo: document.body, global: { mocks: { __: globalThis.__, frappe: globalThis.frappe } } });
	await flushPromises();
	if (screen.open) {
		await wrapper.get('[data-testid="kt-anl-definitions-toggle"]').trigger("click");
		await flushPromises();
	}
	return wrapper;
}

beforeEach(() => {
	document.body.innerHTML = "";
	vi.clearAllMocks();
	installGlobals();
});
afterEach(() => {
	document.body.innerHTML = "";
});

// ---------------------------------------------------------------------------------------------------------------
// The text comparison: the board's ordered landmark texts must all appear, in order, among the page's. A page text
// no board text accounts for must be registered by its text; a board text the page does not draw, as `omits`.
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
	const extra = built.filter((item, i) => !consumed.has(i) && !allowedExtra.has(item.text));
	return { missing, extra };
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

// The shared skeleton comparison matches landmarks by their design-system class, not by element: a board's
// `<details class="kt-disclosure">` and a page's `<div class="kt-disclosure">` are the same landmark to it. The
// element a landmark is built from matters too (a `summary` is not a `button`), so this compares, for each landmark
// the board draws, the elements the page builds it from. A difference must be registered with `{ tag: "<landmark>" }`.
function tagsByLandmark(nodes, into = new Map()) {
	for (const node of nodes) {
		for (const name of node.names) {
			if (!into.has(name)) into.set(name, new Set());
			into.get(name).add(node.tag);
		}
		tagsByLandmark(node.children, into);
	}
	return into;
}
function compareTags(board, built, departures) {
	const allowed = new Set(departures.map((d) => d.tag).filter(Boolean));
	const boardTags = tagsByLandmark(board);
	const builtTags = tagsByLandmark(built);
	const out = [];
	for (const [name, tags] of boardTags) {
		const live = builtTags.get(name);
		if (!live || [...tags].every((tag) => live.has(tag))) continue;
		if (!allowed.has(name)) out.push({ name, board: [...tags], built: [...live] });
	}
	return out;
}
function formatTags(label, diffs) {
	if (!diffs.length) return "";
	return [`${label}: ${diffs.length} landmark(s) built from a different element than the board's and unregistered.`, ...diffs.map((d) => `  UNREGISTERED: ${d.name} is <${d.board.join("|")}> on the board, <${d.built.join("|")}> in the page`)].join("\n");
}

function departuresFor(board) {
	return DEPARTURES[board] || [];
}

function compareBoard(screen, root, departures = departuresFor(screen.board)) {
	const board = analyticsSkeleton(screen.board);
	const built = skeletonOf(root);
	const skeleton = compareSkeletons(board, built, { departures: departures.filter((d) => !d.tag && (d.path || d.testid || d.replaces || d.omits)) });
	const texts = compareTexts(landmarkTexts(analyticsScope(screen.board)), landmarkTexts(root), departures);
	const tags = compareTags(board, built, departures);
	return { skeleton, texts, tags };
}

const messageOf = (screen, { skeleton, texts, tags }) =>
	[formatMismatch(`${screen.board} skeleton`, skeleton), formatTexts(`${screen.board} text`, texts), formatTags(`${screen.board} elements`, tags)].filter(Boolean).join("\n");

describe.each(SCREENS)("$board", (screen) => {
	it("is built out of the board's own containers, in its own order, with its own landmark texts", async () => {
		const wrapper = await mountBoard(screen);
		const root = wrapper.element.querySelector("main");
		const result = compareBoard(screen, root);
		const message = messageOf(screen, result);
		wrapper.unmount();
		expect(message, message).toBe("");
	}, 30_000);

	it("carries no registered departure that the comparison no longer needs", async () => {
		const departures = departuresFor(screen.board);
		if (!departures.length) return;
		const wrapper = await mountBoard(screen);
		const root = wrapper.element.querySelector("main");
		const stale = [];
		departures.forEach((entry, index) => {
			const rest = departures.filter((_, i) => i !== index);
			const without = compareBoard(screen, root, rest);
			const need = without.skeleton.missing.length + without.skeleton.extra.length + without.texts.missing.length + without.texts.extra.length + without.tags.length;
			if (need === 0) stale.push(entry.path || entry.text || entry.tag || (entry.omits || entry.omitsText || []).join(","));
		});
		wrapper.unmount();
		expect(stale, `stale departures for ${screen.board}`).toEqual([]);
	}, 30_000);
});

describe("the departures registry", () => {
	it("gives every entry a reason and an authority, and names only boards this spec compares", () => {
		for (const [board, entries] of Object.entries(DEPARTURES)) {
			expect(COVERED, `${board} is not in COVERED`).toContain(board);
			expect(entries.length).toBeGreaterThan(0);
			for (const entry of entries) {
				expect(entry.reason, `${board}: a departure with no reason`).toBeTruthy();
				expect(entry.authority, `${board}: a departure with no authority`).toBeTruthy();
				expect(entry.path || entry.text || entry.tag || entry.testid || entry.replaces || entry.omits || entry.omitsText, `${board}: a departure that names nothing`).toBeTruthy();
			}
		}
	});
});

describe("the COVERED claim", () => {
	it("lists exactly the boards this spec compares, and every board the files draw is compared", () => {
		expect([...COVERED].sort()).toEqual(SCREENS.map((s) => s.board).sort());
		expect(analyticsBoardIds().sort()).toEqual([...COVERED].sort());
	});
	it("maps each board to a golden payload that exists (31G is the loading state: the call stays pending)", () => {
		for (const screen of SCREENS) {
			if (!screen.pending) expect(FIXTURES[`./fixtures/ANL-DES-${screen.golden}.json`], screen.board).toBeTruthy();
		}
	});
});

describe("the comparison can fail (negative controls)", () => {
	it("reports a page mounted on one board's payload when it is held against another board", async () => {
		const wrapper = await mountBoard(SCREENS.find((s) => s.board === "ANL-DES-21"));
		const root = wrapper.element.querySelector("main");
		const against = compareBoard({ board: "ANL-DES-22" }, root);
		wrapper.unmount();
		expect(messageOf({ board: "ANL-DES-22" }, against)).toContain("MISSING");
	});

	it("reports a container the page drops (the tab bar) and an element it demotes (an h2 turned into a div)", async () => {
		const screen = SCREENS.find((s) => s.board === "ANL-DES-22");
		const wrapper = await mountBoard(screen);
		const root = wrapper.element.querySelector("main");
		root.querySelector(".kt-tabs").remove();
		const heading = root.querySelector("h2");
		const div = document.createElement("div");
		div.innerHTML = heading.innerHTML;
		heading.replaceWith(div);
		const result = compareBoard(screen, root);
		wrapper.unmount();
		const message = messageOf(screen, result);
		expect(message).toContain("MISSING: tabs");
		// the skeleton alone cannot see one h2 of several turned into a div; the landmark text, which names its element, does
		expect(message).toContain('MISSING: <h2> "Outstanding work"');
	});

	it("reports a landmark text the page changes", async () => {
		const screen = SCREENS.find((s) => s.board === "ANL-DES-21");
		const wrapper = await mountBoard(screen);
		const root = wrapper.element.querySelector("main");
		root.querySelector('[data-testid="kt-anl-apply"]').textContent = "Go";
		const message = messageOf(screen, compareBoard(screen, root));
		wrapper.unmount();
		expect(message).toContain('MISSING: <button> "Apply filters"');
		expect(message).toContain('UNREGISTERED: <button> "Go"');
	});
});
