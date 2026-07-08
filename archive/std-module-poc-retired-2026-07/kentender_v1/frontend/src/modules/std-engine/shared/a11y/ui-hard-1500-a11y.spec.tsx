import "@testing-library/jest-dom/vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ApprovalReviewPackageScreen } from "../../approval/pages/ApprovalReviewPackageScreen";
import { AuditTrailViewScreen } from "../../evidence-audit/pages/AuditTrailViewScreen";
import type { AuditTrailEventRow } from "../../evidence-audit/pages/auditTrailViewScreen.types";
import { EvidencePackageViewScreen } from "../../evidence-audit/pages/EvidencePackageViewScreen";
import type { EvidencePackageViewScreenProps } from "../../evidence-audit/pages/evidencePackageViewScreen.types";
import { PublicationConfirmationScreen } from "../../publication/pages/PublicationConfirmationScreen";
import type { PublicationConfirmationScreenProps } from "../../publication/pages/publicationConfirmationScreen.types";
import { ActionAwareButton } from "../action-availability/ActionAwareButton";
import { OperationErrorNotice } from "../operation-state/OperationErrorNotice";
import { OperationLoadingState } from "../operation-state/OperationLoadingState";
import { formatStdEngineAxeViolations, runStdEngineAxe } from "./runStdEngineAxe";
import { useStdEngineDocumentTitle } from "./useStdEngineDocumentTitle";

async function assertStdEngineHasNoAxeViolations(container: HTMLElement): Promise<void> {
	const violations = await runStdEngineAxe(container);
	if (violations.length > 0) {
		console.error(formatStdEngineAxeViolations(violations));
	}
	expect(violations).toEqual([]);
}

function availabilityOk(action_code: string) {
	return {
		message: {
			success: true,
			actor_user_code: "Administrator",
			action_code,
			allowed: true,
			message: "OK",
			required_permission: null,
			risk_level: "Low",
			requires_confirmation: false,
			audit_on_attempt: false,
		},
	};
}

function availabilityDenied(action_code: string, message: string) {
	return {
		message: {
			success: true,
			actor_user_code: "Guest",
			action_code,
			allowed: false,
			message,
			required_permission: "PERM_TENDER_EVIDENCE_EXPORT",
			risk_level: "High",
			requires_confirmation: false,
			audit_on_attempt: false,
		},
	};
}

function evidenceMinimal(overrides: Partial<EvidencePackageViewScreenProps> = {}): EvidencePackageViewScreenProps {
	return {
		tenderCode: "TND-500",
		packageAndTenderLineage: ["PKG-A → Tender TND-500"],
		stdTemplateProfileLines: ["PPRA Works — Rev April 2022"],
		stdInstanceLines: ["Instance bound"],
		generatedOutputsLines: ["Bundle v4"],
		snapshotsLines: ["Snapshot SNAP-1"],
		approvalDecisionsLines: ["Approved"],
		auditEventsLines: ["READINESS_RUN"],
		downstreamConsumptionRefs: ["ORD-1"],
		exportAction: {
			actionCode: "EXPORT_EVIDENCE_PACKAGE",
			objectType: "Tender",
			objectCode: "TND-500",
			label: "Export evidence package",
			onAllowedClick: vi.fn(),
		},
		...overrides,
	};
}

const auditRows: AuditTrailEventRow[] = [
	{
		id: "1",
		eventType: "EVT",
		actor: "a@b.c",
		result: "OK",
		objectLabel: "Tender",
		timestamp: "2026-05-11",
		timestampIso: "2026-05-11",
	},
];

function TitleProbe(props: { title: string }) {
	useStdEngineDocumentTitle(props.title);
	return <p>probe</p>;
}

describe("UI-HARD-1500 — axe smoke (partial tree)", () => {
	afterEach(() => {
		cleanup();
		vi.unstubAllGlobals();
		vi.restoreAllMocks();
	});

	it("EvidencePackageViewScreen has no serious axe violations", async () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("EXPORT_EVIDENCE_PACKAGE")) });
		const { container } = render(<EvidencePackageViewScreen {...evidenceMinimal()} />);
		await waitFor(() => expect(screen.getByTestId("evidence-export-button")).toBeInTheDocument());
		await assertStdEngineHasNoAxeViolations(container);
	});

	it("AuditTrailViewScreen table has no serious axe violations", async () => {
		const { container } = render(<AuditTrailViewScreen tenderCode="TND-1" rows={auditRows} />);
		await assertStdEngineHasNoAxeViolations(container);
	});

	it("PublicationConfirmationScreen has no serious axe violations", async () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("PUBLISH_TENDER")) });
		const props: PublicationConfirmationScreenProps = {
			tenderCode: "TND-9",
			approvalStatusLabel: "Approved",
			approvalReady: true,
			readinessStatus: "Ready",
			readinessNarrative: "OK",
			readinessReady: true,
			outputStatuses: [{ label: "Bundle", statusLine: "v1" }],
			evidencePackageStatus: "Complete",
			publicationSnapshotReadiness: "Ready",
			publishPrerequisitesMet: true,
			publishAction: {
				actionCode: "PUBLISH_TENDER",
				objectType: "Tender",
				objectCode: "TND-9",
				label: "Confirm publication",
				onAllowedClick: vi.fn(),
			},
		};
		const { container } = render(<PublicationConfirmationScreen {...props} />);
		await waitFor(() => expect(screen.getByTestId("publication-confirm-button")).toBeInTheDocument());
		await assertStdEngineHasNoAxeViolations(container);
	});

	it("Operation error + loading notices have no serious axe violations", async () => {
		const { container } = render(
			<div>
				<OperationErrorNotice message="Could not export." resolutionAction="Retry later." referenceCode="E-1" />
				<OperationLoadingState label="Working…" />
			</div>,
		);
		await assertStdEngineHasNoAxeViolations(container);
	});

	it("Approval return form keeps no serious axe violations", async () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("APPROVE_TENDER_PUBLICATION")) });
		const { container } = render(
			<ApprovalReviewPackageScreen
				tenderCode="TND-8"
				tenderSummaryLines={["T"]}
				packageReferenceLines={["P"]}
				stdTemplateProfileSummary={["S"]}
				readinessStatus="Ready"
				readinessNarrative="OK"
				bundlePreviewText="x"
				outputSummaryLines={["o"]}
				boqSummaryLines={["b"]}
				worksRequirementsSummaryLines={["w"]}
				warningsBlockers={[]}
				auditEvidenceSummaryLines={["a"]}
				decisionHistoryLines={["h"]}
				approveAction={{
					actionCode: "APPROVE_TENDER_PUBLICATION",
					objectType: "Tender",
					objectCode: "TND-8",
					label: "Approve",
					onAllowedClick: vi.fn(),
				}}
				returnAction={{
					actionCode: "RETURN_TENDER_FOR_CORRECTION",
					objectType: "Tender",
					objectCode: "TND-8",
					label: "Return",
					onReturnConfirmed: vi.fn(),
				}}
				reasonCodeOptions={[{ value: "X", label: "X" }]}
				criticalityOptions={[{ value: "HIGH", label: "High" }]}
			/>,
		);
		await assertStdEngineHasNoAxeViolations(container);
	});
});

describe("UI-HARD-1500 — manual rules", () => {
	afterEach(() => {
		cleanup();
		vi.unstubAllGlobals();
		vi.restoreAllMocks();
	});

	it("disabled ActionAwareButton exposes denial reason to assistive tech (aria-describedby)", async () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityDenied("X", "Not permitted for this role.")) });
		render(<ActionAwareButton actionCode="X" objectType="T" objectCode="1" label="Do thing" onAllowedClick={vi.fn()} />);
		await waitFor(() => {
			const btn = screen.getByRole("button", { name: /Do thing/i });
			expect(btn).toBeDisabled();
			expect(btn).toHaveAccessibleDescription(/Not permitted for this role/i);
		});
	});

	it("useStdEngineDocumentTitle sets and restores document title", () => {
		const prev = document.title;
		const { unmount } = render(<TitleProbe title="Evidence package" />);
		expect(document.title).toContain("Evidence package");
		unmount();
		expect(document.title).toBe(prev);
	});
});
