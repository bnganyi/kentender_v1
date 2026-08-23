<script setup>
// Vue 3.3 (this bench's pinned version) doesn't support the `defineModel()` macro
// (stabilized in 3.4) — using the standard modelValue prop/emit pattern it desugars to instead.
import { computed } from "vue";

const props = defineProps({
	modelValue: { type: Object, required: true },
	crossEntity: { type: Boolean, default: true },
	periodOptions: { type: Array, default: () => [] }, // distinct effective_period_label values from live data
	entityOptions: { type: Array, default: () => [] }, // [{id, name}] from get_strategy_portfolio's entities
});
const emit = defineEmits(["update:modelValue", "clear"]);

function field(key) {
	return computed({
		get: () => props.modelValue[key],
		set: (value) => emit("update:modelValue", { ...props.modelValue, [key]: value }),
	});
}

// Template auto-unwrapping only applies to top-level script-setup bindings, not to a
// property nested inside a plain object (filters.q rendered the raw ComputedRef, i.e.
// literal "[object Object]", in the search box) — expose each ref at the top level instead.
const q = field("q");
const type = field("type");
const period = field("period");
const status = field("status");
const entity = field("entity");
</script>

<template>
	<div class="kt-pp-filterbar">
		<div class="kt-pp-field kt-pp-field--grow">
			<label for="kt-pp-q">Search</label>
			<input
				id="kt-pp-q"
				v-model="q"
				class="kt-pp-input"
				type="search"
				placeholder="Plan code or title"
			/>
		</div>
		<div class="kt-pp-field">
			<label for="kt-pp-type">Plan type</label>
			<select id="kt-pp-type" v-model="type" class="kt-pp-input">
				<option value="">All plan types</option>
				<option value="Entity Strategic Plan">Entity Strategic Plan</option>
				<option value="Programme Strategy">Programme Strategy</option>
			</select>
		</div>
		<div class="kt-pp-field">
			<label for="kt-pp-period">Period</label>
			<select id="kt-pp-period" v-model="period" class="kt-pp-input">
				<option value="">All periods</option>
				<option v-for="p in periodOptions" :key="p" :value="p">{{ p }}</option>
			</select>
		</div>
		<div class="kt-pp-field">
			<label for="kt-pp-status">Status</label>
			<select id="kt-pp-status" v-model="status" class="kt-pp-input">
				<option value="">All statuses</option>
				<option value="Draft">Draft</option>
				<option value="Submitted">Submitted</option>
				<option value="Returned">Returned</option>
				<option value="Approved">Approved</option>
				<option value="Active">Active</option>
				<option value="Superseded">Superseded</option>
				<option value="Archived">Archived</option>
			</select>
		</div>
		<div v-if="crossEntity" class="kt-pp-field">
			<label for="kt-pp-entity">Entity</label>
			<select id="kt-pp-entity" v-model="entity" class="kt-pp-input">
				<option value="">All entities</option>
				<option v-for="e in entityOptions" :key="e.id" :value="e.name">{{ e.name }}</option>
			</select>
		</div>
		<button type="button" class="kt-pp-btn kt-pp-btn--ghost" @click="$emit('clear')">
			Clear filters
		</button>
	</div>
</template>

<style scoped>
.kt-pp-filterbar {
	display: flex;
	flex-wrap: wrap;
	align-items: flex-end;
	gap: 10px;
}
.kt-pp-field {
	flex: 0 1 170px;
	min-width: 160px;
}
.kt-pp-field--grow {
	flex: 1 1 260px;
	min-width: 220px;
}
.kt-pp-field > label {
	display: block;
	font-size: 12px;
	margin-bottom: 5px;
	color: color-mix(in srgb, var(--ktpp-color-text) 70%, transparent);
}
.kt-pp-input {
	width: 100%;
	min-height: 36px;
	padding: 6px 10px;
	font: inherit;
	font-size: 14px;
	color: var(--ktpp-color-text);
	background: var(--ktpp-color-surface);
	border: 1px solid var(--ktpp-color-divider);
	border-radius: var(--ktpp-radius-md);
}
.kt-pp-input:hover {
	border-color: color-mix(in srgb, var(--ktpp-color-text) 45%, transparent);
}
.kt-pp-input:focus-visible {
	border-color: var(--ktpp-color-accent);
	outline-offset: 0;
}
.kt-pp-btn {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	height: 36px;
	padding-inline: 8px;
	cursor: pointer;
	font-family: var(--ktpp-font-heading);
	font-weight: var(--ktpp-font-heading-weight);
	font-size: 14px;
	background: transparent;
	border: 1px solid transparent;
	border-radius: var(--ktpp-radius-md);
}
.kt-pp-btn--ghost {
	color: var(--ktpp-color-accent);
}
.kt-pp-btn--ghost:hover {
	background: color-mix(in srgb, var(--ktpp-color-accent) 10%, transparent);
}
</style>
