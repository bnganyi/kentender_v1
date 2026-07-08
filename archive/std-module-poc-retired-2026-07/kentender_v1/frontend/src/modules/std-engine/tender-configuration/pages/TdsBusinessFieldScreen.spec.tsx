import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SEC_API_ACTION_AVAILABILITY_METHOD } from "../../shared/action-availability/constants";
import { TdsBusinessFieldScreen } from "./TdsBusinessFieldScreen";

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

describe("TdsBusinessFieldScreen (UI-HARD-0600)", () => {
	afterEach(() => {
		cleanup();
		vi.unstubAllGlobals();
		vi.restoreAllMocks();
	});

	it("exposes pack data-testids for screen, key groups, deadline fields, and save", () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("SAVE")) });
		const onChange = vi.fn();
		const onSave = vi.fn();
		render(
			<TdsBusinessFieldScreen
				instanceCode="SI-100"
				values={{}}
				onChange={onChange}
				saveAction={{
					actionCode: "EDIT_STD_INSTANCE_PARAMETERS",
					objectType: "StdEngineWorksInstance",
					objectCode: "SI-100",
					onAllowedClick: onSave,
				}}
			/>,
		);
		expect(screen.getByTestId("tds-screen")).toBeInTheDocument();
		expect(screen.getByTestId("tds-group-tender-identity")).toBeInTheDocument();
		expect(screen.getByTestId("tds-group-dates")).toBeInTheDocument();
		expect(screen.getByTestId("tds-group-security")).toBeInTheDocument();
		expect(screen.getByTestId("tds-field-submission-deadline")).toBeInTheDocument();
		expect(screen.getByTestId("tds-field-opening-datetime")).toBeInTheDocument();
		expect(screen.getByTestId("tds-save-button")).toBeInTheDocument();
	});

	it("does not expose ITT clauses as editable text; shows structured-field notice", () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("SAVE")) });
		render(
			<TdsBusinessFieldScreen
				instanceCode="SI-1"
				values={{}}
				onChange={vi.fn()}
				saveAction={{
					actionCode: "X",
					objectType: "T",
					objectCode: "SI-1",
					onAllowedClick: vi.fn(),
				}}
			/>,
		);
		expect(screen.getByTestId("tds-itt-not-editable-notice")).toBeInTheDocument();
		const submissionSection = screen.getByTestId("tds-group-submission-instructions");
		expect(submissionSection.querySelector("textarea")).toBeNull();
	});

	it("shows validation errors next to fields", () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("SAVE")) });
		render(
			<TdsBusinessFieldScreen
				instanceCode="SI-1"
				values={{ submission_deadline: "" }}
				onChange={vi.fn()}
				fieldErrors={{ submission_deadline: "Submission deadline is required." }}
				saveAction={{
					actionCode: "X",
					objectType: "T",
					objectCode: "SI-1",
					onAllowedClick: vi.fn(),
				}}
			/>,
		);
		expect(screen.getByTestId("tds-field-submission-deadline-error")).toHaveTextContent("Submission deadline is required.");
	});

	it("forwards field edits via onChange", () => {
		vi.stubGlobal("frappe", { call: vi.fn(async () => availabilityOk("SAVE")) });
		const onChange = vi.fn();
		render(
			<TdsBusinessFieldScreen
				instanceCode="SI-1"
				values={{ tender_title: "" }}
				onChange={onChange}
				saveAction={{
					actionCode: "X",
					objectType: "T",
					objectCode: "SI-1",
					onAllowedClick: vi.fn(),
				}}
			/>,
		);
		fireEvent.change(screen.getByTestId("tds-field-tender-title"), { target: { value: "Road upgrade" } });
		expect(onChange).toHaveBeenCalledWith("tender_title", "Road upgrade");
	});

	it("Save uses ActionAwareButton (SEC-0410)", async () => {
		const call = vi.fn(async (opts: { args?: { action_code?: string } }) =>
			availabilityOk(String(opts.args?.action_code || "")),
		);
		vi.stubGlobal("frappe", { call });
		const onSave = vi.fn();
		render(
			<TdsBusinessFieldScreen
				instanceCode="SI-100"
				values={{}}
				onChange={vi.fn()}
				saveAction={{
					actionCode: "EDIT_STD_INSTANCE_PARAMETERS",
					objectType: "StdEngineWorksInstance",
					objectCode: "SI-100",
					onAllowedClick: onSave,
				}}
			/>,
		);
		await waitFor(() => {
			expect(screen.getByTestId("tds-save-button")).not.toBeDisabled();
		});
		fireEvent.click(screen.getByTestId("tds-save-button"));
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
					object_code: "SI-100",
				}),
			}),
		);
	});
});
