// Structural fidelity for the Tenders screens against their boards
// (TPR-CHG-001 v0.12, `docs/mvp-1-r1/11_tenders/design/`). Each board variant
// is mounted with its fixture and compared container for container, the
// §10.17 guidance region included (`tendersScope` expands the boards'
// TenderGuidance import); registered departures are the only allowed
// differences.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import { nextTick } from "vue";

import { tendersSkeleton } from "../../../../../../tests/ui/fidelity/board.js";
import { compareSkeletons, formatMismatch, skeletonOf } from "../../../../../../tests/ui/fidelity/skeleton.js";
import { COVERED, DEPARTURES } from "../../../../../../tests/ui/fidelity/departures/tenders.js";

import EditorScreen from "./EditorScreen.vue";
import ReviewScreen from "./ReviewScreen.vue";
import ApprovalScreen from "./ApprovalScreen.vue";
import AuthorisationScreen from "./AuthorisationScreen.vue";
import PublicationScreen from "./PublicationScreen.vue";
import PublishedScreen from "./PublishedScreen.vue";
import ClarificationScreen from "./ClarificationScreen.vue";
import AddendumScreen from "./AddendumScreen.vue";
import { addendumData, approvalData, authorisationData, clarificationData, editorRecord, publicationData, publishedData, reviewData, reviewRecord } from "./fixtures.js";

const DESIGN = "docs/mvp-1-r1/11_tenders/design";

const SCREENS = [
	{ name: "EditorScreen", variant: "TPR-DES-03", board: "Draft - Tender Details.dc.html", label: "TPR-DES-03 Draft Tender details", component: EditorScreen, props: { record: editorRecord(), task: "details" } },
	{ name: "EditorScreen", variant: "TPR-DES-03-PHYSICAL", board: "Draft - Tender Details.dc.html", label: "TPR-DES-03 Draft Tender details", options: { show: ["hasMeeting", "isPhysical"], hide: ["isOnline"] }, component: EditorScreen, props: { record: editorRecord("PHYSICAL"), task: "details" } },
	{ name: "EditorScreen", variant: "TPR-DES-03-ONLINE", board: "Draft - Tender Details.dc.html", label: "TPR-DES-03 Draft Tender details", options: { show: ["hasMeeting", "isOnline"], hide: ["isPhysical"] }, component: EditorScreen, props: { record: editorRecord("ONLINE"), task: "details" } },
	{ name: "EditorScreen", variant: "TPR-DES-04", board: "Draft - Supplier and Contract Requirements.dc.html", label: "TPR-DES-04 Draft supplier and contract requirements", options: { guidance: "turn" }, component: EditorScreen, props: { record: editorRecord(), task: "requirements" } },
	{ name: "EditorScreen", variant: "TPR-DES-04-RETURNED", board: "Draft - Supplier and Contract Requirements.dc.html", label: "TPR-DES-04 Draft supplier and contract requirements", options: { guidance: "turn", show: ["isReturned"] }, component: EditorScreen, props: { record: editorRecord("RETURNED"), task: "requirements" } },
	{ name: "ReviewScreen", variant: "TPR-DES-05", board: "Review and Submit.dc.html", label: "TPR-DES-05 Review and submit", component: ReviewScreen, props: { record: reviewRecord(), review: reviewData() } },
	{ name: "ReviewScreen", variant: "TPR-DES-05-NEEDS-ATTENTION", board: "Review and Submit.dc.html", label: "TPR-DES-05 Review and submit", options: { show: ["isBlocked", "o4"], hide: ["isReady"] }, component: ReviewScreen, props: { record: reviewRecord(), review: reviewData("BLOCKED") } },
	{ name: "ApprovalScreen", variant: "TPR-DES-06", board: "HOPF Approval.dc.html", label: "TPR-DES-06 HOPF approval", component: ApprovalScreen, props: approvalData() },
	{ name: "ApprovalScreen", variant: "TPR-DES-06-SEGREGATION", board: "HOPF Approval.dc.html", label: "TPR-DES-06 HOPF approval", options: { show: ["isSegregation"], hide: ["isNormal"] }, component: ApprovalScreen, props: approvalData("SEGREGATION") },
	{ name: "AuthorisationScreen", variant: "TPR-DES-07", board: "AO Publication Authorisation.dc.html", label: "TPR-DES-07 AO publication authorisation", component: AuthorisationScreen, props: { pub: authorisationData(), requisitionReference: "REQ-MOH-2027-033-001" } },
	{ name: "AuthorisationScreen", variant: "TPR-DES-07-SEGREGATION", board: "AO Publication Authorisation.dc.html", label: "TPR-DES-07 AO publication authorisation", options: { show: ["isSegregation"], hide: ["isNormal"] }, component: AuthorisationScreen, props: { pub: authorisationData("SEGREGATION"), requisitionReference: "REQ-MOH-2027-033-001" } },
	...["", "INVALID", "CONFLICT"].map((v) => {
		const data = publicationData(v);
		return {
			name: "PublicationScreen", variant: `TPR-DES-08${v ? `-${v}` : ""}`, board: "Publication Progress and Evidence.dc.html", label: "TPR-DES-08 Publication confirmation",
			options: v === "INVALID" ? { show: ["isInvalid"], hide: ["isBase", "isNotInvalid", "isConflict"] } : v === "CONFLICT" ? { show: ["isConflict", "isNotInvalid"], hide: ["isBase", "isInvalid"] } : {},
			component: PublicationScreen, props: { pub: data, refusal: data._refusal, conflict: data._conflict },
		};
	}),
	...[["HOPF", "", "turn"], ["AO", "", "turn"], ["PO", "", "turn"], ["READER", "", "none"], ["HOPF", "NO-ADDENDUM", "turn"], ["HOPF", "ENDED", "done"]].map(([role, v, kind]) => ({
		name: "PublishedScreen", variant: `TPR-DES-09-${role}${v ? `-${v}` : ""}`, board: "Published Tender.dc.html", label: "TPR-DES-09 Published Tender",
		options: { guidance: kind, ...(v === "NO-ADDENDUM" ? { show: ["noAddenda"], hide: ["hasAddenda"] } : v === "ENDED" ? { show: ["isEnded"], hide: ["isOpen"] } : {}) },
		component: PublishedScreen, props: publishedData(role, v),
	})),
	{ name: "ClarificationScreen", variant: "TPR-DES-11", board: "Respond to Supplier Clarification.dc.html", label: "TPR-DES-11 Respond to supplier clarification", options: { guidance: "turn" }, component: ClarificationScreen, props: { data: clarificationData() } },
	{ name: "ClarificationScreen", variant: "TPR-DES-11-FAILURE", board: "Respond to Supplier Clarification.dc.html", label: "TPR-DES-11 Respond to supplier clarification", options: { guidance: "blocked", show: ["isFailure"], hide: ["isEditable", "isOrdinary"] }, component: ClarificationScreen, props: { data: clarificationData("FAILURE") } },
	...[
		["DRAFT", "turn", {}],
		["HOPF", "turn", { show: ["isHopf", "showComparison"], hide: ["isDraft"] }],
		["AWAITING", "turn", { show: ["showComparison", "showFacts", "showChannelTable"], hide: ["isDraft", "showDeadlineEdit", "showChannelsPlain"] }],
		["ISSUED", "done", { show: ["showComparison", "showFacts", "showChannelTable"], hide: ["isDraft", "showDeadlineEdit", "showChannelsPlain"] }],
		["MATERIAL", "blocked", { show: ["showComparison", "isMaterialAny"], hide: ["isDraft", "showDeadlineEdit", "showChannelsPlain"] }],
		["MATERIAL-WAIT", "waiting", { show: ["showComparison", "isMaterialAny"], hide: ["isDraft", "showDeadlineEdit", "showChannelsPlain"] }],
		["MATERIAL-CLOSED", "blocked", { show: ["showComparison", "isMaterialAny"], hide: ["isDraft", "showDeadlineEdit", "showChannelsPlain"] }],
	].map(([v, kind, options]) => ({
		name: "AddendumScreen", variant: `TPR-DES-10-${v}`, board: "Prepare and Issue Addendum.dc.html", label: "TPR-DES-10 Prepare and issue addendum",
		options: { guidance: kind, ...options }, component: AddendumScreen, props: { data: addendumData(v), identity: `TDA-0001:${v}` },
	})),
];

describe.each(SCREENS)("$name — the structure $variant carries", ({ name, variant, board, label, options, component, props }) => {
	it("is built out of the board's own elements", async () => {
		const wrapper = mount(component, { props, attachTo: document.body });
		await nextTick();
		await nextTick();
		const result = compareSkeletons(tendersSkeleton(`${DESIGN}/${board}`, label, options || {}), skeletonOf(wrapper.element), {
			departures: DEPARTURES[`${name}#${variant}`] || [],
		});
		const message = formatMismatch(`${name} / ${variant}`, result);
		wrapper.unmount();
		expect(message, message).toBe("");
	}, 30_000);
});

describe("the COVERED claim", () => {
	it("lists exactly the variants this spec compares", () => {
		expect([...COVERED].sort()).toEqual([...new Set(SCREENS.map((s) => `${s.name}#${s.variant}`))].sort());
	});
});
