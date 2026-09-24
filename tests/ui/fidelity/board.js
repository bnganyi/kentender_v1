/**
 * Reading a `.dc.html` artboard as the structural oracle.
 *
 * The browser gate renders the artboard in Chromium with the design tool's
 * `support.js` blocked, so the raw `<x-dc>` markup is what gets measured. For
 * a structural comparison none of that is needed — containers and nesting are
 * in the markup itself, not in the layout — so this parses the file directly
 * and the component tests need no browser, no site and no login.
 *
 * Each module's boards were exported at a different time and scope their
 * screens differently, which is why the scope is a per-module function rather
 * than one selector:
 *
 *   - Planning's ten boards are a later export. Each variant is its own
 *     `<section id="U07">` and the screen itself is a `.kt-page` inside it,
 *     matching the live component's own root exactly.
 *   - Departmental Needs is a single earlier export whose sheet carries no
 *     class at all — the `.kt-page`/`.kt-region`/`.kt-group` vocabulary was
 *     extracted *from* that board afterwards and added to the live
 *     stylesheet. Its sheet has to be addressed positionally, the same way
 *     `departmental-needs-fidelity.spec.ts` already does.
 */
import fs from "node:fs";
import path from "node:path";
import { JSDOM } from "jsdom";

import { skeletonOf } from "./skeleton.js";

/**
 * The repo root, found by walking up until `docs/mvp-1-r1` appears, so the
 * same module works from a vitest run (cwd is the repo root), a Playwright run
 * (cwd varies with the target), and a bare `node` invocation.
 */
const REPO_ROOT = (() => {
	let dir = path.resolve(new URL(".", import.meta.url).pathname);
	for (let i = 0; i < 12; i += 1) {
		if (fs.existsSync(path.join(dir, "docs", "mvp-1-r1"))) return dir;
		dir = path.dirname(dir);
	}
	return process.cwd();
})();

const cache = new Map();

function documentFor(relPath) {
	if (!cache.has(relPath)) {
		const full = path.resolve(REPO_ROOT, relPath);
		if (!fs.existsSync(full)) throw new Error(`artboard not found: ${relPath}`);
		cache.set(relPath, new JSDOM(fs.readFileSync(full, "utf8")).window.document);
	}
	return cache.get(relPath);
}

/** Planning: `<section id="U07">` … `<div class="kt-page">`. */
export function planningScope(doc, id) {
	const section = doc.querySelector(`section#${id}`);
	if (!section) throw new Error(`artboard section #${id} not found`);
	const page = section.querySelector(".kt-page");
	if (!page) throw new Error(`artboard section #${id} draws no .kt-page`);
	return page;
}

/** Departmental Needs: the sheet is the last frame's only child div. */
export function needsScope(doc, id) {
	const section = doc.querySelector(`section#${id}`);
	if (!section) throw new Error(`artboard section #${id} not found`);
	const frames = Array.from(section.children).filter((el) => el.tagName === "DIV");
	const frame = frames[frames.length - 1];
	const sheet = frame && frame.firstElementChild;
	if (!sheet) throw new Error(`artboard section #${id} has no sheet`);
	return sheet;
}

/**
 * The board's landmark skeleton for one variant.
 *
 * `scope` defaults to Planning's, which is the shape every later board export
 * uses; Departmental Needs passes `needsScope`.
 */
export function boardSkeleton(relPath, id, scope = planningScope) {
	return skeletonOf(scope(documentFor(relPath), id));
}

/** Every variant id a board file declares, for coverage checks. */
export function variantIds(relPath) {
	return Array.from(documentFor(relPath).querySelectorAll("section[id]")).map((el) => el.id);
}
