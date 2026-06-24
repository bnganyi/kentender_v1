/**
 * PP3/P5 — forbidden technical strings in ordinary Procurement Planning UI.
 */
export const P5_ORDINARY_FLOW_FORBIDDEN_LEAKAGE: RegExp[] = [
	/PLANINCL-/i,
	/source_object_code/i,
	/target_object_code/i,
	/source object/i,
	/target object/i,
	/technical_refs_json/i,
	/locked_summary_json/i,
	/passed_forward_summary_json/i,
	/audit_event_ref/i,
	/handoff code/i,
	/technical refs/i,
];

export function assertNoOrdinaryFlowLeakage(text: string, context?: string): void {
	const body = String(text || '');
	for (const pattern of P5_ORDINARY_FLOW_FORBIDDEN_LEAKAGE) {
		if (pattern.test(body)) {
			const label = context ? `${context}: ` : '';
			throw new Error(`${label}ordinary flow must not contain ${pattern}`);
		}
	}
}
