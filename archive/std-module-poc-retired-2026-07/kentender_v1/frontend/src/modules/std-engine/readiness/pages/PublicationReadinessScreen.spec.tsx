import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SEC_API_ACTION_AVAILABILITY_METHOD } from "../../shared/action-availability/constants";
import { PublicationReadinessScreen } from "./PublicationReadinessScreen";
import type { PublicationReadinessScreenProps } from "./publicationReadinessScreen.types";

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

function minimalProps(
	overrides: Partial<PublicationReadinessScreenProps> = {},
): PublicationReadinessScreenProps {
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
		...overrides,
	};
}

describe("PublicationReadinessScreen (UI-HARD-1000)", () => {
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
		render(<PublicationReadinessScreen {...minimalProps()} />);
		expect(screen.getByTestId("readiness-screen")).toBeInTheDocument();
		expect(screen.getByTestId("readiness-overall-status")).toBeInTheDocument();
		expect(screen.getByTestId("readiness-critical-blockers")).toBeInTheDocument();
		expect(screen.getByTestId("readiness-warnings")).toBeInTheDocument();
		expect(screen.getByTestId("readiness-output-statuses")).toBeInTheDocument();
		await waitFor(() => {
			expect(screen.getByTestId("readiness-run-button")).not.toBeDisabled();
			expect(screen.getByTestId("readiness-next-action")).not.toBeDisabled();
		});
	});

	it("renders doc §15.4 blocker fields and stage link", () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("RUN_PUBLICATION_READINESS")) });
		render(<PublicationReadinessScreen {...minimalProps()} />);
		const blockers = screen.getByTestId("readiness-critical-blockers");
		expect(within(blockers).getByText(/Evaluation Rules \(DEM\) are stale/i)).toBeInTheDocument();
		expect(within(blockers).getByText(/Evaluation cannot legally proceed/i)).toBeInTheDocument();
		expect(within(blockers).getByText(/Regenerate outputs, then rerun readiness/i)).toBeInTheDocument();
		const link = within(blockers).getByRole("link", { name: "Works completion" });
		expect(link).toHaveAttribute("href", "/desk/tenders/TND-100/configure-document/works");
	});

	it("marks stale outputs clearly in readiness-output-statuses", () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("RUN_PUBLICATION_READINESS")) });
		render(<PublicationReadinessScreen {...minimalProps()} />);
		const out = screen.getByTestId("readiness-output-statuses");
		expect(out).toHaveTextContent("STALE");
		expect(out).toHaveTextContent("Evaluation Rules (DEM)");
	});

	it("drives Run Readiness from ActionAwareButton (SEC-0410)", async () => {
		const call = vi.fn(async (opts: { args?: { action_code?: string } }) =>
			availabilityOk(String(opts.args?.action_code || "")),
		);
		vi.stubGlobal("frappe", { call });
		const onRun = vi.fn();
		render(
			<PublicationReadinessScreen
				{...minimalProps({
					runReadinessAction: {
						actionCode: "RUN_PUBLICATION_READINESS",
						objectType: "Tender",
						objectCode: "TND-100",
						label: "Run readiness",
						onAllowedClick: onRun,
					},
				})}
			/>,
		);
		await waitFor(() => expect(screen.getByTestId("readiness-run-button")).not.toBeDisabled());
		fireEvent.click(screen.getByTestId("readiness-run-button"));
		await waitFor(() => expect(onRun).toHaveBeenCalled());
		expect(call).toHaveBeenCalledWith(
			expect.objectContaining({
				method: SEC_API_ACTION_AVAILABILITY_METHOD,
				args: expect.objectContaining({ action_code: "RUN_PUBLICATION_READINESS" }),
			}),
		);
	});

	it("shows empty next action copy when nextAction omitted", async () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("RUN_PUBLICATION_READINESS")) });
		render(<PublicationReadinessScreen {...minimalProps({ nextAction: null })} />);
		await waitFor(() => expect(screen.getByTestId("readiness-run-button")).toBeInTheDocument());
		expect(screen.queryByTestId("readiness-next-action")).not.toBeInTheDocument();
		expect(screen.getByText("No suggested action")).toBeInTheDocument();
	});
});
