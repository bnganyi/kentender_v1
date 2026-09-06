import { Page, expect } from "@playwright/test";
import * as path from "path";

/**
 * Design-fidelity gate helpers (AGENTS.md §6.6).
 *
 * The `.dc.html` artboard is the literal build source for a screen, so it is
 * also the literal *oracle*: these helpers render the artboard itself in the
 * same browser as the live page and derive every expectation from that render
 * — nothing here hardcodes what a screen "should" look like.
 *
 * Two instruments:
 *
 *  1. Landmark subsequence — the ordered visible text of the artboard's
 *     structural elements (card titles, dialog titles, field labels, row
 *     labels, table headers, buttons) must appear, in the same order, in the
 *     live page. Extra live landmarks (tab rows, retry buttons) are allowed;
 *     missing or reordered ones fail. This catches dropped cards, missing
 *     tables, re-derived compositions — the class of drift that behaviour
 *     tests can never see.
 *
 *  2. Geometry probes — numeric measurements taken from the artboard render
 *     (column ratios, row heights, dialog widths, grid label columns,
 *     whether a given text truncates) compared against the same measurement
 *     on the live page, within tolerance.
 *
 * Data values (record ids, dates, names) are deliberately NOT compared:
 * fixtures drift from live data legitimately (e.g. tracker conflict C4 —
 * generated vs mnemonic unit codes). Structure and geometry are the contract.
 */

const LANDMARK_SELECTOR = [
	".kt-card-title",
	".kt-dialog-title",
	".dialog-title",
	"label",
	"legend",
	".kt-label",
	"th",
	"button",
].join(", ");

export function artboardUrl(relPath: string): string {
	// Repo-relative, e.g. "docs/mvp-1-r1/09_unified_system_setup/design/AUTH-DES-01 Organisation structure.dc.html"
	return "file://" + path.resolve(__dirname, "../../..", relPath);
}

export async function openArtboard(page: Page, relPath: string, scope: string): Promise<void> {
	// The artboard's <x-dc> markup is the literal design source. support.js is
	// a dc-runtime that re-renders that markup asynchronously (and can tear it
	// out mid-measurement) — block it so the raw markup plus the _ds
	// stylesheet is exactly what gets measured, deterministically.
	await page.route("**/support.js", (route) => route.abort());
	await page.goto(artboardUrl(relPath), { waitUntil: "load" });
	// Measurements need real layout: the scope must exist and have painted.
	await page.waitForFunction(
		(sel) => {
			const el = document.querySelector(sel);
			return !!el && el.getBoundingClientRect().height > 50;
		},
		scope,
		{ timeout: 15_000 }
	);
	await page.evaluate(() => (document as any).fonts?.ready?.catch(() => undefined));
}

/** Ordered visible landmark texts within `scope` (a CSS selector). */
export async function landmarks(page: Page, scope: string): Promise<string[]> {
	return page.evaluate(
		({ scope, selector }) => {
			const root = document.querySelector(scope);
			if (!root) return [];
			const texts: string[] = [];
			for (const el of Array.from(root.querySelectorAll<HTMLElement>(selector))) {
				if (!el.getClientRects().length) continue; // hidden
				const text = (el.textContent || "").replace(/\s+/g, " ").trim();
				if (text) texts.push(text);
			}
			return texts;
		},
		{ scope, selector: LANDMARK_SELECTOR }
	);
}

/**
 * Assert `wanted` (artboard landmarks) is an ordered subsequence of `got`
 * (live landmarks). On failure, name the first artboard landmark the live
 * page is missing or has out of order.
 */
export function expectLandmarkSubsequence(wanted: string[], got: string[], label: string): void {
	let cursor = 0;
	for (const landmark of wanted) {
		const found = got.indexOf(landmark, cursor);
		if (found === -1) {
			const seenBefore = got.includes(landmark);
			throw new Error(
				`${label}: artboard landmark ${JSON.stringify(landmark)} is ${
					seenBefore ? "OUT OF ORDER" : "MISSING"
				} in the live page.\nArtboard sequence: ${JSON.stringify(wanted)}\nLive sequence: ${JSON.stringify(got)}`
			);
		}
		cursor = found + 1;
	}
	expect(cursor).toBeGreaterThan(0);
}

/** Width of `selector` divided by its parent's width (e.g. a grid column split). */
export async function widthRatio(page: Page, selector: string): Promise<number> {
	return page.evaluate((sel) => {
		const el = document.querySelector<HTMLElement>(sel);
		if (!el || !el.parentElement) return NaN;
		return el.getBoundingClientRect().width / el.parentElement.getBoundingClientRect().width;
	}, selector);
}

export async function boxWidth(page: Page, selector: string): Promise<number> {
	return page.evaluate((sel) => {
		const el = document.querySelector<HTMLElement>(sel);
		return el ? el.getBoundingClientRect().width : NaN;
	}, selector);
}

/** Height of the layout row containing the exact text `text` under `scope`. */
export async function rowHeightByText(page: Page, scope: string, text: string): Promise<number> {
	return page.evaluate(
		({ scope, text }) => {
			const root = document.querySelector(scope);
			if (!root) return NaN;
			const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT);
			let node = walker.nextNode() as HTMLElement | null;
			while (node) {
				const own = Array.from(node.childNodes)
					.filter((n) => n.nodeType === Node.TEXT_NODE)
					.map((n) => n.textContent || "")
					.join("")
					.replace(/\s+/g, " ")
					.trim();
				if (own === text) {
					// The row is the nearest ancestor laid out as a flex row.
					let row: HTMLElement | null = node;
					while (row && row !== root) {
						const cs = getComputedStyle(row);
						if (cs.display.includes("flex") && cs.flexDirection.startsWith("row")) {
							return row.getBoundingClientRect().height;
						}
						row = row.parentElement;
					}
					return node.getBoundingClientRect().height;
				}
				node = walker.nextNode() as HTMLElement | null;
			}
			return NaN;
		},
		{ scope, text }
	);
}

/** First column of a grid row's computed template, in px (e.g. the label column). */
export async function gridLabelColumn(page: Page, selector: string): Promise<number> {
	return page.evaluate((sel) => {
		const el = document.querySelector<HTMLElement>(sel);
		if (!el) return NaN;
		return parseFloat(getComputedStyle(el).gridTemplateColumns.split(" ")[0]);
	}, selector);
}

/**
 * Does the element rendering exactly `text` (or starting with it) fit without
 * ellipsis? Compared for parity: if the artboard shows the full text, the
 * live page must too.
 */
export async function textFits(page: Page, scope: string, text: string): Promise<boolean> {
	return page.evaluate(
		({ scope, text }) => {
			const root = document.querySelector(scope);
			if (!root) return false;
			for (const el of Array.from(root.querySelectorAll<HTMLElement>("*"))) {
				const own = Array.from(el.childNodes)
					.filter((n) => n.nodeType === Node.TEXT_NODE)
					.map((n) => n.textContent || "")
					.join("")
					.replace(/\s+/g, " ")
					.trim();
				if (own === text && el.getClientRects().length) {
					return el.scrollWidth <= el.clientWidth + 1;
				}
			}
			return false;
		},
		{ scope, text }
	);
}

/** Console-error collector that ignores this bench's absent realtime server. */
export function collectPageErrors(page: Page): string[] {
	const errors: string[] = [];
	page.on("console", (msg) => {
		if (msg.type() !== "error") return;
		const text = msg.text();
		// A failed resource load reports only "Failed to load resource: … 404"
		// in its text — the URL lives in location().url. The dev server's
		// socket.io long-poll (a bench without the socketio proxy) is the one
		// such noise source; nothing else is filtered.
		const url = (msg.location() && msg.location().url) || "";
		if (text.includes("socket.io") || url.includes("socket.io") || text.includes("ERR_CONNECTION_REFUSED")) return;
		// Frappe's own app switcher (frappe/public/js/frappe/ui/sidebar/
		// sidebar_header.js, add_app_item) renders its divider rows through the
		// same template as app rows, so each `{ is_divider: true }` entry emits
		// `<img src="undefined">` — one 404 for "<page>/undefined" on every Desk
		// page load in developer mode. Framework code, read-only for this repo
		// (AGENTS.md §2); nothing in a KenTender page can cause or fix it.
		if (/\/undefined$/.test(url)) return;
		errors.push(text);
	});
	return errors;
}

export function expectClose(actual: number, expected: number, tolerance: number, label: string): void {
	if (Number.isNaN(actual) || Number.isNaN(expected)) {
		throw new Error(`${label}: measurement failed (actual=${actual}, expected=${expected})`);
	}
	expect(Math.abs(actual - expected), `${label}: live=${actual} artboard=${expected} ±${tolerance}`).toBeLessThanOrEqual(
		tolerance
	);
}
