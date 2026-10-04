// BDS-CHG-001 v0.8 §10.19 — where a next-step fix is done. The server names
// either a portal path or a task of this bid ({ task: "documents" }); the
// screen never decides it.
export function fixRoute(fix, reference) {
	const target = fix && fix.target;
	if (typeof target === "string" && target.startsWith("/")) return target;
	if (target && typeof target === "object" && target.task) return `/tenders/${reference}/bid/${target.task}`;
	return "";
}
