import { execSync } from "node:child_process";
import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

/**
 * PUB-A3 Publication Setup.
 * Route: /desk/publication-setup/<publication_id>
 */

const PAGE_SLUG = "publication-setup";
const ROOT = '[data-testid="kt-cl-pub-a3-root"]';
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
		throw new Error("PUB-A3 seed failed: " + JSON.stringify(result));
	}
	await loginAsAdministrator(page);
}

function seedBidderFacingForPublish(configId: string) {
	// Mirrors domain test prep so confirm snapshots schemas onto the package.
	execSync(
		`cd ${BENCH} && bench --site ${SITE} execute kentender_procurement.tender_configurations.seed.preview_fixtures._seed_bidder_facing_config --args "('${configId}',)"`,
		{ stdio: "pipe" }
	);
}

async function confirmAndGetPublicationId(
	page: import("@playwright/test").Page,
	configId = CONFIG
): Promise<string> {
	const pubId = await page.evaluate(async (id) => {
		// @ts-expect-error frappe on desk
		await frappe.call({
			method: "kentender_procurement.tender_configurations.generate_tender_configuration_document_preview",
			args: { configuration_id: id },
		});
		// @ts-expect-error frappe on desk
		const r = await frappe.call({
			method: "kentender_procurement.tender_configurations.confirm_tender_package",
			args: { configuration_id: id, payload: { confirm_ready_for_handoff: 1 } },
		});
		const msg = r.message || r;
		return (msg && msg.publication_id) || "";
	}, configId);
	if (!pubId) {
		throw new Error("confirm_tender_package did not return publication_id");
	}
	return pubId;
}

function localDatetimeOffset(days: number, hours = 0): string {
	const d = new Date();
	d.setDate(d.getDate() + days);
	d.setHours(d.getHours() + hours);
	const pad = (n: number) => String(n).padStart(2, "0");
	return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

test.describe.configure({ mode: "serial" });

test.describe("PUB-A3 Publication Setup", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
		await loginAsAdministrator(page);
		await page.goto("/desk", { waitUntil: "domcontentloaded" });
		await seedUi00(page);
	});

	test("open setup, fill fields, save — form stays visible / Ready", async ({ page }) => {
		const pubId = await confirmAndGetPublicationId(page);
		await page.goto(`/desk/${PAGE_SLUG}/${encodeURIComponent(pubId)}`);
		await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });

		await expect(page.getByTestId("kt-cl-pub-a3-context-strip")).toBeVisible();
		await expect(page.getByTestId("kt-cl-pub-a3-strip-pub-ref")).toBeVisible();
		const pubRef = (await page.getByTestId("kt-cl-pub-a3-strip-pub-ref").innerText()).trim();
		expect(pubRef).toMatch(/PUB-\d{4}-\d+/i);
		const pkgRef = (await page.getByTestId("kt-cl-pub-a3-strip-pkg-ref").innerText()).trim();
		expect(pkgRef.length).toBeGreaterThan("Doc Package Ref".length);
		expect(pkgRef).not.toMatch(/^[a-z0-9]{8,12}$/i);
		await expect(page.getByTestId("kt-cl-pub-a3-status")).toBeVisible();
		await expect(page.getByTestId("kt-cl-pub-a3-layout")).toBeVisible();
		await expect(page.getByTestId("kt-cl-pub-a3-mode")).toBeVisible();
		await expect(page.getByTestId("kt-cl-pub-a3-view-package")).toBeVisible();
		await expect(page.getByTestId("kt-cl-pub-a3-validation")).toBeVisible();
		await expect(page.getByTestId("kt-cl-pub-a3-form")).toBeVisible();
		await expect(page.getByTestId("kt-cl-pub-a3-save")).toBeVisible();
		await expect(page.getByTestId("kt-cl-pub-a3-publish")).toBeVisible();
		await expect(page.getByTestId("kt-cl-pub-a3-return")).toBeVisible();

		// Schedule mode exposes publication datetime input (immediate uses readonly).
		await page.locator('input[name="publication_mode"][value="scheduled"]').check();
		await page.getByTestId("kt-cl-pub-a3-field-publication_datetime").fill(localDatetimeOffset(1));
		await page
			.getByTestId("kt-cl-pub-a3-field-tender_notice")
			.fill("Public notice for Playwright publication setup.");
		await page.getByTestId("kt-cl-pub-a3-field-clarification_deadline").fill(localDatetimeOffset(5));
		await page.getByTestId("kt-cl-pub-a3-field-submission_deadline").fill(localDatetimeOffset(14));
		await page.getByTestId("kt-cl-pub-a3-field-opening_datetime").fill(localDatetimeOffset(14, 1));
		await page.getByTestId("kt-cl-pub-a3-field-bidder_visibility").selectOption("All Registered Bidders");
		// Custom switch UI intercepts the native checkbox — force or click the label.
		await page.getByTestId("kt-cl-pub-a3-field-activate_bidder_workspace").check({ force: true });

		await Promise.all([
			page.waitForResponse((r) => r.url().includes("save_publication_setup") && r.ok()),
			page.getByTestId("kt-cl-pub-a3-save").click(),
		]);

		await expect(page.getByTestId("kt-cl-pub-a3-form")).toBeVisible();
		const statusText = await page.getByTestId("kt-cl-pub-a3-status").innerText();
		expect(statusText).toMatch(/Ready to Publish|Scheduled|Awaiting Publication Setup/i);
	});

	test("immediate mode stays selected after publish (not flipped to schedule)", async ({ page }) => {
		seedBidderFacingForPublish(CONFIG);
		const pubId = await confirmAndGetPublicationId(page);

		await page.goto(`/desk/${PAGE_SLUG}/${encodeURIComponent(pubId)}`);
		await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });

		await page.locator('input[name="publication_mode"][value="immediate"]').check({ force: true });
		await page
			.getByTestId("kt-cl-pub-a3-field-tender_notice")
			.fill("Immediate publish mode regression notice.");
		await page.getByTestId("kt-cl-pub-a3-field-clarification_deadline").fill(localDatetimeOffset(5));
		await page.getByTestId("kt-cl-pub-a3-field-submission_deadline").fill(localDatetimeOffset(14));
		await page.getByTestId("kt-cl-pub-a3-field-opening_datetime").fill(localDatetimeOffset(14, 1));
		await page.getByTestId("kt-cl-pub-a3-field-bidder_visibility").selectOption("All Registered Bidders");
		await page.getByTestId("kt-cl-pub-a3-field-activate_bidder_workspace").check({ force: true });

		await Promise.all([
			page.waitForResponse((r) => r.url().includes("save_publication_setup") && r.ok()),
			page.getByTestId("kt-cl-pub-a3-save").click(),
		]);
		await expect(page.locator('input[name="publication_mode"][value="immediate"]')).toBeChecked();

		const published = await page.evaluate(async (id) => {
			// @ts-expect-error frappe on desk
			const r = await frappe.call({
				method: "kentender_procurement.tender_configurations.publish_tender",
				args: { publication_id: id },
			});
			return r.message || r;
		}, pubId);
		expect((published as { status?: string }).status).toBe("Published");
		expect((published as { fields?: { publication_mode?: string } }).fields?.publication_mode).toBe(
			"immediate"
		);

		await page.goto(`/desk/${PAGE_SLUG}/${encodeURIComponent(pubId)}`);
		await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-cl-pub-a3-status")).toContainText(/Published/i);
		await expect(page.locator('input[name="publication_mode"][value="immediate"]')).toBeChecked();
		await expect(page.locator('input[name="publication_mode"][value="scheduled"]')).not.toBeChecked();
		// Effective stamp must remain visible after immediate publish (not the draft placeholder).
		const dtReadonly = (
			await page.getByTestId("kt-cl-pub-a3-field-publication_datetime_readonly").innerText()
		).trim();
		expect(dtReadonly).not.toMatch(/On publish action/i);
		expect(dtReadonly).toMatch(/\d{4}/);
		const pubRef = (await page.getByTestId("kt-cl-pub-a3-strip-pub-ref").innerText()).trim();
		expect(pubRef).toMatch(/PUB-\d{4}-\d+/i);
	});
});
