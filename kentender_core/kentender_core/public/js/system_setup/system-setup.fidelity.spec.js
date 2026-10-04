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
	getMethodProfile: vi.fn(),
	getRegulatoryReferenceVersion: vi.fn(),
	renameRegulatoryReference: vi.fn(),
	createRegulatoryReference: vi.fn(),
	listRegulatoryReferenceVersions: vi.fn(),
	listVerificationHistory: vi.fn(),
	getScheduleProfile: vi.fn(),
	getBusinessDayCalendar: vi.fn(),
	saveRegulatoryReferenceVersion: vi.fn(),
	setReminderThresholdDays: vi.fn(),
	addFundingSource: vi.fn(),
	updateFundingSource: vi.fn(),
	deleteFundingSource: vi.fn(),
}));
vi.mock("./data/procurementSettingsApi.js", () => ({ procurementSettingsApi: settingsApi }));
const orgApi = vi.hoisted(() => ({ getStructure: vi.fn(), getUnit: vi.fn() }));
vi.mock("./data/orgStructureApi.js", () => ({ orgStructureApi: orgApi }));
const uraApi = vi.hoisted(() => ({
	listRows: vi.fn(),
	formOptions: vi.fn(),
	searchUsers: vi.fn(async () => []),
	preview: vi.fn(),
	detail: vi.fn(),
}));
vi.mock("./data/responsibilityApi.js", () => ({ responsibilityApi: uraApi }));

import AddFiscalYearDialog from "./components/AddFiscalYearDialog.vue";
import DisableFiscalYearDialog from "./components/DisableFiscalYearDialog.vue";
import IntakeForm from "./components/IntakeForm.vue";
import FiscalYearsTab from "./tabs/FiscalYearsTab.vue";
import FundingSourceDialog from "./components/FundingSourceDialog.vue";
import ProcurementSettingsTab from "./tabs/ProcurementSettingsTab.vue";
import ReminderSettingCard from "./components/ReminderSettingCard.vue";
import ProcuringEntityTab from "./tabs/ProcuringEntityTab.vue";
import RuleRenameDialog from "./components/RuleRenameDialog.vue";
import RuleVersionDetail from "./components/RuleVersionDetail.vue";
import RuleEditor from "./components/RuleEditor.vue";
import RuleKindFields from "./components/RuleKindFields.vue";
import RuleFormError from "./components/RuleFormError.vue";
import MethodVersionEditor from "./components/MethodVersionEditor.vue";
import SourceCheckScreen from "./components/SourceCheckScreen.vue";
import ScheduleProfileDetail from "./components/ScheduleProfileDetail.vue";
import ScheduleVersionEditor from "./components/ScheduleVersionEditor.vue";
import CalendarDetail from "./components/CalendarDetail.vue";
import CalendarEditor from "./components/CalendarEditor.vue";
import CalendarHistory from "./components/CalendarHistory.vue";
import OrganisationStructureTab from "./tabs/OrganisationStructureTab.vue";
import PromptDialog from "./components/PromptDialog.vue";
import UserResponsibilitiesTab from "./tabs/UserResponsibilitiesTab.vue";
import AssignDialog from "./components/AssignDialog.vue";
import ResponsibilityDetail from "./components/ResponsibilityDetail.vue";
import RevokeDialog from "./components/RevokeDialog.vue";

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
	C05: "C05-Organisation-Structure.dc.html",
	C06: "C06-Users-Responsibilities.dc.html",
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
async function settingsTab(fundingSources, { section = "funding-sources", ...lists } = {}) {
	settingsApi.get.mockResolvedValue({
		outcome: "OK",
		funding_sources: fundingSources,
		method_profiles: [],
		reference_sets: [],
		schedule_profiles: [],
		calendars: [],
		reference_kinds: ["Method eligibility", "Reservation rules", "Exclusive preference", "Preference margins", "Market price index", "Approval applicability", "Publication obligations"],
		verification_statuses: ["Production verification pending", "Verified", "Rejected"],
		...lists,
	});
	const wrapper = mount(ProcurementSettingsTab, {
		props: { route: { tab: "procurement-settings", section, id: "", versionId: "", action: "" } },
		global: globalMocks(),
	});
	await flushPromises();
	return wrapper;
}

// C03BC — the CONFIG specimen: Method eligibility and Reservation rules, each
// Version 1, source check needed, details missing.
const PENDING = "Production verification pending";
const METHOD_RULE = {
	profile: "MPR-OPEN-TENDER-V1",
	procurement_method: "Open Tender",
	version_number: 1,
	status: "Active",
	effective_from: "2027-07-01",
	effective_until: "2028-06-30",
	applicability_basis: "",
	verification_status: PENDING,
	source_instrument: "Public Procurement and Asset Disposal Regulations — source verification pending",
	provision: "",
	source_document: "",
	can_edit: false,
	can_set_validity: false,
	conditions: [],
	details_missing: ["Which date determines the rule to use?", "Provisions", "Conditions and evidence"],
};
const RESERVATION_SET = (hasVersion = true, kind = "Reservation rules", key = "rs-res") => ({
	reference_set: key,
	reference_key: "RESERVATION-RULES",
	reference_kind: kind,
	display_name: kind,
	has_version: hasVersion,
	version: hasVersion
		? { name: "rv-1", version_number: 1, verification_status: PENDING, effective_from: "2027-07-01", effective_until: "2028-06-30", details_missing: ["Instrument"] }
		: null,
});
const rulesTab = (lists) => settingsTab([], { section: "procurement-rules", ...lists });

const RULE_KINDS = ["Method eligibility", "Reservation rules", "Exclusive preference", "Preference margins", "Market price index", "Approval applicability", "Publication obligations"];
const kindCard = (kind) => () =>
	mount(RuleKindFields, { props: { kind, payload: {}, categories: ["Goods", "Works", "Services"], methods: ["Open Tender"] }, global: globalMocks() });
const METHOD_VERSION = {
	...METHOD_RULE,
	verification_status: "Verified",
	conditions: [{ condition_id: "G", kind: "Known fact", description: "Goods", procurement_category: "Goods", minimum_amount: 0, maximum_amount: 0, cumulative_basis: "None", mandatory: true }],
};

// C03D — a pending Reservation rules version with one recorded check.
const CHECK_VERSION = { reference: "rv-1", reference_set: "rs-1", reference_kind: "Reservation rules", display_name: "Reservation rules", version_number: 1, effective_from: "2027-07-01", effective_until: "2028-06-30", verification_status: "Production verification pending", recorded_at: "2026-09-12 10:00:00", recorded_by: "Administrator" };
async function sourceCheck(outcome = "Pending") {
	settingsApi.getRegulatoryReferenceVersion.mockResolvedValue(CHECK_VERSION);
	settingsApi.listRegulatoryReferenceVersions.mockResolvedValue([CHECK_VERSION]);
	settingsApi.listVerificationHistory.mockResolvedValue([
		{ event: "ev-1", outcome: "Pending", source_check_date: "2026-09-12", recorded_at: "2026-09-12 10:00:00", recorded_by: "Administrator", evidence_complete: false, change_reason: "Record the remaining verification work for this reference version." },
	]);
	const wrapper = mount(SourceCheckScreen, { props: { name: "rv-1" }, global: globalMocks() });
	await flushPromises();
	await wrapper.find('[data-testid="kt-sc-result"]').setValue(outcome);
	if (outcome !== "Verified") await wrapper.find('[data-testid="kt-sc-unresolved"]').setValue("The applicable amended source and interpretation have not been established.");
	return wrapper;
}

// C04 — the CONFIG schedule (Open Tender — goods, Version 1) and a calendar.
const MILESTONES = [
	["invitation", "Invitation or advertisement", null, "Statutory"],
	["bid_opening", "Bid opening", 21, ""],
	["evaluation_completion", "Evaluation completion", 30, ""],
	["award_approval", "Tender award approval", 5, "Planning assumption"],
	["award_notification", "Notification of award", 2, "Planning assumption"],
	["contract_signing", "Contract signing", 14, ""],
	["delivery_completion", "Delivery or implementation completion", null, "Source-derived"],
].map(([milestone, label, def, basis], i) => ({ milestone, label, sequence: i + 1, applies: true, counting_rule: "Calendar days", minimum_days: null, maximum_days: null, default_days: def, basis }));
const SCHEDULE = {
	profile: "SPR-OPEN-TENDER-GOODS-V1", profile_name: "Open Tender — goods", procurement_method: "Open Tender", procedure: "Planning example",
	procurement_category: "Goods", version_number: 1, effective_from: "2027-07-01", effective_until: "2028-06-30", applicability_basis: "InvitationDate",
	counting_rule: "Calendar days", calendar: null, estimated_delivery_period_default_days: null, verification_status: "Production verification pending",
	complete: false, gaps: ["bid_opening"], milestones: MILESTONES, can_edit: false, can_set_validity: true, status: "Active",
};
async function scheduleDetail(overrides = {}) {
	settingsApi.getScheduleProfile.mockResolvedValue({ ...SCHEDULE, ...overrides });
	const wrapper = mount(ScheduleProfileDetail, { props: { name: SCHEDULE.profile }, global: globalMocks() });
	await flushPromises();
	return wrapper;
}
const CALENDAR = {
	calendar: "CAL-V1", calendar_name: "", version_number: 1, effective_from: "", effective_until: "", weekend_days: ["Saturday", "Sunday"],
	holidays: [], verification_status: "Production verification pending", source_instrument: "", can_edit: false,
	recorded_at: "2026-09-12 10:00:00", recorded_by: "Administrator", supersedes_version_ids: [],
};
async function calendarView(component, props) {
	settingsApi.getBusinessDayCalendar.mockResolvedValue(CALENDAR);
	settingsApi.listVerificationHistory.mockResolvedValue([]);
	const wrapper = mount(component, { props, global: globalMocks() });
	await flushPromises();
	return wrapper;
}

async function scheduleEditor(props) {
	settingsApi.getScheduleProfile.mockResolvedValue(SCHEDULE);
	const wrapper = mount(ScheduleVersionEditor, {
		props: { methods: ["Open Tender"], categories: ["Goods", "Works", "Services"], milestoneCatalogue: MILESTONES.map(({ milestone, label }) => ({ milestone, label })), ...props },
		global: globalMocks(),
	});
	await flushPromises();
	return wrapper;
}

// Reminders — the saved threshold 7, then an entered value.
async function reminder(entered) {
	const wrapper = mount(ReminderSettingCard, { props: { days: 7 }, global: globalMocks() });
	await wrapper.find('[data-testid="kt-reminder-days"]').setValue(entered);
	return wrapper;
}

// C05/C06 — the AUTH-DES fixtures the boards draw (AUTH v1.9 §13).
const DHP = {
	id: "OU-MOH-DHP",
	name: "Directorate of Digital Health and Policy",
	code: "OU-MOH-DHP",
	status: "Active",
	path: ["Ministry of Health", "Directorate of Digital Health and Policy"],
	descendant_count: 1,
	active_assignments: 2,
	is_root: false,
	actions: { add_child: true, rename: true, deactivate: true, reactivate: false },
};
async function orgTab(result, props = {}) {
	// frappe.ui.Tree draws the rows itself; only the composition around it is
	// the board's (AUTH v1.9 §13.1).
	globalThis.frappe = { ...(globalThis.frappe || {}), ui: { Tree: class { constructor() { this.nodes = {}; this.root_node = null; } } } };
	globalThis.$ = (el) => el;
	orgApi.getStructure.mockResolvedValue(result);
	const wrapper = mount(OrganisationStructureTab, { props: { canRepair: true, ...props }, global: globalMocks() });
	await flushPromises();
	return wrapper;
}
const URA_ROWS = [
	["Grace Wanjiku", "grace.wanjiku", "Departmental Author", "Digital Health", "This unit only", "Permanent", "From now · No scheduled end", "Active"],
	["Dr Peter Kimani", "peter.kimani", "Head of User Department", "Human Resources Management and Development", "This unit only", "Permanent", "From now · No scheduled end", "Active"],
	["Julia Njeri", "julia.njeri", "Head of User Department", "Digital Health", "This unit only", "Acting", "1 Oct 2026 – 30 Nov 2026", "Scheduled"],
	["Mercy Kilonzo", "mercy.kilonzo", "Procurement Planner", "Site-wide", "Entire entity", "Permanent", "From now · No scheduled end", "Active"],
	["Samuel Otieno", "samuel.otieno", "Head of User Department", "Directorate of Digital Health and Policy", "This unit and 1 descendant", "Permanent", "From 1 Jan 2026 · Until 31 Aug 2026", "Expired"],
].map(([name, login, role, scope, coverage, appointment, period, status], index) => ({
	assignment: `URA-2026-000${index + 1}`,
	user_full_name: name,
	user: `${login}@moh.example.test`,
	business_role: role,
	scope_label: scope,
	coverage,
	appointment_type: appointment,
	period_label: period,
	status,
}));
const URA_OPTIONS = {
	responsibilities: [
		{ business_role: "Departmental Author", scope_type: "Organisation Unit", requires_organisation_unit: true },
		{ business_role: "Head of User Department", scope_type: "Organisation Unit", requires_organisation_unit: true },
	],
	organisation_units: [
		{ id: "OU-MOH-DHI", label: "Digital Health", path_label: "Ministry of Health › Directorate of Digital Health and Policy › Digital Health" },
		{ id: "OU-MOH-DHP", label: "Directorate of Digital Health and Policy", path_label: "Ministry of Health › Directorate of Digital Health and Policy" },
	],
	statuses: ["Active", "Scheduled", "Expired", "Revoked"],
};
async function uraTab({ rows = URA_ROWS, listRows, props = {} } = {}) {
	uraApi.formOptions.mockResolvedValue(URA_OPTIONS);
	if (listRows) uraApi.listRows.mockImplementation(listRows);
	else uraApi.listRows.mockResolvedValue({ rows, total: rows.length });
	const wrapper = mount(UserResponsibilitiesTab, { props, global: globalMocks() });
	await flushPromises();
	return wrapper;
}
const GRACE = {
	assignment: "URA-2026-0001",
	user: "grace.wanjiku@moh.example.test",
	user_full_name: "Grace Wanjiku",
	business_role: "Departmental Author",
	scope_type: "Organisation Unit",
	organisation_unit: "OU-MOH-DHI",
	organisation_unit_path: "Ministry of Health › Directorate of Digital Health and Policy › Digital Health",
	organisation_unit_label: "Digital Health",
	coverage: "This unit only",
	appointment_type: "Permanent",
	authority_reference: "",
	effective_from: "",
	effective_to: "",
	effective_label: "From 1 Sep 2026, 09:00 EAT · No scheduled end",
	status: "Active",
	assigned_by: "Administrator",
	assigned_at_label: "1 Sep 2026, 09:00 EAT",
	can_edit: false,
	can_revoke: true,
	expected_version: "v1",
	history: [{ when: "1 Sep 2026, 09:00 EAT", actor: "Administrator", event: "Responsibility assigned", detail: "", changes: [] }],
	diagnostics: { required_projection: ["Departmental Author"], projection_present: true, projection_missing: [], projection_orphaned: [], coverage: "This unit only", overlapping: [], obsolete_rows: {} },
};
const JULIA = {
	...GRACE,
	assignment: "URA-2026-0003",
	user: "julia.njeri@moh.example.test",
	user_full_name: "Julia Njeri",
	business_role: "Head of User Department",
	appointment_type: "Acting",
	authority_reference: "MOH/HR/ACT/2026/041",
	effective_from: "2026-10-01 00:00:00",
	effective_to: "2026-11-30 23:59:59",
	effective_label: "1 Oct 2026, 00:00 EAT – 30 Nov 2026, 23:59 EAT",
	status: "Scheduled",
	assigned_at_label: "1 Sep 2026, 10:05 EAT",
	can_edit: true,
	history: [{ when: "1 Sep 2026, 10:05 EAT", actor: "Administrator", event: "Responsibility assigned", detail: "", changes: [] }],
	diagnostics: { ...GRACE.diagnostics, required_projection: ["Head of User Department"], projection_present: false },
};
function assignDialog(props, preview) {
	uraApi.preview.mockResolvedValue(preview);
	return mount(AssignDialog, { props: { responsibilities: URA_OPTIONS.responsibilities, organisationUnits: URA_OPTIONS.organisation_units, ...props }, global: globalMocks() });
}
const SUMMARY = (sentence, extra = {}) => ({ ok: true, problems: [], conflict: null, summary: sentence, descendant_count: 0, ...extra });

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

	{
		key: "C03BC#list",
		select: "#list > div:first-child",
		live: '[data-testid="kt-procset-rules"]',
		mount: () => rulesTab({ method_profiles: [METHOD_RULE], reference_sets: [RESERVATION_SET()] }),
	},
	// The board draws four specimen cards under the list; no one screen shows
	// all four, so each is compared on its own (`~` names a card inside #list).
	{
		key: "C03BC#list~empty",
		self: true,
		select: "#list > div:nth-child(2) > :nth-child(1)",
		live: '[data-testid="kt-procset-rules-empty"]',
		mount: () => rulesTab({}),
	},
	{
		key: "C03BC#list~no-version",
		self: true,
		select: "#list > div:nth-child(2) > :nth-child(2)",
		live: '[data-testid="kt-procset-rule-noversion-rs-res"]',
		mount: () => rulesTab({ reference_sets: [RESERVATION_SET(false)] }),
	},
	{
		key: "C03BC#list~partial",
		self: true,
		select: "#list > div:nth-child(2) > :nth-child(3)",
		live: '[data-testid="kt-procset-rule-partial"]',
		mount: async () => {
			settingsApi.createRegulatoryReference.mockResolvedValue({ reference_set: "rs-new" });
			settingsApi.saveRegulatoryReferenceVersion.mockRejectedValueOnce(new Error("Enter the obligation code."));
			const wrapper = mount(RuleEditor, { props: { kinds: RULE_KINDS }, global: globalMocks() });
			await wrapper.find('[data-testid="kt-rule-name"]').setValue("Reservation rules");
			await wrapper.find('[data-testid="kt-rule-key"]').setValue("RES");
			await wrapper.find('[data-testid="kt-rule-from"]').setValue("2027-07-01");
			await wrapper.find('[data-testid="kt-rule-save"]').trigger("click");
			await flushPromises();
			return wrapper;
		},
	},
	{
		key: "C03BC#list~not-published",
		self: true,
		select: "#list > div:nth-child(2) > :nth-child(4)",
		live: '[data-testid="kt-procset-rule-unpublished-rs-mpi"]',
		mount: () => rulesTab({ reference_sets: [RESERVATION_SET(false, "Market price index", "rs-mpi")] }),
	},
	{
		key: "C03BC#detail",
		select: "#detail > div",
		live: '[data-testid="kt-procset-rule-card"]',
		mount: async () => {
			settingsApi.getMethodProfile.mockResolvedValue(METHOD_RULE);
			const wrapper = mount(RuleVersionDetail, { props: { name: "MPR-OPEN-TENDER-V1", kind: "method" }, global: globalMocks() });
			await flushPromises();
			return wrapper;
		},
	},
	{
		key: "C03BC#rename",
		self: true,
		select: "#rename .dialog",
		live: ".kt-dialog",
		mount: () => mount(RuleRenameDialog, { props: { referenceSet: "rs-me", name: "Method eligibility" }, global: globalMocks() }),
	},
	{
		key: "C03BC#add",
		select: "#add > div",
		live: '[data-testid="kt-procset-rule-editor"]',
		mount: () => mount(RuleEditor, { props: { kinds: RULE_KINDS, entityTypes: ["National Government Ministry", "County Government", "State Corporation"], categories: ["Goods", "Works", "Services"] }, global: globalMocks() }),
	},
	// One card per kind; Method eligibility keeps its own model and editor (D21).
	{ key: "C03BC#kinds~method" },
	{ key: "C03BC#kinds~reservation", self: true, select: "#kinds .card:nth-child(2)", live: '[data-testid="kt-rule-kind-fields"]', mount: kindCard("Reservation rules") },
	{ key: "C03BC#kinds~exclusive", self: true, select: "#kinds .card:nth-child(3)", live: '[data-testid="kt-rule-kind-fields"]', mount: kindCard("Exclusive preference") },
	{ key: "C03BC#kinds~margins", self: true, select: "#kinds .card:nth-child(4)", live: '[data-testid="kt-rule-kind-fields"]', mount: kindCard("Preference margins") },
	{ key: "C03BC#kinds~price-index", self: true, select: "#kinds .card:nth-child(5)", live: '[data-testid="kt-rule-kind-fields"]', mount: kindCard("Market price index") },
	{ key: "C03BC#kinds~approval", self: true, select: "#kinds .card:nth-child(6)", live: '[data-testid="kt-rule-kind-fields"]', mount: kindCard("Approval applicability") },
	{ key: "C03BC#kinds~publication", self: true, select: "#kinds .card:nth-child(7)", live: '[data-testid="kt-rule-kind-fields"]', mount: kindCard("Publication obligations") },
	{
		key: "C03BC#version",
		select: "#version > div",
		live: '[data-testid="kt-mve-card"]',
		mount: async () => {
			settingsApi.getMethodProfile.mockResolvedValue(METHOD_VERSION);
			const wrapper = mount(MethodVersionEditor, { props: { name: "MPR-OPEN-TENDER-V1", conditionKinds: ["Known fact"], cumulativeBases: ["None"] }, global: globalMocks() });
			await flushPromises();
			return wrapper;
		},
	},
	{
		key: "C03BC#states~read-only",
		self: true,
		select: "#states > div > :nth-child(1)",
		live: '[data-testid="kt-procset-rule-readonly"]',
		mount: async () => {
			settingsApi.getMethodProfile.mockResolvedValue(METHOD_RULE);
			const wrapper = mount(RuleVersionDetail, { props: { name: "MPR-OPEN-TENDER-V1", kind: "method" }, global: globalMocks() });
			await flushPromises();
			return wrapper;
		},
	},
	{ key: "C03BC#states~no-coverage" },
	{
		key: "C03BC#states~overlap",
		self: true,
		select: "#states > div > :nth-child(3)",
		live: '[data-testid="kt-rule-overlap"]',
		mount: () => mount(RuleFormError, { props: { error: "Select valid earlier versions and check the dates this replacement will cover." }, global: globalMocks(), attachTo: document.body }),
	},
	{
		key: "C03BC#states~stale",
		self: true,
		select: "#states > div > :nth-child(4)",
		live: '[data-testid="kt-rule-stale"]',
		mount: () => mount(RuleFormError, { props: { error: "This record changed after you opened it. Refresh and review the latest version." }, global: globalMocks(), attachTo: document.body }),
	},

	{ key: "C03D#pending", select: "#pending > div", live: '[data-testid="kt-source-check-form"]', mount: () => sourceCheck("Pending") },
	{ key: "C03D#verified", select: "#verified > div", live: '[data-testid="kt-source-check-form"]', mount: () => sourceCheck("Verified") },
	{ key: "C03D#rejected", select: "#rejected > div", live: '[data-testid="kt-source-check-form"]', mount: () => sourceCheck("Rejected") },
	{ key: "C03D#history", select: "#history > div", live: '[data-testid="kt-source-check-history"]', mount: () => sourceCheck("Pending") },
	{ key: "C03D#evidence" },

	{
		key: "C04#list",
		select: "#list > div:first-child",
		live: '[data-testid="kt-procset-profiles"]',
		mount: () => settingsTab([], { section: "schedule-profiles", schedule_profiles: [SCHEDULE] }),
	},
	{
		key: "C04#list~empty",
		self: true,
		select: "#list > div:nth-child(2)",
		live: '[data-testid="kt-procset-profiles-empty"]',
		mount: () => settingsTab([], { section: "schedule-profiles" }),
	},
	{ key: "C04#detail", select: "#detail > div", live: '[data-testid="kt-procset-profile-table"]', mount: () => scheduleDetail() },
	// C04 #add draws the add form's identity (as a dialog) and the new-version
	// footer (as a card); the editor is one page holding both (DEPARTURES).
	{
		key: "C04#add~identity",
		self: true,
		select: "#add .dialog .dialog-body > div",
		live: '[data-testid="kt-sve-identity"]',
		mount: () => scheduleEditor({ name: "", mode: "create" }),
	},
	{
		key: "C04#add~version-footer",
		self: true,
		select: "#add .card > .field",
		live: '[data-testid="kt-sve-replacement"] .kt-field',
		mount: () => scheduleEditor({ name: SCHEDULE.profile, mode: "version" }),
	},
	{
		key: "C04#detail~selected-interval",
		self: true,
		select: '#detail > div > div[style*="grid-template-columns"]',
		live: '[data-testid="kt-sve-selected"]',
		mount: async () => {
			const wrapper = await scheduleEditor({ name: SCHEDULE.profile, mode: "version" });
			await wrapper.find('[data-testid="kt-sve-select-contract_signing"]').trigger("click");
			return wrapper;
		},
	},
	{
		key: "C04#calendar~working-days",
		select: "#calendar > div:nth-child(1)",
		live: '[data-testid="kt-procset-profile-calendar"]',
		mount: () => scheduleDetail({ counting_rule: "Working days", calendar: null, gaps: ["working_day_calendar"] }),
	},
	{ key: "C04#calendar~editor", select: "#calendar > div:nth-child(2)", live: '[data-testid="kt-calendar-editor"]', mount: () => calendarView(CalendarEditor, { mode: "create" }) },
	{ key: "C04#calendar-detail", select: "#calendar-detail > div", live: '[data-testid="kt-calendar-detail"]', mount: () => calendarView(CalendarDetail, { name: "CAL-V1" }) },
	{ key: "C04#calendar-version", select: "#calendar-version > div", live: '[data-testid="kt-calendar-editor"]', mount: () => calendarView(CalendarEditor, { mode: "version", name: "CAL-V1" }) },
	{
		key: "C04#calendar-history",
		select: "#calendar-history > div",
		live: '[data-testid="kt-calendar-history"]',
		mount: () => calendarView(CalendarHistory, { name: "CAL-V1", calendarVersions: [{ ...CALENDAR }] }),
	},

	{ key: "Reminders#unchanged", mount: () => mount(ReminderSettingCard, { props: { days: 7 }, global: globalMocks() }) },
	{ key: "Reminders#edited", mount: () => reminder("14") },
	{ key: "Reminders#zero", mount: () => reminder("0") },
	{ key: "Reminders#invalid", mount: () => reminder("400") },

	// Common-States: the Procurement settings tab draws these three states with
	// the same markup as the page (SystemSetup.spec proves the page's own,
	// heading hidden).
	{
		key: "Common#loading",
		self: true,
		select: "#loading .kt-empty",
		live: '[data-testid="kt-procset-loading"]',
		mount: () => {
			settingsApi.get.mockImplementation(() => new Promise(() => {}));
			return mount(ProcurementSettingsTab, { props: { route: { tab: "procurement-settings", section: "", id: "", versionId: "", action: "" } }, global: globalMocks() });
		},
	},
	{
		key: "Common#denied",
		self: true,
		select: "#denied .kt-notice",
		live: '[data-testid="kt-procset-forbidden"]',
		mount: async () => {
			settingsApi.get.mockResolvedValue({ outcome: "FORBIDDEN" });
			const wrapper = mount(ProcurementSettingsTab, { props: { route: { tab: "procurement-settings", section: "", id: "", versionId: "", action: "" } }, global: globalMocks() });
			await flushPromises();
			return wrapper;
		},
	},
	{
		key: "Common#load-error",
		select: "#load-error > div:nth-child(2)",
		live: '[data-testid="kt-procset-error"]',
		mount: async () => {
			settingsApi.get.mockRejectedValue(new Error("boom"));
			const wrapper = mount(ProcurementSettingsTab, { props: { route: { tab: "procurement-settings", section: "", id: "", versionId: "", action: "" } }, global: globalMocks() });
			await flushPromises();
			return wrapper;
		},
	},

	// C05 — Organisation structure (AUTH-DES-01/02/08, CFG §10.12).
	{
		key: "C05#auth-des-01",
		live: '[data-testid="kt-setup-org"]',
		mount: () => orgTab({ state: "ready", root: "OU-MOH", tree: [{ unit_code: "PE-MOH", status: "Active", name: "Ministry of Health" }], selected: DHP }),
	},
	{
		key: "C05#auth-des-02",
		self: true,
		select: "#auth-des-02 .dialog",
		live: '[data-testid="kt-ou-prompt"]',
		mount: () => mount(PromptDialog, {
			props: {
				title: "Add organisation unit",
				label: "Organisation unit name",
				confirmLabel: "Add organisation unit",
				modelValue: "Health Information Systems",
				context: [{ label: "Parent organisation unit", value: "Ministry of Health › Directorate of Digital Health and Policy" }],
				hint: "The unit code is generated when you save.",
			},
			global: globalMocks(),
		}),
	},
	{
		key: "C05#auth-des-08-empty",
		live: '[data-testid="kt-setup-org"]',
		mount: () => orgTab({ state: "empty_root", root: "OU-MOH", tree: [], selected: { ...DHP, id: "OU-MOH", name: "Ministry of Health", is_root: true } }),
	},
	{ key: "C05#auth-des-08-root-admin", live: '[data-testid="kt-setup-org"]', mount: () => orgTab({ state: "needs_repair", tree: [] }) },
	{ key: "C05#auth-des-08-root-sm", live: '[data-testid="kt-setup-org"]', mount: () => orgTab({ state: "needs_repair", tree: [] }, { canRepair: false }) },
	{ key: "C05#auth-des-08-ambiguous", live: '[data-testid="kt-setup-org"]', mount: () => orgTab({ state: "ambiguous", tree: [], conflicts: [] }) },

	// C06 — Users and responsibilities (AUTH-DES-03–08).
	{ key: "C06#auth-des-03", live: '[data-testid="kt-setup-ura"]', mount: () => uraTab() },
	{
		key: "C06#auth-des-04",
		self: true,
		select: "#auth-des-04 .dialog",
		live: '[data-testid="kt-ura-assign"]',
		mount: async () => {
			const wrapper = assignDialog({}, SUMMARY("Grace Wanjiku will be Departmental Author for Digital Health from now with no scheduled end."));
			await flushPromises();
			await wrapper.find('[data-testid="kt-ura-role"]').setValue("Departmental Author");
			await flushPromises();
			return wrapper;
		},
	},
	{
		key: "C06#auth-des-05",
		self: true,
		select: "#auth-des-05 .dialog",
		live: '[data-testid="kt-ura-assign"]',
		mount: async () => {
			const wrapper = assignDialog(
				{ editing: null },
				SUMMARY("Julia Njeri will be Head of User Department for Directorate of Digital Health and Policy from 1 Oct 2026 until 30 Nov 2026.", {
					ok: false,
					descendant_count: 1,
					conflict: { heading: "This office is already held", message: "Dr Peter Kimani holds Head of User Department for this scope until 30 Nov 2026. Revoke that assignment before creating an overlapping one." },
				})
			);
			await flushPromises();
			await wrapper.find('[data-testid="kt-ura-role"]').setValue("Head of User Department");
			await wrapper.find('[data-testid="kt-ura-appointment-acting"]').setValue(true);
			await flushPromises();
			return wrapper;
		},
	},
	{ key: "C06#auth-des-06", live: '[data-testid="kt-ura-detail"]', mount: () => mount(ResponsibilityDetail, { props: { assignment: GRACE }, global: globalMocks() }) },
	{
		key: "C06#auth-des-07",
		self: true,
		select: "#auth-des-07 .dialog",
		live: '[data-testid="kt-ura-revoke"]',
		mount: () => mount(RevokeDialog, { props: { assignment: GRACE }, global: globalMocks() }),
	},
	{ key: "C06#auth-des-06-scheduled", live: '[data-testid="kt-ura-detail"]', mount: () => mount(ResponsibilityDetail, { props: { assignment: JULIA }, global: globalMocks() }) },
	{
		key: "C06#auth-edit-scheduled",
		self: true,
		select: "#auth-edit-scheduled .dialog",
		live: '[data-testid="kt-ura-assign"]',
		mount: async () => {
			const wrapper = assignDialog({ editing: JULIA }, SUMMARY("Julia Njeri will be Head of User Department for Digital Health from 1 Oct 2026 until 30 Nov 2026."));
			await flushPromises();
			return wrapper;
		},
	},
	{
		key: "C06#auth-changed-history",
		live: '[data-testid="kt-ura-detail"]',
		mount: () => mount(ResponsibilityDetail, {
			props: {
				assignment: {
					...JULIA,
					history: [
						{ when: "1 Sep 2026, 10:30 EAT", actor: "Administrator", event: "Scheduled assignment changed", changes: ["Effective to: 30 Nov 2026, 23:59 EAT → 31 Dec 2026, 23:59 EAT"] },
						...JULIA.history,
					],
				},
			},
			global: globalMocks(),
		}),
	},
	{ key: "C06#auth-des-08~loading", select: "#auth-des-08 > div > div:nth-child(1)", live: '[data-testid="kt-setup-ura"]', mount: () => uraTab({ listRows: () => new Promise(() => {}) }) },
	{ key: "C06#auth-des-08~empty", select: "#auth-des-08 > div > div:nth-child(2)", live: '[data-testid="kt-setup-ura"]', mount: () => uraTab({ rows: [] }) },
	{
		key: "C06#auth-des-08~forbidden",
		select: "#auth-des-08 > div > div:nth-child(3)",
		live: '[data-testid="kt-setup-ura"]',
		mount: () => uraTab({ listRows: () => Promise.reject(Object.assign(new Error("no"), { httpStatus: 403 })) }),
	},
	{
		key: "C06#auth-des-08~error",
		select: "#auth-des-08 > div > div:nth-child(4)",
		live: '[data-testid="kt-setup-ura"]',
		mount: () => uraTab({ listRows: () => Promise.reject(new Error("boom")) }),
	},
];

function boardOf(key) {
	const [board, id] = key.split("#");
	return { file: `${D}${BOARDS[board]}`, id };
}

describe("System setup board inventory", () => {
	it("assigns every artboard every CFG board draws — none silently unbuilt", () => {
		// `board#id~card` compares one specimen card inside a drawn artboard.
		const listed = new Set(ARTBOARDS.map((a) => a.key.split("~")[0]));
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
		// The compared element may be the component's own root.
		const root = live ? (wrapper.element.matches?.(live) ? wrapper.element : wrapper.element.querySelector(live)) : wrapper.element;
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
