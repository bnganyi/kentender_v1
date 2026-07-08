/**
 * UI-HARD-0510 — Output impact panel (pack §11 “Output Impact Panel”, doc §9.6).
 */

export type OutputImpactKind = "bundle" | "dsm" | "dom" | "dem" | "dcm";

/** Pack plain-label table + matching `data-testid` suffixes. */
export const OUTPUT_IMPACT_KIND_META: Record<
	OutputImpactKind,
	{ itemTestId: string; displayLabel: string }
> = {
	bundle: { itemTestId: "output-impact-item-bundle", displayLabel: "Tender Document Bundle" },
	dsm: { itemTestId: "output-impact-item-dsm", displayLabel: "Submission Rules (DSM)" },
	dom: { itemTestId: "output-impact-item-dom", displayLabel: "Opening Register (DOM)" },
	dem: { itemTestId: "output-impact-item-dem", displayLabel: "Evaluation Rules (DEM)" },
	dcm: { itemTestId: "output-impact-item-dcm", displayLabel: "Contract Carry-Forward (DCM)" },
};

export type OutputImpactPanelProps = {
	/**
	 * Output kinds affected by the current edit / pending change.
	 * Order is preserved (first occurrence wins if duplicates are passed).
	 */
	affectedKinds: OutputImpactKind[];
	/** Lead-in line above the list (pack example). */
	leadIn?: string;
	/** Short explanation of why regeneration matters (staleness / alignment). */
	explanation?: string | null;
};
