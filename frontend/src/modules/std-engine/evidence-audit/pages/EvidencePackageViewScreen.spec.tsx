import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SEC_API_ACTION_AVAILABILITY_METHOD } from "../../shared/action-availability/constants";
import { EvidencePackageViewScreen } from "./EvidencePackageViewScreen";
import type { EvidencePackageViewScreenProps } from "./evidencePackageViewScreen.types";

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

function minimalProps(overrides: Partial<EvidencePackageViewScreenProps> = {}): EvidencePackageViewScreenProps {
	return {
		tenderCode: "TND-500",
		packageAndTenderLineage: ["PKG-A → Tender TND-500", "Released 2026-04-01"],
		stdTemplateProfileLines: ["PPRA Works — Rev April 2022"],
		stdInstanceLines: ["Instance MOH-STD-2026-014 — bound to tender"],
		generatedOutputsLines: ["Bundle v4", "DSM/DOM/DEM/DCM v3"],
		snapshotsLines: ["Publication snapshot SNAP-001 sealed 2026-05-11"],
		approvalDecisionsLines: ["2026-05-10 — Approved for publication (Administrator)"],
		auditEventsLines: ["2026-05-11 — PUBLICATION_READINESS_RUN — OK"],
		downstreamConsumptionRefs: ["Opening module — DSM consumption token ORD-88"],
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

describe("EvidencePackageViewScreen (UI-HARD-1300)", () => {
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
		render(<EvidencePackageViewScreen {...minimalProps()} />);
		expect(screen.getByTestId("evidence-page")).toBeInTheDocument();
		expect(screen.getByTestId("evidence-lineage")).toBeInTheDocument();
		expect(screen.getByTestId("evidence-std-template")).toBeInTheDocument();
		expect(screen.getByTestId("evidence-generated-outputs")).toBeInTheDocument();
		expect(screen.getByTestId("evidence-snapshots")).toBeInTheDocument();
		expect(screen.getByTestId("evidence-approval-decisions")).toBeInTheDocument();
		await waitFor(() => expect(screen.getByTestId("evidence-export-button")).not.toBeDisabled());
	});

	it("renders doc §18.1 sections including STD instance, audit events, and downstream refs", () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("EXPORT_EVIDENCE_PACKAGE")) });
		render(<EvidencePackageViewScreen {...minimalProps()} />);
		expect(screen.getByRole("heading", { name: /STD instance/i })).toBeInTheDocument();
		expect(screen.getByRole("heading", { name: /Audit events/i })).toBeInTheDocument();
		expect(screen.getByRole("heading", { name: /Downstream consumption references/i })).toBeInTheDocument();
		expect(screen.getByRole("heading", { name: /Evidence export actions/i })).toBeInTheDocument();
	});

	it("drives export from ActionAwareButton (SEC-0410)", async () => {
		const call = vi.fn(async (opts: { args?: { action_code?: string } }) =>
			availabilityOk(String(opts.args?.action_code || "")),
		);
		vi.stubGlobal("frappe", { call });
		const onExport = vi.fn();
		render(
			<EvidencePackageViewScreen
				{...minimalProps({
					exportAction: {
						actionCode: "EXPORT_EVIDENCE_PACKAGE",
						objectType: "Tender",
						objectCode: "TND-500",
						label: "Export evidence package",
						onAllowedClick: onExport,
					},
				})}
			/>,
		);
		await waitFor(() => expect(screen.getByTestId("evidence-export-button")).not.toBeDisabled());
		fireEvent.click(screen.getByTestId("evidence-export-button"));
		await waitFor(() => expect(onExport).toHaveBeenCalled());
		expect(call).toHaveBeenCalledWith(
			expect.objectContaining({
				method: SEC_API_ACTION_AVAILABILITY_METHOD,
				args: expect.objectContaining({ action_code: "EXPORT_EVIDENCE_PACKAGE" }),
			}),
		);
	});

	it("disables export and shows denial when backend disallows (unauthorized)", async () => {
		const call = vi.fn(async () => availabilityDenied("EXPORT_EVIDENCE_PACKAGE", "Evidence export is restricted to auditors."));
		vi.stubGlobal("frappe", { call });
		const onExport = vi.fn();
		render(
			<EvidencePackageViewScreen
				{...minimalProps({
					exportAction: {
						actionCode: "EXPORT_EVIDENCE_PACKAGE",
						objectType: "Tender",
						objectCode: "TND-500",
						label: "Export evidence package",
						onAllowedClick: onExport,
					},
				})}
			/>,
		);
		await waitFor(() => expect(screen.getByTestId("evidence-export-button")).toBeDisabled());
		expect(screen.getByText(/Evidence export is restricted to auditors/i)).toBeInTheDocument();
		fireEvent.click(screen.getByTestId("evidence-export-button"));
		expect(onExport).not.toHaveBeenCalled();
	});
});
