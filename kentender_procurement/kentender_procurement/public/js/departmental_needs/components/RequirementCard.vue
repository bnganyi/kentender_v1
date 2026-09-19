<!-- The six requester-entered values, read-only. §11.1 arrangement per the
     18 Sep 2026 design-board refresh: description/expected result in a
     2-column grid, quantity/unit/required-by in a 3-column grid — a
     §4.10-labelled kt-factstack, not a bordered blueprint card
     (NDS-DES-05/06/07/09/12). The title is never repeated here: the screen
     heading above this component already shows it. -->
<template>
	<div>
		<h6 v-if="showHeading" class="kt-card-title">Requirement details</h6>
		<div class="kt-factstack" style="margin-top: var(--kt-space-4); margin-bottom: var(--kt-space-4)">
			<div class="kt-factstack-text">
				<div>
					<div class="kt-label">Description</div>
					<div class="kt-factstack-value">{{ revision.description }}</div>
				</div>
				<div>
					<div class="kt-label">Expected result</div>
					<div class="kt-factstack-value">{{ revision.expected_operational_result }}</div>
				</div>
			</div>
			<div class="kt-factstack-meta">
				<div>
					<div class="kt-label">Quantity</div>
					<div class="kt-factstack-value">{{ quantityValue }}</div>
				</div>
				<div>
					<div class="kt-label">Unit</div>
					<div class="kt-factstack-value">{{ unitValue }}</div>
				</div>
				<div>
					<div class="kt-label">Required by</div>
					<div class="kt-factstack-value">{{ formatDate(revision.required_by_date) }}</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import { formatDate } from "../data/format.js";

const props = defineProps({
	revision: { type: Object, required: true },
	// §11.1/§11.5–11.10 place the "Requirement details" heading directly
	// above this block; a screen that already supplies its own heading (none
	// currently do) can suppress it.
	showHeading: { type: Boolean, default: true },
});

// §11.1 shows Quantity and Unit as two separate labelled facts, not one
// combined string.
const quantityValue = computed(() => {
	const value = props.revision.indicative_quantity;
	if (value === null || value === undefined || value === "") return "";
	return Number.isInteger(Number(value)) ? String(Number(value)) : String(value);
});
const unitValue = computed(() => props.revision.unit_label || props.revision.unit || "");
</script>
