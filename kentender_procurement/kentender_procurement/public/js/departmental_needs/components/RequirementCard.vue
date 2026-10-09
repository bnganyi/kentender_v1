<!-- The requester-entered values, read-only (six source facts, and from NDS-CHG-001 v1.17 the estimated cost). §11.1 single-sheet
     arrangement (NDS-CHG-001 v1.14, 21 Sep 2026): Description and Expected
     result as the main readable narrative, then Quantity/Unit/Required-by
     collapsed into one compact "{quantity} {unit} · Required by {date}"
     summary line — not a six-row read-only form (NDS-DES-05/06/07/09/12).
     The title is never repeated here: the screen's own heading above this
     component already names it, and every current caller supplies one, so
     this component renders no heading of its own. -->
<template>
	<div class="kt-factstack">
		<div>
			<div class="kt-label">Description</div>
			<p class="kt-factstack-value">{{ revision.description }}</p>
		</div>
		<div>
			<div class="kt-label">Expected result</div>
			<p class="kt-factstack-value">{{ revision.expected_operational_result }}</p>
		</div>
		<div class="kt-factstack-summary">
			<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="5" x="2" y="3" rx="1" /><path d="M4 8v11a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8" /><path d="M10 12h4" /></svg>
			<span>{{ quantityWithUnit }}</span>
			<span class="text-muted">·</span>
			<span>Required by {{ formatDate(revision.required_by_date) }}</span>
		</div>
		<!-- NDS-CHG-001 v1.17 §11.19 — Estimated cost beneath the compact summary. A
		     revision that predates the field says so; one whose payload carries no
		     estimate key at all (an older caller) shows nothing. -->
		<div v-if="showEstimate" style="display: flex; align-items: baseline; gap: 8px" data-testid="nds-estimated-cost-line">
			<span class="kt-label">Estimated cost</span>
			<span class="kt-factstack-value">{{ revision.estimated_total_cost_label || "No estimate recorded" }}</span>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import { formatDate } from "../data/format.js";

const props = defineProps({
	revision: { type: Object, required: true },
});

// "1 Programme" — Quantity and Unit read as one phrase in the compact
// summary, not two separately labelled facts.
const showEstimate = computed(() => "estimated_total_cost_label" in props.revision || "estimated_total_cost" in props.revision);

const quantityWithUnit = computed(() => {
	const value = props.revision.indicative_quantity;
	if (value === null || value === undefined || value === "") return "";
	const quantity = Number.isInteger(Number(value)) ? String(Number(value)) : String(value);
	const unit = props.revision.unit_label || props.revision.unit || "";
	return [quantity, unit].filter(Boolean).join(" ");
});
</script>
