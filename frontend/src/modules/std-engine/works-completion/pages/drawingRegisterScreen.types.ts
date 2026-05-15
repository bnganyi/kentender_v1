/**
 * UI-HARD-0710 — Drawing register (pack §13 “Drawing Register”, doc §12).
 */

/** Pack “Required Fields” + row identity for the register table. */
export type DrawingRegisterRow = {
	id: string;
	drawing_code: string;
	title: string;
	revision: string;
	file_reference: string;
	/** Stored code; UI defaults/fixed to Section VII for drawings (doc §12.2). */
	section_code: string;
	classification: string;
	issue_status: string;
};

/** Doc §12.2 / pack “Section Rule” display. */
export const DRAWING_REGISTER_SECTION_VII_DISPLAY = "Section VII — Drawings";

/** Pack “Required Warning” (exact copy for `drawing-staleness-warning`). */
export const DRAWING_REGISTER_STALENESS_WARNING_PACK =
	"Changing this drawing will make the Tender Document Bundle, Evaluation Rules (DEM), and Contract Carry-Forward (DCM) stale.";

export type DrawingRegisterDraft = {
	drawing_code: string;
	title: string;
	revision: string;
	file_reference: string;
	classification: string;
	issue_status: string;
};

export const EMPTY_DRAWING_REGISTER_DRAFT: DrawingRegisterDraft = {
	drawing_code: "",
	title: "",
	revision: "",
	file_reference: "",
	classification: "",
	issue_status: "",
};

export type DrawingRegisterScreenProps = {
	rows: DrawingRegisterRow[];
	/** When true, show pack staleness warning (e.g. outputs already generated). */
	showStalenessWarning?: boolean;
	/**
	 * Optional controlled draft for the “add” row; if omitted the screen manages its own draft state.
	 */
	draft?: DrawingRegisterDraft;
	onDraftChange?: (draft: DrawingRegisterDraft) => void;
	/** Invoked with draft merged with fixed Section VII binding. Host persists and clears draft. */
	onAddDrawing?: (row: Omit<DrawingRegisterRow, "id">) => void;
};
