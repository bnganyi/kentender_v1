// Structural fidelity for the Procurement Requisitions screens against
// `design/Requisitions - Design Board v2.dc.html` (REQ-CHG-001 v1.11 §13).
// Each drawn variant is mounted with its board fixture and compared container
// for container; registered departures are the only allowed differences.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";

import { boardSkeleton, requisitionsScope } from "../../../../../../tests/ui/fidelity/board.js";
import { compareSkeletons, formatMismatch, skeletonOf } from "../../../../../../tests/ui/fidelity/skeleton.js";
import { COVERED, DEPARTURES } from "../../../../../../tests/ui/fidelity/departures/procurement-requisitions.js";

import AddLaptopDialog from "./AddLaptopDialog.vue";
import AuthoriseDialog from "./AuthoriseDialog.vue";
import AuthorisedScreen from "./AuthorisedScreen.vue";
import DepartmentTaskScreen from "./DepartmentTaskScreen.vue";
import ProcurementTaskScreen from "./ProcurementTaskScreen.vue";
import EditorScreen from "./EditorScreen.vue";
import RequestDetailsTask from "./RequestDetailsTask.vue";
import RequirementsTask from "./RequirementsTask.vue";
import ReviewTask from "./ReviewTask.vue";
import ReasonDialog from "./shared/ReasonDialog.vue";
import StartDialog from "./StartDialog.vue";
import StoppedScreen from "./StoppedScreen.vue";
import VersionScreen from "./VersionScreen.vue";
import WorkspaceScreen from "./WorkspaceScreen.vue";
import { authorised, context, departmentTask, editor, procurementTask, requirements, review, startPreview, stopped, versionReview, workspace } from "./fixtures.js";

const BOARD = "docs/mvp-1-r1/06_requisitions/design/Requisitions - Design Board v2.dc.html";
const FILTERS = { search: "", status: "", department: "", fiscal_year: "" };

const SCREENS = [
	{ name: "WorkspaceScreen", variant: "REQ-DES-01", component: WorkspaceScreen, props: { workspace: workspace(), filters: FILTERS } },
	{ name: "WorkspaceScreen", variant: "REQ-DES-01-DRAFT", component: WorkspaceScreen, props: { workspace: workspace("DRAFT"), filters: FILTERS } },
	{ name: "WorkspaceScreen", variant: "REQ-DES-01-ACTION", component: WorkspaceScreen, props: { workspace: workspace("ACTION"), filters: FILTERS } },
	{ name: "WorkspaceScreen", variant: "REQ-DES-01-NONE", component: WorkspaceScreen, props: { workspace: workspace("NONE"), filters: FILTERS } },
	{ name: "WorkspaceScreen", variant: "REQ-DES-01-TECHNICAL", component: WorkspaceScreen, props: { workspace: workspace("TECHNICAL"), filters: FILTERS } },
	{ name: "StartDialog", variant: "REQ-DES-02", component: StartDialog, props: { preview: startPreview() } },
	{ name: "StartDialog", variant: "REQ-DES-02-UNSUPPORTED", component: StartDialog, props: { preview: startPreview("unsupported") } },
	{ name: "StartDialog", variant: "REQ-DES-02-RULE-UNAVAILABLE", component: StartDialog, props: { preview: startPreview("rule_unavailable") } },
	{ name: "StartDialog", variant: "REQ-DES-02-RESERVATION-UNSUPPORTED", component: StartDialog, props: { preview: startPreview("reservation_unsupported") } },
	{ name: "EditorScreen", variant: "REQ-DES-03", component: EditorScreen, props: { view: editor() } },
	{ name: "RequestDetailsTask", variant: "Purchase and source details", component: RequestDetailsTask, props: { view: editor(), focusSection: "source_details" }, pick: ".kt-disclosure-body" },
	{ name: "RequestDetailsTask", variant: "REQ-DES-03-COMPLETE", component: RequestDetailsTask, props: { view: editor("COMPLETE") }, pick: '[data-section="equipment"]' },
	{ name: "EditorScreen", variant: "REQ-DES-03-RETURNED", component: EditorScreen, props: { view: editor("RETURNED") }, pick: '[data-testid="req-returned"]' },
	{ name: "RequestDetailsTask", variant: "REQ-DES-03-CONTRIBUTOR", component: RequestDetailsTask, props: { view: editor("CONTRIBUTOR") }, saved: true },
	{ name: "AddLaptopDialog", variant: "REQ-DES-04", component: AddLaptopDialog, props: { view: editor() } },
	{ name: "AddLaptopDialog", variant: "REQ-DES-04-ONE-SOURCE", component: AddLaptopDialog, props: { view: { ...editor(), equipment: { ...editor().equipment, add_rows: [editor().equipment.add_rows[1]] } } } },
	{
		name: "AddLaptopDialog", variant: "REQ-DES-04-VALIDATION", component: AddLaptopDialog, props: { view: editor() },
		error: { label: "add-items", code: "REQ_BATCH_ITEM_INVALID", message: "Requested equipment quantity for Digital Health is 140 Each but the approved requirement requests 150 Each", detail: { rows: { "RDL-002": "Must be 150 Each" } } },
	},
	{ name: "EditorScreen", variant: "REQ-DES-05", component: EditorScreen, props: { view: requirements() } },
	{ name: "RequirementsTask", variant: "REQ-DES-05-COMPLETE", component: RequirementsTask, props: { view: requirements("COMPLETE") }, pick: ".req-workbench" },
	{ name: "ReviewTask", variant: "REQ-DES-06", component: ReviewTask, props: { view: review() } },
	{ name: "ReviewTask", variant: "REQ-DES-06-DIRECT-HOD", component: ReviewTask, props: { view: review("DIRECT-HOD") }, pick: [".kt-notice.is-live", ".req-footer"] },
	{
		name: "ReasonDialog", variant: "Withdraw requisition dialog", component: ReasonDialog,
		props: { title: "Withdraw this requisition?", confirmLabel: "Withdraw requisition", placeholder: "State why this requisition is being withdrawn", notice: "The requisition will close without using approved-plan amounts or reserving funding.", noticeTone: "warning", danger: true },
	},
	{ name: "DepartmentTaskScreen", variant: "REQ-DES-07", component: DepartmentTaskScreen, props: { view: departmentTask() } },
	{
		name: "ReasonDialog", variant: "Return dialog", component: ReasonDialog,
		props: { title: "Return this requisition for correction?", reasonLabel: "Correction required (20–1,000 characters)", hint: "State what must change and identify the affected section.", confirmLabel: "Return for correction", sections: ["Technical requirements"] },
	},
	{ name: "ProcurementTaskScreen", variant: "REQ-DES-08", component: ProcurementTaskScreen, props: { view: procurementTask() } },
	{ name: "ProcurementTaskScreen", variant: "Procurement checks", component: ProcurementTaskScreen, props: { view: { ...procurementTask(), checks: { ...procurementTask().checks, open: true } } }, pick: '[data-testid="req-checks"] table' },
	{ name: "ProcurementTaskScreen", variant: "REQ-DES-08-BLOCKING-FUNDING", component: ProcurementTaskScreen, props: { view: procurementTask("BLOCKING-FUNDING") }, pick: [".kt-notice", '[data-testid="req-shortfall"]', ".req-footer .req-actions"] },
	{ name: "ProcurementTaskScreen", variant: "REQ-DES-08-HOLD", component: ProcurementTaskScreen, props: { view: procurementTask("HOLD") }, pick: [".kt-notice", ".req-footer .req-actions"] },
	{ name: "ProcurementTaskScreen", variant: "REQ-DES-08-TECHNICAL", component: ProcurementTaskScreen, props: { view: procurementTask("TECHNICAL") }, pick: [".kt-notice"] },
	{
		name: "ReasonDialog", variant: "Return-to-department dialog", component: ReasonDialog,
		props: { title: "Return this requisition to the department?", reasonLabel: "Correction required (20–1,000 characters)", confirmLabel: "Return to department", notice: "The submitted Version will remain in history and a copied Draft will open for correction.", sections: ["Request details"] },
	},
	{
		name: "ReasonDialog", variant: "Change-submitting-department dialog", component: ReasonDialog,
		props: { title: "Change submitting department and return?", optionLabel: "Submitting department", options: [{ value: "a", label: "Human Resources Management and Development" }], reasonLabel: "Reason (required, 20–500 characters)", max: 500, confirmLabel: "Confirm change and return", notice: "The current submission will remain in history. A copied Draft must be certified by the new submitting department before authorisation." },
	},
	{ name: "ReasonDialog", variant: "REQ-DES-08-CORRECTION", component: ReasonDialog, props: { title: "Request a Planning correction?", reasonLabel: "What is wrong in the approved plan? (required, 20–1,000 characters)", confirmLabel: "Send correction request", notice: "This requisition will be preserved and stopped. It will not reopen automatically after Planning responds.", noticeTone: "warning" } },
	{ name: "AuthoriseDialog", variant: "REQ-DES-09", component: AuthoriseDialog, props: { confirmation: procurementTask().confirmation } },
	{ name: "AuthorisedScreen", variant: "REQ-DES-10", component: AuthorisedScreen, props: { view: authorised() }, open: '[data-testid="req-record-details"] summary' },
	{ name: "AuthorisedScreen", variant: "HOPF before consumption", component: AuthorisedScreen, props: { view: authorised("HOPF") }, pick: [".req-footer"] },
	{ name: "AuthorisedScreen", variant: "Consumed", component: AuthorisedScreen, props: { view: authorised("CONSUMED") }, pick: [".kt-notice.is-live"] },
	{ name: "AuthorisedScreen", variant: "Revoked", component: AuthorisedScreen, props: { view: authorised("REVOKED") }, pick: ['[data-testid="req-revoked"]'] },
	{ name: "ReasonDialog", variant: "Revocation dialog", component: ReasonDialog, props: { title: "Revoke this authorisation?", confirmLabel: "Revoke authorisation", bodyText: "The approved-plan amounts and both funding reservations will be reversed. The authorised requisition will remain in history.", danger: true } },
	{ name: "StoppedScreen", variant: "Planning correction requested", component: StoppedScreen, props: { view: stopped() } },
	{ name: "StoppedScreen", variant: "Outcome unavailable", component: StoppedScreen, props: { view: stopped("UNAVAILABLE") }, pick: [".kt-notice.is-critical"] },
	{ name: "StoppedScreen", variant: "Another request unresolved", component: StoppedScreen, props: { view: stopped("ANOTHER") }, pick: [".kt-notice.is-warning"] },
	{ name: "StoppedScreen", variant: "Fresh-start confirmation · Resolved", component: StoppedScreen, props: { view: stopped("RESOLVED") }, click: '[data-testid="req-start-new"]' },
	{ name: "VersionScreen", variant: "Returned reviewed Version", component: VersionScreen, props: { view: versionReview() } },
];

// A dialog's backdrop is the overlay the board leaves out (it draws the
// dialog on the canvas); compare the dialog itself.
// A variant frame that draws one region of its parent is compared with that
// region of the mounted screen (`pick`).
function built(wrapper, pick) {
	if (Array.isArray(pick)) {
		return { children: pick.map((selector) => {
			const region = wrapper.element.querySelector(selector);
			if (!region) throw new Error(`${selector} is not rendered`);
			return region;
		}) };
	}
	if (pick) {
		const region = wrapper.element.querySelector(pick);
		if (!region) throw new Error(`${pick} is not rendered`);
		return region.classList.contains("kt-disclosure-body") ? region : { children: [region] };
	}
	const dialog = wrapper.element.querySelector && wrapper.element.querySelector(".dialog");
	return dialog ? { children: [dialog] } : wrapper.element;
}

describe.each(SCREENS)("$name — the structure $variant carries", ({ name, variant, component, props, pick, error, saved, open, click }) => {
	it("is built out of the board's own elements", async () => {
		window.sessionStorage.clear();
		const { global, ctx } = context({ api: { saveSummary: async () => ({ ok: true }) } });
		if (error) ctx.commandError.value = error;
		const wrapper = mount(component, { props, global });
		if (open) {
			await wrapper.find(open).trigger("click");
			wrapper.find(open).element.parentElement.open = true;
			wrapper.find(open).element.parentElement.dispatchEvent(new Event("toggle"));
			await new Promise((r) => setTimeout(r, 0));
		}
		if (click) {
			await wrapper.find(click).trigger("click");
		}
		if (saved) {
			await wrapper.find('[data-testid="req-save"]').trigger("click");
			await new Promise((r) => setTimeout(r, 0));
		}
		const result = compareSkeletons(boardSkeleton(BOARD, variant, requisitionsScope), skeletonOf(built(wrapper, pick)), {
			departures: DEPARTURES[`${name}#${variant}`] || [],
		});
		const message = formatMismatch(`${name} / ${variant}`, result);
		expect(message, message).toBe("");
	}, 30_000); // the first comparison parses the whole board
});

describe("the COVERED claim", () => {
	it("lists exactly the variants this spec compares", () => {
		expect([...COVERED].sort()).toEqual([...new Set(SCREENS.map((s) => `${s.name}#${s.variant}`))].sort());
	});
});

describe("the shared vocabulary, on every screen", () => {
	it.each(SCREENS)("$name $variant never puts an editable control inside a read-only fact", ({ component, props }) => {
		const { global } = context();
		const wrapper = mount(component, { props, global });
		for (const fact of wrapper.element.querySelectorAll(".kt-meta-value")) {
			expect(fact.querySelector("input, select, textarea")).toBeNull();
		}
	});
});
