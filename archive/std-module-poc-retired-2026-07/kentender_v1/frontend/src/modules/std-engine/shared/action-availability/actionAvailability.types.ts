/**
 * UI-HARD-0100 / pack §5 — request and response contracts aligned with
 * `ActionAvailabilityService` + SEC-0410 envelope (`success`, `error_code`, …).
 */

export type ActionAvailabilityRiskLevel = "Low" | "Medium" | "High" | "Critical";

/** Single evaluation request (matches SEC-0410 `sec_api_action_availability` args). */
export type ActionAvailabilityRequest = {
	action_code: string;
	object_type: string;
	object_code: string;
	context?: Record<string, unknown>;
};

/** Normalized availability row (matches pack + SEC-0400 payload fields). */
export type ActionAvailabilityResponse = {
	action_code: string;
	allowed: boolean;
	denial_code?: string | null;
	message: string;
	required_permission?: string | null;
	object_state?: string | null;
	risk_level: ActionAvailabilityRiskLevel;
	requires_confirmation: boolean;
	audit_on_attempt: boolean;
};

/** SEC-0410 error envelope (`success: false`). */
export type ActionAvailabilityApiErrorEnvelope = {
	success: false;
	error_code: string;
	message: string;
	details: Record<string, unknown>;
};

/** Successful SEC-0410 single call: availability fields + actor + `success`. */
export type ActionAvailabilityApiSuccessEnvelope = ActionAvailabilityResponse & {
	success: true;
	actor_user_code: string;
};

/** Successful SEC-0410 batch call. */
export type ActionAvailabilityBatchApiSuccessEnvelope = {
	success: true;
	actor_user_code: string;
	items: ActionAvailabilityResponse[];
};
