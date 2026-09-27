import { expect, test } from "@playwright/test";

import { collectPortalConsoleErrors, expectNoFrappeDialog, expectNoHorizontalOverflow, loginToPortal, waitForPortal } from "../../helpers/portal";
import { accountFixture, clearTestMessages, latestTestMessage, restoreAccountWorld } from "./bdsWorld";

/**
 * BDS-CHG-001 v0.8 §10.4–10.5 (plan Phase 11, slices 11.3–11.4) — the supplier
 * Account: Mary sets it up and verifies the official email from the link the
 * Test Mailbox kept; an incomplete Account is fixed from its next step; a
 * pending one resends its link; a suspended one offers nothing but receipts
 * and support; another organisation's person is told the Account is not found.
 * Refusals are named in place — never a Message dialog.
 */
type World = { state: string; organisation: string; password: string; signatory: string; representative: string; other_person: string; official_email: string; legal_name: string; facts: Record<string, string> };

/** A small well-formed one-page PDF (with its cross-reference table), built per run. */
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
const PDF = onePagePdf();
const TRUNCATED_PDF = Buffer.from("%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\n%%EOF\n");

test.describe.configure({ mode: "serial", timeout: 240_000 });

test.describe("BDS-DES-03 / BDS-DES-04 supplier Account", () => {
	test.afterAll(() => {
		restoreAccountWorld();
		clearTestMessages("tenders@afya-acc-pw.example");
	});

	test("Mary sets up the account, opens the verification link and lands on an Active Account", async ({ page }) => {
		const world = accountFixture<World>("reset_account_fixture", { state: "new" });
		clearTestMessages(world.official_email);
		const errors = collectPortalConsoleErrors(page);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.signatory, world.password, "/account");
		const form = page.getByTestId("acc-register");
		await expect(form.locator("h1")).toHaveText("Set up your supplier account");
		await expect(page.locator('[data-kt="next-step"]')).toContainText("Enter the supplier organisation details.");
		await expect(form.locator(".kt-region h2")).toHaveText(["Organisation details", "Official contact", "Your responsibility"]);
		await page.getByTestId("acc-create").click();
		await expect(form.locator(".kt-field-error").first()).toBeVisible();
		await expect(page.getByTestId("acc-authority").locator("xpath=..").locator(".kt-field-error")).toHaveText("Upload the evidence of your authority to sign for the organisation.");
		await expectNoFrappeDialog(page);
		const facts = world.facts;
		await page.getByTestId("acc-legal-name").fill(facts.legal_name);
		await page.getByTestId("acc-registration").fill(facts.registration_number);
		await page.getByTestId("acc-kra").fill(facts.tax_identifier);
		await page.getByTestId("acc-address").fill(facts.registered_address);
		await page.getByTestId("acc-email").fill(facts.official_email);
		await page.getByTestId("acc-phone").fill(facts.official_phone);
		await page.getByTestId("acc-job-title").fill(facts.job_title);
		await page.getByTestId("acc-authority").setInputFiles({ name: "authority.pdf", mimeType: "application/pdf", buffer: TRUNCATED_PDF });
		await page.getByTestId("acc-create").click();
		await expect(page.getByTestId("acc-authority").locator("xpath=..").locator(".kt-field-error")).toHaveText("The file could not be read. Upload a complete PDF, PNG or JPEG file.");
		await expectNoFrappeDialog(page);
		await page.getByTestId("acc-authority").setInputFiles({ name: "mary-wanjiku-signing-authority.pdf", mimeType: "application/pdf", buffer: PDF });
		await expect(page.getByTestId("acc-authority-name")).toHaveText("mary-wanjiku-signing-authority.pdf");
		await page.getByTestId("acc-create").click();
		await expect(page.getByTestId("acc-verify-sent")).toContainText(`We sent a verification link to ${facts.official_email}. Verify it before starting a bid.`);
		await expect(page.getByTestId("acc-verify-sent")).toContainText("Pending verification");
		await expect(page.locator("body")).not.toContainText(/\bActive\b/);

		const message = latestTestMessage(facts.official_email);
		expect(message?.link, "the verification link in the Test Mailbox").toContain("/account/verify?token=");
		await page.goto(new URL(message!.link).pathname + new URL(message!.link).search, { waitUntil: "domcontentloaded" });
		await waitForPortal(page);
		await expect(page.getByTestId("acc-verified")).toHaveText("Your email is verified. The supplier account is ready.");
		await page.getByTestId("acc-verify-continue").click();
		await expect(page).toHaveURL(/\/account$/);
		await expect(page.getByTestId("acc-status")).toHaveText("Active");
		await expect(page.locator('[data-kt="next-step"]')).toContainText("The supplier account is ready.");
		await expect(page.getByTestId("acc-contacts")).toContainText("Verified");

		// the same Account on direct load and after back/forward
		await page.reload({ waitUntil: "domcontentloaded" });
		await waitForPortal(page);
		await expect(page.getByTestId("acc-status")).toHaveText("Active");
		await page.goBack({ waitUntil: "domcontentloaded" });
		await page.goForward({ waitUntil: "domcontentloaded" });
		await waitForPortal(page);
		await expect(page.getByTestId("acc-status")).toHaveText("Active");
		await expectNoFrappeDialog(page);
		expect(errors, errors.join(" | ")).toEqual([]);
	});

	test("an incomplete Account opens Edit organisation on the missing phone; a stale save is refused in place", async ({ page }) => {
		const world = accountFixture<World>("reset_account_fixture", { state: "attention" });
		const errors = collectPortalConsoleErrors(page);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.signatory, world.password, "/account");
		await expect(page.getByTestId("acc-status")).toHaveCount(0);
		const blocked = page.locator('.kt-notice.is-warning[data-kt="next-step"]');
		await expect(blocked).toContainText("Add the missing official phone before continuing.");
		await expect(blocked).toContainText("Enter the official phone number.");
		await blocked.getByRole("button", { name: "Edit organisation" }).click();
		const dialog = page.getByTestId("acc-edit-dialog");
		await expect(page.getByTestId("acc-edit-official_phone")).toBeFocused();

		// another save lands first: this dialog's version is now stale
		const current = await page.evaluate(async (organisation) => {
			const r = await fetch(`/api/method/kentender_suppliers.supplier_accounts.api.get_supplier_account?organisation=${organisation}`);
			return (await r.json()).message.organisation;
		}, world.organisation);
		const other = await page.evaluate(async ({ org }) => {
			const editable = ["legal_name", "country", "registration_number", "tax_identifier", "registered_address", "official_email", "official_phone"];
			const values = { ...Object.fromEntries(editable.map((k) => [k, org[k]])), official_phone: "+254 709 555 299", registered_address: "Westlands Business Park, Nairobi" };
			const body = new URLSearchParams({ organisation: org.organisation, values: JSON.stringify(values), expected_version: String(org.record_version), idempotency_key: `pw-acc-${Date.now()}` });
			const r = await fetch("/api/method/kentender_suppliers.supplier_accounts.api.update_supplier_organisation", { method: "POST", headers: { "X-Frappe-CSRF-Token": (window as unknown as { frappe: { csrf_token: string } }).frappe.csrf_token }, body });
			return (await r.json()).message;
		}, { org: current });
		expect(other.ok, JSON.stringify(other)).toBe(true);
		await page.getByTestId("acc-edit-official_phone").fill("+254 709 555 201");
		await page.getByTestId("acc-edit-save").click();
		await expect(dialog.locator(".kt-notice.is-critical")).toHaveText("Another person changed this account. Reload before continuing.");
		await expect(page.getByTestId("acc-edit-official_phone")).toHaveValue("+254 709 555 201");
		await expectNoFrappeDialog(page);

		// reload: the other save's facts, now complete; an edit from the header saves and reconciles in place
		await page.reload({ waitUntil: "domcontentloaded" });
		await waitForPortal(page);
		await expect(page.getByTestId("acc-status")).toHaveText("Active");
		await expect(page.locator('[data-kt="next-step"]')).toContainText("The supplier account is ready.");
		await expect(page.getByTestId("acc-account")).toContainText("Westlands Business Park, Nairobi");
		await page.getByTestId("acc-edit").click();
		await page.getByTestId("acc-edit-official_phone").fill("+254 709 555 201");
		await page.getByTestId("acc-edit-save").click();
		await expect(page.getByTestId("acc-edit-dialog")).toHaveCount(0);
		await expect(page.getByTestId("acc-account")).toContainText("+254 709 555 201");
		expect(errors, errors.join(" | ")).toEqual([]);
	});

	test("a pending Account resends its link; a failed read is named with Try again", async ({ page }) => {
		const world = accountFixture<World>("reset_account_fixture", { state: "verify" });
		clearTestMessages(world.official_email);
		const errors = collectPortalConsoleErrors(page);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.signatory, world.password, "/account");
		await expect(page.getByTestId("acc-status")).toHaveText("Pending verification");
		await expect(page.locator('[data-kt="next-step"]')).toContainText(`Verify ${world.official_email} before starting a bid.`);
		await expect(page.getByTestId("acc-contacts")).toContainText("Pending verification");
		await page.getByTestId("acc-resend").click();
		await expect(page.getByTestId("acc-message")).toHaveText(`We sent a new verification link to ${world.official_email}.`);
		expect(latestTestMessage(world.official_email)?.link).toContain("/account/verify?token=");

		await page.route("**/api/method/kentender_suppliers.supplier_accounts.api.get_supplier_account*", (route) => route.fulfill({ status: 500, body: "{}" }));
		await page.getByTestId("acc-add-evidence").click();
		await page.getByTestId("acc-evidence-type").selectOption("Tax compliance certificate");
		await page.getByTestId("acc-evidence-file").setInputFiles({ name: "tcc.pdf", mimeType: "application/pdf", buffer: PDF });
		await page.getByTestId("acc-evidence-save").click();
		await expect(page.locator(".acc-load-failure")).toContainText("Try again");
		await page.unroute("**/api/method/kentender_suppliers.supplier_accounts.api.get_supplier_account*");
		await page.locator(".acc-load-failure").getByRole("button", { name: "Try again" }).click();
		await expect(page.locator(".acc-load-failure")).toHaveCount(0);
		await expect(page.getByTestId("acc-evidence")).toContainText("Tax compliance certificate");
		await expectNoFrappeDialog(page);
		expect(errors.filter((e) => !/500 \(Internal Server Error\)/.test(e)), errors.join(" | ")).toEqual([]);
	});

	test("a suspended Account offers only receipts and support, as cards at 390", async ({ page }) => {
		const world = accountFixture<World>("reset_account_fixture", { state: "suspended" });
		const errors = collectPortalConsoleErrors(page);
		await page.setViewportSize({ width: 390, height: 844 });
		await loginToPortal(page, world.signatory, world.password, "/account");
		await expect(page.getByTestId("acc-status")).toHaveText("Account suspended");
		await expect(page.locator('[data-kt="next-step"]')).toContainText("Amina Yusuf is reviewing suspended access.");
		for (const id of ["acc-edit", "acc-resend", "acc-add-person", "acc-add-evidence"]) await expect(page.getByTestId(id)).toHaveCount(0);
		await expect(page.getByTestId("acc-links").getByRole("link")).toHaveText(["View receipts", "Supplier support"]);
		await expect(page.getByTestId("acc-people-cards")).toContainText("Supplier Representative");
		await expect(page.getByTestId("acc-evidence-cards").locator(".acc-card")).toHaveCount(4);
		await expectNoHorizontalOverflow(page);
		expect(errors, errors.join(" | ")).toEqual([]);
	});

	test("another organisation's person is told the Account is not found and is offered their own setup", async ({ page }) => {
		const world = accountFixture<World>("reset_account_fixture", { state: "active" });
		const errors = collectPortalConsoleErrors(page);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.other_person, world.password, `/account?organisation=${world.organisation}`);
		await expect(page.getByTestId("acc-not-found")).toBeVisible();
		await expect(page.locator("body")).not.toContainText(world.legal_name);
		await expect(page.locator("body")).not.toContainText(world.official_email);
		await page.goto("/account", { waitUntil: "domcontentloaded" });
		await waitForPortal(page);
		await expect(page.getByTestId("acc-register")).toContainText("You are signed in as Peter Mwangi.");
		expect(errors, errors.join(" | ")).toEqual([]);
	});
});
