<!-- The PE / department / FY (and optionally intake) band that heads every
     screen in NDS-DES-01, 02, 03, 05, 10. -->
<template>
	<div class="kt-card kt-blueprint" style="margin-bottom: 16px; padding: 20px 24px">
		<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
		<i class="kt-corner bl"></i><i class="kt-corner br"></i>
		<div class="kt-context-grid" :style="{ gridTemplateColumns: `repeat(${items.length}, 1fr)` }">
			<ReadonlyRow
				v-for="item in items"
				:key="item.label"
				:label="item.label"
				:value="item.value"
				strong
			/>
		</div>
	</div>
</template>

<script setup>
import ReadonlyRow from "./ReadonlyRow.vue";

defineProps({ items: { type: Array, required: true } });
</script>
