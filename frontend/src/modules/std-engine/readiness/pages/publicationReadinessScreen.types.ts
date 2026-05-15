import type { ActionAwareButtonProps, ReadinessUiStatus } from "../../shared";

/** Doc §15.4 + pack — blocker row with stage link. */
export type ReadinessBlockerItem = {
  message: string;
  affectedArea: string;
  whyItMatters: string;
  resolutionAction: string;
  stageLinkHref?: string;
  stageLinkLabel?: string;
};

export type ReadinessWarningItem = {
  message: string;
};

export type ReadinessCompletionCategoryRow = {
  id: string;
  label: string;
  status: string;
};

export type ReadinessOutputStatusRow = {
  outputLabel: string;
  stale: boolean;
  statusLine: string;
};

export type PublicationReadinessScreenProps = {
  tenderCode: string;
  overallStatus: ReadinessUiStatus;
  criticalBlockers: ReadinessBlockerItem[];
  warnings: ReadinessWarningItem[];
  completionCategories: ReadinessCompletionCategoryRow[];
  outputStatuses: ReadinessOutputStatusRow[];
  evidenceReadinessSummary: string;
  runReadinessAction: Omit<ActionAwareButtonProps, "buttonTestId">;
  nextAction?: Omit<ActionAwareButtonProps, "buttonTestId"> | null;
};
