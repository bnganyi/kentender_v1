/**
 * UI-HARD-1650 — Evidence / audit UI smoke (pack §21 ticket 1650, doc §21.6).
 *
 * Canonical React surfaces under `std-engine` (Vitest / jsdom).
 * `UI-SMOKE-AUDIT-004`: pack allows “Pass if backend observable”; here we assert the client still
 * drives `EXPORT_EVIDENCE_PACKAGE` through SEC-0410 when `audit_on_attempt` is true (backend records
 * the attempt / export — see procurement audit tests).
 */
import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AuditTrailViewScreen } from "../evidence-audit/pages/AuditTrailViewScreen";
import type { AuditTrailEventRow, AuditTrailViewScreenProps } from "../evidence-audit/pages/auditTrailViewScreen.types";
import { EvidencePackageViewScreen } from "../evidence-audit/pages/EvidencePackageViewScreen";
import type { EvidencePackageViewScreenProps } from "../evidence-audit/pages/evidencePackageViewScreen.types";
import { SEC_API_ACTION_AVAILABILITY_METHOD } from "../shared/action-availability/constants";

function availabilityOk(action_code: string, overrides: Record<string, unknown> = {}) {
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
			...overrides,
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

function evidenceProps(overrides: Partial<EvidencePackageViewScreenProps> = {}): EvidencePackageViewScreenProps {
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

const auditSampleRows: AuditTrailEventRow[] = [
	{
		id: "1",
		eventType: "PUBLICATION_READINESS_RUN",
		actor: "officer@moh.go.ke",
		result: "OK",
		objectLabel: "Tender TND-600",
		timestamp: "2026-05-11 09:00",
		timestampIso: "2026-05-11",
		riskLevel: "Low",
	},
	{
		id: "2",
		eventType: "MANUAL_CRITERIA_EDIT_ATTEMPTED",
		actor: "vendor@x.com",
		result: "Denied",
		objectLabel: "Tender TND-600 / DEM",
		timestamp: "2026-05-10 14:22",
		timestampIso: "2026-05-10",
		riskLevel: "Critical",
		deniedAction: true,
	},
	{
		id: "3",
		eventType: "POST_PUBLICATION_EDIT_ATTEMPTED",
		actor: "officer@moh.go.ke",
		result: "Denied",
		objectLabel: "Tender TND-600 / BOQ",
		timestamp: "2026-05-09 11:00",
		timestampIso: "2026-05-09",
		riskLevel: "High",
		deniedAction: true,
	},
];

function auditProps(overrides: Partial<AuditTrailViewScreenProps> = {}): AuditTrailViewScreenProps {
	return {
		tenderCode: "TND-600",
		rows: auditSampleRows,
		...overrides,
	};
}

describe("UI-HARD-1650 — UI-SMOKE-AUDIT-* (evidence / audit)", () => {
	afterEach(() => {
		cleanup();
		vi.unstubAllGlobals();
		vi.restoreAllMocks();
	});

	it("UI-SMOKE-AUDIT-001 — Auditor can view evidence package", async () => {
		const call = vi.fn(async (opts: { args?: { action_code?: string } }) =>
			availabilityOk(String(opts.args?.action_code || "")),
		);
		vi.stubGlobal("frappe", { call });
		render(<EvidencePackageViewScreen {...evidenceProps()} />);

		expect(screen.getByTestId("evidence-page")).toBeVisible();
		expect(screen.getByTestId("evidence-lineage")).toHaveTextContent(/PKG-A → Tender TND-500/);
		expect(screen.getByRole("heading", { name: /Audit events/i })).toBeInTheDocument();
		expect(screen.getByText(/PUBLICATION_READINESS_RUN — OK/)).toBeInTheDocument();

		await waitFor(() => expect(screen.getByTestId("evidence-export-button")).not.toBeDisabled());
	});

	it("UI-SMOKE-AUDIT-002 — Auditor can filter denied actions", () => {
		render(<AuditTrailViewScreen {...auditProps()} />);
		expect(screen.getByTestId("audit-trail-page")).toBeInTheDocument();

		fireEvent.click(screen.getByTestId("audit-filter-denied-only"));
		const table = screen.getByTestId("audit-event-table");
		expect(within(table).queryByText("PUBLICATION_READINESS_RUN")).not.toBeInTheDocument();
		expect(within(table).getByText("MANUAL_CRITERIA_EDIT_ATTEMPTED")).toBeInTheDocument();
		expect(within(table).getByText("POST_PUBLICATION_EDIT_ATTEMPTED")).toBeInTheDocument();
		expect(screen.getAllByTestId("audit-denied-action-row").length).toBe(2);
	});

	it("UI-SMOKE-AUDIT-003 — Unauthorized user cannot export evidence", async () => {
		vi.stubGlobal("frappe", {
			call: vi.fn(async () => availabilityDenied("EXPORT_EVIDENCE_PACKAGE", "Evidence export is restricted to auditors.")),
		});
		const onExport = vi.fn();
		render(
			<EvidencePackageViewScreen
				{...evidenceProps({
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
		expect(screen.getByTestId("action-denial-reason-EXPORT_EVIDENCE_PACKAGE")).toHaveTextContent(
			/Evidence export is restricted to auditors/i,
		);
		fireEvent.click(screen.getByTestId("evidence-export-button"));
		expect(onExport).not.toHaveBeenCalled();
	});

	it("UI-SMOKE-AUDIT-004 — Export uses audited SEC action path when audit_on_attempt is true", async () => {
		const call = vi.fn(async (opts: { args?: { action_code?: string } }) =>
			availabilityOk(String(opts.args?.action_code || ""), { audit_on_attempt: true }),
		);
		vi.stubGlobal("frappe", { call });
		const onExport = vi.fn();
		render(
			<EvidencePackageViewScreen
				{...evidenceProps({
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
		await waitFor(() => expect(onExport).toHaveBeenCalledTimes(1));

		expect(call).toHaveBeenCalledWith(
			expect.objectContaining({
				method: SEC_API_ACTION_AVAILABILITY_METHOD,
				args: expect.objectContaining({
					action_code: "EXPORT_EVIDENCE_PACKAGE",
					object_type: "Tender",
					object_code: "TND-500",
				}),
			}),
		);
	});
});
