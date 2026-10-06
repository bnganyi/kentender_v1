import { test } from "@playwright/test";
import * as fs from "node:fs";
import * as path from "node:path";

import { login } from "../helpers/auth";

/**
 * HOME-CHG-001 v0.6 Phase 1B (HOME6-0102, HOME6-0109): one screenshot of each Industry page at 1440 and 1024 px, as the
 * person who works in it. Run before the restyle and again after, into different folders, then compare:
 *   CAPTURE_DIR=docs/mvp-1-r1/18_home_page/evidence/phase1b/before scripts/test-site.sh run npx playwright test tests/ui/design-review/capture.spec.ts --workers=1
 * Read-only: nothing is written to the site. A route that cannot be shown still gets a picture (the error is the finding).
 */
const PASSWORD = process.env.UI_SEED_PASSWORD || "Test@123";
const ADMIN = process.env.UI_ADMIN_USER || "Administrator";
const ADMIN_PASSWORD = process.env.UI_ADMIN_PASSWORD || "";
const person = (name: string) => `${name}@moh.example.test`;

type Shot = { name: string; as: string; route: string };
const SHOTS: Shot[] = [
	{ name: "system-setup", as: ADMIN, route: "/desk/system-setup" },
	{ name: "reference-data", as: ADMIN, route: "/desk/reference-data" },
	{ name: "technical-search", as: person("daniel.otieno"), route: "/desk/technical-search" },
	{ name: "strategy", as: person("mercy.kilonzo"), route: "/desk/strategy" },
	{ name: "budget-funding", as: person("josphat.mwangi"), route: "/desk/budget-funding" },
	{ name: "departmental-needs", as: person("peter.kimani"), route: "/desk/departmental-needs" },
	{ name: "procurement-planning", as: person("mercy.kilonzo"), route: "/desk/procurement-planning" },
	{ name: "procurement-requisitions", as: person("charles.mutiso"), route: "/desk/procurement-requisitions" },
	{ name: "tenders", as: person("charles.mutiso"), route: "/desk/tenders" },
	{ name: "tender-record", as: person("charles.mutiso"), route: "/desk/tenders/TND-MOH-2026-010" },
	{ name: "tender-evaluation", as: person("charles.mutiso"), route: "/desk/tenders/TND-MOH-2026-010/evaluation" },
	{ name: "tender-opening", as: person("charles.mutiso"), route: "/desk/tenders/TND-MOH-2026-005/opening" },
	{ name: "award", as: person("charles.mutiso"), route: "/desk/award/AWD-MOH-2026-003" },
	{ name: "procurement-meetings", as: person("amina.hassan"), route: "/desk/procurement-meetings" },
	{ name: "std-templates", as: person("charles.mutiso"), route: "/desk/std-templates" },
	{ name: "tender-security-receipts", as: person("charles.mutiso"), route: "/desk/tender-security-receipts" },
];
const ONLY = (process.env.CAPTURE_ONLY || "").split(",").filter(Boolean);
const WIDTHS = (process.env.CAPTURE_VIEWS || "").split(",").filter(Boolean);
const VIEWS = [
	{ label: "1440", width: 1440, height: 1000 },
	{ label: "1024", width: 1024, height: 768 },
].filter((view) => !WIDTHS.length || WIDTHS.includes(view.label));

test.describe.configure({ mode: "serial", timeout: 300_000 });

for (const shot of SHOTS.filter((s) => !ONLY.length || ONLY.includes(s.name))) {
	test(`capture ${shot.name}`, async ({ page }) => {
		const out = process.env.CAPTURE_DIR;
		if (!out) throw new Error("set CAPTURE_DIR");
		fs.mkdirSync(path.resolve(out), { recursive: true });
		await login(page, shot.as, shot.as === ADMIN ? ADMIN_PASSWORD : PASSWORD);
		for (const view of VIEWS) {
			await page.setViewportSize({ width: view.width, height: view.height });
			await page.goto(shot.route, { waitUntil: "domcontentloaded" });
			await page.locator(".kt-industry, .page-container, .msgprint").first().waitFor({ state: "visible", timeout: 60_000 }).catch(() => {});
			await page.waitForFunction(() => !/Loading/i.test(document.querySelector(".kt-industry")?.textContent || ""), undefined, { timeout: 30_000 }).catch(() => {});
			await page.waitForTimeout(2500);
			await page.screenshot({ path: path.resolve(out, `${shot.name}-${view.label}.png`), fullPage: false });
		}
	});
}
