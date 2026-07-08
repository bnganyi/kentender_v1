import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
	BOQ_RATE_PREPARATION_WARNING_PACK,
	BOQ_STALENESS_WARNING_PACK,
} from "./boqPreparationScreen.types";
import { BoqPreparationScreen } from "./BoqPreparationScreen";

const defaultHeader = {
	currency: "KES",
	pricing_model: "Item rate",
	arithmetic_correction_stage: "Post-opening",
};

const defaultProps = {
	header: defaultHeader,
	bills: [{ id: "b1", code: "BILL-1", title: "Civil works" }],
	items: [
		{
			id: "i1",
			item_no: "1.1",
			description: "Excavation",
			item_type: "Works",
			quantity: "120",
			unit: "m3",
			supplier_input_mode: "Rate Only",
			provisional_or_fixed: "Fixed",
		},
	],
	validationMessages: [] as string[],
};

describe("BoqPreparationScreen (UI-HARD-0800)", () => {
	afterEach(() => {
		cleanup();
	});

	it("exposes pack data-testids", () => {
		render(<BoqPreparationScreen {...defaultProps} />);
		expect(screen.getByTestId("boq-screen")).toBeInTheDocument();
		expect(screen.getByTestId("boq-header")).toBeInTheDocument();
		expect(screen.getByTestId("boq-bills-list")).toBeInTheDocument();
		expect(screen.getByTestId("boq-items-table")).toBeInTheDocument();
		expect(screen.getByTestId("boq-import-button")).toBeInTheDocument();
		expect(screen.getByTestId("boq-validation-summary")).toBeInTheDocument();
		expect(screen.getByTestId("boq-supplier-rate-field-absent")).toBeInTheDocument();
	});

	it("does not render supplier rate columns on the items table", () => {
		render(<BoqPreparationScreen {...defaultProps} />);
		const table = screen.getByTestId("boq-items-table");
		const headers = within(table).getAllByRole("columnheader");
		const text = headers.map((h) => h.textContent).join(" ");
		expect(text).not.toMatch(/\bRate\b/i);
		expect(text).not.toMatch(/supplier rate/i);
	});

	it("shows quantity owner as Procuring Entity and supplier input mode as Rate Only by default", () => {
		render(<BoqPreparationScreen {...defaultProps} />);
		const header = screen.getByTestId("boq-header");
		expect(within(header).getByText("Procuring Entity")).toBeInTheDocument();
		expect(within(header).getByText("Rate Only")).toBeInTheDocument();
	});

	it("shows pack staleness warning when BOQ changes matter post-outputs", () => {
		const { rerender } = render(<BoqPreparationScreen {...defaultProps} showStalenessWarning={false} />);
		expect(screen.queryByTestId("boq-staleness-warning")).not.toBeInTheDocument();
		rerender(<BoqPreparationScreen {...defaultProps} showStalenessWarning />);
		expect(screen.getByTestId("boq-staleness-warning")).toHaveTextContent(BOQ_STALENESS_WARNING_PACK);
	});

	it("includes pack rate-attempt guidance in validation summary", () => {
		render(<BoqPreparationScreen {...defaultProps} />);
		expect(screen.getByTestId("boq-validation-summary")).toHaveTextContent(BOQ_RATE_PREPARATION_WARNING_PACK);
	});

	it("lists structured validation / import errors", () => {
		render(
			<BoqPreparationScreen
				{...defaultProps}
				validationMessages={["Row 4: quantity must be numeric.", "Bill BILL-2: duplicate item number 2.1."]}
			/>,
		);
		const box = screen.getByTestId("boq-validation-summary");
		expect(box).toHaveTextContent("Row 4: quantity must be numeric.");
		expect(box).toHaveTextContent("duplicate item number");
	});

	it("fires import callback", () => {
		const onImport = vi.fn();
		render(<BoqPreparationScreen {...defaultProps} onImportClick={onImport} />);
		fireEvent.click(screen.getByTestId("boq-import-button"));
		expect(onImport).toHaveBeenCalled();
	});
});
