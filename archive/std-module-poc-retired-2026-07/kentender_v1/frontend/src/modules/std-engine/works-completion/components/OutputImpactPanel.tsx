/**
 * UI-HARD-0510 — Output impact panel (pack §11, doc §9.6).
 *
 * Surfaces which generated outputs must be regenerated after source data changes, using plain labels.
 */

import type { ReactElement } from "react";

import { OUTPUT_IMPACT_KIND_META, type OutputImpactKind, type OutputImpactPanelProps } from "./outputImpactPanel.types";

const DEFAULT_LEAD_IN = "Changing this value will require regeneration of:";

const DEFAULT_EXPLANATION_WITH_ITEMS =
	"Regeneration refreshes these generated documents from your latest entries so bidders and evaluators do not rely on stale versions.";

const DEFAULT_EXPLANATION_EMPTY =
	"When a field you change affects standard outputs, those outputs are listed here so you can see what will need regeneration before publication.";

function dedupePreserveOrder(kinds: OutputImpactKind[]): OutputImpactKind[] {
	const seen = new Set<OutputImpactKind>();
	const out: OutputImpactKind[] = [];
	for (const k of kinds) {
		if (!seen.has(k)) {
			seen.add(k);
			out.push(k);
		}
	}
	return out;
}

export function OutputImpactPanel(props: OutputImpactPanelProps): ReactElement {
	const { affectedKinds, leadIn = DEFAULT_LEAD_IN, explanation } = props;
	const unique = dedupePreserveOrder(affectedKinds);
	const hasItems = unique.length > 0;
	const resolvedExplanation = explanation === undefined ? (hasItems ? DEFAULT_EXPLANATION_WITH_ITEMS : DEFAULT_EXPLANATION_EMPTY) : explanation;

	return (
		<div data-testid="output-impact-panel">
			{hasItems ? (
				<>
					<p className="small" style={{ marginBottom: "0.35rem" }}>
						{leadIn}
					</p>
					<ul className="small" style={{ marginBottom: "0.35rem", paddingLeft: "1.25rem" }}>
						{unique.map((kind) => (
							<li key={kind} data-testid={OUTPUT_IMPACT_KIND_META[kind].itemTestId}>
								{OUTPUT_IMPACT_KIND_META[kind].displayLabel}
							</li>
						))}
					</ul>
				</>
			) : (
				<p className="text-muted small" style={{ marginBottom: "0.35rem" }}>
					No affected outputs are listed for the current field yet.
				</p>
			)}
			{resolvedExplanation ? (
				<p className="text-muted small" style={{ marginBottom: 0 }}>
					{resolvedExplanation}
				</p>
			) : null}
		</div>
	);
}
