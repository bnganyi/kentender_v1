// The one command context every Requisitions screen shares (AGENTS.md §6.4):
// the root owns the runner, the reload and navigation; screens inject it so
// no screen keeps its own `pending` flag or reload sequence.
import { inject } from "vue";

export const REQ_CONTEXT = Symbol("procurement-requisitions");

export function useReq() {
	const ctx = inject(REQ_CONTEXT, null);
	if (!ctx) throw new Error("Procurement Requisitions context is missing");
	return ctx;
}
