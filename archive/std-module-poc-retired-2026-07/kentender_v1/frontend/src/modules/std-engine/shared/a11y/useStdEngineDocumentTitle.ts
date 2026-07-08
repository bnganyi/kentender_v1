import { useEffect } from "react";

/**
 * UI-HARD-1500 — meaningful page titles for SPA shells embedding std-engine (doc §20.7).
 * Restores the previous `document.title` on unmount.
 */
export function useStdEngineDocumentTitle(title: string, suffix = "KenTender"): void {
	useEffect(() => {
		const previous = document.title;
		const t = title.trim();
		if (t) {
			document.title = `${t} — ${suffix}`;
		}
		return () => {
			document.title = previous;
		};
	}, [title, suffix]);
}
