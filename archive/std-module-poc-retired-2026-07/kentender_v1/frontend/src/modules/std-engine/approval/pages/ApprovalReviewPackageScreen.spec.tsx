import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SEC_API_ACTION_AVAILABILITY_METHOD } from "../../shared/action-availability/constants";
import { ApprovalReviewPackageScreen } from "./ApprovalReviewPackageScreen";
import type { ApprovalReviewPackageScreenProps } from "./approvalReviewPackageScreen.types";

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

function minimalProps(overrides: Partial<ApprovalReviewPackageScreenProps> = {}): ApprovalReviewPackageScreenProps {
	return {
		tenderCode: "TND-200",
		tenderSummaryLines: ["District Health Centre Rehabilitation", "Procuring entity: Ministry of Health"],
		packageReferenceLines: ["PKG-MOH-2026-001 — Rehabilitation of District Health Centre"],
		stdTemplateProfileSummary: ["PPRA Works — Building and Associated Civil Engineering Works — Rev April 2022"],
		readinessStatus: "Ready",
		readinessNarrative: "Last readiness run: 2026-05-10 — no critical blockers.",
		bundlePreviewText: "=== Tender bundle snapshot (read-only) ===\nSection I …",
		outputSummaryLines: [
			"Bundle: v3 — current",
			"DSM v2 / DOM v2 / DEM v2 / DCM v1 — aligned with snapshot",
		],
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
		...overrides,
	};
}

describe("ApprovalReviewPackageScreen (UI-HARD-1100)", () => {
	afterEach(() => {
		cleanup();
		vi.unstubAllGlobals();
		vi.restoreAllMocks();
	});

	it("exposes pack data-testids", async () => {
		const call = vi.fn(async (opts: { args?: { action_code?: string } }) =>
			availabilityOk(String(opts.args?.action_code || "")),
		);
		vi.stubGlobal("frappe", { call });
		render(<ApprovalReviewPackageScreen {...minimalProps()} />);
		expect(screen.getByTestId("approval-review-page")).toBeInTheDocument();
		expect(screen.getByTestId("approval-review-readonly-banner")).toBeInTheDocument();
		expect(screen.getByTestId("approval-review-bundle-preview")).toBeInTheDocument();
		expect(screen.getByTestId("approval-review-output-summaries")).toBeInTheDocument();
		expect(screen.getByTestId("approval-return-form")).toBeInTheDocument();
		expect(screen.getByTestId("approval-edit-boq-control-absent")).toBeInTheDocument();
		await waitFor(() => {
			expect(screen.getByTestId("approval-decision-approve")).not.toBeDisabled();
			expect(screen.getByTestId("approval-decision-return")).not.toBeDisabled();
		});
	});

	it("does not render BOQ edit inputs (read-only summary only)", () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("APPROVE_TENDER_PUBLICATION")) });
		render(<ApprovalReviewPackageScreen {...minimalProps()} />);
		expect(screen.queryByRole("textbox", { name: /bill item|line rate|supplier rate/i })).not.toBeInTheDocument();
		const boq = screen.getByRole("heading", { name: "BOQ summary" }).closest("section");
		expect(boq).toBeTruthy();
		expect(within(boq!).queryByRole("spinbutton")).not.toBeInTheDocument();
	});

	it("blocks return until §16.4 fields are complete", async () => {
		const call = vi.fn(async (opts: { args?: { action_code?: string } }) =>
			availabilityOk(String(opts.args?.action_code || "")),
		);
		vi.stubGlobal("frappe", { call });
		const onReturn = vi.fn();
		render(
			<ApprovalReviewPackageScreen
				{...minimalProps({
					returnAction: {
						actionCode: "RETURN_TENDER_FOR_CORRECTION",
						objectType: "Tender",
						objectCode: "TND-200",
						label: "Return for correction",
						onReturnConfirmed: onReturn,
					},
				})}
			/>,
		);
		await waitFor(() => expect(screen.getByTestId("approval-decision-return")).not.toBeDisabled());
		fireEvent.click(screen.getByTestId("approval-decision-return"));
		await waitFor(() => expect(screen.getByText("Reason code is required.")).toBeInTheDocument());
		expect(onReturn).not.toHaveBeenCalled();
	});

	it("invokes onReturnConfirmed with payload when form is valid", async () => {
		const call = vi.fn(async (opts: { args?: { action_code?: string } }) =>
			availabilityOk(String(opts.args?.action_code || "")),
		);
		vi.stubGlobal("frappe", { call });
		const onReturn = vi.fn();
		render(
			<ApprovalReviewPackageScreen
				{...minimalProps({
					returnAction: {
						actionCode: "RETURN_TENDER_FOR_CORRECTION",
						objectType: "Tender",
						objectCode: "TND-200",
						label: "Return for correction",
						onReturnConfirmed: onReturn,
					},
				})}
			/>,
		);
		await waitFor(() => expect(screen.getByTestId("approval-decision-return")).not.toBeDisabled());
		fireEvent.change(screen.getByLabelText("reason_code"), { target: { value: "INCOMPLETE_OUTPUTS" } });
		fireEvent.change(screen.getByLabelText("comment"), { target: { value: "DEM still stale vs bundle." } });
		fireEvent.change(screen.getByLabelText("affected_area"), { target: { value: "Generated outputs" } });
		fireEvent.change(screen.getByLabelText("criticality"), { target: { value: "HIGH" } });
		fireEvent.click(screen.getByTestId("approval-decision-return"));
		await waitFor(() =>
			expect(onReturn).toHaveBeenCalledWith({
				reason_code: "INCOMPLETE_OUTPUTS",
				comment: "DEM still stale vs bundle.",
				affected_area: "Generated outputs",
				criticality: "HIGH",
			}),
		);
	});

	it("drives approve from ActionAwareButton (SEC-0410)", async () => {
		const call = vi.fn(async (opts: { args?: { action_code?: string } }) =>
			availabilityOk(String(opts.args?.action_code || "")),
		);
		vi.stubGlobal("frappe", { call });
		const onApprove = vi.fn();
		render(
			<ApprovalReviewPackageScreen
				{...minimalProps({
					approveAction: {
						actionCode: "APPROVE_TENDER_PUBLICATION",
						objectType: "Tender",
						objectCode: "TND-200",
						label: "Approve for publication",
						onAllowedClick: onApprove,
					},
				})}
			/>,
		);
		await waitFor(() => expect(screen.getByTestId("approval-decision-approve")).not.toBeDisabled());
		fireEvent.click(screen.getByTestId("approval-decision-approve"));
		await waitFor(() => expect(onApprove).toHaveBeenCalled());
		expect(call).toHaveBeenCalledWith(
			expect.objectContaining({
				method: SEC_API_ACTION_AVAILABILITY_METHOD,
				args: expect.objectContaining({ action_code: "APPROVE_TENDER_PUBLICATION" }),
			}),
		);
	});
});
