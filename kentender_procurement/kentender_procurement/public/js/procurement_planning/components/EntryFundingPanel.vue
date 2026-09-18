<!-- PLN-CHG-001 v1.23 §10.4 — Funding details (U03-FUNDING), ported from
     U02-U05.dc.html.

     This opens beneath the requirement it belongs to, and the rest of the
     departmental plan stays visible above and below it. Navigating away to a
     separate page for two fields lost the one thing the person needed: the
     other requirements they are comparing this one against.

     The requirement itself is not editable here and never has been — the
     department owns those facts through Departmental Needs. So the panel shows
     just enough of it to know which requirement this is, keeps the rest behind
     a disclosure, and says plainly where a correction to it has to go. -->
<template>
	<div class="pln-funding-panel" data-testid="dpp-funding-panel">
		<h6 class="kt-card-title">Funding details</h6>

		<!-- Enough of the requirement to be sure which one this is. -->
		<div class="kt-meta-row" data-testid="dpp-funding-summary">
			<div>
				<span class="kt-label">Requirement</span>
				<span class="kt-meta-value">{{ entry.title }}</span>
			</div>
			<div>
				<span class="kt-label">Quantity</span>
				<span class="kt-meta-value">{{ entry.quantity_display }}</span>
			</div>
			<div>
				<span class="kt-label">Required by</span>
				<span class="kt-meta-value">{{ entry.required_by_display }}</span>
			</div>
		</div>

		<details class="kt-disclosure" data-testid="dpp-funding-requirement-details">
			<summary class="kt-disclosure-head">
				<span class="kt-disclosure-title">View requirement details</span>
			</summary>
			<div class="kt-disclosure-body">
				<div class="kt-meta-row">
					<div>
						<span class="kt-label">Requirement title</span>
						<span class="kt-meta-value">{{ entry.title }}</span>
					</div>
					<div>
						<span class="kt-label">Description</span>
						<span class="kt-meta-value">{{ entry.description }}</span>
					</div>
					<div>
						<span class="kt-label">Expected result</span>
						<span class="kt-meta-value">{{ entry.expected_operational_result }}</span>
					</div>
					<div>
						<span class="kt-label">Quantity</span>
						<span class="kt-meta-value">{{ quantityNumber }}</span>
					</div>
					<div>
						<span class="kt-label">Unit</span>
						<span class="kt-meta-value">{{ entry.unit_label }}</span>
					</div>
					<div>
						<span class="kt-label">Required by</span>
						<span class="kt-meta-value">{{ entry.required_by_display }}</span>
					</div>
				</div>
			</div>
		</details>

		<div class="kt-field">
			<label for="dpp-funding-line" class="kt-label">Budget line</label>
			<select
				id="dpp-funding-line"
				class="kt-input"
				data-testid="dpp-funding-line"
				:disabled="!canEdit || pending"
				:value="budgetLine"
				@change="$emit('update:budgetLine', $event.target.value)"
			>
				<option value="">Select a budget line</option>
				<option v-for="line in editor.budget_lines || []" :key="line.id" :value="line.id">{{ line.title || line.label }}</option>
			</select>
			<!-- The code beneath the name: the name says what the money is for,
			     the code is what it is looked up by. -->
			<div v-if="selectedLineReference" class="kt-muted" data-testid="dpp-funding-line-code">{{ selectedLineReference }}</div>
		</div>

		<div class="kt-field">
			<label for="dpp-funding-amount" class="kt-label">Estimated cost (KES)</label>
			<input
				id="dpp-funding-amount"
				class="kt-input"
				type="number"
				min="1"
				data-testid="dpp-funding-amount"
				:disabled="!canEdit || pending"
				:value="amount"
				@input="$emit('update:amount', $event.target.value)"
			>
			<!-- Said where the number is entered, because it changes what
			     number the person enters. -->
			<div class="kt-field-hint" data-testid="dpp-funding-amount-hint">
				Enter the full estimated cost, including applicable delivery and other incidental costs.
			</div>
		</div>

		<p v-if="error" class="pln-error-summary" data-testid="dpp-funding-error">{{ error }}</p>

		<div class="pln-footer" data-testid="dpp-funding-footer">
			<button
				v-if="canEdit"
				type="button"
				class="kt-btn kt-btn-ghost"
				data-testid="dpp-funding-exclude"
				:disabled="pending"
				@click="$emit('exclude')"
			>
				Exclude from this year's departmental plan
			</button>
			<span v-else></span>
			<div class="pln-footer-right">
				<button type="button" class="kt-btn kt-btn-secondary" :disabled="pending" @click="$emit('cancel')">Cancel</button>
				<button
					v-if="canEdit"
					type="button"
					class="kt-btn kt-btn-primary"
					data-testid="dpp-funding-save"
					:disabled="pending || !canSave"
					@click="$emit('save')"
				>
					Save details
				</button>
			</div>
		</div>

		<!-- The requirement's own facts are not Planning's to change, and the
		     link says where they are changed instead. -->
		<p class="kt-muted pln-funding-correction" data-testid="dpp-funding-correct-source">
			<a href="#" data-testid="dpp-funding-correct-link" @click.prevent="$emit('correct-source')">Correct the source requirement</a>
			Source changes require their own Departmental Needs review.
		</p>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	editor: { type: Object, default: () => ({}) },
	budgetLine: { type: String, default: "" },
	amount: { type: [String, Number], default: "" },
	pending: Boolean,
	error: String,
});

defineEmits(["save", "cancel", "exclude", "correct-source", "update:budgetLine", "update:amount"]);

const entry = computed(() => props.editor.entry || {});
const canEdit = computed(() => Boolean(props.editor.can_edit && props.editor.mutable));
const quantityNumber = computed(() => String(entry.value.quantity ?? ""));

const selectedLineReference = computed(() => {
	const line = (props.editor.budget_lines || []).find((row) => row.id === props.budgetLine);
	return line ? line.reference || line.id : "";
});

// Both facts are needed for the requirement to count as funded; the control
// says so by staying unavailable rather than failing on the server.
const canSave = computed(() => Boolean(props.budgetLine) && Number(props.amount) > 0);
</script>
