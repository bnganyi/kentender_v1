import type { StdEngineBlockerItem } from "../../shared";

/** One eligible STD binding option (doc §7.4). */
export type ReleaseStdOption = {
	versionCode: string;
	title: string;
	revision: string;
	authority: string;
	profile?: string;
	supportedMethods: string[];
	requiresBoq: boolean;
	requiresSpecifications: boolean;
	requiresDrawings: boolean;
};

export type ReleaseEligibilityStatus = "eligible" | "blocked" | "unknown";

export type ReleaseToTenderPageProps = {
	packageCode: string;
	packageTitle: string;
	summaryLines?: { label: string; value: string }[];
	eligibilityStatus: ReleaseEligibilityStatus;
	/** Secondary line under eligibility (e.g. compatible STD summary from wireframe). */
	compatibleStdSummary?: string;
	/** Doc §7.3 — use `code` prefixes `PLAN_`, `STD_`, `PERM_`, `REL_` for grouping. */
	blockers?: StdEngineBlockerItem[];
	stdOptions: ReleaseStdOption[];
	/** Controlled selection (optional); when omitted, single-option auto-select is internal. */
	selectedStdVersionCode?: string;
	onSelectedStdChange?: (versionCode: string) => void;
	/** After successful release — drives [G] + configure link. */
	releaseResult?: { tenderCode: string; stdInstanceCode: string } | null;
	/** SEC-0410 / action availability context for release. */
	releaseAvailabilityContext?: Record<string, unknown>;
	/** Invoked when `ActionAwareButton` fires after backend allows release (host performs POST). */
	onReleaseClick?: () => void;
};
