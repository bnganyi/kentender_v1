import { expect, test } from "@playwright/test";

import { collectPortalConsoleErrors, expectNoFrappeDialog, expectNoHorizontalOverflow, loginToPortal, waitForPortal } from "../../helpers/portal";
import { bdsFixture, restoreBdsWorld } from "./bdsWorld";

/**
 * BDS-CHG-001 v0.8 §10.10–10.11 (plan Phase 11, slices 11.9–11.10) —
 * Requirements and supporting evidence, then Price, as David of Afya (Test)
 * on a new bid on the Tenders test Tender: answer one requirement with its
 * file in the response drawer (a refused file first shows Evidence rejected), enter the offered goods, then the price, and
 * see the server's bid total. Another organisation sees nothing.
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

test.describe("BDS-DES-09 Requirements / BDS-DES-10 Price", () => {
	test.afterAll(() => restoreBdsWorld());

	test("David answers a requirement with its file, the offered goods, then the price", async ({ page }) => {
		const world = bdsFixture<World>("reset_my_bids_fixture", { state: "started" });
		const errors = collectPortalConsoleErrors(page);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.representative, world.password, `/tenders/${world.tender_reference}/bid/requirements`);
		const table = page.getByTestId("bds-technical-table");
		await expect(table.locator("tr", { hasText: "Memory" })).toContainText("Minimum 16 GB");
		await expect(page.getByTestId("bds-requirements-nav").getByRole("link")).toHaveCount(6);

		// one requirement in the drawer, with its file
		const battery = table.locator("tr", { hasText: "Battery runtime" });
		await battery.getByRole("button", { name: "Battery runtime" }).click();
		const drawer = page.getByTestId("bds-response-drawer");
		await expect(drawer.getByRole("dialog")).toHaveAccessibleName("Battery runtime");
		await drawer.locator("select").first().selectOption({ index: 1 });
		await drawer.locator("input.kt-input[inputmode=decimal]").first().fill("10");
		// a refused file is the Evidence rejected state; Choose another file reopens the picker
		await drawer.locator("input[type=file]").setInputFiles({ name: "empty-datasheet.pdf", mimeType: "application/pdf", buffer: Buffer.alloc(0) });
		const rejected = drawer.getByTestId("bds-state-evidence-rejected");
		await expect(rejected.locator("strong")).toHaveText("This file could not be accepted.");
		await expect(rejected).toContainText("File is empty or unreadable.");
		const chooser = page.waitForEvent("filechooser");
		await rejected.getByRole("button", { name: "Choose another file" }).click();
		await (await chooser).setFiles({ name: "apexbook-datasheet.pdf", mimeType: "application/pdf", buffer: onePagePdf() });
		await expect(drawer.locator(".bds-file-row", { hasText: "apexbook-datasheet.pdf" })).toBeVisible();
		await expect(rejected).toHaveCount(0);
		await drawer.getByTestId("bds-drawer-save").click();
		await expect(drawer).toHaveCount(0);
		await expect(battery).toContainText("10");
		await expect(battery).toContainText("apexbook-datasheet.pdf");

		// the offered goods, then Save and continue
		const goods = page.locator("#bds-region-goods");
		await goods.locator("input.kt-input:not([type=date])").first().fill("ApexBook Pro 14");
		await goods.locator("input[type=date]").fill("2027-09-15");
		await page.getByTestId("bds-requirements-save").click();
		await expect(page).toHaveURL(new RegExp(`/tenders/${world.tender_reference}/bid/price$`));

		// the price: each entry saves and the server's totals come back
		await expect(page.getByTestId("bds-bid-total")).toHaveText("—");
		await expect(page.getByTestId("bds-price-missing")).toBeVisible();
		await page.getByTestId("bds-unit-price-1").fill("160000");
		await page.getByTestId("bds-unit-price-1").blur();
		await page.getByTestId("bds-tax-1").fill("6400000");
		await page.getByTestId("bds-tax-1").blur();
		await expect(page.getByTestId("bds-bid-total")).toHaveText("KES 46,400,000.00");
		await expect(page.getByTestId("bds-price-line-1")).toContainText("KES 40,000,000.00");
		await page.reload({ waitUntil: "domcontentloaded" });
		await waitForPortal(page);
		await expect(page.getByTestId("bds-bid-total")).toHaveText("KES 46,400,000.00");
		await page.goBack({ waitUntil: "domcontentloaded" });
		await waitForPortal(page);
		await expect(page.getByTestId("bds-requirements-task").locator("#bds-region-goods input.kt-input").first()).toHaveValue("ApexBook Pro 14");
		await page.setViewportSize({ width: 390, height: 844 });
		await expect(page.getByTestId("bds-technical-cards")).toBeVisible();
		await expectNoHorizontalOverflow(page);
		await expectNoFrappeDialog(page);
		expect(errors.filter((e) => !/404 \(Not Found\)/.test(e)), errors.join(" | ")).toEqual([]);
	});

	test("another organisation's person is told the bid is not found", async ({ page }) => {
		const world = bdsFixture<World>("reset_my_bids_fixture", { state: "started" });
		await page.setViewportSize({ width: 1440, height: 1024 });
		for (const task of ["requirements", "price"]) {
			await loginToPortal(page, world.other_user, world.password, `/tenders/${world.tender_reference}/bid/${task}`);
			await expect(page.getByTestId("bds-state-bid-not-found")).toBeVisible();
			await expect(page.locator("body")).not.toContainText(world.bid_reference);
		}
	});
});
