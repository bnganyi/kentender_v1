import { expect, test } from "@playwright/test";

import { collectPortalConsoleErrors, expectNoFrappeDialog, expectNoHorizontalOverflow, loginToPortal, waitForPortal } from "../../helpers/portal";
import { bdsFixture, restoreBdsWorld } from "./bdsWorld";

/**
 * BDS-CHG-001 v0.8 §10.13 (plan Phase 11, slice 11.12) — Submit bid on the
 * Tenders test Tender for Afya (Test), a labelled test environment with the
 * Test Trust Service and Test Tender Box. Mary, the Authorised Signatory,
 * ticks the final confirmation, confirms in the dialog and the bid is signed
 * and accepted; the operating worlds (signing down, custody down, a closed
 * gate, a definite rejection, an uncertain attempt, no certificate) each
 * show their own state and no Submit. Another organisation sees nothing.
 */
type World = { tender_reference: string; bid_reference: string; password: string; representative: string; signatory: string; other_user: string };

test.describe.configure({ mode: "serial", timeout: 300_000 });

test.describe("BDS-DES-12 Submit bid", () => {
	test.afterAll(() => restoreBdsWorld());

	test("Mary confirms, signs and submits; the receipt opens and My bids says Submitted", async ({ page }) => {
		const world = bdsFixture<World>("reset_my_bids_fixture", { state: "review" });
		const errors = collectPortalConsoleErrors(page);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.signatory, world.password, `/tenders/${world.tender_reference}/bid/review`);
		await page.getByTestId("bds-review-action").click();
		await expect(page).toHaveURL(new RegExp(`/tenders/${world.tender_reference}/bid/submit$`));
		await expect(page.getByTestId("bds-submit-consequence")).toContainText("After submission, this Version cannot be edited.");
		await expect(page.getByTestId("bds-submit-time")).toContainText("Current server time");
		await expect(page.getByTestId("bds-submit-summary")).toContainText(`${world.bid_reference} · Draft Version`);
		await expect(page.getByTestId("bds-submit-signatory").locator(".kt-status")).toHaveText("Ready");
		const open = page.getByTestId("bds-submit-open");
		await expect(open).toBeDisabled();
		await page.getByTestId("bds-submit-decision").locator("label.kt-checkbox").click();
		await expect(open).toBeEnabled();

		// reload keeps the page; the confirmation starts unticked again
		await page.reload({ waitUntil: "domcontentloaded" });
		await waitForPortal(page);
		await expect(page.getByTestId("bds-submit-open")).toBeDisabled();
		await page.getByTestId("bds-submit-decision").locator("label.kt-checkbox").click();
		await page.getByTestId("bds-submit-open").click();
		const dialog = page.getByRole("dialog", { name: "Submit this bid?" });
		await expect(dialog).toBeVisible();
		await expect(dialog).toContainText(world.tender_reference);
		await dialog.getByRole("button", { name: "Cancel" }).click();
		await expect(dialog).toHaveCount(0);
		await page.getByTestId("bds-submit-open").click();
		await page.getByTestId("bds-submit-confirm").click();
		await expect(page).toHaveURL(new RegExp(`/tenders/${world.tender_reference}/bid/receipt/RCPT-`), { timeout: 60_000 });

		await page.goto("/my-bids", { waitUntil: "domcontentloaded" });
		await waitForPortal(page);
		await expect(page.getByTestId(`bds-bid-row-${world.bid_reference}`)).toContainText("Submitted");
		await expectNoFrappeDialog(page);
		expect(errors.filter((e) => !/404 \(Not Found\)/.test(e)), errors.join(" | ")).toEqual([]);
	});

	test("each operating world has its own state and no Submit", async ({ page }) => {
		const world = bdsFixture<World>("reset_my_bids_fixture", { state: "review" });
		const submit = `/tenders/${world.tender_reference}/bid/submit`;
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.signatory, world.password, submit);
		const cases: [string, Record<string, unknown>, string][] = [
			["set_submission_world", { world: "signature" }, "Digital signing is temporarily unavailable"],
			["set_submission_world", { world: "service" }, "Electronic submission is temporarily unavailable"],
		];
		for (const [fn, kwargs, title] of cases) {
			bdsFixture(fn, kwargs);
			await page.reload({ waitUntil: "domcontentloaded" });
			await waitForPortal(page);
			await expect(page.getByTestId("bds-submit-notice").locator("strong")).toHaveText(title);
			await expect(page.getByTestId("bds-submit-decision")).toHaveCount(0);
		}
		bdsFixture("set_submission_world", { world: "normal" });
		bdsFixture("set_gate", { closed: true });
		await page.reload({ waitUntil: "domcontentloaded" });
		await waitForPortal(page);
		await expect(page.getByTestId("bds-submit-notice").locator("strong")).toHaveText("Electronic bid submission is not available yet");
		await expect(page.getByTestId("bds-submit-action")).toHaveText("Back to bid");
		bdsFixture("set_gate", { closed: false });

		// no certificate: Check certificate is a fresh read and changes nothing
		bdsFixture("revoke_signatory_certificate");
		await page.reload({ waitUntil: "domcontentloaded" });
		await waitForPortal(page);
		await expect(page.getByTestId("bds-submit-signatory").locator(".kt-status")).toHaveText("Not available");
		await page.getByRole("button", { name: "Check certificate" }).click();
		await expect(page.getByTestId("bds-certificate-check")).toHaveText("A valid digital signature certificate is required before you can submit.");
		await expect(page.getByTestId("bds-submit-decision")).toHaveCount(0);
		await page.setViewportSize({ width: 390, height: 844 });
		await expectNoHorizontalOverflow(page);
	});

	test("a definite rejection offers a new confirmation; an uncertain attempt is pending with View status", async ({ page }) => {
		const world = bdsFixture<World>("reset_my_bids_fixture", { state: "review" });
		const submit = `/tenders/${world.tender_reference}/bid/submit`;
		bdsFixture("set_submission_world", { world: "reject" });
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.signatory, world.password, submit);
		await page.getByTestId("bds-submit-decision").locator("label.kt-checkbox").click();
		await page.getByTestId("bds-submit-open").click();
		await page.getByTestId("bds-submit-confirm").click();
		await expect(page.locator(".kt-next-step-headline")).toHaveText("The tender box rejected this attempt; no bid was submitted.");
		await expect(page.locator(".kt-next-step-sentence")).toContainText("Reference TBX-REJECT-033-01.");
		await expect(page.getByTestId("bds-submit-decision")).toHaveCount(0);

		// Try confirmation again, this time the tender box does not answer
		bdsFixture("set_submission_world", { world: "uncertain" });
		await page.getByRole("button", { name: "Try confirmation again" }).click();
		await page.getByTestId("bds-submit-decision").locator("label.kt-checkbox").click();
		await page.getByTestId("bds-submit-open").click();
		await page.getByTestId("bds-submit-confirm").click();
		const pending = page.getByTestId("bds-submit-pending");
		await expect(pending).toContainText("We are checking this submission attempt.");
		await expect(pending.getByRole("link", { name: "View status" })).toHaveAttribute("href", `${submit.replace(/submit$/, "status")}`);
		await expect(pending.getByRole("button")).toBeDisabled();
		await expect(page.getByTestId("bds-submit-open")).toHaveCount(0);
		await page.reload({ waitUntil: "domcontentloaded" });
		await waitForPortal(page);
		await expect(page.getByTestId("bds-submit-pending")).toBeVisible();
	});

	test("David is not offered Submit; another organisation is told the bid is not found", async ({ page }) => {
		const world = bdsFixture<World>("reset_my_bids_fixture", { state: "review" });
		await page.setViewportSize({ width: 1440, height: 1024 });
		await loginToPortal(page, world.representative, world.password, `/tenders/${world.tender_reference}/bid/submit`);
		await expect(page.locator(".kt-next-step-headline")).toContainText("must submit this bid.");
		await expect(page.getByTestId("bds-submit-decision")).toHaveCount(0);
		await page.context().clearCookies();
		await loginToPortal(page, world.other_user, world.password, `/tenders/${world.tender_reference}/bid/submit`);
		await expect(page.getByTestId("bds-state-bid-not-found")).toBeVisible();
		await expect(page.locator("body")).not.toContainText(world.bid_reference);
	});
});
