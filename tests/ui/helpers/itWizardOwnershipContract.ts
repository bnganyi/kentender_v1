import { expect, type FrameLocator } from "@playwright/test";

/** Field source types from Matrix 99 / Correction Plan 98. */
export const FIELD_SOURCE_TYPES = [
	"USER_ENTERED",
	"TEMPLATE_PREFILLED",
	"DERIVED",
	"OWNED_ELSEWHERE",
	"STD_LOCKED",
	"NOT_CONFIGURED",
] as const;

export type FieldSourceType = (typeof FIELD_SOURCE_TYPES)[number];

export const INVENTORY_FORBIDDEN_MAGICAL = [
	"2,500 Concurrent Users",
	"42 Locations (East/West)",
	"180 VPN Managed Devices",
	"RBAC / MFA",
	"Access Logic",
	"Data Residency",
	"Primary HQ",
	"7/10 Items",
];

export async function expectInventoryOwnershipSurface(inventory: FrameLocator) {
	const summary = inventory.locator("[data-itw-inv-summary-host]");
	const security = inventory.locator("[data-itw-inv-security-host]");
	await expect(summary).toBeVisible();
	await expect(security).toBeVisible();
	// Seeded configs source-back items; empty configs show Not configured — both must expose Source.
	await expect(summary).toContainText(/Not configured|Source:/);
	await expect(security).toContainText(/Not configured|Source:/);
	await expect(security.locator('[data-itw-inv-security-value="title"]')).toBeVisible();
	await expect(security.locator('[data-itw-inv-security-value="classification"]')).toBeVisible();
	await expect(security.locator('[data-itw-inv-security-value="required_action"]')).toBeVisible();
	await expect(security.locator('[data-itw-inv-security-value="bidder_consideration"]')).toBeVisible();
	for (const pattern of INVENTORY_FORBIDDEN_MAGICAL) {
		await expect(inventory.getByText(pattern, { exact: false })).toHaveCount(0);
	}
	await expect(inventory.getByText(/Quantity|Unit Price|Pricing Class/)).toHaveCount(0);
}

export async function expectOwnedElsewhereReference(
	host: FrameLocator,
	options: { sourceLabel: RegExp | string; editLabel: RegExp | string },
) {
	await expect(host.getByText(options.sourceLabel)).toBeVisible();
	await expect(host.getByRole("button", { name: options.editLabel })).toBeVisible();
}
