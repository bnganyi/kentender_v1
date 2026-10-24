// Tooling check for the Contract Management boards (CM-CHG-001 v0.8, plan
// Phase 0, tracker CM8-001 and CM8-011). No screen exists yet; this proves the
// design can be read mechanically and that the committed board inventory is
// the design's own list, so a changed design fails here until the inventory is
// regenerated (`reconciliation/tools/`).
import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

import { cmBoardIds, cmDialogSkeleton, cmKit, cmSkeleton } from "../board.js";
import { COVERED, DEPARTURES, NOT_COMPARED } from "../departures/contracts.js";

const ROOT = (() => {
	let dir = path.resolve(new URL(".", import.meta.url).pathname);
	for (let i = 0; i < 12; i += 1) {
		if (fs.existsSync(path.join(dir, "docs", "mvp-1-r1"))) return dir;
		dir = path.dirname(dir);
	}
	return process.cwd();
})();
const INVENTORY = path.join(ROOT, "docs/mvp-1-r1/21_contract_management/reconciliation/artboard_inventory.md");

function inventory() {
	const text = fs.readFileSync(INVENTORY, "utf8");
	const rows = text.split("\n").filter((line) => /^\| \d+ \| /.test(line)).map((line) => line.split("|").map((c) => c.trim()));
	const header = /(\d+) boards in (\d+) designs: (\d+) main, (\d+) state variants, (\d+) dialog boards/.exec(text);
	const slices = new Map();
	for (const cells of rows) slices.set(cells[2], (slices.get(cells[2]) || 0) + 1);
	return { ids: rows.map((c) => c[2]), kinds: rows.map((c) => c[5]), slices: rows.map((c) => c[11]), header: header && header.slice(1).map(Number) };
}

describe("CM boards read from the design's own code", () => {
	const kit = cmKit();
	const ids = cmBoardIds();

	it("loads the four data files and every board has a unique id", () => {
		expect(kit.files).toEqual(["cm-data-1.js", "cm-data-2.js", "cm-data-3.js", "cm-data-4.js"]);
		expect(ids.length).toBeGreaterThan(0);
		expect(new Set(ids).size).toBe(ids.length);
	});

	it("matches the committed inventory exactly, in the design's order", () => {
		const inv = inventory();
		expect(inv.ids, "artboard_inventory.md is stale: rerun reconciliation/tools/extract_boards.mjs and build_inventory.py").toEqual(ids);
		const designs = new Set(kit.screens.map((s) => s.d)).size;
		const dialogs = kit.screens.filter((s) => s.dialog).length;
		const mains = kit.screens.filter((s) => !s.dialog && s.id === s.d).length;
		expect(inv.header).toEqual([ids.length, designs, mains, ids.length - mains - dialogs, dialogs]);
	});

	it("puts every board in exactly one slice and one kind", () => {
		const inv = inventory();
		expect(inv.slices.every((s) => /^[3-9] /.test(s))).toBe(true);
		expect(inv.kinds.every((k) => ["Main", "State", "Dialog"].includes(k))).toBe(true);
	});

	it("renders every board through the page's own template with a page root (dialog boards a dialog)", () => {
		const failures = [];
		for (const s of kit.screens) {
			try {
				const skeleton = s.dialog ? cmDialogSkeleton(s.id) : cmSkeleton(s.id);
				if (!skeleton) failures.push(`${s.id}: empty skeleton`);
			} catch (error) {
				failures.push(`${s.id}: ${error.message}`);
			}
		}
		expect(failures).toEqual([]);
	});

	it("compares or records every board of the design, and no board is both", () => {
		const recorded = new Set(Object.keys(NOT_COMPARED));
		expect(ids.filter((id) => !COVERED.includes(id) && !recorded.has(id)), "a board neither compared nor recorded as not compared").toEqual([]);
		expect([...recorded].filter((id) => COVERED.includes(id)), "a board both compared and recorded as not compared").toEqual([]);
	});

	it("keeps the departures registry honest: only real boards, a reason for every exclusion", () => {
		const known = new Set(ids);
		expect(Object.keys(DEPARTURES).filter((id) => !known.has(id)), "departure for an unknown board").toEqual([]);
		expect([...COVERED].filter((id) => !known.has(id)), "COVERED names an unknown board").toEqual([]);
		for (const [id, reason] of Object.entries(NOT_COMPARED)) {
			expect(known.has(id), `NOT_COMPARED names unknown board ${id}`).toBe(true);
			expect(String(reason).length, `NOT_COMPARED ${id} needs a reason`).toBeGreaterThan(20);
		}
	});
});
