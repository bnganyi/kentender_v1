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
 * Procurement Requisitions (REQ-CHG-001 v1.11 board v2): each family is a
 * `div#desNN` holding its base frame (`.kt-panel-lg`, or `.dialog` for a
 * dialog artboard), and a sibling "variants" block whose frames each open with
 * a `.sub` caption naming the variant ("REQ-DES-01-DRAFT · …"). A frame is
 * addressed by family id ("REQ-DES-01") or by the caption it opens with
 * ("REQ-DES-01-DRAFT", or any caption prefix such as "Return dialog").
 *
 * `.cap`/`.sub` captions are design-tool annotation, not screen content, and
 * are stripped. A dialog frame keeps itself as a landmark (the dialog IS the
 * artboard); a page frame is compared by its children, since the build's own
 * page container is the frame.
 */
export function requisitionsScope(doc, id) {
	let frame = null;
	const family = /^REQ-DES-(\d\d)$/.exec(id);
	if (family) {
		const block = doc.querySelector(`div#des${family[1]}`);
		if (!block) throw new Error(`artboard family ${id} not found`);
		frame = block.querySelector(":scope > .kt-panel-lg, :scope > .dialog, :scope > div > div > .dialog, :scope > div > .kt-panel-lg");
	} else {
		const caption = Array.from(doc.querySelectorAll(".sub")).find((el) => el.textContent.trim().startsWith(id));
		if (!caption) throw new Error(`artboard variant ${id} not found`);
		frame = caption.closest(".kt-panel-lg") || caption.nextElementSibling;
	}
	if (!frame) throw new Error(`artboard ${id} draws no frame`);
	const clone = frame.cloneNode(true);
	for (const note of clone.querySelectorAll(".sub, .cap")) note.remove();
	return clone.classList.contains("dialog") ? { children: [clone] } : clone;
}

/**
 * Tenders (TPR-CHG-001 v0.12 design set): one board per file, the screen is
 * the element carrying `data-screen-label` ("TPR-DES-03 Draft Tender
 * details"). Two design-tool constructs are resolved statically so the
 * markup reads as the screen the variant shows:
 *
 *   - `<sc-if value="{{name}}">` is the board's own conditional. A variant
 *     names the conditions it sets (`show`/`hide`); any other block keeps the
 *     board's default, its `hint-placeholder-val`. Shown blocks are unwrapped,
 *     hidden ones removed.
 *   - `<dc-import name="TenderGuidance">` draws the §10.17 guidance region.
 *     It is expanded to the landmarks kentender_core's shared components
 *     render (`data-kt="journey"`, and `data-kt="next-step"` — inside a
 *     warning notice for "Your turn, blocked"), so a screen that drops its
 *     tracker or misplaces its next step fails like any other container.
 *     A variant whose kind is a template expression states it (`guidance`).
 *
 * `.cap`/`.sub` captions are design-tool annotation and are stripped.
 */
export function tendersScope(doc, id, { show = [], hide = [], guidance = "", selector = "" } = {}) {
	// A board without a screen label (TPR-DES-02's dialog-over-workspace) is
	// addressed by selector instead.
	const root = doc.querySelector(selector || `[data-screen-label="${id}"]`);
	if (!root) throw new Error(`artboard ${id} not found`);
	const clone = root.cloneNode(true);
	const nameOf = (el) => String(el.getAttribute("value") || "").replace(/^\{\{\s*|\s*\}\}$/g, "");
	for (let block = clone.querySelector("sc-if"); block; block = clone.querySelector("sc-if")) {
		const name = nameOf(block);
		const visible = show.includes(name) || (!hide.includes(name) && block.getAttribute("hint-placeholder-val") === "{{true}}");
		if (visible) block.replaceWith(...Array.from(block.childNodes));
		else block.remove();
	}
	for (let loop = clone.querySelector("sc-for"); loop; loop = clone.querySelector("sc-for")) loop.replaceWith(...Array.from(loop.childNodes));
	// A disclosure chevron's open state is a computed class on some boards
	// (`class="{{evalChevron}}"` → "kt-disclosure-chevron is-open"); read it
	// as the chevron it always is.
	for (const el of Array.from(clone.querySelectorAll("[class]"))) {
		if (/^\{\{\s*\w*chevron\w*\s*\}\}$/i.test(el.getAttribute("class").trim())) el.setAttribute("class", "kt-disclosure-chevron");
		// …and a count card's class carries its accent state the same way
		// (`class="{{c.cls}}"` → "kt-kpi-card is-live")
		else if (/^\{\{.*\}\}$/.test(el.getAttribute("class").trim()) && el.parentElement && el.parentElement.classList.contains("kt-kpi-row")) el.setAttribute("class", "kt-kpi-card");
	}
	const ownerDoc = clone.ownerDocument;
	for (const node of Array.from(clone.querySelectorAll('dc-import[name="TenderGuidance"]'))) {
		const raw = node.getAttribute("kind") || "none";
		const kind = /^\{\{/.test(raw) ? guidance : raw;
		if (!kind) throw new Error(`${id}: the TenderGuidance kind is a template expression; the variant must state it`);
		const parts = [];
		const journey = ownerDoc.createElement("div");
		journey.setAttribute("data-kt", "journey");
		parts.push(journey);
		if (["turn", "waiting", "done"].includes(kind)) {
			const step = ownerDoc.createElement("div");
			step.setAttribute("data-kt", "next-step");
			parts.push(step);
		} else if (kind === "blocked") {
			const step = ownerDoc.createElement("div");
			step.setAttribute("class", "kt-notice is-warning");
			step.setAttribute("data-kt", "next-step");
			const icon = ownerDoc.createElement("span");
			icon.setAttribute("class", "kt-notice-icon");
			step.appendChild(icon);
			parts.push(step);
		}
		node.replaceWith(...parts);
	}
	for (const note of clone.querySelectorAll(".sub, .cap")) note.remove();
	return clone;
}

/** One Tenders variant's landmark skeleton (see `tendersScope`). */
export function tendersSkeleton(relPath, id, options = {}) {
	const scope = tendersScope(documentFor(relPath), id, options);
	// a dialog artboard keeps the dialog itself as a landmark (see setupSkeleton)
	return skeletonOf(options.self ? { children: [scope] } : scope);
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

/**
 * System setup: every artboard is an element with an `id` (`div#configured`,
 * `div#add.dialog`), not a `<section>`, and sits beside the page frame the
 * board repeats on every file. Artboards are addressed by selector so a
 * sub-state inside a larger artboard (`#forms .card:nth-of-type(2)`) can be
 * compared on its own.
 *
 * `self` keeps the matched element as a landmark of its own: a dialog
 * artboard IS the dialog, and comparing only its children would let a build
 * drop the dialog container and still pass.
 */
export function setupSkeleton(relPath, selector, { self = false } = {}) {
	const el = documentFor(relPath).querySelector(selector);
	if (!el) throw new Error(`artboard ${selector} not found in ${relPath}`);
	return skeletonOf(self ? { children: [el] } : el);
}

/**
 * Every artboard a System setup board draws: each element with an `id`,
 * except ids that exist only to label a control (`aria-labelledby`,
 * `label[for]`). Used to prove that no drawn state is left unassigned.
 */
export function setupArtboardIds(relPath) {
	const doc = documentFor(relPath);
	const labelTargets = new Set();
	for (const el of doc.querySelectorAll("[aria-labelledby]")) {
		for (const id of el.getAttribute("aria-labelledby").split(/\s+/)) labelTargets.add(id);
	}
	for (const el of doc.querySelectorAll("label[for]")) labelTargets.add(el.getAttribute("for"));
	return Array.from(doc.querySelectorAll("[id]"))
		.map((el) => el.id)
		.filter((id) => !labelTargets.has(id));
}

/**
 * Bid Submission (BDS-CHG-001 v0.8, `docs/mvp-1-r1/12_bid_submission/design/`,
 * "Bid Board v3 - A…E"). Every variant is a `[data-screen-label]` holding two
 * frames side by side — the 1440 × 1024 desktop frame first, the 390 × 844
 * narrow frame second — each with the portal shell (header, body, footer)
 * around one `main.kt-page`. The shell is kentender_core's portal page, so the
 * screen compared is the `main` alone; the fold marker and captions are
 * design-tool annotation.
 */
export function bidSubmissionScope(doc, id, { frame = "desktop" } = {}) {
	const root = doc.querySelector(`[data-screen-label="${id}"]`);
	if (!root) throw new Error(`artboard ${id} not found`);
	const frames = Array.from(root.querySelectorAll("div")).filter((el) => /width:\s*(1440|390)px/.test(el.getAttribute("style") || ""));
	const wanted = frames.find((el) => (el.getAttribute("style") || "").includes(frame === "narrow" ? "width:390px" : "width:1440px"));
	if (!wanted) throw new Error(`artboard ${id} draws no ${frame} frame`);
	const main = wanted.querySelector("main.kt-page, main") || wanted;
	const clone = main.cloneNode(true);
	for (const note of clone.querySelectorAll(".sub, .cap")) note.remove();
	// The boards draw the guidance region (§10.19) as `.kt-guidance` holding
	// the full journey row, its reduced fallback and the next step, all by
	// class. kentender_core's shared components render the same answer as
	// the `data-kt="journey"` / `data-kt="next-step"` landmarks (the blocked
	// kind inside a warning notice), so the board is read that way: one
	// journey, then the next step as drawn.
	for (const region of clone.querySelectorAll(".kt-guidance")) {
		const journeys = Array.from(region.querySelectorAll(".kt-journey")).filter((el) => !el.parentElement.closest(".kt-journey"));
		if (journeys.length) {
			const marker = clone.ownerDocument.createElement("div");
			marker.setAttribute("data-kt", "journey");
			journeys[0].replaceWith(marker);
			for (const extra of journeys.slice(1)) extra.remove();
		}
		for (const step of region.querySelectorAll(".kt-next-step")) step.setAttribute("data-kt", "next-step");
	}
	return clone;
}

/** One Bid Submission variant's landmark skeleton at one frame. */
export function bidSubmissionSkeleton(relPath, id, options = {}) {
	return skeletonOf(bidSubmissionScope(documentFor(relPath), id, options));
}

/**
 * The BDS-DES-16 common-state catalogue's cells (BDS-CHG-001 §10.17), read
 * from the board: each cell's label, heading, message and one action. The
 * live states are compared with these by text (the catalogue is one sheet,
 * so there is no per-state container to compare structurally).
 */
export function bidSubmissionStateCells(relPath, id, options = {}) {
	const scope = bidSubmissionScope(documentFor(relPath), id, options);
	return [...scope.querySelectorAll("span.kt-label")].map((label) => {
		const cell = label.parentElement;
		const message = [...cell.children].find((child) => child.tagName === "SPAN" && !child.classList.contains("kt-label"));
		return {
			label: label.textContent.trim(),
			heading: (cell.querySelector("strong")?.textContent || "").trim(),
			message: (message?.textContent || "").trim(),
			action: (cell.querySelector(".btn")?.textContent || "").trim(),
		};
	});
}

/**
 * Bid Opening (BOP-CHG-001 v0.10 design set): one file,
 * `14_bid_opening/design/Bid Opening Artboards v0.9.2.dc.html`, whose boards
 * are `<sc-if value="{{ is.<id> }}">` blocks (a1, c3, r6 …) in a
 * reviewer shell. The screen is the block's `.kt-page`; the top bar above it
 * is the shared page rail, which the build never redraws. The boards draw the
 * shared guidance region literally, so the journey (`ol.kt-journey`) and the
 * next step (`.kt-next-step`) are marked with the `data-kt` landmarks the
 * shared components render. `.cap`/`.sub` captions are stripped.
 */
export function bidOpeningScope(doc, id) {
	const block = Array.from(doc.querySelectorAll("sc-if")).find((el) => String(el.getAttribute("value") || "").replace(/\s+/g, "") === `{{is.${id}}}`);
	if (!block) throw new Error(`Bid Opening board ${id} not found`);
	const page = block.querySelector(".kt-page");
	if (!page) throw new Error(`Bid Opening board ${id} draws no .kt-page`);
	const clone = page.cloneNode(true);
	for (const el of clone.querySelectorAll("ol.kt-journey")) el.setAttribute("data-kt", "journey");
	for (const el of clone.querySelectorAll(".kt-next-step")) el.setAttribute("data-kt", "next-step");
	for (const note of clone.querySelectorAll(".sub, .cap")) note.remove();
	return clone;
}

export const BID_OPENING_BOARDS = "docs/mvp-1-r1/14_bid_opening/design/Bid Opening Artboards v0.9.2.dc.html";

/** One Bid Opening board's landmark skeleton (see `bidOpeningScope`). */
export function bidOpeningSkeleton(id, relPath = BID_OPENING_BOARDS) {
	return skeletonOf(bidOpeningScope(documentFor(relPath), id));
}
