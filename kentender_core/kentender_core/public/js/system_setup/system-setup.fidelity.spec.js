// Structural fidelity for System setup, against its own CFG-CHG-002 v0.14
// boards (docs/mvp-1-r1/09_unified_system_setup/design).
//
// Until 24 Sep 2026 System setup was compared only by the landmark gate, which
// reads text and so cannot see a container at all. This spec is the structural
// half: every artboard every CFG board draws is listed below, and each is
// either compared against the component that builds it or explicitly queued
// for the Phase 5 re-port (tests/ui/fidelity/departures/system-setup.js).
//
// Three rules, all enforced here rather than stated:
//   1. No drawn state is unassigned — a new artboard id fails the inventory.
//   2. A compared artboard must match, or be queued with a reason.
//   3. A queued artboard that now matches FAILS, so the queue cannot rot and
//      COVERED is the honest list of what is done.
import { flushPromises, mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import { setupArtboardIds, setupSkeleton } from "../../../../../tests/ui/fidelity/board.js";
import { compareSkeletons, formatMismatch, skeletonOf } from "../../../../../tests/ui/fidelity/skeleton.js";
import { COVERED, DEPARTURES, FRAGMENTS, REBUILD_QUEUE } from "../../../../../tests/ui/fidelity/departures/system-setup.js";
import { globalMocks } from "./components/spec_helpers.js";

const siteApi = vi.hoisted(() => ({
	previewFiscalYear: vi.fn(async () => null),
	configure: vi.fn(),
	update: vi.fn(),
	listFiscalYears: vi.fn(),
	listFiscalYearIntakeHistory: vi.fn(),
}));
vi.mock("./data/siteConfigApi.js", () => ({ siteConfigApi: siteApi }));
const settingsApi = vi.hoisted(() => ({
	get: vi.fn(),
	setReminderThresholdDays: vi.fn(),
	addFundingSource: vi.fn(),
	updateFundingSource: vi.fn(),
	deleteFundingSource: vi.fn(),
}));
vi.mock("./data/procurementSettingsApi.js", () => ({ procurementSettingsApi: settingsApi }));

import AddFiscalYearDialog from "./components/AddFiscalYearDialog.vue";
import DisableFiscalYearDialog from "./components/DisableFiscalYearDialog.vue";
import IntakeForm from "./components/IntakeForm.vue";
import FiscalYearsTab from "./tabs/FiscalYearsTab.vue";
import FundingSourceDialog from "./components/FundingSourceDialog.vue";
import ProcurementSettingsTab from "./tabs/ProcurementSettingsTab.vue";
import ReminderSettingCard from "./components/ReminderSettingCard.vue";
import ProcuringEntityTab from "./tabs/ProcuringEntityTab.vue";

const D = "docs/mvp-1-r1/09_unified_system_setup/design/";
const BOARDS = {
	C01: "C01-Procuring-Entity.dc.html",
	C02: "C02-Financial-Years.dc.html",
	C03A: "C03A-Funding-Sources.dc.html",
	C03BC: "C03BC-Procurement-Rules.dc.html",
	C03D: "C03D-Source-Checks.dc.html",
	C04: "C04-Schedules-Calendars.dc.html",
	Reminders: "Reminders.dc.html",
	Common: "Common-States.dc.html",
};

const ROUTES = ["Cabinet Secretary", "County Executive Committee Member", "Board of Directors", "Council"];
function site(overrides = {}) {
	return {
		configured: true,
		procuring_entity: {
			pe_name: "Ministry of Health",
			pe_code: "PE-MOH",
			pe_type: "National Government Ministry",
			ppra_registration: "PPRA/PE/2019/0114",
			timezone: "Africa/Nairobi",
			statutory_approval_route: "Cabinet Secretary",
			entity_is_county: false,
			configured_by: "Administrator",
			configured_at_label: "29 Jun 2026, 10:10 EAT",
			approval_applicability: { result: "Rule not source-checked", reference: "APPROVAL-APPLICABILITY-V1" },
			expected_version: "v1",
		},
		pe_types: ["National Government Ministry", "County Government"],
		timezones: ["Africa/Nairobi"],
		statutory_approval_routes: ROUTES,
		root_unit: { name: "Ministry of Health", code: "PE-MOH" },
		...overrides,
	};
}

// C02 CONFIG fixture rows, as the board draws them (§10.3).
function fyRow(overrides = {}) {
	return {
		fiscal_year: "2027-2028",
		label: "FY 2027/28",
		period_label: "1 Jul 2027–30 Jun 2028",
		phase: "Upcoming",
		disabled: false,
		reference_count: 0,
		expected_version: "v1",
		needs_submission_open: true,
		needs_submission_closes_label: "25 Nov 2026, 23:59 EAT",
		dpp_submission_open: true,
		dpp_submission_closes_label: "30 Nov 2026, 23:59 EAT",
		disposal_plan_submission_open: false,
		disposal_plan_submission_closes_label: "",
		...overrides,
	};
}
const CURRENT_YEAR = fyRow({
	fiscal_year: "2026-2027",
	label: "FY 2026/27",
	period_label: "1 Jul 2026–30 Jun 2027",
	phase: "Current",
	needs_submission_open: false,
	needs_submission_closes_label: "",
	dpp_submission_open: false,
	dpp_submission_closes_label: "",
});
async function yearsTab(rows, props = {}) {
	siteApi.listFiscalYears.mockResolvedValue({ fiscal_years: rows, count: rows.length });
	siteApi.listFiscalYearIntakeHistory.mockResolvedValue({
		count: 1,
		entries: [{ activity: "Departmental needs", financial_year: "FY 2027/28", change: "Open", previous_value: "—", new_value: "25 Nov 2026, 23:59 EAT", reason: "Annual needs call.", changed_by: "Administrator", changed_at: "1 Nov 2026, 08:02 EAT" }],
	});
	const wrapper = mount(FiscalYearsTab, { props, global: globalMocks() });
	await flushPromises();
	return wrapper;
}

// Every artboard, by board. `mount` returns the element to compare, or is
// absent when no component can render the state from props today. `self`
// compares the artboard element itself as a landmark (a dialog artboard IS the
// dialog).
// C03A — the funding sources the board draws, all referenced by a Budget
// line (so no Remove) except where a test says otherwise.
const SOURCES = ["Government of Kenya", "Development partner", "Appropriation in Aid"].map((label, index) => ({
	name: `FS-${index + 1}`,
	label,
	enabled: true,
	referenced: true,
	expected_version: "v1",
}));
async function settingsTab(fundingSources) {
	settingsApi.get.mockResolvedValue({ outcome: "OK", funding_sources: fundingSources, method_profiles: [], reference_sets: [], schedule_profiles: [], calendars: [] });
	const wrapper = mount(ProcurementSettingsTab, {
		props: { route: { tab: "procurement-settings", section: "funding-sources", id: "", versionId: "", action: "" } },
		global: globalMocks(),
	});
	await flushPromises();
	return wrapper;
}

const ARTBOARDS = [
	{ key: "C01#configured", mount: () => mount(ProcuringEntityTab, { props: { site: site() }, global: globalMocks() }) },
	{
		key: "C01#first-run",
		mount: () => mount(ProcuringEntityTab, { props: { site: site({ configured: false, procuring_entity: null, root_unit: null }) }, global: globalMocks() }),
	},
	{
		// A specimen: the board draws only the type, the county answer and the
		// notice — compared as a fragment of the full screen.
		key: "C01#conflict",
		mount: async () => {
			siteApi.update.mockRejectedValueOnce(new Error("The county answer does not match the entity details."));
			const wrapper = mount(ProcuringEntityTab, { props: { site: site() }, global: globalMocks() });
			await wrapper.find('[data-testid="kt-setup-pe-type"]').setValue("County Government");
			await wrapper.find('[data-testid="kt-setup-pe-submit"]').trigger("click");
			return wrapper;
		},
	},
	{
		key: "C01#missing-authority",
		mount: async () => {
			const wrapper = mount(ProcuringEntityTab, { props: { site: site({ configured: false, procuring_entity: null, root_unit: null }) }, global: globalMocks() });
			await wrapper.find('[data-testid="kt-setup-pe-submit"]').trigger("click");
			return wrapper;
		},
	},

	{ key: "C02#overview", mount: () => yearsTab([fyRow(), CURRENT_YEAR]) },
	{
		key: "C02#overview-disabled",
		mount: async () => {
			const wrapper = await yearsTab([fyRow({ disabled: true, needs_submission_open: false, dpp_submission_open: false })]);
			await wrapper.find('[data-testid="kt-fy-include-disabled"] input').setValue(true);
			return wrapper;
		},
	},
	{ key: "C02#narrow", live: '[data-testid="kt-fy-cards"]', select: "#narrow > div", mount: () => yearsTab([fyRow()]) },
	{ key: "C02#empty", mount: () => yearsTab([]) },
	{
		key: "C02#add-year",
		self: true,
		select: "#add-year .dialog",
		mount: async () => {
			siteApi.previewFiscalYear.mockResolvedValue({ fiscal_year: "2028-2029", label: "FY 2028/29", period_label: "1 Jul 2028–30 Jun 2029", exists: false, company_missing: false });
			const wrapper = mount(AddFiscalYearDialog, { global: globalMocks() });
			await wrapper.find('[data-testid="kt-fy-start-year"]').setValue("2028");
			return wrapper;
		},
	},
	{ key: "C02#detail", mount: () => yearsTab([fyRow(), CURRENT_YEAR], { subpath: "year/2027-2028" }) },
	{
		key: "C02#detail-row-variants",
		mount: () =>
			yearsTab([fyRow({ dpp_submission_closes_label: "", needs_submission_open: false, needs_submission_closed_at_label: "25 Nov 2026, 23:59 EAT" })], {
				subpath: "year/2027-2028",
			}),
	},
	{
		key: "C02#disable",
		self: true,
		select: "#disable .dialog",
		mount: () => mount(DisableFiscalYearDialog, { props: { row: fyRow(), blockers: ["Departmental needs submissions are still open."] }, global: globalMocks() }),
	},
	{
		key: "C02#forms",
		self: true,
		select: "#forms .card",
		mount: () => mount(IntakeForm, { props: { mode: "open", row: fyRow() }, global: globalMocks() }),
	},
	{
		// #form-states draws the three mutually exclusive form-state notices side
		// by side. Compared: the deadline-error notice as the form renders it
		// (icon included); the expired and stale notices share its shape and are
		// asserted with their own icons and copy in IntakeForm.spec.
		key: "C02#form-states",
		self: true,
		select: "#form-states .kt-notice",
		live: '[data-testid="kt-fy-intake-deadline-error"]',
		mount: () =>
			mount(IntakeForm, { props: { mode: "open", row: fyRow(), error: "Enter a closing time later than the current time." }, global: globalMocks() }),
	},

	{ key: "C03A#list", live: '[data-testid="kt-procset-sources"]', mount: () => settingsTab(SOURCES) },
	{
		key: "C03A#add",
		self: true,
		select: "#add",
		live: ".kt-dialog",
		mount: async () => {
			const wrapper = mount(FundingSourceDialog, { props: { creating: true }, global: globalMocks() });
			await wrapper.find('[data-testid="kt-fs-name"]').setValue("Development partner");
			return wrapper;
		},
	},
	{
		key: "C03A#edit",
		self: true,
		select: "#edit",
		live: ".kt-dialog",
		mount: () =>
			mount(FundingSourceDialog, {
				props: { source: { name: "FS-2", label: "Development partner", enabled: false, referenced: false, expected_version: "v1" } },
				global: globalMocks(),
			}),
	},
	{
		key: "C03A#disabled",
		self: true,
		select: "#disabled table",
		live: '[data-testid="kt-procset-sources"] table',
		mount: () => settingsTab([{ ...SOURCES[1], enabled: false }]),
	},
	{
		key: "C03A#duplicate",
		self: true,
		live: '[data-testid="kt-fs-duplicate"]',
		mount: async () => {
			const wrapper = mount(FundingSourceDialog, { props: { creating: true, existing: SOURCES }, global: globalMocks() });
			await wrapper.find('[data-testid="kt-fs-name"]').setValue("Development partner");
			return wrapper;
		},
	},
	{ key: "C03A#empty", self: true, select: "#empty > div", live: '[data-testid="kt-procset-sources-empty"]', mount: () => settingsTab([]) },

	{ key: "C03BC#list" },
	{ key: "C03BC#detail" },
	{ key: "C03BC#rename" },
	{ key: "C03BC#add" },
	{ key: "C03BC#kinds" },
	{ key: "C03BC#version" },
	{ key: "C03BC#states" },

	{ key: "C03D#pending" },
	{ key: "C03D#verified" },
	{ key: "C03D#rejected" },
	{ key: "C03D#history" },
	{ key: "C03D#evidence" },

	{ key: "C04#list" },
	{ key: "C04#detail" },
	{ key: "C04#add" },
	{ key: "C04#calendar" },
	{ key: "C04#calendar-detail" },
	{ key: "C04#calendar-version" },
	{ key: "C04#calendar-history" },

	{ key: "Reminders#unchanged", mount: () => mount(ReminderSettingCard, { props: { days: 7 }, global: globalMocks() }) },
	{ key: "Reminders#edited" },
	{ key: "Reminders#zero" },
	{ key: "Reminders#invalid" },

	{ key: "Common#loading" },
	{ key: "Common#denied" },
	{ key: "Common#load-error" },
];

function boardOf(key) {
	const [board, id] = key.split("#");
	return { file: `${D}${BOARDS[board]}`, id };
}

describe("System setup board inventory", () => {
	it("assigns every artboard every CFG board draws — none silently unbuilt", () => {
		const listed = new Set(ARTBOARDS.map((a) => a.key));
		const drawn = Object.keys(BOARDS).flatMap((board) => setupArtboardIds(`${D}${BOARDS[board]}`).map((id) => `${board}#${id}`));
		expect(drawn.filter((key) => !listed.has(key)), "drawn artboards with no entry here").toEqual([]);
		expect([...listed].filter((key) => !drawn.includes(key)), "entries for artboards no board draws").toEqual([]);
	});

	it("keeps COVERED and REBUILD_QUEUE disjoint and complete", () => {
		const keys = ARTBOARDS.map((a) => a.key);
		expect(COVERED.filter((key) => key in REBUILD_QUEUE), "both covered and queued").toEqual([]);
		expect(keys.filter((key) => !COVERED.includes(key) && !(key in REBUILD_QUEUE)), "neither covered nor queued").toEqual([]);
		expect([...COVERED, ...Object.keys(REBUILD_QUEUE)].filter((key) => !keys.includes(key)), "names no artboard").toEqual([]);
	});
});

describe.each(ARTBOARDS)("$key", ({ key, mount: mountIt, select, self, live }) => {
	const fragment = FRAGMENTS.includes(key);
	it("is built out of the board's own containers", async () => {
		const queued = REBUILD_QUEUE[key];
		if (!mountIt) {
			expect(queued, `${key}: nothing renders it and it is not queued`).toBeTruthy();
			return;
		}
		const wrapper = await mountIt();
		await flushPromises();
		const { file, id } = boardOf(key);
		const board = setupSkeleton(file, select || `#${id}`, { self });
		const root = live ? wrapper.element.querySelector(live) : wrapper.element;
		expect(root, `${key}: ${live} not rendered`).toBeTruthy();
		const built = self ? skeletonOf({ children: [root] }) : skeletonOf(root);
		const result = compareSkeletons(board, built, { departures: DEPARTURES[key] || [] });
		// A specimen board draws a fragment of the screen: every container it
		// draws must be present in order, and the rest of the screen is not
		// the specimen's business.
		if (fragment) result.extra = [];
		const message = formatMismatch(key, result);
		if (queued) {
			expect(message, `${key} now matches its board — move it from REBUILD_QUEUE to COVERED`).not.toBe("");
		} else {
			expect(message, message).toBe("");
		}
	});
});
