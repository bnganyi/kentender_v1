<script setup>
// Recursive flat-indented hierarchy renderer shared by the Plan workspace
// (read-only), the Structure editor (editable), and the Review task
// (read-only) — STR-DES-04/05/07/10b. Matches the `tree` shape returned by
// kentender_strategy.api.strategy_ui_api.get_strategy_tree.
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
	"Strategic Outcome": "#047857",
	"Performance Indicator": "#92610a",
	"Performance Target": "#92610a",
};

const CHILD_TYPE = {
	Pillar: "Programme",
	Programme: "Sub-programme",
	"Sub-programme": "Strategic Objective",
	"Strategic Objective": "Strategic Outcome",
};
const CAN_ADD_INDICATOR = new Set(["Strategic Objective", "Strategic Outcome"]);

function dot(nodeType) {
	return DOT_COLOR[nodeType] || "#666";
}
function canAddChild(node) {
	return !props.readOnly && (Boolean(CHILD_TYPE[node.node_type]) || CAN_ADD_INDICATOR.has(node.node_type));
}
function addChildLabel(node) {
	if (node.node_type === "Performance Indicator") return "Add target";
	if (CAN_ADD_INDICATOR.has(node.node_type)) return "Add indicator";
	return "Add child";
}
function onAddChild(node) {
	if (node.node_type === "Performance Indicator") {
		emit("add-child", { parent: node, childType: "Performance Target" });
	} else if (CAN_ADD_INDICATOR.has(node.node_type) && !CHILD_TYPE[node.node_type]) {
		emit("add-child", { parent: node, childType: "Performance Indicator" });
	} else {
		emit("add-child", { parent: node, childType: CHILD_TYPE[node.node_type] });
	}
}
</script>

<template>
	<template v-for="node in nodes" :key="node.id">
		<div
			class="kt-tree-row"
			:class="{ selected: node.id === selectedId }"
			:style="{ paddingLeft: `${8 + depth * 20}px` }"
			@click="$emit('select', node)"
		>
			<span class="kt-tree-dot" :style="{ background: dot(node.node_type) }"></span>
			<span>{{ node.title }}</span>
			<span class="kt-tree-type">{{ node.node_type }}</span>
			<button
				v-if="canAddChild(node)"
				type="button"
				class="kt-add-child"
				@click.stop="onAddChild(node)"
			>
				{{ addChildLabel(node) }}
			</button>
		</div>
		<StructureTree
			v-if="node.children && node.children.length"
			:nodes="node.children"
			:depth="depth + 1"
			:selected-id="selectedId"
			:read-only="readOnly"
			@select="$emit('select', $event)"
			@add-child="$emit('add-child', $event)"
		/>
	</template>
</template>
