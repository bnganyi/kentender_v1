import { execSync } from "node:child_process";
import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

const CANONICAL_PACKAGE_ID = "KE-PPRA-IT-2022-04";

function ensureCanonicalStdImport() {
	const zipPath =
		"/home/midasuser/frappe-bench/apps/kentender_v1/docs/std-prod-impl/data/KE-PPRA-IT-2022-04_Seed_Package_v1_1.zip";
	execSync(
		`cd /home/midasuser/frappe-bench && bench --site kentender.midas.com execute kentender_procurement.std_engine.package_import.draft_cleanup.force_reset_package_state_for_tests --kwargs '${JSON.stringify({ package_id: CANONICAL_PACKAGE_ID, family_code: "KE-PPRA-IT" })}'`,
		{ stdio: "ignore" },
	);
	execSync(
		`cd /home/midasuser/frappe-bench && bench --site kentender.midas.com execute kentender_procurement.std_engine.package_import.commit.run --kwargs '${JSON.stringify({ zip_path: zipPath })}'`,
		{ stdio: "ignore" },
	);
}

function approveLegalReview() {
	execSync(
		`cd /home/midasuser/frappe-bench && bench --site kentender.midas.com execute kentender_procurement.std_engine.services.legal_review_service.approve_all_pending --kwargs '${JSON.stringify({ package_id: CANONICAL_PACKAGE_ID })}'`,
		{ stdio: "ignore" },
	);
	execSync(
		`cd /home/midasuser/frappe-bench && bench --site kentender.midas.com execute kentender_procurement.std_engine.services.activation_readiness_service.sync_activation_flags --kwargs '${JSON.stringify({ package_id: CANONICAL_PACKAGE_ID })}'`,
		{ stdio: "ignore" },
	);
}

test.describe("STD Engine Step 1 activation readiness", () => {
	test.beforeAll(() => {
		ensureCanonicalStdImport();
	});

	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
	});

	test("governance readiness API reports activation allowed after legal approval", async ({ page }) => {
		approveLegalReview();
		await page.goto("/desk/std-review-and-approval");
		const iframe = page.frameLocator('[data-testid="std-prod-std-review-and-approval-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});

		const payload = await page.evaluate(async (packageId) => {
			const response = await fetch(
				`/api/method/kentender_procurement.std_engine.api.governance_api.get_activation_readiness?package_id=${encodeURIComponent(packageId)}`,
			);
			if (!response.ok) {
				throw new Error(`readiness HTTP ${response.status}`);
			}
			return response.json();
		}, CANONICAL_PACKAGE_ID);
		const readiness = payload?.message || payload;

		expect(readiness?.ok).toBe(true);
		expect(readiness?.data?.activationAllowed).toBe(true);
		expect(readiness?.data?.legalReviewComplete).toBe(true);
		expect(readiness?.packageContext?.packageId).toBe(CANONICAL_PACKAGE_ID);
	});
});
