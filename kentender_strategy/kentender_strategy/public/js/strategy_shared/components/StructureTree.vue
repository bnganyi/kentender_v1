<script setup>
// Recursive hierarchy renderer shared by the Plan workspace (read-only), the
// Structure editor (editable), and the Review task (read-only) — STR-DES-04/
// 05/07/10b. Matches the `tree` shape returned by
// kentender_strategy.api.strategy_ui_api.get_strategy_tree.
//
// Row shape and indentation port STR-DES-04.dc.html class-for-class rather
// than approximating from memory of the design tokens (AGENTS.md §6.6): each
// node is two stacked lines — icon + bold title, then a second line
// (indented under the title) holding the "· Type" label and the trailing
// "Add …" action — and the parent/child connector is a single `border-left`
// on the recursive children wrapper (the artboard's `.tree-kids`), not a
// per-row drawn line segment.
import { ref } from "vue";

const props = defineProps({
	nodes: { type: Array, required: true },
	depth: { type: Number, default: 0 },
	selectedId: { type: String, default: null },
	readOnly: { type: Boolean, default: false },
});
const emit = defineEmits(["select", "add-child"]);

const DOT_COLOR = {
	Pillar: "#003d9b",
	Programme: "#003d9b",
	"Sub-programme": "#003d9b",
	"Strategic Objective": "#047857",
	"Performance Indicator": "#92610a",
	"Performance Target": "#92610a",
};

// STR-DES-04 per-type node icons (same SVG paths as the Structure summary
// figures on the Overview tab) — ported verbatim so the tree row icon and
// the summary card icon for a given node type are always the same glyph.
const NODE_ICON = {
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

const CHILD_TYPE = {
	Pillar: "Programme",
	Programme: "Sub-programme",
	"Sub-programme": "Strategic Objective",
	"Strategic Objective": "Performance Indicator",
	"Performance Indicator": "Performance Target",
};

// Single source of truth for the "Add …" row label, keyed by the type of
// child that will actually be created — so the label can never drift from
// what onAddChild() emits. Matches v1.6 §12.5's exact action table.
const ADD_CHILD_LABEL = {
	Programme: "Add programme",
	"Sub-programme": "Add sub-programme",
	"Strategic Objective": "Add objective",
	"Performance Indicator": "Add indicator",
	"Performance Target": "Add target",
};

// STR-DES-04: only the structural layers (Pillar/Programme/Sub-programme/
// Strategic Objective) ever draw a collapse chevron. A Performance
// Indicator's Targets have no collapse affordance at all — they render
// directly beneath it, always expanded, matching STR-DES-04's markup (its
// Performance Indicator and Performance Target rows never emit the chevron
// <svg>, only the structural rows do).
const COLLAPSIBLE_TYPES = new Set(["Pillar", "Programme", "Sub-programme", "Strategic Objective"]);

function dot(nodeType) {
	return DOT_COLOR[nodeType] || "#666";
}
function icon(nodeType) {
	return NODE_ICON[nodeType] || '<circle cx="12" cy="12" r="9"/>';
}

// STR-DES-04b: collapse/expand affordance per row. Purely a local rendering
// decision for whichever recursion level owns this node's row — no need to
// share state across the recursive component boundary.
const collapsed = ref(new Set());
function hasChildren(node) {
	return Boolean(node.children && node.children.length);
}
function canCollapse(node) {
	return COLLAPSIBLE_TYPES.has(node.node_type) && hasChildren(node);
}
function isCollapsed(node) {
	return canCollapse(node) && collapsed.value.has(node.id);
}
function toggleCollapse(node, event) {
	event.stopPropagation();
	const next = new Set(collapsed.value);
	if (next.has(node.id)) next.delete(node.id);
	else next.add(node.id);
	collapsed.value = next;
}
function countDescendants(node) {
	if (!node.children) return 0;
	return node.children.reduce((sum, c) => sum + 1 + countDescendants(c), 0);
}
function childType(node) {
	return CHILD_TYPE[node.node_type];
}
function canAddChild(node) {
	return !props.readOnly && Boolean(childType(node));
}
function addChildLabel(node) {
	return ADD_CHILD_LABEL[childType(node)] || "Add child";
}
function onAddChild(node) {
	emit("add-child", { parent: node, childType: childType(node) });
}
</script>

<template>
	<template v-for="node in nodes" :key="node.id">
		<div class="kt-tree-node" :class="{ selected: node.id === selectedId }" @click="$emit('select', node)">
			<div class="kt-tree-row" :style="{ gap: canCollapse(node) ? '6px' : '8px' }">
				<button
					v-if="canCollapse(node)"
					type="button"
					class="kt-tree-toggle"
					:class="{ collapsed: isCollapsed(node) }"
					@click.stop="toggleCollapse(node, $event)"
				>
					<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
				</button>
				<svg
					width="15"
					height="15"
					viewBox="0 0 24 24"
					fill="none"
					:stroke="dot(node.node_type)"
					stroke-width="1.5"
					stroke-linecap="round"
					stroke-linejoin="round"
					style="flex-shrink: 0; margin-top: 2px"
					v-html="icon(node.node_type)"
				></svg>
				<strong class="kt-tree-title">{{ node.title }}</strong>
			</div>
			<div class="kt-tree-meta" :style="{ paddingLeft: canCollapse(node) ? '33px' : '23px' }">
				<span class="kt-tree-type">
					&middot; {{ node.node_type }}
					<span v-if="isCollapsed(node)" class="kt-tree-hidden-count">({{ countDescendants(node) }} {{ __("hidden") }})</span>
				</span>
				<button v-if="canAddChild(node)" type="button" class="kt-add-child" @click.stop="onAddChild(node)">
					{{ addChildLabel(node) }}
				</button>
			</div>
		</div>
		<div v-if="hasChildren(node) && !isCollapsed(node)" class="kt-tree-kids">
			<StructureTree
				:nodes="node.children"
				:depth="depth + 1"
				:selected-id="selectedId"
				:read-only="readOnly"
				@select="$emit('select', $event)"
				@add-child="$emit('add-child', $event)"
			/>
		</div>
	</template>
</template>
