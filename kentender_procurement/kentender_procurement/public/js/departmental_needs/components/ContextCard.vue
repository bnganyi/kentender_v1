<!-- The department / FY (and other read-only context) band that heads
     several screens (NDS-DES-04/05/06/08/09). NDS-CHG-001 v1.13 §11.1 — a
     compact shaded group, not a bordered blueprint card. -->
<template>
	<div class="kt-panel" style="margin-bottom: var(--kt-space-4)">
		<div class="kt-context-grid" :style="{ gridTemplateColumns: `repeat(${items.length}, 1fr)` }">
			<ReadonlyRow
				v-for="item in items"
				:key="item.label"
				:label="item.label"
				:value="item.value"
				:volatile="!!item.volatile"
				strong
			/>
		</div>
	</div>
</template>

<script setup>
import ReadonlyRow from "./ReadonlyRow.vue";

defineProps({ items: { type: Array, required: true } });
</script>
