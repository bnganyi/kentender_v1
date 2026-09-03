<script setup>
// AUTH-DES-01's "Selected unit" panel, ported row-for-row: labelled rows on
// a 130px label column (Unit name, Code, Path, Status, Included units), then
// the action row and the affected-responsibilities link. Every action's
// availability comes from the server's own `actions` map (§9.2) — never from
// a client-side status-to-action rule. No Procuring Entity appears: one site
// is one PE.
defineProps({
	unit: { type: Object, required: true },
	busy: { type: Boolean, default: false },
});
const emit = defineEmits(["add", "rename", "deactivate", "reactivate", "view-affected"]);

function includedLabel(count) {
	if (!count) return __("No descendants");
	return count === 1 ? __("1 descendant") : __("{0} descendants", [count]);
}
</script>

<template>
	<div class="kt-card kt-blueprint" data-testid="kt-ou-detail">
		<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
		<div class="kt-card-title">{{ __("Selected unit") }}</div>

		<div class="kt-panel-rows">
			<div class="kt-panel-row">
				<span class="kt-label">{{ __("Unit name") }}</span>
				<span class="kt-panel-name">{{ unit.name }}</span>
			</div>
			<div class="kt-panel-row">
				<span class="kt-label">{{ __("Code") }}</span>
				<span class="kt-panel-code">{{ unit.code }}</span>
			</div>
			<div class="kt-panel-row">
				<span class="kt-label">{{ __("Path") }}</span>
				<span class="kt-panel-value">{{ unit.path.join(" › ") }}</span>
			</div>
			<div class="kt-panel-row">
				<span class="kt-label">{{ __("Status") }}</span>
				<span>
					<span class="kt-status" :class="unit.status === 'Active' ? 'is-live' : 'is-pending'">
						{{ unit.status === "Active" ? __("Active") : __("Inactive") }}
					</span>
				</span>
			</div>
			<div class="kt-panel-row">
				<span class="kt-label">{{ __("Included units") }}</span>
				<span class="kt-panel-value">{{ includedLabel(unit.descendant_count) }}</span>
			</div>
		</div>

		<div class="kt-unit-actions">
			<button
				v-if="unit.actions.add_child"
				type="button"
				class="kt-btn kt-btn-primary"
				:disabled="busy"
				data-testid="kt-ou-add"
				@click="emit('add')"
			>{{ __("Add organisation unit") }}</button>
			<button
				v-if="unit.actions.rename"
				type="button"
				class="kt-btn kt-btn-secondary"
				:disabled="busy"
				data-testid="kt-ou-rename"
				@click="emit('rename')"
			>{{ __("Edit name") }}</button>
			<button
				v-if="unit.actions.deactivate"
				type="button"
				class="kt-btn kt-btn-secondary"
				:disabled="busy"
				data-testid="kt-ou-deactivate"
				@click="emit('deactivate')"
			>{{ __("Deactivate") }}</button>
			<button
				v-if="unit.actions.reactivate"
				type="button"
				class="kt-btn kt-btn-secondary"
				:disabled="busy"
				data-testid="kt-ou-reactivate"
				@click="emit('reactivate')"
			>{{ __("Reactivate") }}</button>
		</div>

		<a
			v-if="unit.active_assignments"
			href="#"
			class="kt-affected"
			data-testid="kt-ou-affected"
			@click.prevent="emit('view-affected')"
		>
			{{ unit.active_assignments === 1
				? __("View 1 affected responsibility")
				: __("View {0} affected responsibilities", [unit.active_assignments]) }}
			<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M5 12h14" /><path d="m13 6 6 6-6 6" /></svg>
		</a>
	</div>
</template>
