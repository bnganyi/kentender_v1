<!-- The six requester-entered values, read-only (NDS-DES-05/06/07/12). -->
<template>
	<div class="kt-card kt-blueprint" style="margin-bottom: 16px; padding: 20px 24px">
		<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
		<i class="kt-corner bl"></i><i class="kt-corner br"></i>
		<div class="kt-card-title" style="margin-bottom: 16px">{{ title }}</div>
		<ReadonlyRow label="Description" :value="version.description" />
		<ReadonlyRow
			label="Expected operational result"
			:value="version.expected_operational_result"
		/>
		<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 16px">
			<ReadonlyRow
				label="Indicative quantity"
				:value="quantityLabel"
				style="margin-top: 0"
			/>
			<ReadonlyRow
				label="Required by"
				:value="formatDate(version.required_by_date)"
				style="margin-top: 0"
			/>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import ReadonlyRow from "./ReadonlyRow.vue";
import { formatDate, quantityWithUnit } from "../data/format.js";

const props = defineProps({
	version: { type: Object, required: true },
	title: { type: String, default: "Requirement" },
});

const quantityLabel = computed(() => quantityWithUnit(props.version));
</script>
