import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { WorksRequirementsScreen } from "./WorksRequirementsScreen";

describe("WorksRequirementsScreen (UI-HARD-0700)", () => {
	afterEach(() => {
		cleanup();
	});

	it("exposes pack-required data-testids for screen, listed components, upload, and classification", () => {
		render(<WorksRequirementsScreen />);
		expect(screen.getByTestId("works-requirements-screen")).toBeInTheDocument();
		expect(screen.getByTestId("works-component-specifications")).toBeInTheDocument();
		expect(screen.getByTestId("works-component-site-information")).toBeInTheDocument();
		expect(screen.getByTestId("works-component-hse")).toBeInTheDocument();
		expect(screen.getByTestId("works-component-method-statement")).toBeInTheDocument();
		expect(screen.getByTestId("works-attachment-upload")).toBeInTheDocument();
		expect(screen.getByTestId("works-attachment-classification")).toBeInTheDocument();
	});

	it("renders all seven doc §11.1 component cards with status visible", () => {
		render(
			<WorksRequirementsScreen
				componentStatuses={{
					specifications: "Complete",
					site_information: "Incomplete",
					hse: "Needs Attention",
				}}
			/>,
		);
		expect(screen.getByTestId("works-component-environmental-social")).toBeInTheDocument();
		expect(screen.getByTestId("works-component-work-programme")).toBeInTheDocument();
		expect(screen.getByTestId("works-component-quality")).toBeInTheDocument();
		const spec = screen.getByTestId("works-component-specifications");
		expect(within(spec).getByText("Complete")).toBeInTheDocument();
		expect(within(screen.getByTestId("works-component-site-information")).getByText("Incomplete")).toBeInTheDocument();
		expect(within(screen.getByTestId("works-component-hse")).getByText("Needs Attention")).toBeInTheDocument();
	});

	it("keeps file upload disabled until component, section, and classification are set", () => {
		render(<WorksRequirementsScreen />);
		const upload = screen.getByTestId("works-attachment-upload");
		const fileInput = within(upload).getByLabelText(/file/i) as HTMLInputElement;
		expect(fileInput).toBeDisabled();
		fireEvent.change(within(upload).getByLabelText(/component binding/i), { target: { value: "specifications" } });
		expect(fileInput).toBeDisabled();
		fireEvent.change(within(upload).getByLabelText(/section binding/i), { target: { value: "Section IV" } });
		expect(fileInput).toBeDisabled();
		fireEvent.change(screen.getByTestId("works-attachment-classification"), { target: { value: "internal_only" } });
		expect(fileInput).not.toBeDisabled();
	});

	it("shows supplier-facing classification guidance when Supplier Facing is selected", () => {
		render(<WorksRequirementsScreen />);
		const upload = screen.getByTestId("works-attachment-upload");
		fireEvent.change(within(upload).getByLabelText(/component binding/i), { target: { value: "quality" } });
		fireEvent.change(within(upload).getByLabelText(/section binding/i), { target: { value: "Sec A" } });
		fireEvent.change(screen.getByTestId("works-attachment-classification"), { target: { value: "supplier_facing" } });
		expect(screen.getByText(/Supplier Facing:/i)).toBeInTheDocument();
		expect(screen.getByText(/Bundle and DCM readiness/i)).toBeInTheDocument();
	});

	it("notifies host when a file is chosen with bindings", () => {
		const onChosen = vi.fn();
		render(<WorksRequirementsScreen onAttachmentFileChosen={onChosen} />);
		const upload = screen.getByTestId("works-attachment-upload");
		fireEvent.change(within(upload).getByLabelText(/component binding/i), { target: { value: "hse" } });
		fireEvent.change(within(upload).getByLabelText(/section binding/i), { target: { value: "Section VI" } });
		fireEvent.change(screen.getByTestId("works-attachment-classification"), { target: { value: "contract_facing" } });
		const file = new File(["x"], "hse.pdf", { type: "application/pdf" });
		const fileInput = within(upload).getByLabelText(/file/i) as HTMLInputElement;
		fireEvent.change(fileInput, { target: { files: [file] } });
		expect(onChosen).toHaveBeenCalledWith(
			expect.objectContaining({
				componentId: "hse",
				sectionCode: "Section VI",
				classification: "contract_facing",
				file,
			}),
		);
	});
});
