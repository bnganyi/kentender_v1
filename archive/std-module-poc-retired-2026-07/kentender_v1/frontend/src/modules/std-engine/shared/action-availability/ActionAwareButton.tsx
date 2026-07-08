/**
 * UI-HARD-0110 — `<ActionAwareButton />` (pack §6).
 *
 * Renders from `getActionAvailability` (UI-HARD-0100); never enables legal actions from props alone.
 */

import { useCallback, useEffect, useId, useMemo, useState, type ReactElement } from "react";

import { ActionAvailabilityClientError, getActionAvailability } from "./actionAvailabilityClient";
import type { ActionAvailabilityResponse } from "./actionAvailability.types";

export type ActionAwareButtonProps = {
	actionCode: string;
	objectType: string;
	objectCode: string;
	label: string;
	variant?: "primary" | "secondary" | "danger";
	hideWhenDenied?: boolean;
	onAllowedClick: () => void;
	confirmationTitle?: string;
	confirmationMessage?: string;
	/** Passed as SEC-0410 `context` (optional; required for meaningful authz in real Desk). */
	availabilityContext?: Record<string, unknown>;
	/** When set, overrides default `action-aware-button-*` on the primary `<button>` (Desk parity, e.g. UI-HARD-0200). */
	buttonTestId?: string;
};

type LoadState =
	| { kind: "loading" }
	| { kind: "ready"; availability: ActionAvailabilityResponse }
	| { kind: "error"; message: string };

function escapeHtml(text: string): string {
	return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function sanitizeActionCodeForTestId(actionCode: string): string {
	return String(actionCode || "").replace(/[^A-Za-z0-9_-]/g, "_");
}

function testId(kind: "button" | "denial" | "confirmation", actionCode: string): string {
	const safe = sanitizeActionCodeForTestId(actionCode);
	if (kind === "button") {
		return `action-aware-button-${safe}`;
	}
	if (kind === "denial") {
		return `action-denial-reason-${safe}`;
	}
	return `action-confirmation-${safe}`;
}

function variantClass(variant: ActionAwareButtonProps["variant"]): string {
	if (variant === "danger") {
		return "btn btn-danger";
	}
	if (variant === "secondary") {
		return "btn btn-default";
	}
	return "btn btn-primary";
}

function runDeskOrBrowserConfirm(messageHtml: string, onYes: () => void): void {
	const g = globalThis as typeof globalThis & {
		frappe?: { confirm?: (msg: string, yes?: () => void, no?: () => void) => unknown };
	};
	if (typeof g.frappe?.confirm === "function") {
		g.frappe.confirm(messageHtml, () => onYes());
		return;
	}
	const stripped = messageHtml.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
	if (window.confirm(stripped)) {
		onYes();
	}
}

export function ActionAwareButton(props: ActionAwareButtonProps): ReactElement | null {
	const {
		actionCode,
		objectType,
		objectCode,
		label,
		variant = "primary",
		hideWhenDenied = false,
		onAllowedClick,
		confirmationTitle,
		confirmationMessage,
		availabilityContext,
		buttonTestId,
	} = props;

	const [state, setState] = useState<LoadState>({ kind: "loading" });
	const denialId = useId();

	const contextKey = useMemo(() => JSON.stringify(availabilityContext ?? {}), [availabilityContext]);

	const ids = useMemo(() => {
		const button = (buttonTestId || "").trim() || testId("button", actionCode);
		return {
			button,
			denial: testId("denial", actionCode),
			confirm: testId("confirmation", actionCode),
		};
	}, [actionCode, buttonTestId]);

	useEffect(() => {
		let cancelled = false;
		(async () => {
			try {
				const availability = await getActionAvailability(
					{
						action_code: actionCode,
						object_type: objectType,
						object_code: objectCode,
						context: availabilityContext,
					},
					{},
				);
				if (!cancelled) {
					setState({ kind: "ready", availability });
				}
			} catch (err) {
				const msg =
					err instanceof ActionAvailabilityClientError
						? err.envelope.message
						: err instanceof Error
							? err.message
							: "Unable to evaluate action availability.";
				if (!cancelled) {
					setState({ kind: "error", message: msg });
				}
			}
		})();
		return () => {
			cancelled = true;
		};
		// `contextKey` tracks serialized `availabilityContext` without re-running on referential churn of `{}`.
	}, [actionCode, objectType, objectCode, contextKey]);

	const onPrimaryClick = useCallback(() => {
		if (state.kind !== "ready") {
			return;
		}
		const { availability } = state;
		if (!availability.allowed) {
			return;
		}
		if (!availability.requires_confirmation) {
			onAllowedClick();
			return;
		}
		const title = (confirmationTitle || "").trim();
		const body = (confirmationMessage || availability.message || "").trim();
		const html = title ? `<p><strong>${escapeHtml(title)}</strong></p><p>${escapeHtml(body)}</p>` : `<p>${escapeHtml(body)}</p>`;
		runDeskOrBrowserConfirm(html, () => onAllowedClick());
	}, [state, onAllowedClick, confirmationTitle, confirmationMessage]);

	if (state.kind === "loading") {
		return (
			<button type="button" className={variantClass(variant)} disabled data-testid={ids.button} aria-busy="true">
				{label}
			</button>
		);
	}

	if (state.kind === "error") {
		return (
			<button type="button" className={variantClass(variant)} disabled data-testid={ids.button} title={state.message}>
				{label}
			</button>
		);
	}

	const { availability } = state;
	if (!availability.allowed && hideWhenDenied) {
		return null;
	}

	const denied = !availability.allowed;
	const denialText = availability.message || "This action is not available.";

	return (
		<>
			{availability.allowed && availability.requires_confirmation ? (
				<span data-testid={ids.confirm} className="sr-only">
					confirmation-required
				</span>
			) : null}
			<button
				type="button"
				className={variantClass(variant)}
				disabled={denied}
				data-testid={ids.button}
				title={denied ? denialText : availability.message || label}
				onClick={denied ? undefined : onPrimaryClick}
				aria-describedby={denied ? denialId : undefined}
			>
				{label}
			</button>
			{denied ? (
				<span id={denialId} data-testid={ids.denial} className="text-muted small" style={{ display: "block", marginTop: "0.25rem" }}>
					{denialText}
				</span>
			) : null}
		</>
	);
}
