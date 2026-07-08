import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SEC_API_ACTION_AVAILABILITY_METHOD } from "../../shared/action-availability/constants";
import { OfficialStdLibraryPage } from "./OfficialStdLibraryPage";

function availabilityPayload(action_code: string) {
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

describe("OfficialStdLibraryPage (UI-HARD-0200)", () => {
	afterEach(() => {
		cleanup();
		vi.unstubAllGlobals();
		vi.restoreAllMocks();
	});

	it("renders pack selectors and uses ActionAwareButton-backed header actions", async () => {
		const call = vi.fn(async (opts: { method?: string; args?: { action_code?: string } }) => {
			expect(opts.method).toBe(SEC_API_ACTION_AVAILABILITY_METHOD);
			const code = opts.args?.action_code || "";
			return availabilityPayload(code);
		});
		vi.stubGlobal("frappe", { call });

		const onImport = vi.fn();
		render(<OfficialStdLibraryPage templateCount={0} onImportClick={onImport} />);

		expect(screen.getByTestId("std-library-page")).toBeInTheDocument();
		expect(screen.getByTestId("std-library-header-title")).toHaveTextContent("Official STD Library");
		expect(screen.getByTestId("std-library-create-instance-button-absent")).toBeInTheDocument();
		expect(screen.getByTestId("std-library-advanced-view-toggle")).toBeInTheDocument();

		await waitFor(() => {
			expect(screen.getByTestId("std-library-import-package-button")).not.toBeDisabled();
		});
		fireEvent.click(screen.getByTestId("std-library-import-package-button"));
		expect(onImport).toHaveBeenCalled();
	});

	it("does not surface prohibited primary-action labels", () => {
		vi.stubGlobal("frappe", {
			call: vi.fn(async (opts: { args?: { action_code?: string } }) =>
				availabilityPayload(String(opts.args?.action_code || "")),
			),
		});
		const { container } = render(<OfficialStdLibraryPage />);
		const text = container.textContent || "";
		expect(text).not.toContain("Create STD Instance");
		expect(text).not.toContain("Release to Tender");
		expect(text).not.toContain("Publish Tender");
	});
});
