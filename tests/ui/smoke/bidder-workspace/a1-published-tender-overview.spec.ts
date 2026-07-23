import { execSync } from "node:child_process";
import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

/**
 * BW-A1 Published Tender Overview.
 * Route: /desk/published-tender-overview/<publication_ref>
 */

const PAGE_SLUG = "published-tender-overview";
const ROOT = '[data-testid="kt-cl-bw-a1-root"]';
const CONFIG = "TCFG-SEED-TCFG-RP";
const BENCH = "/home/midasuser/frappe-bench";
const SITE = "kentender.midas.com";

async function seedUi00(page: import("@playwright/test").Page) {
	await page.waitForFunction(() => typeof (window as unknown as { frappe?: unknown }).frappe !== "undefined");
	const result = await page.evaluate(async () => {
		// @ts-expect-error frappe on desk
		const r = await frappe.call({
			method: "kentender_procurement.tender_configurations.seed_ui00_dashboard_for_tests",
			args: { clear: 1 },
		});
		return r.message || r;
	});
	if (!result || !(result as { configurations?: string[] }).configurations) {
		throw new Error("BW-A1 seed failed: " + JSON.stringify(result));
	}
	await loginAsAdministrator(page);
}

function seedBidderFacingForPublish(configId: string) {
	execSync(
		`cd ${BENCH} && bench --site ${SITE} execute kentender_procurement.tender_configurations.seed.preview_fixtures._seed_bidder_facing_config --args "('${configId}',)"`,
		{ stdio: "pipe" }
	);
}

function localDatetimeOffset(days: number, hours = 0): string {
	const d = new Date();
	d.setDate(d.getDate() + days);
	d.setHours(d.getHours() + hours);
	const pad = (n: number) => String(n).padStart(2, "0");
	return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

async function publishAndGetRef(
	page: import("@playwright/test").Page,
	configId = CONFIG
): Promise<{ publicationId: string; publicationRef: string }> {
	seedBidderFacingForPublish(configId);
	const out = await page.evaluate(async (id) => {
		// @ts-expect-error frappe on desk
		await frappe.call({
			method: "kentender_procurement.tender_configurations.generate_tender_configuration_document_preview",
			args: { configuration_id: id },
		});
		const schema = JSON.stringify({
			version: 1,
			sections: [
				{
					section_key: "eligibility_declarations",
					title: "Eligibility & Declarations",
					required: true,
				},
				{ section_key: "price_schedule", title: "Price Schedule", required: true },
			],
		});
		// @ts-expect-error frappe on desk
		await frappe.call({
			method: "frappe.client.set_value",
			args: {
				doctype: "Tender Configuration",
				name: id,
				fieldname: "bidder_submission_schema",
				value: schema,
			},
		});
		// @ts-expect-error frappe on desk
		await frappe.call({
			method: "frappe.client.set_value",
			args: {
				doctype: "Tender Configuration",
				name: id,
				fieldname: "short_scope_summary",
				value:
					"Provision of ICT equipment and related services for the BW-A1 Playwright smoke tender.",
			},
		});
		// @ts-expect-error frappe on desk
		const conf = await frappe.call({
			method: "kentender_procurement.tender_configurations.confirm_tender_package",
			args: { configuration_id: id, payload: { confirm_ready_for_handoff: 1 } },
		});
		const pubId = (conf.message || conf).publication_id;
		const now = new Date();
		const pad = (n: number) => String(n).padStart(2, "0");
		const stamp = (days: number, hours = 0) => {
			const d = new Date(now.getTime());
			d.setDate(d.getDate() + days);
			d.setHours(d.getHours() + hours);
			return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:00`;
		};
		// @ts-expect-error frappe on desk
		await frappe.call({
			method: "kentender_procurement.tender_configurations.save_publication_setup",
			args: {
				publication_id: pubId,
				payload: {
					publication_mode: "immediate",
					publication_datetime: stamp(0),
					tender_notice: "BW-A1 Playwright published tender notice.",
					clarification_deadline: stamp(2),
					submission_deadline: stamp(14),
					opening_datetime: stamp(14, 1),
					bidder_visibility: "All Registered Bidders",
					activate_bidder_workspace: 1,
					acknowledgement_confirmed: 1,
				},
			},
		});
		// @ts-expect-error frappe on desk
		const published = await frappe.call({
			method: "kentender_procurement.tender_configurations.publish_tender",
			args: { publication_id: pubId },
		});
		const msg = published.message || published;
		return {
			publicationId: pubId,
			publicationRef: msg.publication_ref || "",
		};
	}, configId);
	if (!out.publicationRef) {
		// Fallback: read from DocType
		const ref = execSync(
			`cd ${BENCH} && bench --site ${SITE} execute frappe.client.get_value --kwargs "{'doctype':'IT Tender Publication Record','filters':{'name':'${out.publicationId}'},'fieldname':'publication_ref'}"`,
			{ encoding: "utf-8" }
		).trim();
		const match = ref.match(/PUB-\d{4}-\d+/);
		if (!match) {
			throw new Error("Could not resolve publication_ref: " + ref);
		}
		out.publicationRef = match[0];
	}
	return out;
}

test.describe.configure({ mode: "serial" });

test.describe("BW-A1 Published Tender Overview", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
		await loginAsAdministrator(page);
		await page.goto("/desk", { waitUntil: "domcontentloaded" });
		await seedUi00(page);
	});

	test("open overview — Start Bid, package docs, schema checklist, tender info", async ({ page }) => {
		const { publicationRef } = await publishAndGetRef(page);
		await page.goto(`/desk/${PAGE_SLUG}/${encodeURIComponent(publicationRef)}`);
		await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-cl-bw-a1-layout")).toBeVisible();
		await expect(page.getByTestId("kt-cl-bw-a1-title")).toBeVisible();
		await expect(page.getByTestId("kt-cl-bw-a1-primary-cta-label")).toHaveText("Start Bid");
		await expect(page.getByTestId("kt-cl-bw-a1-primary-cta")).toBeEnabled();

		const docText = (await page.getByTestId("kt-cl-bw-a1-documents").innerText()).toLowerCase();
		expect(docText).not.toContain("bill of quantities (boq)");
		expect(docText).not.toContain("technical specifications");
		await expect(page.getByTestId("kt-cl-bw-a1-doc-row").first()).toBeVisible();

		const checklist = page.getByTestId("kt-cl-bw-a1-submit-checklist");
		await expect(checklist).toContainText("Eligibility & Declarations");
		await expect(checklist).toContainText("Price Schedule");

		await expect(page.getByTestId("kt-cl-bw-a1-info-row").first()).toBeVisible();
		const infoText = await page.getByTestId("kt-cl-bw-a1-tender-info").innerText();
		expect(infoText).toMatch(/Procurement Method|STD Family|Bid Security/i);
		expect(infoText).not.toMatch(/^[a-f0-9]{12}$/m);
	});

	test("past deadline shows Closed and disables Start Bid", async ({ page }) => {
		const { publicationId, publicationRef } = await publishAndGetRef(page);
		const past = localDatetimeOffset(-1).replace("T", " ") + ":00";
		// db.set_value bypasses setup_locked validation on published records.
		execSync(
			`cd ${BENCH} && bench --site ${SITE} execute frappe.db.set_value --args "('IT Tender Publication Record', '${publicationId}', 'submission_deadline', '${past}')"`,
			{ stdio: "pipe" }
		);
		await page.goto(`/desk/${PAGE_SLUG}/${encodeURIComponent(publicationRef)}`);
		await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-cl-bw-a1-primary-cta-label")).toHaveText("Closed");
		await expect(page.getByTestId("kt-cl-bw-a1-primary-cta")).toBeDisabled();
		await expect(page.getByTestId("kt-cl-bw-a1-status-chip")).toContainText("Closed");
		await expect(page.getByTestId("kt-cl-bw-a1-documents")).toBeVisible();
		await expect(page.getByTestId("kt-cl-bw-a1-clarifications")).toBeVisible();
	});
});
