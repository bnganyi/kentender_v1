import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
	DRAWING_REGISTER_SECTION_VII_DISPLAY,
	DRAWING_REGISTER_STALENESS_WARNING_PACK,
} from "./drawingRegisterScreen.types";
import { DrawingRegisterScreen } from "./DrawingRegisterScreen";

const sampleRows = [
	{
		id: "1",
		drawing_code: "DWG-01",
		title: "General arrangement",
		revision: "A",
		file_reference: "s3://bucket/dwg-01.pdf",
		section_code: "SECTION_VII_DRAWINGS",
		classification: "Contract Facing",
		issue_status: "Issued",
	},
];

describe("DrawingRegisterScreen (UI-HARD-0710)", () => {
	afterEach(() => {
		cleanup();
	});

	it("exposes pack data-testids", () => {
		render(<DrawingRegisterScreen rows={[]} />);
		expect(screen.getByTestId("drawing-register-screen")).toBeInTheDocument();
		expect(screen.getByTestId("drawing-register-table")).toBeInTheDocument();
		expect(screen.getByTestId("drawing-add-row")).toBeInTheDocument();
		expect(screen.getByTestId("drawing-field-code")).toBeInTheDocument();
		expect(screen.getByTestId("drawing-field-revision")).toBeInTheDocument();
		expect(screen.getByTestId("drawing-section-vii-binding")).toBeInTheDocument();
	});

	it("shows fixed Section VII binding (doc §12.2)", () => {
		render(<DrawingRegisterScreen rows={[]} />);
		expect(screen.getByTestId("drawing-section-vii-binding")).toHaveTextContent(DRAWING_REGISTER_SECTION_VII_DISPLAY);
	});

	it("shows pack staleness warning copy when outputs exist / flag set", () => {
		const { rerender } = render(<DrawingRegisterScreen rows={[]} showStalenessWarning={false} />);
		expect(screen.queryByTestId("drawing-staleness-warning")).not.toBeInTheDocument();
		rerender(<DrawingRegisterScreen rows={[]} showStalenessWarning />);
		const w = screen.getByTestId("drawing-staleness-warning");
		expect(w).toHaveTextContent(DRAWING_REGISTER_STALENESS_WARNING_PACK);
	});

	it("renders register rows with required columns", () => {
		render(<DrawingRegisterScreen rows={sampleRows} />);
		const table = screen.getByTestId("drawing-register-table");
		expect(within(table).getByText("DWG-01")).toBeInTheDocument();
		expect(within(table).getByText("General arrangement")).toBeInTheDocument();
		expect(within(table).getByText("A")).toBeInTheDocument();
		expect(within(table).getByText("s3://bucket/dwg-01.pdf")).toBeInTheDocument();
		expect(within(table).getByText("Issued")).toBeInTheDocument();
		expect(within(table).getAllByText(DRAWING_REGISTER_SECTION_VII_DISPLAY).length).toBeGreaterThanOrEqual(1);
	});

	it("adds drawing with Section VII code via callback", () => {
		const onAdd = vi.fn();
		render(<DrawingRegisterScreen rows={[]} onAddDrawing={onAdd} />);
		fireEvent.change(screen.getByTestId("drawing-field-code"), { target: { value: "DWG-02" } });
		fireEvent.change(screen.getByTestId("drawing-field-revision"), { target: { value: "B" } });
		fireEvent.change(screen.getByLabelText(/title/i), { target: { value: "Detail" } });
		fireEvent.change(screen.getByLabelText(/file reference/i), { target: { value: "file.pdf" } });
		fireEvent.change(screen.getByLabelText(/^classification/i), { target: { value: "Internal Only" } });
		fireEvent.change(screen.getByLabelText(/issue status/i), { target: { value: "Draft" } });
		fireEvent.click(screen.getByTestId("drawing-add-row"));
		expect(onAdd).toHaveBeenCalledWith(
			expect.objectContaining({
				drawing_code: "DWG-02",
				title: "Detail",
				revision: "B",
				file_reference: "file.pdf",
				section_code: "SECTION_VII_DRAWINGS",
				classification: "Internal Only",
				issue_status: "Draft",
			}),
		);
	});
});
