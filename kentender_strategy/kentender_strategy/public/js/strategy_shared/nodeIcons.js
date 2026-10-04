// STR-DES-03/04/06/07 per-type node icons (Lucide paths, stroke 1.5) — one
// source for the tree rows and the Structure summary rows, so a type always
// draws the same glyph in the same tone.
export const NODE_ICON = {
	Pillar: '<rect x="4" y="4" width="6" height="16"/><rect x="14" y="4" width="6" height="16"/>',
	Programme:
		'<path d="m12.83 2.18 8.58 3.9a1 1 0 0 1 0 1.83l-8.58 3.9a2 2 0 0 1-1.66 0L2.6 7.91a1 1 0 0 1 0-1.83z"/><path d="M2 12a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 12"/><path d="M2 17a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 17"/>',
	"Sub-programme":
		'<line x1="6" y1="3" x2="6" y2="15"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M18 9a9 9 0 0 1-9 9"/>',
	"Strategic Objective": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
	"Performance Indicator": '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
	"Performance Target":
		'<circle cx="12" cy="12" r="10"/><line x1="12" y1="2" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="22"/><line x1="2" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="22" y2="12"/>',
};

export const NODE_TONE = {
	Pillar: "var(--kt-status-draft)",
	Programme: "var(--kt-status-draft)",
	"Sub-programme": "var(--kt-status-draft)",
	"Strategic Objective": "var(--kt-status-live)",
	"Performance Indicator": "var(--kt-status-attention)",
	"Performance Target": "var(--kt-status-attention)",
};

// §4.7 — visible type labels over the unchanged stored node types.
export const NODE_LABEL = {
	Pillar: "Pillar",
	Programme: "Programme",
	"Sub-programme": "Sub-programme",
	"Strategic Objective": "Objective",
	"Performance Indicator": "Indicator",
	"Performance Target": "Target",
};

export function iconPath(nodeType) {
	return NODE_ICON[nodeType] || '<circle cx="12" cy="12" r="9"/>';
}
export function iconTone(nodeType) {
	return NODE_TONE[nodeType] || "var(--kt-color-neutral-600)";
}
export function typeLabel(nodeType) {
	return NODE_LABEL[nodeType] || nodeType;
}
