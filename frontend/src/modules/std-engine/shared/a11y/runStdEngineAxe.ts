/**
 * UI-HARD-1500 — automated axe checks for std-engine React surfaces (pack §20).
 *
 * JSDOM partial trees skip rules that require a full document (landmark, `lang`, contrast).
 *
 * `axe-core` ships `export =` typings; we use a narrow runtime wrapper for ESM + `moduleResolution: "Bundler"`.
 */

import axeModule from "axe-core";

type AxeViolation = {
	id: string;
	impact?: string | null;
	help: string;
	nodes?: unknown[];
};

type AxeRunResult = { violations: AxeViolation[] };

type AxeRunner = {
	run(context: HTMLElement, options?: Record<string, unknown>): Promise<AxeRunResult>;
};

const axe = axeModule as unknown as AxeRunner;

/** Rules that routinely false-positive or are unsupported in Vitest JSDOM partial renders. */
export const STD_ENGINE_AXE_PARTIAL_TREE_OPTIONS: Record<string, unknown> = {
	rules: {
		"color-contrast": { enabled: false },
		"meta-viewport": { enabled: false },
		"page-has-heading-one": { enabled: false },
		"landmark-one-main": { enabled: false },
		region: { enabled: false },
		"html-has-lang": { enabled: false },
		"document-title": { enabled: false },
	},
};

const DEFAULT_IMPACT = ["critical", "serious"] as const;

export function formatStdEngineAxeViolations(violations: AxeViolation[]): string {
	return violations
		.map((v) => `${v.id} [${v.impact}] — ${v.nodes?.length ?? 0} node(s): ${v.help}`)
		.join("\n");
}

/** Returns WCAG-style violations at or above configured impact (defaults: critical + serious). */
export async function runStdEngineAxe(
	container: HTMLElement,
	options?: Record<string, unknown>,
	impactFilter: readonly string[] = DEFAULT_IMPACT,
): Promise<AxeViolation[]> {
	const results = await axe.run(container, {
		...STD_ENGINE_AXE_PARTIAL_TREE_OPTIONS,
		...options,
	});
	return results.violations.filter((v) => v.impact && impactFilter.includes(v.impact));
}
