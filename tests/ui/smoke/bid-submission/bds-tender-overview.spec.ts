import { expect, test } from "@playwright/test";

import { collectPortalConsoleErrors, expectNoFrappeDialog, expectNoHorizontalOverflow, loginToPortal, waitForPortal } from "../../helpers/portal";
import { bdsFixture, restoreBdsWorld } from "./bdsWorld";

/**
 * BDS-CHG-001 v0.8 §10.3 / §11.2 (plan Phase 11, slice 11.2) — BDS-DES-02
 * Published Tender overview, as a signed-out visitor, a supplier with a
 * Draft (and its question), and another supplier who starts a bid. Nobody
 * sees another organisation's bid. The world closes the production gate
 * through the test controls (the GATE world), so the page says electronic
 * submission is not available yet.
 */
type World = { tender_reference: string; bid_reference: string; password: string; afya_user: string; kisiwa_user: string };

test.describe.configure({ mode: "serial", timeout: 240_000 });

test.describe("BDS-DES-02 Published Tender overview", () => {
	let world: World;
	test.beforeAll(() => {
		world = bdsFixture<World>("reset_overview_fixture", { gate_closed: true });
	});
	test.afterAll(() => restoreBdsWorld());

	test("a signed-out visitor reads the Tender and is asked to sign in to start", async ({ page }) => {
		const errors = collectPortalConsoleErrors(page);
		await page.setViewportSize({ width: 1440, height: 1024 });
		const response = await page.goto(`/tenders/${world.tender_reference}`, { waitUntil: "domcontentloaded" });
		expect(response?.status()).toBe(200);
		await waitForPortal(page);
		const screen = page.getByTestId("bds-tender-overview");
		await expect(screen.locator("h1.kt-page-title")).toBeVisible();
		await expect(page.getByTestId("bds-overview-action")).toHaveText("Sign in to start bid");
		await expect(page.getByTestId("bds-overview-action")).toHaveAttribute("href", `/login?redirect-to=/tenders/${world.tender_reference}`);
		await expect(screen.locator(".kt-region h2")).toHaveText(["Key dates", "What is being procured", "Tender documents", "Addenda and clarification answers", "Before you start"]);
		await expect(page.getByTestId("bds-overview-notice")).toContainText("Electronic bid submission is not available yet");
		const view = page.getByTestId("bds-documents-table").getByRole("link", { name: "View" }).first();
		const document = await page.request.get((await view.getAttribute("href")) || "");
		expect(document.status()).toBe(200);
		expect(document.headers()["content-disposition"]).toContain("inline");
		await page.setViewportSize({ width: 390, height: 844 });
		await expect(page.getByTestId("bds-documents-cards")).toBeVisible();
		await expectNoHorizontalOverflow(page);
		await expectNoFrappeDialog(page);
		expect(errors, errors.join(" | ")).toEqual([]);
	});

	test("a supplier with a Draft continues it and asks a question; the answer names nothing of the bid", async ({ page }) => {
		const errors = collectPortalConsoleErrors(page);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.afya_user, world.password, `/tenders/${world.tender_reference}`);
		await expect(page.getByTestId("bds-overview-status")).toContainText(/^Draft · \d of 5 tasks complete$/);
		await expect(page.getByTestId("bds-overview-action")).toHaveText("Continue bid");
		await expect(page.getByTestId("bds-overview-action")).toHaveAttribute("href", `/tenders/${world.tender_reference}/bid`);
		await page.getByTestId("bds-ask-question").click();
		const dialog = page.getByTestId("bds-question-dialog");
		await expect(dialog.getByRole("dialog")).toHaveAccessibleName("Ask a question about this Tender");
		await dialog.getByTestId("bds-question-text").fill("Short");
		await dialog.getByTestId("bds-question-send").click();
		await expect(dialog.locator(".kt-field-error")).toHaveText("Enter a question of 10 to 2,000 characters.");
		await dialog.getByTestId("bds-question-text").fill("May the offered laptops ship in two lots before the latest delivery date?");
		await dialog.getByTestId("bds-question-send").click();
		await expect(dialog.getByTestId("bds-question-sent")).toContainText(/^Question received \d{1,2} \w{3} \d{4}, \d{2}:\d{2} EAT$/);
		await dialog.getByTestId("bds-question-close").click();
		await expectNoFrappeDialog(page);
		expect(errors, errors.join(" | ")).toEqual([]);
	});

	test("another supplier starts a bid with the verified notice email and sees only its own Draft", async ({ page }) => {
		const errors = collectPortalConsoleErrors(page);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.kisiwa_user, world.password, `/tenders/${world.tender_reference}`);
		await expect(page.getByTestId("bds-overview-status")).toHaveCount(0);
		await expect(page.locator("body")).not.toContainText(world.bid_reference);
		await expect(page.locator("body")).not.toContainText("Afya");
		await page.getByTestId("bds-overview-action").click();
		const dialog = page.getByTestId("bds-start-dialog");
		await expect(dialog.getByRole("dialog")).toHaveAccessibleName("Who is bidding?");
		await expect(dialog.getByTestId("bds-start-single")).toBeChecked();
		await expect(dialog.getByTestId("bds-notice-contact")).toHaveValue(/.+/);
		await expect(dialog.locator("#bds-notice-help")).toHaveText("Mandatory Tender notices will be sent here. You can change this later to another verified Account email.");
		await dialog.getByTestId("bds-start-submit").click();
		await expect(page.getByTestId("bds-start-dialog")).toHaveCount(0);
		await expect(page.getByTestId("bds-overview-action")).toHaveText("Continue bid");
		await expect(page.getByTestId("bds-overview-status")).toContainText("Draft");
		await page.setViewportSize({ width: 390, height: 844 });
		await expectNoHorizontalOverflow(page);
		expect(errors, errors.join(" | ")).toEqual([]);
	});

	test("while supplier support information is missing the Tender stays readable and each viewer is told what still works", async ({ page }) => {
		const errors = collectPortalConsoleErrors(page);
		try {
			expect(bdsFixture<{ status: string }>("set_portal_information", { complete: false }).status).toBe("Incomplete");
			await page.setViewportSize({ width: 1440, height: 1024 });
			await page.goto(`/tenders/${world.tender_reference}`, { waitUntil: "domcontentloaded" });
			await waitForPortal(page);
			const visitor = page.getByTestId("bds-state-portal-information-new-visitor");
			await expect(visitor.locator("strong")).toHaveText("Supplier support information is temporarily unavailable.");
			await expect(visitor).toContainText("You can read this Tender. Starting a new bid is unavailable until support and legal information is restored.");
			await expect(visitor.getByRole("button", { name: "Try again" })).toBeVisible();
			await expect(page.getByTestId("bds-tender-overview").locator(".kt-region h2").first()).toHaveText("Key dates");

			await loginToPortal(page, world.afya_user, world.password, `/tenders/${world.tender_reference}`);
			const draft = page.getByTestId("bds-state-portal-information-draft");
			await expect(draft).toContainText("Your saved bid is still here.");
			await expect(draft.getByRole("link", { name: "Continue saved bid" })).toHaveAttribute("href", `/tenders/${world.tender_reference}/bid`);
			await expect(page.getByTestId("bds-overview-action")).toHaveText("Continue bid");
			await page.setViewportSize({ width: 390, height: 844 });
			await expectNoHorizontalOverflow(page);
			await expectNoFrappeDialog(page);
			expect(errors, errors.join(" | ")).toEqual([]);
		} finally {
			bdsFixture("set_portal_information", { complete: true });
		}
	});
});
