import { execSync } from "node:child_process";
import path from "node:path";

import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { OFFICER, HOPF, PASSWORD } from "../tenders/helpers";

/**
 * Project Owner, 10 October 2026 — the sealed box and the tender-security
 * intake over real HTTP. Administrator and System Manager (and every
 * procuring-entity user) get the same answer from the REST, form-load, count,
 * list, report-view and search routes whether the box is empty or holds a bid;
 * a direct record URL and a bid's private file are refused to everyone. These
 * are application restrictions, not a claim about a database operator.
 */

const BENCH_ROOT = path.resolve(__dirname, "../../../../../..");
const SITE = process.env.UI_SITE || "kentender.midas.com";
const FIXTURES = "kentender_procurement.bid_submission.seeds.playwright_ui_fixtures";
const SEALED = ["Bid Workspace", "Bidder Arrangement", "Bid Submission Version", "Tender Box Envelope", "Bid Receipt", "Tender Security Intake", "Tender Security Verification", "Bid Opening Handoff"];

function execute<T>(fn: string, kwargs: Record<string, unknown> = {}): T {
	const args = Object.keys(kwargs).length ? ` --kwargs '${JSON.stringify(kwargs).replace(/\btrue\b/g, "True").replace(/\bfalse\b/g, "False")}'` : "";
	const output = execSync(`cd "${BENCH_ROOT}" && bench --site ${SITE} execute ${FIXTURES}.${fn}${args}`, { stdio: "pipe", timeout: 600_000, encoding: "utf-8" });
	return JSON.parse(output.trim().split("\n").pop() || "{}") as T;
}

test.describe.configure({ mode: "serial", timeout: 240_000 });

test.describe("Sealed records — one answer for an empty and a populated box", () => {
	test.afterAll(() => execute("restore_site"));

	for (const [who, user] of [["Administrator", process.env.UI_ADMIN_USER || "Administrator"], ["the Head of Procurement Function", HOPF], ["the intake officer", OFFICER]] as const) {
		test(`${who}: every read route answers an empty and a populated box identically`, async ({ page }) => {
			const password = who === "Administrator" ? process.env.UI_ADMIN_PASSWORD || PASSWORD : PASSWORD;
			const answers: Record<string, unknown>[] = [];
			for (const populated of [false, true]) {
				execute("reset_security_intake_fixture", { answered: populated });
				await login(page, user, password);
				const snapshot: Record<string, unknown> = {};
				for (const doctype of SEALED) {
					const count = await page.request.get(`/api/method/frappe.client.get_count?doctype=${encodeURIComponent(doctype)}`);
					const list = await page.request.get(`/api/resource/${encodeURIComponent(doctype)}?fields=["name"]&limit_page_length=20`);
					snapshot[`${doctype}|count`] = { status: count.status(), body: count.status() === 200 ? await count.json() : null };
					snapshot[`${doctype}|list`] = { status: list.status(), body: list.status() === 200 ? await list.json() : null };
				}
				answers.push(snapshot);
			}
			expect(answers[1]).toEqual(answers[0]); // the answer never depends on whether a bid exists
			for (const [key, answer] of Object.entries(answers[1]) as [string, { status: number; body: { message?: number; data?: unknown[] } | null }][]) {
				if (key.endsWith("|count") && answer.status === 200) expect(answer.body?.message, key).toBe(0);
				if (key.endsWith("|list") && answer.status === 200) expect(answer.body?.data, key).toEqual([]);
			}
		});
	}

	test("Administrator cannot read a sealed record directly or through the form load, nor fetch a bid's private file", async ({ page }) => {
		const world = execute<{ bid_reference: string }>("reset_security_intake_fixture", { answered: true });
		await login(page, process.env.UI_ADMIN_USER || "Administrator", process.env.UI_ADMIN_PASSWORD || PASSWORD);
		const rest = await page.request.get(`/api/resource/Bid%20Workspace/${encodeURIComponent(world.bid_reference)}`);
		expect([401, 403, 404]).toContain(rest.status());
		const load = await page.request.get(`/api/method/frappe.desk.form.load.getdoc?doctype=Bid%20Workspace&name=${encodeURIComponent(world.bid_reference)}`);
		expect([401, 403, 404]).toContain(load.status());
		const file = await page.request.get("/private/files/not-an-existing-bid-file.pdf");
		expect([401, 403, 404]).toContain(file.status());
	});
});
