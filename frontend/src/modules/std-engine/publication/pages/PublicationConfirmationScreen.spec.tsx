import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SEC_API_ACTION_AVAILABILITY_METHOD } from "../../shared/action-availability/constants";
import { PUBLICATION_IMMUTABILITY_WARNING_TEXT } from "./publicationConfirmationScreen.constants";
import { PublicationConfirmationScreen } from "./PublicationConfirmationScreen";
import type { PublicationConfirmationScreenProps } from "./publicationConfirmationScreen.types";

function availabilityOk(action_code: string, requires_confirmation = false) {
	return {
		message: {
			success: true,
			actor_user_code: "Administrator",
			action_code,
			allowed: true,
			message: requires_confirmation ? "Confirm irreversible publication." : "OK",
			required_permission: null,
			risk_level: "Critical",
			requires_confirmation,
			audit_on_attempt: true,
		},
	};
}

function minimalProps(overrides: Partial<PublicationConfirmationScreenProps> = {}): PublicationConfirmationScreenProps {
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

describe("PublicationConfirmationScreen (UI-HARD-1200)", () => {
	afterEach(() => {
		cleanup();
		vi.unstubAllGlobals();
		vi.restoreAllMocks();
	});

	it("exposes pack data-testids and exact immutability warning copy", () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("PUBLISH_TENDER")) });
		render(<PublicationConfirmationScreen {...minimalProps()} />);
		expect(screen.getByTestId("publication-page")).toBeInTheDocument();
		expect(screen.getByTestId("publication-approval-status")).toBeInTheDocument();
		expect(screen.getByTestId("publication-readiness-status")).toBeInTheDocument();
		expect(screen.getByTestId("publication-output-statuses")).toBeInTheDocument();
		expect(screen.getByTestId("publication-evidence-status")).toBeInTheDocument();
		const warn = screen.getByTestId("publication-immutability-warning");
		expect(warn).toHaveTextContent(PUBLICATION_IMMUTABILITY_WARNING_TEXT);
	});

	it("disables publish control when prerequisites are not met", () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("PUBLISH_TENDER")) });
		const onPublish = vi.fn();
		render(
			<PublicationConfirmationScreen
				{...minimalProps({
					publishPrerequisitesMet: false,
					approvalReady: false,
					readinessReady: false,
					publishAction: {
						actionCode: "PUBLISH_TENDER",
						objectType: "Tender",
						objectCode: "TND-300",
						label: "Confirm publication",
						onAllowedClick: onPublish,
					},
				})}
			/>,
		);
		const btn = screen.getByTestId("publication-confirm-button");
		expect(btn).toBeDisabled();
		expect(screen.getByText(/Approval and readiness must both be satisfied/i)).toBeInTheDocument();
	});

	it("drives publish from ActionAwareButton when prerequisites are met (SEC-0410)", async () => {
		const call = vi.fn(async (opts: { args?: { action_code?: string } }) =>
			availabilityOk(String(opts.args?.action_code || "")),
		);
		vi.stubGlobal("frappe", { call });
		const onPublish = vi.fn();
		render(
			<PublicationConfirmationScreen
				{...minimalProps({
					publishAction: {
						actionCode: "PUBLISH_TENDER",
						objectType: "Tender",
						objectCode: "TND-300",
						label: "Confirm publication",
						onAllowedClick: onPublish,
					},
				})}
			/>,
		);
		await waitFor(() => expect(screen.getByTestId("publication-confirm-button")).not.toBeDisabled());
		fireEvent.click(screen.getByTestId("publication-confirm-button"));
		await waitFor(() => expect(onPublish).toHaveBeenCalled());
		expect(call).toHaveBeenCalledWith(
			expect.objectContaining({
				method: SEC_API_ACTION_AVAILABILITY_METHOD,
				args: expect.objectContaining({ action_code: "PUBLISH_TENDER" }),
			}),
		);
	});

	it("uses confirmation when backend requires it", async () => {
		const call = vi.fn(async (opts: { args?: { action_code?: string } }) =>
			availabilityOk(String(opts.args?.action_code || ""), true),
		);
		vi.stubGlobal("frappe", { call });
		const confirm = vi.spyOn(window, "confirm").mockReturnValue(true);
		const onPublish = vi.fn();
		render(
			<PublicationConfirmationScreen
				{...minimalProps({
					publishAction: {
						actionCode: "PUBLISH_TENDER",
						objectType: "Tender",
						objectCode: "TND-300",
						label: "Confirm publication",
						confirmationTitle: "Publish tender",
						confirmationMessage: "This cannot be undone.",
						onAllowedClick: onPublish,
					},
				})}
			/>,
		);
		await waitFor(() => expect(screen.getByTestId("publication-confirm-button")).not.toBeDisabled());
		expect(screen.getByTestId("action-confirmation-PUBLISH_TENDER")).toHaveTextContent("confirmation-required");
		fireEvent.click(screen.getByTestId("publication-confirm-button"));
		await waitFor(() => expect(confirm).toHaveBeenCalled());
		await waitFor(() => expect(onPublish).toHaveBeenCalled());
		confirm.mockRestore();
	});

	it("shows user-readable blocker after publication failure", () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("PUBLISH_TENDER")) });
		render(
			<PublicationConfirmationScreen
				{...minimalProps({
					publicationLastError: {
						message: "Snapshot service refused to seal: maintenance window.",
						resolutionAction: "Retry after 09:00 or contact platform support.",
					},
				})}
			/>,
		);
		expect(screen.getByRole("alert")).toHaveTextContent("Snapshot service refused to seal");
		expect(screen.getByRole("alert")).toHaveTextContent("Retry after 09:00");
	});
});
