import { expect, test } from "@playwright/test";

import { collectPortalConsoleErrors, expectNoFrappeDialog, expectNoHorizontalOverflow, loginToPortal, waitForPortal } from "../../helpers/portal";
import { bdsFixture, restoreBdsWorld } from "./bdsWorld";

/**
 * BDS-CHG-001 v0.8 §10.9 (plan Phase 11, slice 11.8) — Company, declarations
 * and tender security, as David of Afya (Test) on a new bid on the Tenders
 * test Tender: confirm a declaration in the response drawer, enter the tender
 * security with its proof, keep the contact bid-specific, and see the
 * physical original as not yet recorded. Another organisation sees nothing.
 */
type World = { tender_reference: string; bid_reference: string; password: string; representative: string; other_user: string };

function onePagePdf(): Buffer {
	const objects = ["<< /Type /Catalog /Pages 2 0 R >>", "<< /Type /Pages /Kids [3 0 R] /Count 1 >>", "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] >>"];
	let out = "%PDF-1.4\n";
	const offsets: number[] = [];
	objects.forEach((body, i) => {
		offsets.push(Buffer.byteLength(out));
		out += `${i + 1} 0 obj\n${body}\nendobj\n`;
	});
	const xref = Buffer.byteLength(out);
	out += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n${offsets.map((o) => `${String(o).padStart(10, "0")} 00000 n \n`).join("")}`;
	out += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`;
	return Buffer.from(out);
}

test.describe.configure({ mode: "serial", timeout: 300_000 });

test.describe("BDS-DES-08 Company, declarations and tender security", () => {
	test.afterAll(() => restoreBdsWorld());

	test("David confirms a declaration, enters the tender security with its proof and continues", async ({ page }) => {
		const world = bdsFixture<World>("reset_my_bids_fixture", { state: "started" });
		const errors = collectPortalConsoleErrors(page);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.representative, world.password, `/tenders/${world.tender_reference}/bid`);
		await page.getByTestId("bds-task-company").getByRole("link").click();
		await expect(page).toHaveURL(new RegExp(`/tenders/${world.tender_reference}/bid/company$`));
		const table = page.getByTestId("bds-declarations-table");
		await expect(table).toContainText("Form of Tender");
		await expect(table).toContainText("Youth reservation declaration");
		await expect(page.getByTestId("bds-company-facts")).toContainText("Afya Digital Supplies (Test) Limited");

		// a declaration in the response drawer
		const row = table.locator("tr", { hasText: "Self-declaration — not debarred" });
		await row.getByRole("button", { name: "View declaration" }).click();
		const drawer = page.getByTestId("bds-response-drawer");
		await expect(drawer.getByRole("dialog")).toHaveAccessibleName("Self-declaration — not debarred");
		await expect(drawer.getByTestId("bds-drawer-statement")).toBeVisible();
		await drawer.locator(".kt-checkbox").first().click();
		await drawer.getByTestId("bds-drawer-save").click();
		await expect(drawer).toHaveCount(0);
		await expect(row).toContainText("Confirmed");
		await expect(row).toContainText("Confirmed by David Ouma");

		// a refused contact phone is named in place
		await page.getByTestId("bds-contact-phone").fill("call me");
		await page.getByTestId("bds-company-save").click();
		await expect(page.locator(".kt-field-error", { hasText: "telephone" })).toBeVisible();
		await expect(page.getByTestId("bds-contact-phone")).toHaveValue("call me");
		await expectNoFrappeDialog(page);
		await page.getByTestId("bds-contact-phone").fill("+254 709 555 015");

		// tender security and its proof
		await expect(page.getByTestId("bds-security-empty")).toBeVisible();
		const region = page.locator(".kt-region", { has: page.getByRole("heading", { name: "Tender security" }) });
		await region.locator("select").first().selectOption("Demand Bank Guarantee");
		const inputs = region.locator("input.kt-input:not([type=date])");
		await inputs.nth(0).fill("KCB Bank Kenya");
		await inputs.nth(1).fill("KCB/TG/2099/7788");
		await inputs.nth(2).fill("500000");
		await region.locator("input[type=date]").first().fill("2027-11-15");
		await region.locator("input[type=file]").setInputFiles({ name: "tender-security.pdf", mimeType: "application/pdf", buffer: onePagePdf() });
		await expect(region.locator(".bds-file-row", { hasText: "tender-security.pdf" })).toBeVisible();
		await page.getByTestId("bds-company-save").click();
		await expect(page).toHaveURL(new RegExp(`/tenders/${world.tender_reference}/bid/requirements$`));

		await page.goto(`/tenders/${world.tender_reference}/bid/company`, { waitUntil: "domcontentloaded" });
		await waitForPortal(page);
		await expect(page.getByTestId("bds-security-empty")).toHaveCount(0);
		await expect(page.getByTestId("bds-security-physical")).toContainText("Physical original not yet recorded");
		await page.setViewportSize({ width: 390, height: 844 });
		await expect(page.getByTestId("bds-declarations-cards")).toBeVisible();
		await expectNoHorizontalOverflow(page);
		expect(errors.filter((e) => !/404 \(Not Found\)/.test(e)), errors.join(" | ")).toEqual([]);
	});

	test("the questionnaire asks each question in the official words and shows details only when they apply", async ({ page }) => {
		const world = bdsFixture<World>("reset_my_bids_fixture", { state: "started" });
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.representative, world.password, `/tenders/${world.tender_reference}/bid/company`);
		const row = page.getByTestId("bds-declarations-table").locator("tr", { hasText: /Confidential business questionnaire/i });
		await row.getByRole("button", { name: "View declaration" }).click();
		const drawer = page.getByTestId("bds-response-drawer");
		const question = (words: string) => drawer.locator("fieldset", { has: page.locator("legend", { hasText: words }) });

		// every conflict is its own question in the official words, never "Conflict of interest item N"
		await expect(drawer).not.toContainText(/Conflict of interest item \d/);
		await expect(question("3. Tenderer has the same legal representative as another tenderer")).toBeVisible();
		await expect(drawer).not.toContainText("Disclosure of Interest item");
		await expect(question("receives or has received any direct or indirect subsidy")).toBeVisible();

		// details are asked only for a Yes, and only for that question
		const subsidy = question("receives or has received any direct or indirect subsidy");
		await expect(drawer.getByText("If YES, provide details of the relationship with Tenderer")).toHaveCount(0);
		await subsidy.getByRole("radio", { name: "Yes" }).check();
		await expect(drawer.getByText("If YES, provide details of the relationship with Tenderer")).toHaveCount(1);
		await subsidy.getByRole("radio", { name: "No" }).check();
		await expect(drawer.getByText("If YES, provide details of the relationship with Tenderer")).toHaveCount(0);

		// item 9 (has the conflict been resolved?) appears only after item 7 or 8 is Yes
		const resolved = "Has the conflict stemming from such relationship";
		const seven = question("directly or indirectly involved in the preparation of the Tender document");
		await expect(question(resolved)).toHaveCount(0);
		await seven.getByRole("radio", { name: "Yes" }).check();
		await expect(question(resolved)).toBeVisible();
		await seven.getByRole("radio", { name: "No" }).check();
		await expect(question(resolved)).toHaveCount(0);

		// the standing business facts are not asked here: they are the business profile copied from the Account
		await expect(drawer.getByText("Sole proprietor: name in full")).toHaveCount(0);
		await expect(drawer.getByText("Nominal capital (Kenya Shillings)")).toHaveCount(0);
		await expect(drawer.getByText("Trade licence expiry date")).toHaveCount(0);
		await page.screenshot({ path: "test-results/bds-questionnaire-drawer.png", fullPage: false });
	});

	test("the business profile is copied from the Account, read-only, and complete at once", async ({ page }) => {
		const world = bdsFixture<World>("reset_my_bids_fixture", { state: "started" });
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.representative, world.password, `/tenders/${world.tender_reference}/bid/company`);
		const row = page.getByTestId("bds-declarations-table").locator("tr", { hasText: /Business profile/i });
		await expect(row.locator(".kt-status")).toHaveText("Complete");
		await row.getByRole("button", { name: "View business profile" }).click();
		const drawer = page.getByTestId("bds-response-drawer");
		await expect(drawer.locator("select").first()).toHaveValue("Registered company");
		await expect(drawer.locator("select").first()).toBeDisabled();
		await expect(drawer.getByText("Nominal capital (Kenya Shillings)")).toBeVisible();
		await expect(drawer.locator('[data-testid^="bds-rowgroup-table-"]').first()).toContainText("Kenyan");
		await expect(drawer.locator("input:not([disabled])")).toHaveCount(0); // nothing here is the bidder's to type
		await expect(drawer.getByTestId("bds-drawer-save")).toHaveCount(0);
		await page.screenshot({ path: "test-results/bds-business-profile-drawer.png", fullPage: false });
	});

	test("the Form of Tender asks for commission recipients only on a Yes, names a refused cell in place and keeps the saved rows", async ({ page }) => {
		const world = bdsFixture<World>("reset_my_bids_fixture", { state: "started" });
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.representative, world.password, `/tenders/${world.tender_reference}/bid/company`);
		const row = page.getByTestId("bds-declarations-table").locator("tr", { hasText: /^Form of Tender/ });
		await row.getByRole("button", { name: "View declaration" }).click();
		const drawer = page.getByTestId("bds-response-drawer");
		const paid = drawer.locator("fieldset", { has: page.locator("legend", { hasText: "commissions, gratuities or fees" }) });
		const table = drawer.locator("fieldset", { has: page.locator("legend", { hasText: "Each recipient of a commission, gratuity or fee" }) });

		// no recipients are asked for until the question is answered Yes
		await expect(table).toHaveCount(0);
		await paid.getByRole("radio", { name: "Yes" }).check();
		await expect(table).toBeVisible();
		await table.getByLabel("Name of recipient").fill("Acme Facilitation Agents");
		await table.getByLabel("Full address").fill("12 Moi Avenue, Nairobi");
		await table.getByLabel("Reason for the commission, gratuity or fee").fill("Introduction to the Procuring Entity");
		await table.getByLabel("Amount").fill("ten");
		await drawer.getByTestId("bds-drawer-save").click();
		// the refused cell is named at its own cell, the entry is kept and nothing was saved
		await expect(table.getByLabel("Amount").locator("xpath=..").locator(".kt-field-error")).toHaveText("Enter a number.");
		await expect(table.getByLabel("Name of recipient")).toHaveValue("Acme Facilitation Agents");
		// amount and currency are two cells
		await table.getByLabel("Amount").fill("15000");
		await table.getByLabel("Currency").selectOption("KES");
		await drawer.getByTestId("bds-drawer-save").click();
		await expect(drawer).toHaveCount(0);
		await expect(row.locator(".kt-status")).toHaveText("In progress"); // the page has re-read what was saved

		// what was saved is there when the form is opened again; a No takes the table away
		await row.getByRole("button", { name: "View declaration" }).click();
		await expect(table.getByLabel("Name of recipient")).toHaveValue("Acme Facilitation Agents");
		await expect(table.getByLabel("Amount")).toHaveValue("15000.00");
		await expect(table.getByLabel("Currency")).toHaveValue("KES");
		await paid.getByRole("radio", { name: "No" }).check();
		await expect(table).toHaveCount(0);
		await page.screenshot({ path: "test-results/bds-form-of-tender-commissions.png", fullPage: false });
	});

	test("the persons with an interest are a table, asked only on a Yes, and ten rows are the most", async ({ page }) => {
		const world = bdsFixture<World>("reset_my_bids_fixture", { state: "started" });
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.representative, world.password, `/tenders/${world.tender_reference}/bid/company`);
		const row = page.getByTestId("bds-declarations-table").locator("tr", { hasText: /Confidential business questionnaire/i });
		await row.getByRole("button", { name: "View declaration" }).click();
		const drawer = page.getByTestId("bds-response-drawer");
		const question = drawer.locator("fieldset", { has: page.locator("legend", { hasText: "Does any person in the Procuring Entity have an interest" }) });
		const table = drawer.locator("fieldset", { has: page.locator("legend", { hasText: "Persons in the Procuring Entity who have an interest" }) });
		await expect(table).toHaveCount(0);
		await question.getByRole("radio", { name: "Yes" }).check();
		await expect(table).toBeVisible();
		for (let i = 0; i < 9; i += 1) await table.getByRole("button", { name: "Add row" }).click();
		await expect(table.getByTestId(/^bds-rowgroup-row-/)).toHaveCount(10);
		await expect(table.getByRole("button", { name: "Table is full" })).toBeDisabled();
		await question.getByRole("radio", { name: "No" }).check();
		await expect(table).toHaveCount(0);
	});

	test("another organisation's person is told the bid is not found", async ({ page }) => {
		const world = bdsFixture<World>("reset_my_bids_fixture", { state: "started" });
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.other_user, world.password, `/tenders/${world.tender_reference}/bid/company`);
		await expect(page.getByTestId("bds-state-bid-not-found")).toBeVisible();
		await expect(page.locator("body")).not.toContainText(world.bid_reference);
	});
});
