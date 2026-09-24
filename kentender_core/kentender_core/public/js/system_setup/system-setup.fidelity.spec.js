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
import { COVERED, DEPARTURES, REBUILD_QUEUE } from "../../../../../tests/ui/fidelity/departures/system-setup.js";
import { globalMocks } from "./components/spec_helpers.js";

vi.mock("./data/siteConfigApi.js", () => ({
	siteConfigApi: { previewFiscalYear: vi.fn(async () => null), configure: vi.fn(), update: vi.fn() },
}));
vi.mock("./data/procurementSettingsApi.js", () => ({
	procurementSettingsApi: { setReminderThresholdDays: vi.fn(), addFundingSource: vi.fn(), updateFundingSource: vi.fn() },
}));

import AddFiscalYearDialog from "./components/AddFiscalYearDialog.vue";
import FundingSourceEditor from "./components/FundingSourceEditor.vue";
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

// Every artboard, by board. `mount` returns the element to compare, or is
// absent when no component can render the state from props today. `self`
// compares the artboard element itself as a landmark (a dialog artboard IS the
// dialog).
const ARTBOARDS = [
	{ key: "C01#configured", mount: () => mount(ProcuringEntityTab, { props: { site: site() }, global: globalMocks() }) },
	{
		key: "C01#first-run",
		mount: () => mount(ProcuringEntityTab, { props: { site: site({ configured: false, procuring_entity: null, root_unit: null }) }, global: globalMocks() }),
	},
	{ key: "C01#conflict" },
	{ key: "C01#missing-authority" },

	{ key: "C02#overview" },
	{ key: "C02#overview-disabled" },
	{ key: "C02#narrow" },
	{ key: "C02#empty" },
	{ key: "C02#add-year", self: true, select: "#add-year .dialog", mount: () => mount(AddFiscalYearDialog, { global: globalMocks() }) },
	{ key: "C02#detail" },
	{ key: "C02#detail-row-variants" },
	{ key: "C02#disable" },
	{ key: "C02#forms" },
	{ key: "C02#form-states" },

	{ key: "C03A#list" },
	{ key: "C03A#add", self: true, mount: () => mount(FundingSourceEditor, { props: { creating: true }, global: globalMocks() }) },
	{
		key: "C03A#edit",
		self: true,
		mount: () => mount(FundingSourceEditor, { props: { source: { name: "FS-2", label: "Development partner", enabled: true, expected_version: "v1" } }, global: globalMocks() }),
	},
	{ key: "C03A#disabled" },
	{ key: "C03A#duplicate", self: true },
	{ key: "C03A#empty" },

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

describe.each(ARTBOARDS)("$key", ({ key, mount: mountIt, select, self }) => {
	it("is built out of the board's own containers", async () => {
		const queued = REBUILD_QUEUE[key];
		if (!mountIt) {
			expect(queued, `${key}: nothing renders it and it is not queued`).toBeTruthy();
			return;
		}
		const wrapper = mountIt();
		await flushPromises();
		const { file, id } = boardOf(key);
		const board = setupSkeleton(file, select || `#${id}`, { self });
		const built = self ? skeletonOf({ children: [wrapper.element] }) : skeletonOf(wrapper.element);
		const result = compareSkeletons(board, built, { departures: DEPARTURES[key] || [] });
		const message = formatMismatch(key, result);
		if (queued) {
			expect(message, `${key} now matches its board — move it from REBUILD_QUEUE to COVERED`).not.toBe("");
		} else {
			expect(message, message).toBe("");
		}
	});
});
