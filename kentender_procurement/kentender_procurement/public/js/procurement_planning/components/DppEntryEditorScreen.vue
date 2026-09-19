<!-- PLN-CHG-001 v1.23 §10.4 — Add or edit a departmental requirement
     (U04-DIRECT / U04-EDIT), ported from U02-U05.dc.html.

     This page exists for requirements the department states itself, which did
     not come through Departmental Needs. Everything on it is the department's
     own: there is no Need field, no bypass reason, no Strategy, no procurement
     method and no attachment — those are other people's decisions, made later.

     Funding for an *accepted* requirement is not here. It opens beneath its
     own row on the departmental plan (U03-FUNDING), where the rest of the
     plan stays visible. -->
<template>
	<div class="pln-entry-editor">
		<div class="pln-sheet">
			<div class="pln-masthead">
				<div>
					<h1 class="kt-page-title" data-testid="dpp-editor-title">{{ isNew ? "Add a requirement" : entry.title }}</h1>
					<p v-if="isNew" class="kt-page-lede">
						Add a departmental requirement that was not created through Departmental Needs.
					</p>
					<p v-else class="kt-muted pln-row-ref" data-testid="dpp-editor-reference">{{ entry.entry_id }}</p>
				</div>
				<div v-if="!isNew" class="pln-header-actions">
					<span class="kt-status" :class="editor.mutable ? 'is-attention' : 'is-muted'">{{ editor.mutable ? "Draft" : "Submitted" }}</span>
				</div>
			</div>

			<div class="kt-meta-row pln-context-row" data-testid="dpp-editor-context">
				<div>
					<span class="kt-label">Department</span>
					<span class="kt-meta-value">{{ context.department }}</span>
				</div>
				<div>
					<span class="kt-label">Financial year</span>
					<span class="kt-meta-value">{{ context.financial_year }}</span>
				</div>
			</div>

			<div class="kt-field">
				<label for="dpp-title" class="kt-label">Requirement title</label>
				<input id="dpp-title" class="kt-input" data-testid="dpp-f-title" :disabled="!canEdit" v-model="form.title">
			</div>
			<div class="kt-field">
				<label for="dpp-description" class="kt-label">Description</label>
				<textarea id="dpp-description" class="kt-input" rows="3" data-testid="dpp-f-description" :disabled="!canEdit" v-model="form.description"></textarea>
			</div>
			<div class="kt-field">
				<label for="dpp-result" class="kt-label">Expected result</label>
				<textarea id="dpp-result" class="kt-input" rows="2" data-testid="dpp-f-result" :disabled="!canEdit" v-model="form.expected_operational_result"></textarea>
			</div>

			<!-- Quantity and Unit side by side, and never merged into one field. -->
			<div class="pln-entry-pair">
				<div class="kt-field">
					<label for="dpp-quantity" class="kt-label">Quantity</label>
					<input id="dpp-quantity" class="kt-input" type="number" min="1" step="1" data-testid="dpp-f-quantity" :disabled="!canEdit" v-model="form.quantity">
				</div>
				<div class="kt-field">
					<label for="dpp-unit" class="kt-label">Unit</label>
					<select id="dpp-unit" class="kt-input" data-testid="dpp-f-unit" :disabled="!canEdit" v-model="form.unit">
						<option value="">Select a unit</option>
						<option v-for="unit in editor.units || []" :key="unit.id" :value="unit.id">{{ unit.label }}</option>
					</select>
				</div>
			</div>

			<div class="kt-field">
				<label for="dpp-required-by" class="kt-label">Required by</label>
				<input id="dpp-required-by" class="kt-input" type="date" data-testid="dpp-f-required-by" :disabled="!canEdit" v-model="form.required_by_date">
			</div>

			<div class="kt-field">
				<label for="dpp-budget-line" class="kt-label">Budget line</label>
				<select id="dpp-budget-line" class="kt-input" data-testid="dpp-f-budget-line" :disabled="!canEdit" v-model="form.budget_line">
					<option value="">Select a budget line</option>
					<option v-for="line in editor.budget_lines || []" :key="line.id" :value="line.id">{{ line.title || line.label }}</option>
				</select>
				<div v-if="selectedLineReference" class="kt-muted" data-testid="dpp-f-budget-line-code">{{ selectedLineReference }}</div>
			</div>

			<div class="kt-field">
				<label for="dpp-amount" class="kt-label">Estimated cost (KES)</label>
				<input id="dpp-amount" class="kt-input" type="number" min="1" data-testid="dpp-f-amount" :disabled="!canEdit" v-model="form.indicative_amount">
			</div>

			<p v-if="errorSummary" class="pln-error-summary" data-testid="dpp-editor-error">{{ errorSummary }}</p>

			<div class="pln-footer" data-testid="dpp-editor-footer">
				<!-- U04-EDIT — removing a requirement the department added is the
				     department's own to do; it has no place on a new one. -->
				<button
					v-if="!isNew && canEdit"
					type="button"
					class="kt-btn kt-btn-ghost"
					data-testid="dpp-editor-remove"
					:disabled="pending"
					@click="$emit('remove')"
				>
					Remove requirement
				</button>
				<span v-else></span>
				<div class="pln-footer-right">
					<button type="button" class="kt-btn kt-btn-secondary" data-testid="dpp-editor-cancel" :disabled="pending" @click="$emit('cancel')">
						{{ isNew ? "Cancel" : "Back to departmental plan" }}
					</button>
					<button
						v-if="canEdit"
						type="button"
						class="kt-btn kt-btn-primary"
						data-testid="dpp-editor-save"
						:disabled="pending || !complete"
						@click="$emit('save-direct', { ...form })"
					>
						{{ isNew ? "Add requirement" : "Save requirement" }}
					</button>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, reactive, watch } from "vue";

const props = defineProps({
	editor: { type: Object, default: () => ({}) },
	pending: Boolean,
	errorSummary: String,
});

defineEmits(["save-direct", "remove", "cancel"]);

const entry = computed(() => props.editor.entry || {});
const context = computed(() => props.editor.context || {});
const isNew = computed(() => !entry.value.entry_id);
const canEdit = computed(() => Boolean(props.editor.can_edit && props.editor.mutable));

const form = reactive({
	title: "",
	description: "",
	expected_operational_result: "",
	quantity: "",
	unit: "",
	required_by_date: "",
	budget_line: "",
	indicative_amount: "",
});

// AGENTS.md §6.4 — the controls are bound to the department's own draft. A
// quiet in-place refresh that carries nothing new must not discard what they
// have typed since, so re-hydration is keyed to the record actually moving.
watch(
	() => props.editor,
	(next, previous) => {
		if (previous && (previous.record_version ?? null) === (next?.record_version ?? null)) return;
		const row = next?.entry || {};
		form.title = row.title || "";
		form.description = row.description || "";
		form.expected_operational_result = row.expected_operational_result || "";
		form.quantity = row.quantity ?? "";
		form.unit = row.unit || "";
		form.required_by_date = row.required_by_date || "";
		form.budget_line = row.budget_line || "";
		form.indicative_amount = row.indicative_amount ?? "";
	},
	{ immediate: true },
);

const selectedLineReference = computed(() => {
	const line = (props.editor.budget_lines || []).find((row) => row.id === form.budget_line);
	return line ? line.reference || line.id : "";
});

// Every field is required for the requirement to be a requirement; the control
// says so by staying unavailable rather than failing on the server.
const complete = computed(() =>
	Boolean(
		form.title.trim() && form.description.trim() && form.expected_operational_result.trim()
		&& Number(form.quantity) > 0 && form.unit && form.required_by_date
		&& form.budget_line && Number(form.indicative_amount) > 0,
	),
);
</script>
