/**
 * UI-HARD-1630 — Readiness / approval / publication UI smoke (pack §21 ticket 1630, doc §21.4).
 *
 * Canonical React surfaces under `std-engine` (Vitest / jsdom).
 */
import "@testing-library/jest-dom/vitest";
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ApprovalReviewPackageScreen } from "../approval/pages/ApprovalReviewPackageScreen";
import type { ApprovalReviewPackageScreenProps } from "../approval/pages/approvalReviewPackageScreen.types";
import { PublicationReadinessScreen } from "../readiness/pages/PublicationReadinessScreen";
import type { PublicationReadinessScreenProps } from "../readiness/pages/publicationReadinessScreen.types";
import { PUBLICATION_IMMUTABILITY_WARNING_TEXT } from "../publication/pages/publicationConfirmationScreen.constants";
import { PublicationConfirmationScreen } from "../publication/pages/PublicationConfirmationScreen";
import type { PublicationConfirmationScreenProps } from "../publication/pages/publicationConfirmationScreen.types";
import { PublishedStateSummaryScreen } from "../publication/pages/PublishedStateSummaryScreen";
import type { PublishedStateSummaryScreenProps } from "../publication/pages/publishedStateSummaryScreen.types";

function availabilityOk(action_code: string, requires_confirmation = false) {
	return {
		message: {
			success: true,
			actor_user_code: "Administrator",
			action_code,
			allowed: true,
			message: requires_confirmation ? "Confirm irreversible publication." : "OK",
			required_permission: null,
			risk_level: "Low",
			requires_confirmation,
			audit_on_attempt: false,
		},
	};
}

function readinessProps(): PublicationReadinessScreenProps {
	return {
		tenderCode: "TND-100",
		overallStatus: "Blocked",
		criticalBlockers: [
			{
				message: "Evaluation Rules (DEM) are stale.",
				affectedArea: "Evaluation Rules (DEM)",
				whyItMatters: "Evaluation cannot legally proceed from outdated rules.",
				resolutionAction: "Regenerate outputs, then rerun readiness.",
				stageLinkHref: "/desk/tenders/TND-100/configure-document/works",
				stageLinkLabel: "Works completion",
			},
		],
		warnings: [{ message: "Bundle snapshot is older than latest works save." }],
		completionCategories: [
			{ id: "works", label: "Works completion", status: "Complete" },
			{ id: "outputs", label: "Generated outputs", status: "Incomplete" },
		],
		outputStatuses: [
			{ outputLabel: "Evaluation Rules (DEM)", stale: true, statusLine: "Generated 2026-01-01 — superseded" },
			{ outputLabel: "Submission Rules (DSM)", stale: false, statusLine: "Current" },
		],
		evidenceReadinessSummary: "Evidence pack draft: 12 items linked; 2 placeholders.",
		runReadinessAction: {
			actionCode: "RUN_PUBLICATION_READINESS",
			objectType: "Tender",
			objectCode: "TND-100",
			label: "Run readiness",
			onAllowedClick: vi.fn(),
		},
		nextAction: {
			actionCode: "GENERATE_STD_OUTPUTS",
			objectType: "Tender",
			objectCode: "TND-100",
			label: "Regenerate tender outputs",
			onAllowedClick: vi.fn(),
		},
	};
}

function approvalProps(): ApprovalReviewPackageScreenProps {
	return {
		tenderCode: "TND-200",
		tenderSummaryLines: ["District Health Centre Rehabilitation", "Procuring entity: Ministry of Health"],
		packageReferenceLines: ["PKG-MOH-2026-001 — Rehabilitation of District Health Centre"],
		stdTemplateProfileSummary: ["PPRA Works — Building and Associated Civil Engineering Works — Rev April 2022"],
		readinessStatus: "Ready",
		readinessNarrative: "Last readiness run: 2026-05-10 — no critical blockers.",
		bundlePreviewText: "=== Tender bundle snapshot (read-only) ===\nSection I …",
		outputSummaryLines: ["Bundle: v3 — current", "DSM v2 / DOM v2 / DEM v2 / DCM v1 — aligned with snapshot"],
		boqSummaryLines: ["12 bill items", "Quantities owner: Procuring entity", "No supplier rates in review package"],
		worksRequirementsSummaryLines: ["Drawing register: 8 rows", "Environmental / social: submitted"],
		warningsBlockers: [
			{
				code: "WRN_SNAPSHOT",
				message: "Snapshot is one day older than latest officer save.",
				severity: "warning",
				affectedArea: "Evidence",
			},
		],
		auditEvidenceSummaryLines: ["Last evidence export: not run", "Audit events in window: 42"],
		decisionHistoryLines: ["2026-05-09 — Submitted for approval by Procurement Officer"],
		approveAction: {
			actionCode: "APPROVE_TENDER_PUBLICATION",
			objectType: "Tender",
			objectCode: "TND-200",
			label: "Approve for publication",
			onAllowedClick: vi.fn(),
		},
		returnAction: {
			actionCode: "RETURN_TENDER_FOR_CORRECTION",
			objectType: "Tender",
			objectCode: "TND-200",
			label: "Return for correction",
			onReturnConfirmed: vi.fn(),
		},
		reasonCodeOptions: [
			{ value: "INCOMPLETE_OUTPUTS", label: "Incomplete outputs" },
			{ value: "POLICY_GAP", label: "Policy / compliance gap" },
		],
		criticalityOptions: [
			{ value: "HIGH", label: "High" },
			{ value: "MEDIUM", label: "Medium" },
		],
	};
}

function publicationProps(overrides: Partial<PublicationConfirmationScreenProps> = {}): PublicationConfirmationScreenProps {
	return {
		tenderCode: "TND-300",
		approvalStatusLabel: "Approved for publication (2026-05-10)",
		approvalReady: true,
		readinessStatus: "Ready",
		readinessNarrative: "Last run: no blockers.",
		readinessReady: true,
		outputStatuses: [
			{ label: "Bundle", statusLine: "v4 — current" },
			{ label: "DSM / DOM / DEM / DCM", statusLine: "v3 — aligned with snapshot" },
		],
		evidencePackageStatus: "Evidence package: complete (12 artefacts).",
		publicationSnapshotReadiness: "Snapshot builder: ready — no pending officer edits.",
		publishPrerequisitesMet: true,
		publishAction: {
			actionCode: "PUBLISH_TENDER",
			objectType: "Tender",
			objectCode: "TND-300",
			label: "Confirm publication",
			onAllowedClick: vi.fn(),
		},
		...overrides,
	};
}

function publishedProps(): PublishedStateSummaryScreenProps {
	return {
		tenderCode: "TND-400",
		snapshotCode: "SNAP-MOH-2026-0007",
		bundleVersion: "Bundle v5 (published 2026-05-11)",
		dsmVersion: "DSM v4",
		domVersion: "DOM v4",
		demVersion: "DEM v4",
		dcmVersion: "DCM v2",
		evidencePackageHref: "/desk/tenders/TND-400/evidence",
		evidencePackageLinkLabel: "View sealed evidence package",
		nextLifecycleStep: "Opening session scheduling — assign Opening Officer in Tender Operations.",
		addendumReissueGuidance:
			"Material changes after publication require a formal addendum or a controlled reissue per PPRA guidance; contact Procurement Legal before altering scope or evaluation rules.",
	};
}

describe("UI-HARD-1630 — UI-SMOKE-PUB-* (readiness / approval / publication)", () => {
	afterEach(() => {
		cleanup();
		vi.unstubAllGlobals();
		vi.restoreAllMocks();
	});

	it("UI-SMOKE-PUB-001 — Readiness blockers link to affected sections", () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("RUN_PUBLICATION_READINESS")) });
		render(<PublicationReadinessScreen {...readinessProps()} />);
		const blockers = screen.getByTestId("readiness-critical-blockers");
		expect(within(blockers).getByText(/Evaluation Rules \(DEM\) are stale/i)).toBeInTheDocument();
		const link = within(blockers).getByRole("link", { name: "Works completion" });
		expect(link).toHaveAttribute("href", "/desk/tenders/TND-100/configure-document/works");
	});

	it("UI-SMOKE-PUB-002 — Approver review is read-only", async () => {
		const call = vi.fn(async (opts: { args?: { action_code?: string } }) =>
			availabilityOk(String(opts.args?.action_code || "")),
		);
		vi.stubGlobal("frappe", { call });
		render(<ApprovalReviewPackageScreen {...approvalProps()} />);
		expect(screen.getByTestId("approval-review-readonly-banner")).toBeVisible();
		const bundle = screen.getByTestId("approval-review-bundle-preview");
		expect(within(bundle).getByText(/Section I/)).toBeInTheDocument();
		expect(within(bundle).queryByRole("textbox")).toBeNull();
		await waitFor(() => {
			expect(screen.getByTestId("approval-decision-approve")).not.toBeDisabled();
		});
	});

	it("UI-SMOKE-PUB-003 — Approver cannot edit BOQ", () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("APPROVE_TENDER_PUBLICATION")) });
		render(<ApprovalReviewPackageScreen {...approvalProps()} />);
		expect(screen.getByTestId("approval-edit-boq-control-absent")).toBeInTheDocument();
		expect(screen.queryByRole("textbox", { name: /bill item|line rate|supplier rate/i })).not.toBeInTheDocument();
		const boq = screen.getByRole("heading", { name: "BOQ summary" }).closest("section");
		expect(boq).toBeTruthy();
		expect(within(boq!).queryByRole("spinbutton")).not.toBeInTheDocument();
	});

	it("UI-SMOKE-PUB-004 — Publish button disabled without approval", () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("PUBLISH_TENDER")) });
		render(
			<PublicationConfirmationScreen
				{...publicationProps({
					publishPrerequisitesMet: false,
					approvalReady: false,
					readinessReady: false,
					publishAction: {
						actionCode: "PUBLISH_TENDER",
						objectType: "Tender",
						objectCode: "TND-300",
						label: "Confirm publication",
						onAllowedClick: vi.fn(),
					},
				})}
			/>,
		);
		expect(screen.getByTestId("publication-confirm-button")).toBeDisabled();
		expect(screen.getByText(/Approval and readiness must both be satisfied/i)).toBeInTheDocument();
	});

	it("UI-SMOKE-PUB-005 — Publication warning shown before publish", () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("PUBLISH_TENDER")) });
		render(<PublicationConfirmationScreen {...publicationProps()} />);
		const warn = screen.getByTestId("publication-immutability-warning");
		expect(warn).toHaveTextContent(PUBLICATION_IMMUTABILITY_WARNING_TEXT);
		const publish = screen.getByTestId("publication-confirm-button");
		/* Immutability region is rendered above the publish action (doc §17). */
		expect(warn.compareDocumentPosition(publish) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
	});

	it("UI-SMOKE-PUB-006 — Published tender shows snapshot/output versions", () => {
		render(<PublishedStateSummaryScreen {...publishedProps()} />);
		expect(screen.getByTestId("published-snapshot-code")).toHaveTextContent("SNAP-MOH-2026-0007");
		expect(screen.getByTestId("published-output-version-bundle")).toHaveTextContent("Bundle v5");
		expect(screen.getByTestId("published-output-version-dsm")).toHaveTextContent("DSM v4");
		expect(screen.getByTestId("published-output-version-dom")).toHaveTextContent("DOM v4");
		expect(screen.getByTestId("published-output-version-dem")).toHaveTextContent("DEM v4");
		expect(screen.getByTestId("published-output-version-dcm")).toHaveTextContent("DCM v2");
	});
});
