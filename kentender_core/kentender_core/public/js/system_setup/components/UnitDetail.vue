<script setup>
// AUTH-DES-01's selected unit, ported from C05 #auth-des-01: the unit's name
// as a heading, its five facts, then the actions and the affected-
// responsibilities link. Every action's availability comes from the server's
// own `actions` map (§9.2) — never from a client-side status rule. No
// Procuring Entity appears: one site is one PE.
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
	<div data-testid="kt-ou-detail">
		<h3 style="margin:0 0 12px">{{ unit.name }}</h3>
		<dl class="kt-setup-facts">
			<dt class="kt-label">{{ __("Unit name") }}</dt>
			<dd>{{ unit.name }}</dd>
			<dt class="kt-label">{{ __("Code") }}</dt>
			<dd>{{ unit.code }}</dd>
			<dt class="kt-label">{{ __("Path") }}</dt>
			<dd>{{ unit.path.join(" › ") }}</dd>
			<dt class="kt-label">{{ __("Status") }}</dt>
			<dd>
				<span class="kt-status" :class="unit.status === 'Active' ? 'is-live' : 'is-pending'">
					{{ unit.status === "Active" ? __("Active") : __("Inactive") }}
				</span>
			</dd>
			<dt class="kt-label">{{ __("Included units") }}</dt>
			<dd>{{ includedLabel(unit.descendant_count) }}</dd>
		</dl>

		<div class="kt-unit-actions">
			<button
				v-if="unit.actions.add_child"
				type="button"
				class="kt-btn kt-btn-primary"
				:disabled="busy"
				data-testid="kt-ou-add"
				@click="emit('add')"
			>
				<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M12 5v14M5 12h14" /></svg>{{ __("Add organisation unit") }}
			</button>
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
			<a
				v-if="unit.active_assignments"
				href="#"
				class="kt-affected"
				data-testid="kt-ou-affected"
				@click.stop.prevent="emit('view-affected')"
			>
				{{ unit.active_assignments === 1
					? __("View 1 affected responsibility")
					: __("View {0} affected responsibilities", [unit.active_assignments]) }}
			</a>
		</div>
	</div>
</template>
