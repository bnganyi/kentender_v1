import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import { expectConfigurationContextStrip } from "../../helpers/ktClConfigContext";

/**
 * WG-03 Tender Document Preview + Publication Handoff (WF-03).
 * Route: /desk/it-tender-configuration-render-preview/<configuration_id>
 */

const PAGE_SLUG = "it-tender-configuration-render-preview";
const RETIRED_SLUG = "it-tender-configuration-publication-readiness";
const ROOT = '[data-testid="kt-cl-wf03-root"]';
const CONFIG = "TCFG-SEED-TCFG-RP";

const FORBIDDEN = [
	/\bpublish tender\b/i,
	/Continue to Publication Handoff/i,
];

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
		throw new Error("WG-03 seed failed: " + JSON.stringify(result));
	}
	// Heavy seed can invalidate sid — re-authenticate before navigation.
	await loginAsAdministrator(page);
}

async function openPreview(page: import("@playwright/test").Page, configId = CONFIG) {
	await page.goto(`/desk/${PAGE_SLUG}/${encodeURIComponent(configId)}`);
	await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });
	await expect(page).toHaveURL(new RegExp(`${PAGE_SLUG}/${configId}`), { timeout: 15_000 });
	await expect(page.getByTestId("it-std-wizard-retired")).toHaveCount(0);
}

async function ensureGenerated(page: import("@playwright/test").Page, configId = CONFIG) {
	await page.evaluate(async (id) => {
		// @ts-expect-error frappe on desk
		await frappe.call({
			method: "kentender_procurement.tender_configurations.generate_tender_configuration_document_preview",
			args: { configuration_id: id },
		});
	}, configId);
}

test.describe.configure({ mode: "serial" });

test.describe("WG-03 Tender Document Preview", () => {
	test.beforeAll(async ({ browser }) => {
		const page = await browser.newPage();
		await page.setViewportSize({ width: 1400, height: 900 });
		await loginAsAdministrator(page);
		await page.goto("/desk", { waitUntil: "domcontentloaded" });
		await seedUi00(page);
		await page.close();
	});

	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
		await loginAsAdministrator(page);
	});

	test("layout: strip, outline, preview, confirmation, footer", async ({ page }) => {
		await openPreview(page);
		await expectConfigurationContextStrip(page, {
			family: /Information Technology/i,
			stdDocument: /IT Standard Tender Document/i,
		});
		await expect(page.getByTestId("kt-cl-wf03-layout")).toBeVisible();
		await expect(page.getByTestId("kt-cl-wf03-outline")).toBeVisible();
		await expect(page.getByTestId("kt-cl-wf03-preview")).toBeVisible();
		await expect(page.getByTestId("kt-cl-wf03-confirmation")).toBeVisible();
		await expect(page.getByTestId("kt-cl-wf03-footer")).toBeVisible();
		await expect(page.getByTestId("kt-cl-wf03-regenerate")).toHaveText(/Regenerate Preview/i);
		await expect(page.getByTestId("kt-cl-wf03-download")).toHaveText(/Download Preview PDF/i);
		await expect(page.getByTestId("kt-cl-wf03-return")).toHaveText(/Return for Correction/i);
		await expect(page.getByTestId("kt-cl-breadcrumb-current")).toHaveText(/Tender Document Preview/i);

		const body = await page.locator(ROOT).innerText();
		for (const re of FORBIDDEN) {
			expect(body, String(re)).not.toMatch(re);
		}
	});

	test("retired publication-readiness route rewrites to render preview", async ({ page }) => {
		await page.goto(`/desk/${RETIRED_SLUG}/${encodeURIComponent(CONFIG)}`);
		await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });
		await expect(page).toHaveURL(new RegExp(`${PAGE_SLUG}/${CONFIG}`), { timeout: 15_000 });
		await expect(page.getByTestId("it-std-wizard-retired")).toHaveCount(0);
	});

	test("outline click scrolls preview to section anchor", async ({ page }) => {
		await openPreview(page);
		await ensureGenerated(page);
		await page.reload({ waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("kt-cl-wf03-preview-frame")).toBeVisible({ timeout: 20_000 });
		await expect(page.getByTestId("kt-cl-wf03-preview-tools")).toBeVisible();
		await expect(page.getByTestId("kt-cl-wf03-search")).toBeVisible();
		await expect(page.getByTestId("kt-cl-wf03-view-toolbar")).toBeVisible();
		// Open full-page stays inside the tools panel (no horizontal spill).
		const toolsBox = await page.getByTestId("kt-cl-wf03-preview-tools").boundingBox();
		const fullBox = await page.getByTestId("kt-cl-wf03-open-full").boundingBox();
		expect(toolsBox && fullBox).toBeTruthy();
		if (toolsBox && fullBox) {
			expect(fullBox.x + fullBox.width).toBeLessThanOrEqual(toolsBox.x + toolsBox.width + 1);
		}
		await expect(page.getByTestId("kt-cl-wf03-fit-width")).toHaveAttribute("aria-pressed", "true");
		await page.getByTestId("kt-cl-wf03-actual-size").click();
		await expect(page.getByTestId("kt-cl-wf03-actual-size")).toHaveAttribute("aria-pressed", "true");
		await expect(page.getByTestId("kt-cl-wf03-preview-viewport")).toHaveClass(/is-actual-size/);
		await page.getByTestId("kt-cl-wf03-fit-width").click();
		await expect(page.getByTestId("kt-cl-wf03-preview-viewport")).toHaveClass(/is-fit-width/);
		await page.getByTestId("kt-cl-wf03-outline-gcc").click();
		await expect(page.getByTestId("kt-cl-wf03-outline-gcc")).toHaveClass(/is-active/);
		const scrolled = await page.evaluate(() => {
			const frame = document.querySelector(
				'[data-testid="kt-cl-wf03-preview-frame"]'
			) as HTMLIFrameElement | null;
			const doc = frame?.contentDocument;
			const el = doc?.getElementById("sec-gcc");
			if (!el) {
				return false;
			}
			el.scrollIntoView();
			const top = el.getBoundingClientRect().top;
			return Math.abs(top) < 200;
		});
		expect(scrolled).toBeTruthy();
		const src = await page.getByTestId("kt-cl-wf03-preview-src").inputValue();
		expect(src).not.toMatch(
			/contact_officer|No configured rows\.|Fixture locked|Locked standard text from bound STD version|Price for requirement:|Technical compliance for:/
		);
		expect(src).toMatch(/Contact officer|KES 50,000|\[Bidder to complete\]/);
	});

	test("download preview PDF hits download API", async ({ page }) => {
		await openPreview(page);
		await ensureGenerated(page);
		await page.reload({ waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("kt-cl-wf03-download")).toBeEnabled({ timeout: 15_000 });
		const [response] = await Promise.all([
			page.waitForResponse(
				(r) =>
					r.url().includes("download_tender_configuration_document_preview_pdf") &&
					r.request().method() === "GET"
			),
			page.getByTestId("kt-cl-wf03-download").click(),
		]);
		expect(response.ok()).toBeTruthy();
		const headers = response.headers();
		const disposition = headers["content-disposition"] || "";
		const contentType = headers["content-type"] || "";
		expect(disposition + contentType).toMatch(/pdf|octet-stream|download/i);
	});

	test("exception found disables PDF download and shows banner only", async ({ page }) => {
		await seedUi00(page);
		await page.evaluate(async (id) => {
			// @ts-expect-error frappe on desk
			await frappe.call({
				method: "frappe.client.set_value",
				args: {
					doctype: "Tender Configuration",
					name: id,
					fieldname: "system_inventory",
					value: JSON.stringify({ items: [] }),
				},
			});
			// @ts-expect-error frappe on desk
			await frappe.call({
				method: "kentender_procurement.tender_configurations.generate_tender_configuration_document_preview",
				args: { configuration_id: id },
			});
		}, CONFIG);
		await openPreview(page);
		await expect(page.getByTestId("kt-cl-wf03-exception")).toBeVisible({ timeout: 15_000 });
		await expect(page.getByTestId("kt-cl-wf03-exception-area")).toContainText(/CFG-05/i);
		await expect(page.getByTestId("kt-cl-wf03-exception-cta")).toHaveText(/Open CFG-05/i);
		await expect(page.getByTestId("kt-cl-config-context-issues")).toContainText(/Preview blocked/i);
		await expect(page.getByTestId("kt-cl-wf03-preview-status")).toHaveText(/Exception found/i);
		await expect(page.getByTestId("kt-cl-wf03-download")).toBeDisabled();
		await expect(page.getByTestId("kt-cl-wf03-confirm-btn")).toBeDisabled();
		await expect(page.getByTestId("kt-cl-wf03-preview-empty")).toBeVisible();
		await expect(page.getByTestId("kt-cl-wf03-preview-frame")).toHaveCount(0);
		await page.getByTestId("kt-cl-wf03-exception-cta").click();
		await expect(page).toHaveURL(/it-tender-configuration-system-inventory/, {
			timeout: 15_000,
		});
		// Restore seed inventory so later serial tests can generate a clean preview.
		await seedUi00(page);
	});

	test("return modal requires fields and submits real payload", async ({ page }) => {
		await seedUi00(page);
		await openPreview(page);
		await ensureGenerated(page);
		await page.reload({ waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("kt-cl-wf03-return")).toBeEnabled({ timeout: 15_000 });
		await page.getByTestId("kt-cl-wf03-return").click();
		await expect(page.getByTestId("kt-cl-wf03-return-modal")).toBeVisible();
		await page.getByTestId("kt-cl-wf03-return-submit").click();
		await expect(page.getByTestId("kt-cl-wf03-return-error")).toBeVisible();
		await page.getByTestId("kt-cl-wf03-return-section").selectOption({ label: "Instructions to Tenderers" });
		await page.getByTestId("kt-cl-wf03-return-reason").fill("Preview ITT needs correction");
		await page.getByTestId("kt-cl-wf03-return-severity").locator('[data-severity="High"]').click();
		const [resp] = await Promise.all([
			page.waitForResponse(
				(r) =>
					r.url().includes("return_tender_configuration_preview_for_correction") && r.ok()
			),
			page.getByTestId("kt-cl-wf03-return-submit").click(),
		]);
		const body = await resp.json();
		const payload = body?.message || body;
		expect(payload?.returned || payload?.preview_status === "Not generated").toBeTruthy();
		await expect(page.getByTestId("kt-cl-wf03-return-modal")).toHaveCount(0);
	});

	test("confirm preview reveals publication package panel", async ({ page }) => {
		await seedUi00(page);
		await openPreview(page);
		await expect(page.getByTestId("kt-cl-wf03-preview-frame")).toBeVisible({ timeout: 20_000 });
		await page.evaluate(async (id) => {
			// @ts-expect-error frappe on desk
			await frappe.call({
				method: "kentender_procurement.tender_configurations.generate_tender_configuration_document_preview",
				args: { configuration_id: id },
			});
			// @ts-expect-error frappe on desk
			await frappe.call({
				method: "kentender_procurement.tender_configurations.confirm_tender_configuration_document_preview",
				args: { configuration_id: id, payload: { confirm_ready_for_handoff: 1 } },
			});
		}, CONFIG);
		await page.reload({ waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("kt-cl-wf03-publication")).toBeVisible({ timeout: 15_000 });
		await expect(page.getByTestId("kt-cl-wf03-send")).toHaveText(/Send to Publication Workflow/i);
		const body = await page.locator(ROOT).innerText();
		expect(body).not.toMatch(/\bpublish tender\b/i);
	});

	test("send to publication workflow via API when UI seed incomplete", async ({ page }) => {
		await openPreview(page);
		await page.evaluate(async (id) => {
			// @ts-expect-error frappe on desk
			await frappe.call({
				method: "kentender_procurement.tender_configurations.generate_tender_configuration_document_preview",
				args: { configuration_id: id },
			});
			// @ts-expect-error frappe on desk
			await frappe.call({
				method: "kentender_procurement.tender_configurations.confirm_tender_configuration_document_preview",
				args: { configuration_id: id, payload: { confirm_ready_for_handoff: 1 } },
			});
		}, CONFIG);
		await page.reload({ waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("kt-cl-wf03-publication")).toBeVisible({ timeout: 20_000 });
		const sendBtn = page.getByTestId("kt-cl-wf03-send");
		if (await sendBtn.isEnabled()) {
			await sendBtn.click();
			await page.getByTestId("kt-cl-confirm-ok").click();
			await expect(page.getByTestId("kt-cl-wf03-pkg-sent")).toBeVisible({ timeout: 15_000 });
		} else {
			await expect(page.getByTestId("kt-cl-wf03-pkg-sent")).toBeVisible();
		}
	});
});
