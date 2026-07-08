import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SEC_API_ACTION_AVAILABILITY_METHOD } from "../../shared/action-availability/constants";
import { SCC_COMPLETION_PERIOD_HELP } from "./sccBusinessFieldScreen.types";
import { SccBusinessFieldScreen } from "./SccBusinessFieldScreen";

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

describe("SccBusinessFieldScreen (UI-HARD-0610)", () => {
	afterEach(() => {
		cleanup();
		vi.unstubAllGlobals();
		vi.restoreAllMocks();
	});

	it("exposes pack data-testids for screen, key groups, completion period field, and save", () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("X")) });
		render(
			<SccBusinessFieldScreen
				instanceCode="SI-200"
				values={{}}
				onChange={vi.fn()}
				saveAction={{
					actionCode: "EDIT_STD_INSTANCE_PARAMETERS",
					objectType: "StdEngineWorksInstance",
					objectCode: "SI-200",
					onAllowedClick: vi.fn(),
				}}
			/>,
		);
		expect(screen.getByTestId("scc-screen")).toBeInTheDocument();
		expect(screen.getByTestId("scc-group-completion-period")).toBeInTheDocument();
		expect(screen.getByTestId("scc-group-defects-liability")).toBeInTheDocument();
		expect(screen.getByTestId("scc-group-performance-security")).toBeInTheDocument();
		expect(screen.getByTestId("scc-field-completion-period-days")).toBeInTheDocument();
		expect(screen.getByTestId("scc-save-button")).toBeInTheDocument();
	});

	it("shows pack completion-period help example", () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("X")) });
		render(
			<SccBusinessFieldScreen
				instanceCode="SI-1"
				values={{}}
				onChange={vi.fn()}
				saveAction={{ actionCode: "X", objectType: "T", objectCode: "SI-1", onAllowedClick: vi.fn() }}
			/>,
		);
		expect(screen.getByTestId("scc-completion-period-help")).toHaveTextContent(SCC_COMPLETION_PERIOD_HELP);
	});

	it("explains contract carry-forward (DCM) and blocks GCC as editable text", () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("X")) });
		render(
			<SccBusinessFieldScreen
				instanceCode="SI-1"
				values={{}}
				onChange={vi.fn()}
				saveAction={{ actionCode: "X", objectType: "T", objectCode: "SI-1", onAllowedClick: vi.fn() }}
			/>,
		);
		expect(screen.getByTestId("scc-dcm-carry-forward-note")).toHaveTextContent("Contract Carry-Forward (DCM)");
		const dispute = screen.getByTestId("scc-group-dispute-resolution");
		expect(screen.getByTestId("scc-gcc-not-editable-notice")).toBeInTheDocument();
		expect(dispute.querySelector("textarea")).toBeNull();
	});

	it("forwards field edits via onChange", () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("X")) });
		const onChange = vi.fn();
		render(
			<SccBusinessFieldScreen
				instanceCode="SI-1"
				values={{ payment_currency: "" }}
				onChange={onChange}
				saveAction={{ actionCode: "X", objectType: "T", objectCode: "SI-1", onAllowedClick: vi.fn() }}
			/>,
		);
		fireEvent.change(screen.getByTestId("scc-field-payment-currency"), { target: { value: "KES" } });
		expect(onChange).toHaveBeenCalledWith("payment_currency", "KES");
	});

	it("shows validation errors next to fields", () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("X")) });
		render(
			<SccBusinessFieldScreen
				instanceCode="SI-1"
				values={{ completion_period_days: "" }}
				onChange={vi.fn()}
				fieldErrors={{ completion_period_days: "Completion period is required." }}
				saveAction={{ actionCode: "X", objectType: "T", objectCode: "SI-1", onAllowedClick: vi.fn() }}
			/>,
		);
		expect(screen.getByTestId("scc-field-completion-period-days-error")).toHaveTextContent("Completion period is required.");
	});

	it("Save uses ActionAwareButton (SEC-0410)", async () => {
		const call = vi.fn(async (opts: { args?: { action_code?: string } }) =>
			availabilityOk(String(opts.args?.action_code || "")),
		);
		vi.stubGlobal("frappe", { call });
		const onSave = vi.fn();
		render(
			<SccBusinessFieldScreen
				instanceCode="SI-200"
				values={{}}
				onChange={vi.fn()}
				saveAction={{
					actionCode: "EDIT_STD_INSTANCE_PARAMETERS",
					objectType: "StdEngineWorksInstance",
					objectCode: "SI-200",
					onAllowedClick: onSave,
				}}
			/>,
		);
		await waitFor(() => {
			expect(screen.getByTestId("scc-save-button")).not.toBeDisabled();
		});
		fireEvent.click(screen.getByTestId("scc-save-button"));
		await waitFor(() => expect(onSave).toHaveBeenCalled());
		const saveCall = call.mock.calls.find(
			(c) => (c[0] as { args?: { action_code?: string } })?.args?.action_code === "EDIT_STD_INSTANCE_PARAMETERS",
		);
		expect(saveCall?.[0]).toEqual(
			expect.objectContaining({
				method: SEC_API_ACTION_AVAILABILITY_METHOD,
				args: expect.objectContaining({
					action_code: "EDIT_STD_INSTANCE_PARAMETERS",
					object_type: "StdEngineWorksInstance",
					object_code: "SI-200",
				}),
			}),
		);
	});
});
