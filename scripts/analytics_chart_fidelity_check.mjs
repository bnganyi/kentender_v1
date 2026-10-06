#!/usr/bin/env node
// ANL-CHG-001 v0.8 plan Phase 4 — the chart components draw what the boards draw.
//
// For each chart, the board's own markup (rendered with the design pack's stylesheet and the board's style block,
// as the board renders) and the Vue component's markup (A1 fixture values; rendered with only the scoped
// kt_analytics_ds.bundle.css) are put in boxes of the same width in Chromium, screenshotted and compared pixel by pixel.
// Visually hidden tables take no space, so they do not show.
//
//   KT_ANALYTICS_DUMP=/tmp/chart_dump.json npx vitest run --project analytics dump    # renders the components
//   node scripts/analytics_chart_fidelity_check.mjs /tmp/chart_dump.json
//   STACK=v1 node ...   the component side also loads the kentender apps' app-wide stylesheets
//   STACK=v2 node ...   ... and Frappe's desk.bundle.css as well (the board then uses Frappe's --font-stack, so the typeface matches)
//   NORMAL_TRACKING=1   sets letter-spacing: normal on the component side, to separate Frappe's body tracking (0.02em) from other differences

import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const DESIGN = path.join(ROOT, "docs/mvp-1-r1/19_analytics/design");
const DS = fs.readdirSync(path.join(DESIGN, "_ds")).map((d) => path.join(DESIGN, "_ds", d)).find((d) => fs.existsSync(path.join(d, "styles.css")));
const PACK = fs.readFileSync(path.join(DS, "styles.css"), "utf8").replace(/@font-face\s*\{[^}]*\}/g, "");
const SCOPED = fs.readFileSync(path.join(ROOT, "kentender_core/kentender_core/public/js/analytics/kt_analytics_ds.bundle.css"), "utf8");
const STACK = (process.env.STACK || "v0").toLowerCase();
function oldStylesheets() {
	const files = [];
	for (const app of fs.readdirSync(ROOT).filter((d) => d.startsWith("kentender_") && fs.existsSync(path.join(ROOT, d, d, "hooks.py")))) {
		const block = fs.readFileSync(path.join(ROOT, app, app, "hooks.py"), "utf8").match(/app_include_css\s*=\s*\[([\s\S]*?)\n\]/);
		if (!block) continue;
		for (const m of block[1].matchAll(/\/assets\/(kentender_\w+)\/css\/([\w.-]+\.css)/g)) {
			const file = path.join(ROOT, m[1], m[1], "public/css", m[2]);
			if (fs.existsSync(file)) files.push(file);
		}
	}
	return [...new Set(files)].map((f) => fs.readFileSync(f, "utf8"));
}
const frappeDist = path.resolve(ROOT, "../frappe/frappe/public/dist/css");
const DESK = fs.readFileSync(path.join(frappeDist, fs.readdirSync(frappeDist).find((f) => /^desk\.bundle\..*\.css$/.test(f))), "utf8");
const FONT_STACK = (DESK.match(/--font-stack:\s*([^;]+);/) || [])[1];
const TRACKING = process.env.NORMAL_TRACKING ? [".kt-industry.kt-analytics{letter-spacing:normal}"] : [];
const COMPONENT_CSS = STACK === "v2" ? [DESK, ...oldStylesheets(), SCOPED, ...TRACKING] : STACK === "v1" ? [...oldStylesheets(), SCOPED, ...TRACKING] : [SCOPED];
const dump = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));

const TR = "Analytics Tenders and Requisitions", OV = "Analytics Overview", PL = "Analytics Planning and Needs";
// where the board draws it: file, artboard, the region heading (or a selector), and which children of the region to take
const CASES = [
	{ name: "stage", file: TR, ab: "ANL-DES-22", h2: "Tenders by stage", pick: [0] },
	{ name: "stageSelected", file: TR, ab: "ANL-DES-23", h2: "Tenders by stage", pick: [1] },
	{ name: "monthly", file: TR, ab: "ANL-DES-22", h2: "Recorded each month", pick: [0, 1, 2] },
	{ name: "range", file: OV, ab: "ANL-DES-21", h2: "Time between key steps", pick: [0, 1] },
	{ name: "bands", file: OV, ab: "ANL-DES-21", h2: "Outstanding matters by waiting time", pick: [0, 1] },
	{ name: "coverage", file: OV, ab: "ANL-DES-21", h2: "Plan coverage", pick: [1, 2] },
	{ name: "strip", file: OV, ab: "ANL-DES-21", card: ".kt-kpi-card:nth-child(5)", pick: [2, 3] },
	{ name: "items", file: PL, ab: "ANL-DES-25", h2: "Coverage by Plan item", pick: [0, 1], last: true },
	{ name: "dept", file: PL, ab: "ANL-DES-25", h2: "Coverage by department", pick: [0] },
	{ name: "timing", file: PL, ab: "ANL-DES-25", h2: "Tender invitation timing", pick: [0, 1, 2] },
	{ name: "funding", file: OV, ab: "ANL-DES-28", h2: "Funding position", pick: [2, 3] },
];

async function boardSnippet(browser, c) {
	const page = await browser.newPage({ viewport: { width: 1600, height: 1200 } });
	await page.route("**/*", (r) => (r.request().url().endsWith(".js") ? r.abort() : r.continue()));
	await page.goto(pathToFileURL(path.join(DESIGN, "Analytics", c.file + ".dc.html")).href);
	const out = await page.evaluate((c) => {
		const ab = document.getElementById(c.ab);
		let region;
		if (c.card) region = ab.querySelector(c.card);
		else {
			const heads = [...ab.querySelectorAll("h2")].filter((h) => h.textContent.trim().startsWith(c.h2));
			region = (c.last ? heads[heads.length - 1] : heads[0]).parentElement;
		}
		const kids = [...region.children].filter((k) => !(k.tagName === "H2"));
		const cs = getComputedStyle(region);
		return {
			width: region.getBoundingClientRect().width,
			gap: cs.rowGap === "normal" ? "0px" : cs.rowGap,
			html: c.pick.map((i) => kids[c.card ? i : i].outerHTML).join(""),
			kids: kids.length,
		};
	}, c);
	const style = await page.evaluate(() => (document.querySelector("style") || {}).textContent || "");
	await page.close();
	return { ...out, style };
}

const doc = (css, inner, width, gap, wrapped) => `<!doctype html><html><head><meta charset="utf-8">${STACK === "v2" && !wrapped ? `<style>:root{--font-stack:${FONT_STACK}}</style>` : ""}${[].concat(css).map((sheet) => `<style>${sheet}</style>`).join("")}</head><body style="margin:0;padding:8px;background:#fff">${wrapped ? '<div class="kt-industry kt-analytics">' : ""}<div id="c" style="position:relative;background:#fff;width:${width}px;display:flex;flex-direction:column;gap:${gap}">${inner}</div>${wrapped ? "</div>" : ""}</body></html>`;

const browser = await chromium.launch();
let failed = false;
const rows = [];
for (const c of CASES) {
	const snip = await boardSnippet(browser, c);
	const shots = [];
	for (const [css, inner, wrapped] of [[PACK + "\n" + snip.style, snip.html, false], [COMPONENT_CSS, dump[c.name], true]]) {
		const page = await browser.newPage({ viewport: { width: 1000, height: 900 }, deviceScaleFactor: 1 });
		await page.setContent(doc(css, inner, snip.width, snip.gap, wrapped));
		const box = await page.locator("#c").boundingBox();
		const png = await page.locator("#c").screenshot();
		shots.push({ png, box });
		await page.close();
	}
	const cmp = await browser.newPage();
	await cmp.setContent("<canvas id=a></canvas><canvas id=b></canvas>");
	const res = await cmp.evaluate(async ([a, b]) => {
		const load = (data) => new Promise((ok) => { const i = new Image(); i.onload = () => ok(i); i.src = "data:image/png;base64," + data; });
		const [ia, ib] = await Promise.all([load(a), load(b)]);
		const w = Math.max(ia.width, ib.width), h = Math.max(ia.height, ib.height);
		const px = (img) => { const cv = document.createElement("canvas"); cv.width = w; cv.height = h; const g = cv.getContext("2d"); g.fillStyle = "#fff"; g.fillRect(0, 0, w, h); g.drawImage(img, 0, 0); return g.getImageData(0, 0, w, h).data; };
		const da = px(ia), db = px(ib);
		let diff = 0, max = 0, x0 = w, x1 = -1, y0 = h, y1 = -1;
		for (let i = 0; i < da.length; i += 4) {
			const d = Math.max(Math.abs(da[i] - db[i]), Math.abs(da[i + 1] - db[i + 1]), Math.abs(da[i + 2] - db[i + 2]));
			if (d > 0) { diff++; if (d > max) max = d; const x = (i / 4) % w, y = Math.floor(i / 4 / w); x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y); }
		}
		return { board: [ia.width, ia.height], component: [ib.width, ib.height], pixels: w * h, differing: diff, maxChannelDelta: max, box: diff ? [x0, y0, x1, y1] : null };
	}, [shots[0].png.toString("base64"), shots[1].png.toString("base64")]);
	await cmp.close();
	rows.push({ name: c.name, ...res });
	if (res.differing || res.board.join() !== res.component.join()) failed = true;
	fs.mkdirSync("/tmp/claude-1002/fidelity", { recursive: true });
	fs.writeFileSync(`/tmp/claude-1002/fidelity/${c.name}-board.png`, shots[0].png);
	fs.writeFileSync(`/tmp/claude-1002/fidelity/${c.name}-component.png`, shots[1].png);
}
await browser.close();
for (const r of rows) console.log(`${r.name.padEnd(14)} board ${r.board.join("x")}  component ${r.component.join("x")}  differing pixels ${r.differing} of ${r.pixels}  max channel delta ${r.maxChannelDelta}${r.box ? "  differing pixels lie in x " + r.box[0] + "-" + r.box[2] + ", y " + r.box[1] + "-" + r.box[3] : ""}`);
process.exit(failed ? 1 : 0);
