import { execSync } from "node:child_process";
import path from "node:path";

import { Page, Route } from "@playwright/test";

/**
 * CFG-CHG-002 v0.14 §10.1/§13 (tracker CFG14-401) — System setup's fixture
 * worlds for browser specs.
 *
 * Site worlds (built by the real commands in
 * kentender_core.seeds.playwright_ui_fixtures, undone by `restoreSite`):
 *   - `reset_config`       CONFIG — canonical site, disposal plans closed
 *   - `reset_config_rules` CONFIG-RULES — a pending Reservation rules V1
 *   - `reset_config_swap`  CONFIG-SWAP — departmental plans open for the
 *                          current year with no closing date
 * Every spec that builds one calls `restoreSite()` in afterAll: the intake
 * flags these worlds move are read by Needs, Planning and Budget.
 *
 * Browser-side worlds (the shared site is never unconfigured or emptied):
 *   - `asFirstRun(page)`   CONFIG-FIRST — the real workspace response with
 *                          no entity and no root
 *   - `asEmpty(page, …)`   CONFIG-EMPTY — the real list responses with the
 *                          named lists emptied
 * Both transform the server's own response, so their shape cannot drift from
 * it. The first-run save itself is proved by the Python suite (atomic
 * entity + root, test_site_configuration), not by a browser substitute.
 */

const BENCH_ROOT = path.resolve(__dirname, "../../../../../..");
const SITE = process.env.UI_SITE || "kentender.midas.com";
const FIXTURES = "kentender_core.seeds.playwright_ui_fixtures";

function bench(command: string): string {
	try {
		return execSync(`cd "${BENCH_ROOT}" && bench --site ${SITE} ${command}`, {
			stdio: "pipe",
			timeout: 300_000,
			encoding: "utf-8",
		});
	} catch (error: any) {
		const stderr = (error?.stderr || "").toString().trim();
		const stdout = (error?.stdout || "").toString().trim();
		throw new Error(`bench ${command} failed\n${stderr || stdout || error?.message}`);
	}
}

function parseResult<T>(fn: string, output: string): T {
	const line = output.trim().split("\n").pop() || "";
	try {
		return JSON.parse(line) as T;
	} catch (error) {
		throw new Error(`${fn}: could not parse bench execute output:\n${output}`);
	}
}

export type ConfigWorld = {
	pe_code: string;
	root_unit: string;
	fiscal_year_open: string;
	fiscal_year_current: string;
	needs_submission: { fiscal_year: string; closes_at: string } | null;
	dpp_submission: { fiscal_year: string; closes_at: string } | null;
	disposal_plan_submission: { fiscal_year: string; closes_at: string } | null;
	reservation_reference_set?: string;
	reservation_version?: string;
};

/** Build one site world; read every id from the result, never hardcode it. */
export function resetWorld(fn: "reset_config" | "reset_config_rules" | "reset_config_swap"): ConfigWorld {
	return parseResult<ConfigWorld>(fn, bench(`execute ${FIXTURES}.${fn}`));
}

/** A System-Manager-only login for the second setup role (removed by restoreSite). */
export function systemManager(): { user: string; password: string } {
	return parseResult<{ user: string; password: string }>("ensure_system_manager", bench(`execute ${FIXTURES}.ensure_system_manager`));
}

/** C06: one Desk user with no business role or assignment (removed by restoreSite). */
export type ResponsibilitiesWorld = { user: string; full_name: string; unit: string; unit_name: string };
export function resetResponsibilities(): ResponsibilitiesWorld {
	return parseResult<ResponsibilitiesWorld>("reset_responsibilities", bench(`execute ${FIXTURES}.reset_responsibilities`));
}

/** Undo every site world (idempotent). Call in afterAll of every spec that built one. */
export function restoreSite(): void {
	bench(`execute ${FIXTURES}.restore_site`);
}

const WORKSPACE = "**/api/method/kentender_core.api.site_configuration_api.get_system_setup_workspace";
const FISCAL_YEARS = "**/api/method/kentender_core.api.site_configuration_api.list_fiscal_years";
const SETTINGS = "**/api/method/kentender_core.api.procurement_settings_api.get_procurement_settings";

async function transform(page: Page, url: string, change: (message: any) => void): Promise<void> {
	await page.route(url, async (route: Route) => {
		const response = await route.fetch();
		const body = await response.json();
		if (body && body.message) change(body.message);
		await route.fulfill({ response, json: body });
	});
}

/** CONFIG-FIRST: the page as it reads before any entity or root exists. */
export async function asFirstRun(page: Page): Promise<void> {
	await transform(page, WORKSPACE, (message) => {
		message.configured = false;
		message.procuring_entity = null;
		message.root_unit = null;
		message.needs_submission = null;
		message.dpp_submission = null;
		message.disposal_plan_submission = null;
	});
}

/** CONFIG-EMPTY: the named lists empty, everything else as the server returned it. */
export async function asEmpty(
	page: Page,
	lists: { years?: boolean; fundingSources?: boolean; rules?: boolean; schedules?: boolean }
): Promise<void> {
	if (lists.years) {
		await transform(page, FISCAL_YEARS, (message) => {
			if (Array.isArray(message.rows)) message.rows = [];
			if (Array.isArray(message.fiscal_years)) message.fiscal_years = [];
			if ("count" in message) message.count = 0;
		});
	}
	if (lists.fundingSources || lists.rules || lists.schedules) {
		await transform(page, SETTINGS, (message) => {
			if (lists.fundingSources) message.funding_sources = [];
			if (lists.rules) {
				message.method_profiles = [];
				message.reference_sets = [];
			}
			if (lists.schedules) {
				message.schedule_profiles = [];
				message.calendars = [];
			}
		});
	}
}

const STRUCTURE = "**/api/method/kentender_core.api.organisation_structure_api.get_organisation_structure";

/** AUTH-DES-08 empty root: the server's own structure, read as having no units yet. */
export async function asEmptyOrganisation(page: Page): Promise<void> {
	await transform(page, STRUCTURE, (message) => {
		if (message.state === "ready") message.state = "empty_root";
	});
}

