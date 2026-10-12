/**
 * The comparator's own tests, written from the three shapes that have actually
 * shipped past the existing gate — a dropped wrapper, a heading demoted to a
 * label, and a field rebuilt as a read-only fact row. If this file passes
 * while any of those three is present, the instrument is not worth having.
 */
import { describe, expect, it } from "vitest";
import { JSDOM } from "jsdom";

import { compareSkeletons, formatMismatch, skeletonOf } from "./skeleton.js";

function skeleton(html) {
	return skeletonOf(new JSDOM(`<body><div id="root">${html}</div></body>`).window.document.getElementById("root"));
}

function compare(boardHtml, builtHtml, options) {
	return compareSkeletons(skeleton(boardHtml), skeleton(builtHtml), options);
}

const BOARD_PLAN_CHECKS = `
	<div class="kt-region">
		<h2>Plan checks</h2>
		<div class="kt-group"><div class="kt-meta-row"><span class="kt-label">Funding</span></div></div>
	</div>`;

describe("the three shapes that shipped past the landmark gate", () => {
	it("catches a dropped wrapper the board draws", () => {
		// Exactly what happened to Plan checks: the group rule disappeared and
		// nothing noticed, because a wrapper has no text of its own.
		const built = `
			<div class="kt-region">
				<h2>Plan checks</h2>
				<div class="kt-meta-row"><span class="kt-label">Funding</span></div>
			</div>`;
		const result = compare(BOARD_PLAN_CHECKS, built);
		expect(result.missing).toHaveLength(1);
		expect(result.missing[0].path).toBe("region > group");
		expect(formatMismatch("U07", result)).toContain("MISSING: region > group");
	});

	it("catches a region heading demoted to a label", () => {
		// "Approval" was present, in the right order, as a .kt-label. The text
		// comparison matched; the structure was gone.
		const board = `<div class="kt-region is-secondary"><h2>Approval</h2><div class="kt-notice"></div></div>`;
		const built = `<div class="kt-meta-row"><span class="kt-label">Approval</span></div>`;
		const result = compare(board, built);
		expect(result.missing.map((m) => m.path)).toEqual([
			"region.is-secondary",
		]);
	});

	it("catches an editable field rebuilt as a read-only fact row", () => {
		// The U09 incident: ten defects, every fidelity assertion green.
		const board = `<div class="kt-region"><h2>Estimated cost</h2><div class="field"></div></div>`;
		const built = `<div class="kt-region"><h2>Estimated cost</h2><div class="kt-meta-row"></div></div>`;
		const result = compare(board, built);
		expect(result.missing[0].path).toBe("region > field");
		expect(result.extra.map((e) => e.path)).toContain("region > meta-row");
	});

	it("passes once each is restored", () => {
		expect(compare(BOARD_PLAN_CHECKS, BOARD_PLAN_CHECKS)).toEqual({ missing: [], extra: [] });
	});
});

describe("what the contract deliberately tolerates", () => {
	it("allows implementation-only wrappers the board had no need of", () => {
		const built = `
			<div class="kt-region">
				<h2>Plan checks</h2>
				<div class="pln-layout-shim"><template-root><div class="kt-group">
					<div class="kt-meta-row"><span class="kt-label">Funding</span></div>
				</div></template-root></div>
			</div>`;
		expect(compare(BOARD_PLAN_CHECKS, built)).toEqual({ missing: [], extra: [] });
	});

	it("treats the board's own class vocabulary as the live one", () => {
		// Planning's boards draw `.field` and `table.table`; the live app uses
		// the Industry `.field` and `.table`. That is the porting
		// convention, not a defect.
		const board = `<div class="kt-region"><div class="field"></div><table class="table"></table></div>`;
		const built = `<div class="kt-region"><div class="field"></div><table class="table"></table></div>`;
		expect(compare(board, built)).toEqual({ missing: [], extra: [] });
	});

	it("lets a build add a modifier but not drop the one the board chose", () => {
		const board = `<div class="kt-notice is-critical"></div>`;
		expect(compare(board, `<div class="kt-notice is-critical is-live"></div>`).missing).toEqual([]);
		expect(compare(board, `<div class="kt-notice"></div>`).missing).toHaveLength(1);
	});

	it("does not care what the board put inside a region, only that the region is there", () => {
		const board = `<div class="kt-region"><h2>A</h2></div>`;
		const built = `<div class="kt-region"><h2>A</h2><p>live copy the board never wrote</p></div>`;
		expect(compare(board, built)).toEqual({ missing: [], extra: [] });
	});
});

describe("additions the board does not draw", () => {
	const board = `<div class="kt-region"><h2>Plan checks</h2></div>`;
	const built = `
		<div class="kt-region">
			<h2>Plan checks</h2>
			<div class="kt-meta-row" data-testid="ppl-reservation-summary"></div>
		</div>`;

	it("fails when unregistered", () => {
		const result = compare(board, built);
		expect(result.extra).toEqual([{ path: "region > meta-row", testid: "ppl-reservation-summary" }]);
		expect(formatMismatch("U07", result)).toContain("UNREGISTERED");
	});

	it("passes when the registry names it", () => {
		const departures = [{ testid: "ppl-reservation-summary", because: "…", authority: "owner ruling" }];
		expect(compare(board, built, { departures })).toEqual({ missing: [], extra: [] });
	});
});

describe("order and nesting, not just presence", () => {
	it("catches a container that exists but under the wrong parent", () => {
		const board = `<div class="kt-region"><div class="kt-group"><div class="kt-meta-row"></div></div></div>`;
		const built = `<div class="kt-region"><div class="kt-group"></div><div class="kt-meta-row"></div></div>`;
		const result = compare(board, built);
		expect(result.missing[0].path).toBe("region > group > meta-row");
		expect(result.extra[0].path).toBe("region > meta-row");
	});

	it("catches two sections swapped", () => {
		const board = `<div class="kt-region"></div><div class="kt-region is-secondary"></div>`;
		const built = `<div class="kt-region is-secondary"></div><div class="kt-region"></div>`;
		// The secondary region satisfies the board's plain one; the board's
		// secondary then has nothing left to match.
		expect(compare(board, built).missing).toHaveLength(1);
	});
});

/**
 * Strategy and Budget are framed differently from Planning and Departmental
 * Needs. Neither uses `.kt-page`/`.kt-region`/`.kt-group` at all: their boards
 * and their live screens both frame content with `.blueprint`/`.card`,
 * summarise with a `.kt-kpi-row` of `.kt-kpi-card`s, switch with `.kt-tabs`,
 * and — in Budget — draw an expandable `.kt-record` whose detail is revealed
 * by a toggle. Those containers carry the same weight for these two modules
 * that `.kt-group` carries for Planning, and the comparator could not see any
 * of them before this block.
 */
describe("the Strategy and Budget frame vocabulary", () => {
	it("catches a blueprint frame dropped around a card", () => {
		// AGENTS.md §6.6 records this exact shipped defect for the STD screens:
		// "real content in bare .card with no .blueprint/.corner frame".
		const board = `<div class="blueprint"><div class="card"><h3 class="kt-card-title">Allocations</h3></div></div>`;
		const built = `<div class="card"><h3 class="kt-card-title">Allocations</h3></div>`;
		const result = compare(board, built);
		expect(result.missing.map((m) => m.path)).toEqual(["blueprint"]);
	});

	it("catches a KPI row rebuilt as loose cards", () => {
		const board = `<div class="kt-kpi-row"><div class="kt-kpi-card">Approved</div><div class="kt-kpi-card">Committed</div></div>`;
		const built = `<div><div class="kt-kpi-card">Approved</div><div class="kt-kpi-card">Committed</div></div>`;
		const result = compare(board, built);
		expect(result.missing.map((m) => m.path)).toEqual(["kpi-row"]);
	});

	it("catches a tab bar dropped while its tabs survive", () => {
		const board = `<div class="kt-tabs"><button class="kt-tab">Overview</button><button class="kt-tab">History</button></div>`;
		const built = `<div><button class="kt-tab">Overview</button><button class="kt-tab">History</button></div>`;
		const result = compare(board, built);
		expect(result.missing.map((m) => m.path)).toEqual(["tabs"]);
	});

	it("catches an expandable record rebuilt with no way to expand it", () => {
		// The Budget boards draw each allocation and each approval line as a
		// `.kt-record` whose `.kt-record-detail` is revealed by its toggle. A
		// build that renders the record but flattens the detail is a different
		// screen, and every word on it is still identical.
		const board = `
			<div class="kt-record">
				<div class="kt-record-main"><span class="kt-record-title">Line 1</span><button class="kt-record-toggle"></button></div>
				<div class="kt-record-detail"><span class="kt-label">Source</span></div>
			</div>`;
		const built = `
			<div class="kt-record">
				<div class="kt-record-main"><span class="kt-record-title">Line 1</span></div>
				<span class="kt-label">Source</span>
			</div>`;
		const result = compare(board, built);
		expect(result.missing.map((m) => m.path).sort()).toEqual([
			"record > record-detail",
			"record > record-main > record-toggle",
		]);
	});

	it("passes when all four are built as the board draws them", () => {
		const board = `
			<div class="blueprint"><div class="card">
				<div class="kt-kpi-row"><div class="kt-kpi-card">Approved</div></div>
				<div class="kt-tabs"><button class="kt-tab">Overview</button></div>
				<div class="kt-record">
					<div class="kt-record-main"><button class="kt-record-toggle"></button></div>
					<div class="kt-record-detail"><span class="kt-label">Source</span></div>
				</div>
			</div></div>`;
		expect(compare(board, board)).toEqual({ missing: [], extra: [] });
	});

	it("treats the Strategy board's bare frame classes as the live kt- ones", () => {
		// STR-DES-05 draws `class="blueprint"` and `class="card"`; the live
		// screens render `.blueprint`/`.card`. Same container, and the
		// porting convention is the only difference — exactly as `.field` and
		// `table.table` are already aliased above.
		const board = `<div class="blueprint"><div class="card"><h3 class="kt-card-title">Structure</h3></div></div>`;
		const built = `<div class="blueprint"><div class="card"><h3 class="kt-card-title">Structure</h3></div></div>`;
		expect(compare(board, built)).toEqual({ missing: [], extra: [] });
	});
});

describe("how many of a repeated thing the live world holds", () => {
	const BOARD_KPIS = `<div class="kt-kpi-row"><div class="kt-kpi-card"><span class="kt-label">A</span></div><div class="kt-kpi-card"><span class="kt-label">B</span></div></div>`;

	it("does not report extra siblings that are repeats of what the board draws", () => {
		// The Budget workspace board draws two summary cards; the live Active
		// year draws four. That is a difference in what the fixture holds, not
		// in what the screen is built from — and which figures are shown is
		// already compared, by label, by the landmark text gate.
		const built = `<div class="kt-kpi-row">${"<div class=\"kt-kpi-card\"><span class=\"kt-label\">X</span></div>".repeat(4)}</div>`;
		expect(compare(BOARD_KPIS, built)).toEqual({ missing: [], extra: [] });
	});

	it("still reports a sibling that is a different container", () => {
		const built = `<div class="kt-kpi-row"><div class="kt-kpi-card"><span class="kt-label">X</span></div><div class="kt-notice">Heads up</div></div>`;
		const result = compare(BOARD_KPIS, built);
		expect(result.extra.map((e) => e.path)).toEqual(["kpi-row > notice"]);
	});

	it("still reports a repeat whose own insides differ from the board's", () => {
		// A second card that has grown a table inside it is not a repeat of the
		// first — it is a different structure wearing the same class.
		const built = `<div class="kt-kpi-row"><div class="kt-kpi-card"><span class="kt-label">X</span></div><div class="kt-kpi-card"><table class="table"></table></div></div>`;
		const result = compare(BOARD_KPIS, built);
		expect(result.extra.map((e) => e.path)).toEqual(["kpi-row > kpi-card"]);
	});
});

describe("an element that is several landmarks at once", () => {
	it("recognises every landmark class on one element, not just the first listed", () => {
		// How the frame is actually written in both modules: one element
		// carrying `card blueprint`, not a blueprint wrapping a card.
		// Classifying it by whichever class this module happened to list first
		// made the live Budget "no baseline" panel read as an `empty` with no
		// card at all, and reported the board's card as missing.
		const board = `<div class="card blueprint"><h2>No allocation</h2></div>`;
		const built = `<div class="card blueprint kt-empty"><h2>No allocation</h2></div>`;
		expect(compare(board, built)).toEqual({ missing: [], extra: [] });
	});

	it("still fails when the build drops one of the classes the board draws", () => {
		// The AGENTS.md §6.6 defect in its real form: content left in a bare
		// `.card` with the `.blueprint` frame dropped.
		const board = `<div class="card blueprint"><h2>Allocations</h2></div>`;
		const built = `<div class="card"><h2>Allocations</h2></div>`;
		const result = compare(board, built);
		expect(result.missing.map((m) => m.path)).toEqual(["card+blueprint"]);
	});

	it("lets the build add a landmark class the board did not draw", () => {
		const board = `<div class="card"><h2>Allocations</h2></div>`;
		const built = `<div class="card kt-empty"><h2>Allocations</h2></div>`;
		expect(compare(board, built)).toEqual({ missing: [], extra: [] });
	});
});

describe("the notice icon", () => {
	it("catches a notice built without the icon its board draws", () => {
		// The same shape as the disclosure chevron: an SVG has no text, so the
		// landmark gate cannot see it, and the severity colour that tells a
		// warning from an info is carried BY the icon — kt_industry_tokens.css
		// styles `.kt-notice.is-warning .kt-notice-icon` and its siblings. A
		// notice without one is an incomplete notice, not a styling choice.
		const board = `<div class="kt-notice is-warning"><svg class="kt-notice-icon"></svg><div class="kt-notice-body">Changes requested.</div></div>`;
		const built = `<div class="kt-notice is-warning"><div class="kt-notice-body">Changes requested.</div></div>`;
		const result = compare(board, built);
		expect(result.missing.map((m) => m.path)).toEqual(["notice.is-warning > notice-icon"]);
	});

	it("passes once the icon is there", () => {
		const board = `<div class="kt-notice is-live"><svg class="kt-notice-icon"></svg><div class="kt-notice-body">Matched.</div></div>`;
		expect(compare(board, board)).toEqual({ missing: [], extra: [] });
	});
});

describe("a severity that is a reading of the data, not a choice of container", () => {
	it("ignores a KPI card's severity, which is computed from its own number", () => {
		// `BudgetDetailScreen` sets the Available card to is-live or is-critical
		// from `available > 0`; the board hardcodes the one its fixture happened
		// to show. That is the same thing a status pill's severity is — row
		// data — and status is already excluded from this instrument for
		// exactly that reason.
		const board = `<div class="kt-kpi-row"><div class="kt-kpi-card is-attention"><span class="kt-label">Available</span></div></div>`;
		const built = `<div class="kt-kpi-row"><div class="kt-kpi-card is-live"><span class="kt-label">Available</span></div></div>`;
		expect(compare(board, built)).toEqual({ missing: [], extra: [] });
	});

	it("still holds a notice to the severity the board chose", () => {
		// A notice is the opposite case: its severity IS the message, and the
		// build does not get to decide that a warning is really an info.
		const board = `<div class="kt-notice is-critical"><div class="kt-notice-body">Blocked</div></div>`;
		const built = `<div class="kt-notice is-info"><div class="kt-notice-body">Blocked</div></div>`;
		const result = compare(board, built);
		expect(result.missing.map((m) => m.path)).toEqual(["notice.is-critical"]);
	});
});

describe("names the design system does not define", () => {
	it("is transparent to the board's kt-facts and to the live kt-grid-2 alike", () => {
		// Neither `.kt-facts` nor `.kt-fact-value` has a rule in
		// kt_industry_tokens.css; the board carries their layout inline. And
		// `.kt-grid-2`, which the live screens use in the same place, is layout
		// — the thing a build is explicitly free to add. Treating either as a
		// container put the board's fields one level above the build's and
		// reported every one of them missing on BUD-DES-02.
		const board = `<div class="kt-facts"><div class="field"><span class="kt-label">Approval reference</span></div></div>`;
		const built = `<div class="kt-grid-2"><div class="field"><span class="kt-label">Approval reference</span></div></div>`;
		expect(compare(board, built)).toEqual({ missing: [], extra: [] });
	});

	it("still sees the fields inside them", () => {
		const board = `<div class="kt-facts"><div class="field"><span class="kt-label">Approval reference</span></div></div>`;
		const built = `<div class="kt-grid-2"><span class="kt-label">Approval reference</span></div>`;
		expect(compare(board, built).missing.map((m) => m.path)).toEqual(["field"]);
	});
});

describe("KT-STD-001 v1.8 §2.9 guidance components (data-kt landmarks)", () => {
	const BOARD = `
		<div class="kt-page">
			<div class="kt-page-head"><div><h1>Prepare plan update</h1><div class="kt-page-scope">PLN · Version 2</div></div></div>
			<div data-kt="journey"><ol><li><div>Preparation</div></li></ol></div>
			<div data-kt="next-step" class="kt-notice is-warning"><svg class="kt-notice-icon"></svg><div>Over budget</div></div>
			<div class="kt-region"><h2>Purchases</h2></div>
		</div>`;

	it("passes the shared components, which carry the same attributes", () => {
		const built = `
			<div class="kt-page">
				<div class="kt-page-head"><div><h1>Prepare plan update</h1><div class="kt-page-scope">PLN · Version 2</div></div></div>
				<div class="kt-journey" data-kt="journey"><ol class="kt-journey-stages"><li class="kt-journey-stage"><div class="kt-journey-label">Preparation</div></li></ol></div>
				<div class="kt-notice is-warning kt-next-step-block" data-kt="next-step"><svg class="kt-notice-icon"></svg><div class="kt-next-step-block-body">Over budget</div></div>
				<div class="kt-region"><h2>Purchases</h2></div>
			</div>`;
		const result = compare(BOARD, built);
		expect(result.missing).toEqual([]);
		expect(result.extra).toEqual([]);
	});

	it("catches a dropped tracker", () => {
		const built = BOARD.replace(/<div data-kt="journey">.*?<\/ol><\/div>/s, "");
		expect(compare(BOARD, built).missing.map((m) => m.path)).toContain("page > journey");
	});

	it("catches a blocked block that lost its next-step marker (a plain warning in its place)", () => {
		const built = BOARD.replace('data-kt="next-step" ', "");
		expect(compare(BOARD, built).missing.length).toBeGreaterThan(0);
	});
});

describe("design-system omissions (DS-REV-004)", () => {
	it("does not require the icon the boards drew inside a blocked next step", () => {
		const boardHtml = '<div class="kt-notice is-warning kt-next-step" data-kt="next-step"><svg class="kt-notice-icon"></svg><div class="kt-notice-body"></div></div>';
		const builtHtml = '<div class="kt-notice is-warning kt-next-step" data-kt="next-step"><div class="kt-notice-body"></div></div>';
		expect(compare(boardHtml, builtHtml).missing).toEqual([]);
	});

	it("still requires that icon in any other notice", () => {
		const boardHtml = '<div class="kt-notice is-warning"><svg class="kt-notice-icon"></svg><div class="kt-notice-body"></div></div>';
		const builtHtml = '<div class="kt-notice is-warning"><div class="kt-notice-body"></div></div>';
		expect(compare(boardHtml, builtHtml).missing.map((m) => m.path)).toHaveLength(1);
	});
});
