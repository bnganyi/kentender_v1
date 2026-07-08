/**
 * UI-HARD-0001 — forces `tsc --noEmit` to resolve every workflow + shared barrel.
 * @packageDocumentation
 */
import * as adminLibrary from "./admin-library";
import * as approval from "./approval";
import * as evidenceAudit from "./evidence-audit";
import * as outputs from "./outputs";
import * as publication from "./publication";
import * as readiness from "./readiness";
import * as shared from "./shared";
import * as tenderConfiguration from "./tender-configuration";
import * as worksCompletion from "./works-completion";
import { STD_ENGINE_SHARED_A11Y, STD_ENGINE_SHARED_OPERATION_STATE } from "./shared";

/** Retained reference so imports are not tree-shaken away under `verbatimModuleSyntax` (if enabled later). */
export const __stdEngineWorkflowImportVerification = [
	adminLibrary,
	approval,
	evidenceAudit,
	outputs,
	publication,
	readiness,
	tenderConfiguration,
	worksCompletion,
	shared,
	STD_ENGINE_SHARED_OPERATION_STATE,
	STD_ENGINE_SHARED_A11Y,
] as const;
