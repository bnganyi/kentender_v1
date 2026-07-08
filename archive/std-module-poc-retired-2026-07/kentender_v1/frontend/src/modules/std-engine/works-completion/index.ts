/** Works completion workspace workflow (UI-HARD-0500+). */
export const STD_ENGINE_WORKFLOW_WORKS_COMPLETION = "std-engine/works-completion" as const;
export { OutputImpactPanel } from "./components/OutputImpactPanel";
export { OUTPUT_IMPACT_KIND_META } from "./components/outputImpactPanel.types";
export type { OutputImpactKind, OutputImpactPanelProps } from "./components/outputImpactPanel.types";
export { BoqPreparationScreen } from "./pages/BoqPreparationScreen";
export { BOQ_RATE_PREPARATION_WARNING_PACK, BOQ_STALENESS_WARNING_PACK } from "./pages/boqPreparationScreen.types";
export type {
	BoqBill,
	BoqHeaderValues,
	BoqItemRow,
	BoqPreparationScreenProps,
} from "./pages/boqPreparationScreen.types";
export { DrawingRegisterScreen } from "./pages/DrawingRegisterScreen";
export {
	DRAWING_REGISTER_SECTION_VII_DISPLAY,
	DRAWING_REGISTER_STALENESS_WARNING_PACK,
	EMPTY_DRAWING_REGISTER_DRAFT,
} from "./pages/drawingRegisterScreen.types";
export type { DrawingRegisterDraft, DrawingRegisterRow, DrawingRegisterScreenProps } from "./pages/drawingRegisterScreen.types";
export { WorksCompletionWorkspacePage } from "./pages/WorksCompletionWorkspacePage";
export { WorksRequirementsScreen } from "./pages/WorksRequirementsScreen";
export { WORKS_REQUIREMENT_CARD_DEFS } from "./pages/worksRequirementsScreen.types";
export type {
	AttachmentClassification,
	WorksRequirementCardDef,
	WorksRequirementComponentId,
	WorksRequirementStatus,
	WorksRequirementsScreenProps,
} from "./pages/worksRequirementsScreen.types";
export { WORKS_COMPLETION_SIDEBAR_STAGES } from "./pages/worksCompletionWorkspace.types";
export type {
	WorksCompletionAvailabilityAction,
	WorksCompletionStageId,
	WorksCompletionStageRow,
	WorksCompletionWorkspacePageProps,
} from "./pages/worksCompletionWorkspace.types";
