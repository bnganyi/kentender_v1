#!/usr/bin/env node
// ANL-CHG-001 v0.8 plan Phase 4, gate ANL-G04: the scoped Analytics stylesheet gives the same computed styles as the
// board, class for class. The method is Home Phase 1A's (HOME6-0104), widened to every artboard:
//
//   original  the design pack's own styles.css plus the board's local style block, the way the board renders;
//   scoped    kt_analytics_ds.bundle.css only, the artboard wrapped in `.kt-industry.kt-analytics`.
//
// Every element of every artboard (22 boards) is compared on every computed CSS property, including ::before and
// ::after, with the scoped copy loaded in three stacks:
//   V0  the scoped stylesheet alone;
//   V1  plus every app-wide stylesheet the kentender apps load in Desk (the "old stylesheet" leaks, HOME6-0112);
//   V2  plus Frappe's own desk.bundle.css (the real Desk stack; font-family text is expected to differ because
//       Frappe's --font-stack names more fallback faces than the pack's literal fallback).
// Then hover and keyboard focus on the first element of each interactive kind.
//
//   node scripts/analytics_design_scope_check.mjs            # prints a summary, exits 1 on a difference in V0 or V1
//
// Needs Playwright's Chromium (from the repository's node_modules). Opens file:// pages only; no server, no login.

import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const BENCH_APPS = path.resolve(ROOT, "../");
const DESIGN = path.join(ROOT, "docs/mvp-1-r1/19_analytics/design");
const DS = fs.readdirSync(path.join(DESIGN, "_ds")).map((d) => path.join(DESIGN, "_ds", d)).find((d) => fs.existsSync(path.join(d, "styles.css")));
const BOARDS = fs.readdirSync(path.join(DESIGN, "Analytics")).filter((f) => f.endsWith(".dc.html")).sort().map((f) => path.join(DESIGN, "Analytics", f));
const SCOPED = fs.readFileSync(path.join(ROOT, "kentender_core/kentender_core/public/js/analytics/kt_analytics_ds.bundle.css"), "utf8");
const PACK = fs.readFileSync(path.join(DS, "styles.css"), "utf8").replace(/@font-face\s*\{[^}]*\}/g, "");

function oldStylesheets() {
	const files = [];
	for (const app of fs.readdirSync(ROOT).filter((d) => d.startsWith("kentender_") && fs.existsSync(path.join(ROOT, d, d, "hooks.py")))) {
		const hooks = fs.readFileSync(path.join(ROOT, app, app, "hooks.py"), "utf8");
		const block = hooks.match(/app_include_css\s*=\s*\[([\s\S]*?)\n\]/);
		if (!block) continue;
		for (const m of block[1].matchAll(/\/assets\/(kentender_\w+)\/css\/([\w.-]+\.css)/g)) {
			const file = path.join(ROOT, m[1], m[1], "public/css", m[2]);
			if (fs.existsSync(file)) files.push(file);
		}
	}
	return [...new Set(files)];
}
const OLD = oldStylesheets().map((f) => fs.readFileSync(f, "utf8"));
const frappeDist = path.resolve(ROOT, "../frappe/frappe/public/dist/css");
const DESK = fs.readFileSync(path.join(frappeDist, fs.readdirSync(frappeDist).find((f) => /^desk\.bundle\..*\.css$/.test(f))), "utf8");

const VARIANTS = {
	V0: { label: "scoped only", css: [SCOPED], strict: true },
	V1: { label: "scoped + the kentender apps' app-wide stylesheets", css: [...OLD, SCOPED], strict: true },
	V2: { label: "scoped + Frappe desk.bundle.css + the app-wide stylesheets", css: [DESK, ...OLD, SCOPED, ...(process.env.NORMAL_TRACKING ? [".kt-industry.kt-analytics{letter-spacing:normal}"] : [])], strict: false },
};

// Optional narrowing while iterating: ONLY_VARIANTS=V0,V1  ONLY_BOARDS="Overview,States"  NO_STATES=1  VERBOSE=1
const ONLY_VARIANTS = (process.env.ONLY_VARIANTS || "").split(",").filter(Boolean);
const ONLY_BOARDS = (process.env.ONLY_BOARDS || "").split(",").filter(Boolean);

const FONT_STACK = (DESK.match(/--font-stack:\s*([^;]+);/) || [])[1];
const frameHtml = (css, wrapped, fontStack) => `<!doctype html><html><head><meta charset="utf-8">${fontStack ? `<style>:root{--font-stack:${fontStack}}</style>` : ""}${[].concat(css).map((sheet) => `<style>${sheet}</style>`).join("")}</head><body style="margin:0">${wrapped ? '<div class="kt-industry kt-analytics"><div id="root"></div></div>' : '<div id="root"></div>'}</body></html>`;

async function artboards(browser, board) {
	const page = await browser.newPage({ viewport: { width: 1600, height: 1200 } });
	await page.route("**/*", (r) => (r.request().url().endsWith(".js") ? r.abort() : r.continue()));
	await page.goto(pathToFileURL(board).href);
	const boards = await page.evaluate(() => [...document.querySelectorAll('[id^="ANL-DES-"]')].map((el) => ({ id: el.id, html: el.outerHTML })));
	const style = await page.evaluate(() => (document.querySelector("style") || {}).textContent || "");
	await page.close();
	return { boards, style };
}

// Runs in the page: compares two subtrees on every computed property, with ::before and ::after.
function compareInPage({ ignore }) {
	const [a, b] = [document.getElementById("A"), document.getElementById("B")];
	const A = a.contentDocument.getElementById("root"), B = b.contentDocument.getElementById("root");
	const ea = [...A.querySelectorAll("*")], eb = [...B.querySelectorAll("*")];
	if (ea.length !== eb.length) return { elements: ea.length, error: `element count ${ea.length} vs ${eb.length}`, diffs: [] };
	const diffs = [];
	const sig = (el) => el.tagName.toLowerCase() + (el.className && el.className.baseVal === undefined && el.className ? "." + String(el.className).trim().split(/\s+/).join(".") : "");
	const props = new Set();
	for (let i = 0; i < ea.length; i++) {
		for (const pseudo of [null, "::before", "::after"]) {
			const ca = a.contentWindow.getComputedStyle(ea[i], pseudo), cb = b.contentWindow.getComputedStyle(eb[i], pseudo);
			if (pseudo && ca.content === "none" && cb.content === "none") continue;
			for (let k = 0; k < ca.length; k++) {
				const p = ca[k];
				if (ignore.includes(p)) continue;
				props.add(p);
				const va = ca.getPropertyValue(p), vb = cb.getPropertyValue(p);
				if (va !== vb) diffs.push({ el: sig(ea[i]) + (pseudo || ""), prop: p, original: va, scoped: vb });
			}
		}
	}
	return { elements: ea.length, properties: props.size, diffs };
}

function summarise(diffs) {
	const byKey = new Map();
	for (const d of diffs) {
		const key = `${d.prop} | ${d.el}`;
		if (!byKey.has(key)) byKey.set(key, { ...d, count: 0 });
		byKey.get(key).count++;
	}
	return [...byKey.values()];
}

const STATES = [
	[".btn-primary", "btn-primary"], [".btn-secondary", "btn-secondary"], [".btn-ghost", "btn-ghost"],
	[".kt-tab:has(input:checked)", "selected tab"], [".kt-tab:not(:has(input:checked))", "unselected tab"],
	["a[href]", "link"], ["summary.kt-disclosure-head", "disclosure head"], ["select.input", "select"], ["input.input", "text input"],
];

async function main() {
	const browser = await chromium.launch();
	const report = { variants: {}, states: {}, artboards: [], dsChecked: 0 };
	const results = {};
	const cmp = await browser.newPage({ viewport: { width: 1600, height: 1200 } });
	try {
		for (const board of BOARDS.filter((b) => !ONLY_BOARDS.length || ONLY_BOARDS.some((n) => b.includes(n)))) {
			const { boards, style } = await artboards(browser, board);
			for (const [vname, v] of Object.entries(VARIANTS).filter(([n]) => !ONLY_VARIANTS.length || ONLY_VARIANTS.includes(n))) {
				await cmp.setContent(`<body><iframe id="A" style="width:1560px;height:1100px;border:0"></iframe><iframe id="B" style="width:1560px;height:1100px;border:0"></iframe></body>`);
				await cmp.evaluate(([a, b]) => { document.getElementById("A").srcdoc = a; document.getElementById("B").srcdoc = b; }, [frameHtml(PACK + "\n" + style, false, vname === "V2" ? FONT_STACK : null), frameHtml(v.css, true)]);
				await cmp.waitForFunction(() => ["A", "B"].every((id) => document.getElementById(id).contentDocument && document.getElementById(id).contentDocument.getElementById("root")));
				for (const ab of boards) {
					await cmp.evaluate(([html]) => { for (const id of ["A", "B"]) document.getElementById(id).contentDocument.getElementById("root").innerHTML = html; }, [ab.html]);
					const ignore = vname === "V2" ? [] : [];
					const out = await cmp.evaluate(compareInPage, { ignore });
					const key = vname;
					results[key] ??= { boards: 0, elements: 0, diffs: [], errors: [] };
					results[key].boards++;
					results[key].elements += out.elements;
					if (out.error) results[key].errors.push(`${ab.id}: ${out.error}`);
					results[key].diffs.push(...out.diffs.map((d) => ({ ...d, board: ab.id })));
					if (!report.artboards.includes(ab.id)) report.artboards.push(ab.id);
					report.properties = Math.max(report.properties || 0, out.properties || 0);
					// hover and keyboard focus, on the first element of each kind in this artboard
					if ((vname === "V1" || (vname === "V0" && board.includes("Overview"))) && !process.env.NO_STATES) {
						const fa = await (await cmp.$("#A")).contentFrame(), fb = await (await cmp.$("#B")).contentFrame();
						for (const [selector, name] of STATES) {
							const la = fa.locator(`#root ${selector}`).first(), lb = fb.locator(`#root ${selector}`).first();
							if (!(await la.count())) continue;
							for (const mode of ["focus", "hover"]) {
								// only one frame can hold focus or the pointer at a time: apply the state to one copy, read it, then the other
								const read = (f) => f.evaluate(([sel, mode]) => {
									const el = document.querySelector(`#root ${sel}`);
									const rows = [];
									for (const e of [el, ...el.querySelectorAll("*")]) for (const pseudo of [null, "::before", "::after"]) {
										const cs = getComputedStyle(e, pseudo);
										const row = {};
										for (const p of cs) row[p] = cs.getPropertyValue(p);
										rows.push(row);
									}
									return { rows, state: mode === "focus" ? el.matches(":focus-visible") || el.matches(":has(:focus-visible)") : el.matches(":hover") };
								}, [selector, mode]);
								const probe = [];
								for (const [l, f] of [[la, fa], [lb, fb]]) {
									await cmp.mouse.move(2, 2);
									if (mode === "focus") await l.focus(); else await l.hover();
									await cmp.waitForTimeout(300); // let the 120 ms and 200 ms colour transitions settle before reading
									probe.push(await read(f));
									await f.evaluate(() => document.activeElement && document.activeElement.blur());
								}
								const sk = `${vname}|${name}|${mode}`;
								report.states[sk] ??= { elements: 0, applied: true, diffs: 0, examples: [] };
								report.states[sk].elements += probe[0].rows.length;
								if (!probe[0].state || !probe[1].state) report.states[sk].applied = false;
								probe[0].rows.forEach((row, i) => Object.entries(row).forEach(([prop, value]) => {
									const other = probe[1].rows[i][prop];
									if (value !== other) { report.states[sk].diffs++; if (report.states[sk].examples.length < 4) report.states[sk].examples.push(`${ab.id}: ${prop}:${value} vs ${other}`); }
								}));
							}
							await fa.evaluate(() => document.activeElement && document.activeElement.blur());
							await fb.evaluate(() => document.activeElement && document.activeElement.blur());
							await cmp.mouse.move(2, 2);
						}
					}
				}
			}
		}
	} finally {
		await browser.close();
	}
	let failed = false;
	console.log(`artboards compared: ${report.artboards.length} (${report.artboards.join(", ")})`);
	console.log(`computed properties per element: ${report.properties}`);
	for (const [vname, r] of Object.entries(results)) {
		const sum = summarise(r.diffs);
		console.log(`\n${vname} (${VARIANTS[vname].label}): ${r.boards} artboards, ${r.elements} elements, ${r.diffs.length} differing property values, ${sum.length} distinct (property, element) pairs; element-count errors: ${r.errors.length}`);
		for (const e of r.errors) console.log("  ERROR", e);
		const byProp = new Map();
		for (const d of sum) byProp.set(d.prop, (byProp.get(d.prop) || 0) + 1);
		if (process.env.VERBOSE) for (const d of sum) console.log(`    ${d.board} ${d.el} ${d.prop}: original=${JSON.stringify(d.original).slice(0, 70)} scoped=${JSON.stringify(d.scoped).slice(0, 70)}`);
		for (const [prop, n] of [...byProp].sort((x, y) => y[1] - x[1]).slice(0, 12)) {
			const ex = sum.find((d) => d.prop === prop);
			console.log(`  ${prop}: ${n} pairs, e.g. ${ex.el} [${ex.board}] original=${JSON.stringify(ex.original).slice(0, 80)} scoped=${JSON.stringify(ex.scoped).slice(0, 80)}`);
		}
		if (!VARIANTS[vname].strict) {
			// Frappe's own global rules (typeface list, scrollbar, tap highlight, tracking, custom properties) reach every Desk
			// page alike; what is left is what Frappe's CSS changes about the board's own classes.
			// (appearance, outline-width, user-select and cursor on the hidden radio inputs and the buttons have no visible effect.)
			const noise = /^(--|font-family$|font-variation-settings$|scrollbar-|text-size-adjust$|-webkit-|letter-spacing$|text-align$|appearance$|outline-width$|user-select$)/;
			const rest = sum.filter((d) => !noise.test(d.prop));
			console.log(`  of which not Desk-global noise: ${rest.length} (property, element) pairs`);
			if (process.env.VERBOSE) {
				const byEl = new Map();
				for (const d of rest) { const k = d.el; byEl.set(k, [...(byEl.get(k) || []), `${d.prop}: ${String(d.original).slice(0, 24)} -> ${String(d.scoped).slice(0, 24)}`]); }
				for (const [el, list] of byEl) console.log(`    ${el}: ${[...new Set(list)].slice(0, 6).join(" | ")}`);
			}
			const byProp2 = new Map();
			for (const d of rest) byProp2.set(d.prop, (byProp2.get(d.prop) || 0) + 1);
			for (const [prop, n] of [...byProp2].sort((x, y) => y[1] - x[1]).slice(0, 25)) {
				const ex = rest.find((d) => d.prop === prop);
				console.log(`    ${prop}: ${n} pairs, e.g. ${ex.el} [${ex.board}] original=${JSON.stringify(ex.original).slice(0, 60)} scoped=${JSON.stringify(ex.scoped).slice(0, 60)}`);
			}
		}
		if (VARIANTS[vname].strict && (r.diffs.length || r.errors.length)) failed = true;
	}
	console.log("\nstates (element + descendants, all computed properties incl. pseudo-elements):");
	for (const [k, s] of Object.entries(report.states)) {
		console.log(`  ${k}: ${s.elements} element-pseudo rows, state applied in both: ${s.applied}, differences: ${s.diffs}${s.examples.length ? " e.g. " + s.examples.join(" ; ") : ""}`);
		if (s.diffs) failed = true;
	}
	process.exit(failed ? 1 : 0);
}
main();
