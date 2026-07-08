export type BlockerSeverity = "critical" | "warning" | "info";

/** One readiness / validation blocker row (doc §15.4, pack §6). */
export type StdEngineBlockerItem = {
	/** Stable id for selectors and analytics; not shown to ordinary users as primary copy. */
	code: string;
	message: string;
	severity: BlockerSeverity;
	affectedArea: string;
	whyItMatters?: string;
	/** Plain-language fix / next step. */
	resolutionAction?: string;
	/** In-app or desk hash link to the affected workflow section. */
	affectedSectionHref?: string;
	/** Optional deep link for a dedicated resolution screen. */
	resolutionHref?: string;
};
