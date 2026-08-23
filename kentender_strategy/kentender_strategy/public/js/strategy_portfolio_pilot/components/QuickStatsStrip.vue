<script setup>
defineProps({
	items: { type: Array, required: true }, // [{ key, count, label, filterable? }]
	activeKey: { type: String, default: "" },
});
const emit = defineEmits(["select"]);

function onClick(item) {
	if (item.filterable === false) return;
	emit("select", item.key);
}
</script>

<template>
	<div class="kt-pp-stats">
		<button
			v-for="item in items"
			:key="item.key"
			type="button"
			class="kt-pp-stats__cell"
			:class="{ 'kt-pp-stats__cell--static': item.filterable === false }"
			@click="onClick(item)"
		>
			<span class="kt-pp-stats__count">{{ item.count }}</span>
			<span class="kt-pp-stats__label">{{ item.label }}</span>
			<span v-if="activeKey === item.key" class="kt-pp-stats__indicator"></span>
		</button>
	</div>
</template>

<style scoped>
.kt-pp-stats {
	display: grid;
	grid-template-columns: repeat(4, 1fr);
	border: 1px solid var(--ktpp-color-divider);
}
.kt-pp-stats__cell {
	text-align: left;
	background: transparent;
	border: 0;
	border-right: 1px solid var(--ktpp-color-divider);
	padding: 13px 17px 15px;
	cursor: pointer;
	font: inherit;
	color: inherit;
	display: flex;
	flex-direction: column;
	gap: 2px;
}
.kt-pp-stats__cell:last-child {
	border-right: 0;
}
.kt-pp-stats__cell:hover {
	background: color-mix(in srgb, var(--ktpp-color-text) 4%, transparent);
}
.kt-pp-stats__cell--static {
	cursor: default;
}
.kt-pp-stats__cell--static:hover {
	background: transparent;
}
.kt-pp-stats__count {
	font-family: var(--ktpp-font-heading);
	font-size: 30px;
	line-height: 1;
}
.kt-pp-stats__label {
	font-size: 11px;
	letter-spacing: 0.08em;
	text-transform: uppercase;
	color: color-mix(in srgb, var(--ktpp-color-text) 60%, transparent);
}
.kt-pp-stats__indicator {
	display: block;
	height: 2px;
	margin-top: 9px;
	background: var(--ktpp-color-accent);
	width: 34px;
}
</style>
