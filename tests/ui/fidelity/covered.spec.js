// `COVERED` in a departures registry is the module's claim of which screens
// are structurally compared against their boards. Until 24 Sep 2026 nothing
// imported it: AGENTS.md §6.6 said "a screen not in COVERED is not done", and
// no test failed when a name sat there with no comparison behind it.
//
// This makes the claim checkable: every COVERED entry must be named by a
// fidelity spec that imports the same registry, so each one points at a real
// comparison. (Which screens *should* be listed is a per-module fact; System
// setup's own spec enforces that direction too, against every drawn artboard.)
import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const ROOT = (() => {
	let dir = path.resolve(new URL(".", import.meta.url).pathname);
	for (let i = 0; i < 12; i += 1) {
		if (fs.existsSync(path.join(dir, "docs", "mvp-1-r1"))) return dir;
		dir = path.dirname(dir);
	}
	return process.cwd();
})();
const REGISTRY_DIR = path.join(ROOT, "tests", "ui", "fidelity", "departures");

function specFiles() {
	const out = [];
	const skip = new Set(["node_modules", ".git", "docs", "artifacts", "test-results", "dist"]);
	function walk(dir, depth) {
		if (depth > 12) return;
		for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
			if (skip.has(entry.name)) continue;
			const full = path.join(dir, entry.name);
			if (entry.isDirectory()) walk(full, depth + 1);
			else if (/\.spec\.(js|ts)$/.test(entry.name)) out.push(full);
		}
	}
	for (const top of fs.readdirSync(ROOT)) {
		if (top === "tests" || top.startsWith("kentender_")) walk(path.join(ROOT, top), 0);
	}
	return out;
}

const SPECS = specFiles().map((file) => ({ file, text: fs.readFileSync(file, "utf8") }));
const REGISTRIES = fs.readdirSync(REGISTRY_DIR).filter((name) => name.endsWith(".js"));

describe.each(REGISTRIES)("departures/%s", (registry) => {
	it("names in COVERED only screens a spec importing this registry actually compares", async () => {
		const mod = await import(path.join(REGISTRY_DIR, registry));
		const covered = mod.COVERED || [];
		const importers = SPECS.filter((spec) => spec.text.includes(`departures/${registry}`));
		if (covered.length) expect(importers.map((s) => path.relative(ROOT, s.file)), "no spec imports this registry").not.toEqual([]);
		const comparing = importers.filter((spec) => /expectStructure\(|compareSkeletons\(/.test(spec.text));
		if (covered.length) expect(comparing.length, "no importing spec runs a structural comparison").toBeGreaterThan(0);
		// A spec may name a screen by its board label rather than its
		// component (Budget's browser spec says "BUD-DES-02"); the registry
		// states that label in COVERED_AS so the link stays explicit.
		const aliases = mod.COVERED_AS || {};
		const unbacked = covered.filter((entry) => {
			const names = [entry, String(entry).split("#")[0], aliases[entry]].filter(Boolean);
			return !comparing.some((spec) => names.some((name) => spec.text.includes(`"${name}`)));
		});
		expect(unbacked, "COVERED entries no importing spec names").toEqual([]);
	});
});
