/**
 * UI-HARD-0100 — Action availability API client (SEC-0410 `frappe.call` bridge).
 *
 * Desk convention: `await frappe.call(...)` resolves to `{ message: <handler_return> }`.
 */

import {
	SEC_API_ACTION_AVAILABILITY_BATCH_METHOD,
	SEC_API_ACTION_AVAILABILITY_METHOD,
} from "./constants";
import type {
	ActionAvailabilityApiErrorEnvelope,
	ActionAvailabilityBatchApiSuccessEnvelope,
	ActionAvailabilityRequest,
	ActionAvailabilityResponse,
	ActionAvailabilityRiskLevel,
} from "./actionAvailability.types";

import { ActionAvailabilityClientError } from "./actionAvailabilityClient.errors";

export type { ActionAvailabilityRequest, ActionAvailabilityResponse } from "./actionAvailability.types";
export { ActionAvailabilityClientError };

type FrappeCallArgs = {
	method: string;
	type?: string;
	args?: Record<string, unknown>;
};

type FrappeCallFn = (opts: FrappeCallArgs) => Promise<unknown>;

function getFrappeCall(): FrappeCallFn {
	const g = globalThis as typeof globalThis & {
		frappe?: { call?: FrappeCallFn };
	};
	const fn = g.frappe?.call;
	if (typeof fn !== "function") {
		throw new Error(
			"frappe.call is not available. The action availability client must run inside Frappe Desk (or tests must mock globalThis.frappe.call).",
		);
	}
	return fn;
}

function unwrapFrappeMessage(raw: unknown): unknown {
	if (raw && typeof raw === "object" && "message" in raw) {
		return (raw as { message: unknown }).message;
	}
	return raw;
}

function asRisk(value: unknown): ActionAvailabilityRiskLevel {
	const s = String(value || "").trim();
	if (s === "Low" || s === "Medium" || s === "High" || s === "Critical") {
		return s;
	}
	return "Medium";
}

function normalizeAvailabilityRow(row: Record<string, unknown>): ActionAvailabilityResponse {
	const denial = row.denial_code;
	const req = row.required_permission;
	const ostate = row.object_state;
	return {
		action_code: String(row.action_code ?? ""),
		allowed: Boolean(row.allowed),
		message: String(row.message ?? ""),
		risk_level: asRisk(row.risk_level),
		requires_confirmation: Boolean(row.requires_confirmation),
		audit_on_attempt: Boolean(row.audit_on_attempt),
		denial_code: denial == null || denial === "" ? null : String(denial),
		required_permission: req == null || req === "" ? null : String(req),
		object_state: ostate == null || ostate === "" ? null : String(ostate),
	};
}

function assertErrorEnvelope(value: unknown): ActionAvailabilityApiErrorEnvelope {
	if (!value || typeof value !== "object") {
		return {
			success: false,
			error_code: "SEC_CLIENT_INVALID_ENVELOPE",
			message: "Server returned an empty or non-object response.",
			details: {},
		};
	}
	const o = value as Record<string, unknown>;
	if (o.success !== false) {
		return {
			success: false,
			error_code: "SEC_CLIENT_INVALID_ENVELOPE",
			message: "Server returned success without an availability payload.",
			details: { raw: value },
		};
	}
	return {
		success: false,
		error_code: String(o.error_code || "SEC_CLIENT_UNKNOWN_ERROR"),
		message: String(o.message || "Request failed."),
		details: typeof o.details === "object" && o.details !== null ? (o.details as Record<string, unknown>) : {},
	};
}

async function invoke(method: string, args: Record<string, unknown>): Promise<unknown> {
	const call = getFrappeCall();
	const raw = await call({
		method,
		type: "POST",
		args,
	});
	return unwrapFrappeMessage(raw);
}

export type GetActionAvailabilityOptions = {
	/** Optional explicit actor (SEC-0410 `actor`); defaults to session user server-side. */
	actor?: string;
};

/**
 * Single action availability (pack `getActionAvailability`).
 */
export async function getActionAvailability(
	request: ActionAvailabilityRequest,
	options?: GetActionAvailabilityOptions,
): Promise<ActionAvailabilityResponse> {
	const args: Record<string, unknown> = {
		action_code: request.action_code,
		object_type: request.object_type,
		object_code: request.object_code,
		context: request.context ?? {},
	};
	if (options?.actor) {
		args.actor = options.actor;
	}
	const payload = await invoke(SEC_API_ACTION_AVAILABILITY_METHOD, args);
	if (!payload || typeof payload !== "object") {
		throw new ActionAvailabilityClientError({
			success: false,
			error_code: "SEC_CLIENT_EMPTY_RESPONSE",
			message: "Empty response from action availability API.",
			details: {},
		});
	}
	const o = payload as Record<string, unknown>;
	if (o.success === false) {
		throw new ActionAvailabilityClientError(assertErrorEnvelope(o));
	}
	if (o.success !== true) {
		throw new ActionAvailabilityClientError({
			success: false,
			error_code: "SEC_CLIENT_INVALID_ENVELOPE",
			message: "Response missing success flag.",
			details: { raw: payload },
		});
	}
	return normalizeAvailabilityRow(o);
}

export type GetBatchActionAvailabilityOptions = {
	/** Merged into each item context (SEC-0410 batch `context`). */
	context?: Record<string, unknown>;
	actor?: string;
};

/**
 * Batch action availability (pack `getBatchActionAvailability`).
 */
export async function getBatchActionAvailability(
	items: ActionAvailabilityRequest[],
	options?: GetBatchActionAvailabilityOptions,
): Promise<ActionAvailabilityResponse[]> {
	if (!Array.isArray(items) || items.length === 0) {
		throw new ActionAvailabilityClientError({
			success: false,
			error_code: "SEC_API_ITEMS_REQUIRED",
			message: "items is required and must contain at least one request object.",
			details: {},
		});
	}
	const args: Record<string, unknown> = {
		items: items.map((row) => ({
			action_code: row.action_code,
			object_type: row.object_type,
			object_code: row.object_code,
			context: row.context ?? {},
		})),
		context: options?.context ?? {},
	};
	if (options?.actor) {
		args.actor = options.actor;
	}
	const payload = await invoke(SEC_API_ACTION_AVAILABILITY_BATCH_METHOD, args);
	if (!payload || typeof payload !== "object") {
		throw new ActionAvailabilityClientError({
			success: false,
			error_code: "SEC_CLIENT_EMPTY_RESPONSE",
			message: "Empty response from batch action availability API.",
			details: {},
		});
	}
	const o = payload as Record<string, unknown>;
	if (o.success === false) {
		throw new ActionAvailabilityClientError(assertErrorEnvelope(o));
	}
	if (o.success !== true) {
		throw new ActionAvailabilityClientError({
			success: false,
			error_code: "SEC_CLIENT_INVALID_ENVELOPE",
			message: "Batch response missing success flag.",
			details: { raw: payload },
		});
	}
	const typed = o as unknown as ActionAvailabilityBatchApiSuccessEnvelope;
	const rows = Array.isArray(typed.items) ? typed.items : [];
	return rows.map((row) => normalizeAvailabilityRow(row as unknown as Record<string, unknown>));
}

/** Pack camelCase aliases. */
export const getActionAvailabilityBatch = getBatchActionAvailability;
