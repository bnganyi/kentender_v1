// The one icon per module (HOME §10B.1, KT-STD-001 v1.22 §2.6.11): the owner key the
// server sends maps to a name in home_icons.js. The label is the server's (`module`).
export const MODULE_ICONS = {
	strategy: "target",
	budget: "wallet",
	needs: "lightbulb",
	planning: "clipboard-list",
	requisitions: "file-check",
	tenders: "megaphone",
	bid_opening: "inbox",
	evaluation: "scale",
	award: "badge-check",
	support: "circle-alert",
	suppliers: "users",
};

export function moduleIcon(owner) {
	return MODULE_ICONS[owner] || "file-check";
}
