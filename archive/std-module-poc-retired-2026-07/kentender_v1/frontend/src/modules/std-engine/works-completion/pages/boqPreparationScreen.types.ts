/**
 * UI-HARD-0800 — BOQ preparation (pack §13 BOQ, doc §13).
 */

export type BoqHeaderValues = {
	currency: string;
	pricing_model: string;
	/** Shown as Procuring Entity when omitted (pack acceptance). */
	quantity_owner?: string;
	/** Shown as Rate Only when omitted (pack acceptance). */
	supplier_input_mode?: string;
	arithmetic_correction_stage: string;
};

export type BoqBill = {
	id: string;
	code: string;
	title: string;
};

export type BoqItemRow = {
	id: string;
	item_no: string;
	description: string;
	unit: string;
	quantity: string;
	item_type: string;
	supplier_input_mode: string;
	provisional_or_fixed: string;
};

/** Pack “Required Staleness Warning” (exact). */
export const BOQ_STALENESS_WARNING_PACK =
	"Changing the BOQ will make the Tender Document Bundle, Submission Rules, Evaluation Rules, and Contract Carry-Forward stale.";

/** Pack “Required Warning on Rate Attempt” (exact). */
export const BOQ_RATE_PREPARATION_WARNING_PACK =
	"Supplier rates are entered during bid submission, not during tender preparation.";

export type BoqPreparationScreenProps = {
	header: BoqHeaderValues;
	bills: BoqBill[];
	items: BoqItemRow[];
	/** Structured validation / import errors (doc §13.5). */
	validationMessages: string[];
	showStalenessWarning?: boolean;
	onHeaderFieldChange?: (field: keyof BoqHeaderValues, value: string) => void;
	onImportClick?: () => void;
	onExportClick?: () => void;
};
