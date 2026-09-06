import { execSync } from "node:child_process";
import path from "node:path";

/**
 * PLN-CHG-001 v1.12 decision D13 — the Procurement Planning browser specs
 * move the site's single-valued intake flags onto their fixture year
 * (2098-2099). Whatever ran, put the flags back on the year that was open
 * before (the §8 seed's 2027-2028). A no-op when nothing was moved.
 */
export default async function globalTeardown(): Promise<void> {
	const benchRoot = path.resolve(__dirname, "../../../..");
	const site = process.env.UI_SITE || "kentender.midas.com";
	try {
		execSync(
			`cd "${benchRoot}" && bench --site ${site} execute kentender_procurement.procurement_planning.seeds.playwright_ui_fixtures.restore_site`,
			{ stdio: "pipe", timeout: 120_000 }
		);
	} catch (error: any) {
		// eslint-disable-next-line no-console
		console.warn(`globalTeardown: restore_site failed: ${(error?.stderr || error?.message || "").toString().trim()}`);
	}
}
