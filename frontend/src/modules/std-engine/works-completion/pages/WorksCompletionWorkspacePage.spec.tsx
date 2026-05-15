import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { useMemo, useState, type ReactElement } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SEC_API_ACTION_AVAILABILITY_METHOD } from "../../shared/action-availability/constants";
import { WorksCompletionWorkspacePage } from "./WorksCompletionWorkspacePage";
import type { WorksCompletionStageId } from "./worksCompletionWorkspace.types";

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

function minimalProps(overrides: Partial<Parameters<typeof WorksCompletionWorkspacePage>[0]> = {}) {
	return {
		tenderCode: "TND-1",
		tenderTitle: "District Health Centre Rehabilitation",
		packageCode: "PKG-MOH-2026-001",
		procurementCategory: "Works",
		procurementMethod: "Open Tender",
		selectedStdTemplate: "PPRA Works — Rev April 2022",
		instanceState: "Draft configuration",
		publicationState: "Not published",
		saveAction: {
			actionCode: "EDIT_STD_INSTANCE_PARAMETERS",
			objectType: "StdEngineWorksInstance",
			objectCode: "SI-1",
			onAllowedClick: vi.fn(),
		},
		generateOutputsAction: {
			actionCode: "GENERATE_STD_OUTPUTS",
			objectType: "Tender",
			objectCode: "TND-1",
			onAllowedClick: vi.fn(),
		},
		runReadinessAction: {
			actionCode: "RUN_PUBLICATION_READINESS",
			objectType: "Tender",
			objectCode: "TND-1",
			onAllowedClick: vi.fn(),
		},
		...overrides,
	};
}

function ControlledWrapper(): ReactElement {
	const [stage, setStage] = useState<WorksCompletionStageId>("tds");
	const actions = useMemo(
		() => ({
			saveAction: {
				actionCode: "EDIT_STD_INSTANCE_PARAMETERS",
				objectType: "StdEngineWorksInstance",
				objectCode: "SI-1",
				onAllowedClick: vi.fn(),
			},
			generateOutputsAction: {
				actionCode: "GENERATE_STD_OUTPUTS",
				objectType: "Tender",
				objectCode: "TND-1",
				onAllowedClick: vi.fn(),
			},
			runReadinessAction: {
				actionCode: "RUN_PUBLICATION_READINESS",
				objectType: "Tender",
				objectCode: "TND-1",
				onAllowedClick: vi.fn(),
			},
		}),
		[],
	);
	return (
		<WorksCompletionWorkspacePage
			tenderCode="TND-1"
			tenderTitle="District Health Centre Rehabilitation"
			packageCode="PKG-MOH-2026-001"
			procurementCategory="Works"
			procurementMethod="Open Tender"
			selectedStdTemplate="PPRA Works — Rev April 2022"
			instanceState="Draft configuration"
			publicationState="Not published"
			{...actions}
			selectedStageId={stage}
			onStageSelect={setStage}
		/>
	);
}

describe("WorksCompletionWorkspacePage (UI-HARD-0500)", () => {
	afterEach(() => {
		cleanup();
		vi.unstubAllGlobals();
		vi.restoreAllMocks();
	});

	it("exposes pack layout data-testids", () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("EDIT_STD_INSTANCE_PARAMETERS")) });
		render(<WorksCompletionWorkspacePage {...minimalProps()} />);
		expect(screen.getByTestId("works-completion-page")).toBeInTheDocument();
		expect(screen.getByTestId("works-context-header")).toBeInTheDocument();
		expect(screen.getByTestId("works-progress-sidebar")).toBeInTheDocument();
		expect(screen.getByTestId("works-main-panel")).toBeInTheDocument();
		expect(screen.getByTestId("works-blockers-panel")).toBeInTheDocument();
		expect(screen.getByTestId("works-output-impact-panel")).toBeInTheDocument();
		expect(screen.getByTestId("works-save-action")).toBeInTheDocument();
		expect(screen.getByTestId("works-generate-outputs-action")).toBeInTheDocument();
		expect(screen.getByTestId("works-run-readiness-action")).toBeInTheDocument();
	});

	it("renders doc §9.3 tender context fields in the header", () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("X")) });
		render(<WorksCompletionWorkspacePage {...minimalProps()} />);
		const h = screen.getByTestId("works-context-header");
		expect(h).toHaveTextContent("District Health Centre Rehabilitation");
		expect(h).toHaveTextContent("TND-1");
		expect(h).toHaveTextContent("PKG-MOH-2026-001");
		expect(h).toHaveTextContent("Works");
		expect(h).toHaveTextContent("Open Tender");
		expect(h).toHaveTextContent("PPRA Works");
		expect(h).toHaveTextContent("Draft configuration");
		expect(h).toHaveTextContent("Not published");
	});

	it("shows blockers in plain language via BlockerList", () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("X")) });
		render(
			<WorksCompletionWorkspacePage
				{...minimalProps({
					blockers: [
						{
							code: "BOQ_INCOMPLETE",
							message: "Bills of Quantities is incomplete.",
							severity: "warning",
							affectedArea: "BOQ",
						},
						{
							code: "BOQ_ITEM",
							message: "Item 2.1 is missing quantity.",
							severity: "warning",
							affectedArea: "BOQ",
						},
					],
				})}
			/>,
		);
		const panel = screen.getByTestId("works-blockers-panel");
		expect(panel).toHaveTextContent("Bills of Quantities is incomplete.");
		expect(panel).toHaveTextContent("Item 2.1 is missing quantity.");
	});

	it("embeds UI-HARD-0510 OutputImpactPanel with pack selectors under works-output-impact-panel", () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("X")) });
		render(
			<WorksCompletionWorkspacePage
				{...minimalProps({
					outputImpactAffectedKinds: ["bundle", "dsm", "dom"],
				})}
			/>,
		);
		const outer = screen.getByTestId("works-output-impact-panel");
		expect(within(outer).getByTestId("output-impact-panel")).toBeInTheDocument();
		expect(within(outer).getByTestId("output-impact-item-bundle")).toHaveTextContent("Tender Document Bundle");
		expect(within(outer).getByTestId("output-impact-item-dsm")).toHaveTextContent("Submission Rules (DSM)");
		expect(within(outer).getByTestId("output-impact-item-dom")).toHaveTextContent("Opening Register (DOM)");
	});

	it("updates main panel stage label from sidebar in uncontrolled mode", () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("X")) });
		render(<WorksCompletionWorkspacePage {...minimalProps()} />);
		const sidebar = screen.getByTestId("works-progress-sidebar");
		expect(within(screen.getByTestId("works-main-panel")).getByRole("heading", { level: 4 })).toHaveTextContent("TDS");
		fireEvent.click(within(sidebar).getByRole("button", { name: "BOQ" }));
		expect(within(screen.getByTestId("works-main-panel")).getByRole("heading", { level: 4 })).toHaveTextContent("BOQ");
	});

	it("supports controlled stage selection", () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("X")) });
		render(<ControlledWrapper />);
		const sidebar = screen.getByTestId("works-progress-sidebar");
		fireEvent.click(within(sidebar).getByRole("button", { name: "SCC" }));
		expect(within(screen.getByTestId("works-main-panel")).getByRole("heading", { level: 4 })).toHaveTextContent("SCC");
	});

	it("Save uses ActionAwareButton (SEC-0410)", async () => {
		const call = vi.fn(async (opts: { args?: { action_code?: string } }) =>
			availabilityOk(String(opts.args?.action_code || "")),
		);
		vi.stubGlobal("frappe", { call });
		const onSave = vi.fn();
		const p = minimalProps();
		render(<WorksCompletionWorkspacePage {...p} saveAction={{ ...p.saveAction, onAllowedClick: onSave }} />);
		await waitFor(() => {
			expect(screen.getByTestId("works-save-action")).not.toBeDisabled();
		});
		fireEvent.click(screen.getByTestId("works-save-action"));
		await waitFor(() => expect(onSave).toHaveBeenCalled());
		const saveCall = call.mock.calls.find((c) => (c[0] as { args?: { action_code?: string } })?.args?.action_code === "EDIT_STD_INSTANCE_PARAMETERS");
		expect(saveCall?.[0]).toEqual(
			expect.objectContaining({
				method: SEC_API_ACTION_AVAILABILITY_METHOD,
				args: expect.objectContaining({
					action_code: "EDIT_STD_INSTANCE_PARAMETERS",
					object_type: "StdEngineWorksInstance",
					object_code: "SI-1",
				}),
			}),
		);
	});

	it("renders disabled placeholders when generate/readiness actions are null", () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("EDIT_STD_INSTANCE_PARAMETERS")) });
		render(
			<WorksCompletionWorkspacePage
				{...minimalProps({
					generateOutputsAction: null,
					runReadinessAction: null,
				})}
			/>,
		);
		expect(screen.getByTestId("works-generate-outputs-action")).toBeDisabled();
		expect(screen.getByTestId("works-run-readiness-action")).toBeDisabled();
	});
});
