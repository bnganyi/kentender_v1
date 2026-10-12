// BDS-CHG-001 v0.8 §10.19 — where a next-step fix is done. The server names
// either a portal path, a task of this bid ({ task: "documents" }) or one of
// its screens ({ screen: "status" }); a fix it names by id alone is taken to
// the page that id means. The screen never decides it. A fix that is a command
// (Check certificate, Submit bid, Contact support) is not a route and is done
// by components/BidGuidance.vue.
const BY_ID = { review_bid: "review", continue_bid: "" };

export function fixRoute(fix, reference) {
	const target = fix && fix.target;
	if (typeof target === "string" && target.startsWith("/")) return target;
	if (target && typeof target === "object" && target.task) return `/tenders/${reference}/bid/${target.task}`;
	if (target && typeof target === "object" && target.screen) return `/tenders/${reference}/bid/${target.screen}`;
	if (fix && !target && Object.prototype.hasOwnProperty.call(BY_ID, fix.fix_id)) return `/tenders/${reference}/bid${BY_ID[fix.fix_id] ? "/" + BY_ID[fix.fix_id] : ""}`;
	return "";
}
