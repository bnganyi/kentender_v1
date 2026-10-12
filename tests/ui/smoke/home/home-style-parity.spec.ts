import { expect, test } from "@playwright/test";
import path from "node:path";

import { CHARLES, openHomeFromMenu, putWorldClock } from "./helpers";

/**
 * HOME-CHG-001 v0.6 Phase 8 (row HOME6-0804): the page's type, colour and shape against the board's, element by element.
 * The structural gate (`Home.fidelity.spec.js`) cannot see a style the page inherits from Desk, which is how Desk's
 * 0.26 px letter spacing reached every line of Home. Each pair below names a role, the board's element (found by its
 * own text on HOME-DES-21, Charles) and the live element playing the same role; both are read in Chromium and their
 * computed styles must agree. Read-only; run on the test site:
 *   scripts/test-site.sh run npx playwright test tests/ui/smoke/home/home-style-parity.spec.ts --workers=1
 */
test.describe.configure({ mode: "serial", timeout: 240_000 });
test.beforeAll(() => putWorldClock());

const BOARD = "docs/mvp-1-r1/18_home_page/design/Home/Home.dc.html";

type Role = {
	role: string;
	board?: string; // the board it is read from (default HOME-DES-21)
	text?: string; // the board's element, found by its own text (the nth leaf carrying exactly that text) ...
	selector?: string; // ... or by a selector inside the board's <main>
	nth?: number;
	live: string;
	box?: boolean; // compare the container's own box (border, padding, ground) as well as its type
	boxOnly?: boolean; // a container with no text of its own (an icon chip): its box only
};

const ROLES: Role[] = [
	{ role: "sheet", selector: "main", live: ".kt-home .kt-home-sheet", box: true },
	{ role: "title", text: "Good morning, Charles", live: ".kt-home .kt-home-title" },
	{ role: "responsibilities", text: "Head of Procurement Function, site-wide", live: ".kt-home .kt-home-sub" },
	{ role: "updated", text: "Updated 18 June 2027, 10:00 EAT", live: ".kt-home .kt-home-updated" },
	{ role: "summary column", selector: ".kt-kpi-card", live: ".kt-home .kt-home-kpi", box: true },
	{ role: "summary heading", text: "My work", live: ".kt-home .kt-home-kpi .kt-kpi-head" },
	{ role: "summary figure", text: "3", live: ".kt-home .kt-home-kpi .kt-home-figure" },
	{ role: "summary label", text: "actions for you", live: ".kt-home .kt-home-kpi .kt-home-figure-label" },
	{ role: "region heading", text: "My work", nth: 1, live: "#my-work h2" },
	{ role: "module chip (main column)", selector: "section .kt-icon-chip", live: "#my-work .kt-home-chip-main", box: true, boxOnly: true },
	{ role: "row title", text: "Clinic equipment requisition", live: "#my-work .kt-home-row-title" },
	{ role: "row action", text: "Authorise requisition", live: "#my-work .kt-home-action" },
	{ role: "row timing", text: "Received 2 days ago (16 June, 11:00)", live: "#my-work .kt-home-row .kt-home-quiet:last-of-type" },
	{ role: "Coming up badge", text: "In 7 days", live: "#coming-up .kt-home-badge", box: true },
	{ role: "Continue (primary)", text: "Continue", live: "#my-work .btn-primary", box: true },
	{ role: "Continue (standard)", text: "Continue", nth: 1, live: "#my-work .btn-secondary", box: true },
	{ role: "Show more (ghost)", board: "HOME-DES-26", text: "Show 1 more", live: "#my-work .btn-ghost", box: true },
	{ role: "View record", text: "View record", live: "#coming-up .kt-home-link" },
	{ role: "rail heading", text: "Waiting on others", nth: 1, live: "#waiting h2" },
	{ role: "rail title", text: "Supply of UPS units", live: "#waiting .kt-home-rail-title" },
	{ role: "rail state", text: "Waiting for Amina Hassan to decide publication", live: "#waiting .kt-home-rail-state" },
	{ role: "rail timing", text: "Waiting 2 days (since 16 June, 15:30)", live: "#waiting .kt-home-rail-time" },
	{ role: "Analytics link", text: "See all in Procurement Analytics", live: ".kt-home-analytics-link" },
];
/**
 * Differences from the board that the Project Owner approved after the board was drawn (DS-REV-003 control shape,
 * DS-REV-005 corner radius, white field fill, 6 Oct 2026; KT-STD-001 v1.23–v1.25; DS-REV-006 blue-grey control edge #8590a6, 9 Oct 2026; KT-STD-001 v1.28). The page must show exactly the value
 * named here, so the gate still fails if the page drifts anywhere else. Retire an entry when the board is redrawn.
 */
const APPROVED_DEPARTURES: Record<string, string> = {
	"sheet|borderTopLeftRadius": "4px",
	"Continue (primary)|borderTopLeftRadius": "2px",
	"Continue (standard)|backgroundColor": "rgb(255, 255, 255)",
	"Continue (standard)|borderTopColor": "rgb(133, 144, 166)",
	"Continue (standard)|borderLeftColor": "rgb(133, 144, 166)",
	"Continue (standard)|borderTopLeftRadius": "2px",
	"Show more (ghost)|borderTopLeftRadius": "2px",
};
const PROPS = ["fontFamily", "fontSize", "fontWeight", "lineHeight", "letterSpacing", "color", "textDecorationLine", "textTransform", "fontStyle"];
const BOX_PROPS = ["backgroundColor", "borderTopWidth", "borderTopColor", "borderLeftWidth", "borderLeftColor", "borderTopLeftRadius", "paddingTop", "paddingRight", "paddingBottom", "paddingLeft"];

// Runs in the page: one element's computed type, colour and (for a box) shape, as plain strings.
const readStyle = (el: Element, props: string[]) => {
	const style = getComputedStyle(el as HTMLElement);
	const out: Record<string, string> = {};
	for (const prop of props) out[prop] = (style as any)[prop];
	if (out.fontFamily) out.fontFamily = out.fontFamily.split(",")[0].replace(/"/g, "").trim();
	return out;
};

test("every role in the page is typed, coloured and shaped as the board draws it", async ({ page, browser }) => {
	const context = await browser.newContext({ viewport: { width: 1440, height: 1100 } });
	const board = await context.newPage();
	await board.route(/support\.js/, (route) => route.abort());
	await board.goto("file://" + path.resolve(BOARD));
	await board.waitForSelector("#HOME-DES-21 main");
	await page.setViewportSize({ width: 1440, height: 1100 });
	await openHomeFromMenu(page, CHARLES);

	const differences: string[] = [];
	for (const item of ROLES) {
		const { role, text, selector, live: liveSelector } = item;
		const nth = item.nth || 0;
		const props = item.boxOnly ? [...BOX_PROPS, "height"] : item.box ? [...PROPS, ...BOX_PROPS, "height"] : PROPS;
		const wanted = await board.evaluate(
			({ id, text, selector, nth, props, readSrc }) => {
				const read = new Function("el", "props", `return (${readSrc})(el, props)`) as (el: Element, props: string[]) => Record<string, string>;
				const main = document.querySelector(`#${id} main`) as Element;
				const found = selector
					? Array.from(selector === "main" ? [main] : main.querySelectorAll(selector))
					: Array.from(main.querySelectorAll("*")).filter((el) => {
							if (el.tagName === "svg" || el.closest("svg")) return false;
							const flat = (node: Element) => node.textContent!.replace(/\s+/g, " ").trim();
							return flat(el) === text && !Array.from(el.children).some((child) => child.tagName !== "svg" && flat(child) === text);
					  });
				if (!found[nth]) return null;
				const out = read(found[nth], props);
				if (props.includes("height")) out.height = String(Math.round(found[nth].getBoundingClientRect().height));
				return out;
			},
			{ id: item.board || "HOME-DES-21", text, selector, nth, props, readSrc: readStyle.toString() },
		);
		const live = await page.evaluate(
			({ selector, props, readSrc }) => {
				const read = new Function("el", "props", `return (${readSrc})(el, props)`) as (el: Element, props: string[]) => Record<string, string>;
				const el = document.querySelector(selector);
				if (!el) return null;
				const out = read(el, props);
				if (props.includes("height")) out.height = String(Math.round(el.getBoundingClientRect().height));
				return out;
			},
			{ selector: liveSelector, props, readSrc: readStyle.toString() },
		);
		if (!wanted) { differences.push(`${role}: the board has no element for ${text || selector}`); continue; }
		if (!live) { differences.push(`${role}: the page has no element for ${liveSelector}`); continue; }
		for (const prop of props) {
			if (prop === "height" && !/Continue|badge|Show more|chip|summary column/.test(role)) continue; // text wraps with the width the Desk sidebar leaves it
			if (live[prop] === APPROVED_DEPARTURES[`${role}|${prop}`]) continue;
			if (wanted[prop] !== live[prop]) differences.push(`${role}: ${prop} is ${live[prop]} on the page, ${wanted[prop]} on the board`);
		}
	}
	expect(differences, differences.join("\n")).toEqual([]);
});
