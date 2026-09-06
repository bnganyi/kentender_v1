<!-- PLN-UI-03 (accepted-Need funding, PLN-DES-03) and PLN-UI-04 (direct
     requirement, PLN-DES-04) in one screen: the mode is the entry's source
     origin. Need facts render read-only in the artboard's exact order;
     Planning owns only Procurement Budget Line and indicative amount on a
     Need-origin entry (§12.3), or — PLN-AC-092 — a not-proceeding reason in
     their place. A direct entry carries exactly the eight defined values
     (§12.4); units come only from enabled ERPNext UOM records. -->
<template>
	<div class="pln-editor">
		<template v-if="isNeed">
			<h1 class="kt-page-title">Complete funding details</h1>
			<p class="kt-page-lede">
				Add the Planning-owned funding details for this accepted departmental
				requirement.
			</p>
			<span class="kt-status is-attention">Accepted Need</span>

			<div class="kt-card kt-blueprint pln-card-pad" data-testid="dpp-need-facts">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
				<i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div class="kt-card-title">Accepted requirement</div>
				<div class="pln-field-grid">
					<div class="pln-ro-field">
						<label>Title</label>
						<div class="pln-val">{{ entry.title }}</div>
					</div>
					<div class="pln-ro-field" style="grid-column: 1 / -1">
						<label>Description</label>
						<div class="pln-val">{{ entry.description }}</div>
					</div>
					<div class="pln-ro-field" style="grid-column: 1 / -1">
						<label>Expected operational result</label>
						<div class="pln-val">{{ entry.expected_operational_result }}</div>
					</div>
					<div class="pln-ro-field">
						<label>Quantity</label>
						<div class="pln-val">{{ entry.quantity_display }}</div>
					</div>
					<div class="pln-ro-field">
						<label>Unit</label>
						<div class="pln-val">{{ entry.unit_label }}</div>
					</div>
					<div class="pln-ro-field">
						<label>Required by</label>
						<div class="pln-val">{{ entry.required_by_display }}</div>
					</div>
					<div class="pln-ro-field">
						<label>Accepted Need</label>
						<div class="pln-val">{{ entry.need_reference_line }}</div>
					</div>
				</div>
			</div>
		</template>

		<template v-else>
			<h1 class="kt-page-title">{{ isNew ? "Add direct requirement" : "Edit direct requirement" }}</h1>
			<p class="kt-page-lede">
				Add a requirement the department already knows it needs to procure.
			</p>
			<span class="kt-status is-pending">{{ isNew ? "New" : "Direct requirement" }}</span>

			<div class="kt-card kt-blueprint pln-card-pad" data-testid="dpp-editor-context">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
				<i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div class="pln-field-grid">
					<div class="pln-ro-field">
						<label>Department</label>
						<div class="pln-val">{{ context.department }}</div>
					</div>
					<div class="pln-ro-field">
						<label>Financial Year</label>
						<div class="pln-val">{{ context.financial_year }}</div>
					</div>
				</div>
			</div>

			<div class="kt-card kt-blueprint pln-card-pad">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
				<i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div class="kt-card-title">Requirement</div>
				<div class="pln-field-grid">
					<div class="pln-field" style="grid-column: 1 / -1">
						<label for="dpp-title">Title</label>
						<input id="dpp-title" type="text" class="kt-input" v-model="form.title" data-testid="dpp-f-title" />
					</div>
					<div class="pln-field" style="grid-column: 1 / -1">
						<label for="dpp-description">Description</label>
						<textarea id="dpp-description" class="kt-input" rows="3" v-model="form.description" data-testid="dpp-f-description"></textarea>
					</div>
					<div class="pln-field" style="grid-column: 1 / -1">
						<label for="dpp-result">Expected operational result</label>
						<textarea id="dpp-result" class="kt-input" rows="3" v-model="form.expected_operational_result" data-testid="dpp-f-result"></textarea>
					</div>
					<div class="pln-field">
						<label for="dpp-quantity">Quantity</label>
						<input id="dpp-quantity" type="number" min="1" step="1" class="kt-input" v-model="form.quantity" data-testid="dpp-f-quantity" />
					</div>
					<div class="pln-field">
						<label for="dpp-unit">Unit</label>
						<select id="dpp-unit" class="kt-input" v-model="form.unit" data-testid="dpp-f-unit">
							<option v-for="unit in units" :key="unit.id" :value="unit.id">{{ unit.label }}</option>
						</select>
					</div>
					<div class="pln-field">
						<label for="dpp-required-by">Required by</label>
						<input id="dpp-required-by" type="date" class="kt-input" v-model="form.required_by_date" data-testid="dpp-f-required-by" />
					</div>
				</div>
			</div>
		</template>

		<!-- funding card — shared by both modes -->
		<div class="kt-card kt-blueprint pln-card-pad" data-testid="dpp-funding">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-card-title">{{ isNeed ? "Planning funding" : "Funding" }}</div>
			<div class="pln-field-grid">
				<div class="pln-field">
					<label for="dpp-budget-line">Procurement Budget Line</label>
					<select
						id="dpp-budget-line"
						class="kt-input"
						v-model="form.budget_line"
						data-testid="dpp-f-budget-line"
						:disabled="form.not_proceeding"
					>
						<option v-for="line in budgetLines" :key="line.id" :value="line.id">{{ line.label }}</option>
					</select>
				</div>
				<div class="pln-ro-field">
					<label>Currency</label>
					<div class="pln-val">{{ currency }}</div>
				</div>
				<div class="pln-field">
					<label for="dpp-amount">Indicative amount</label>
					<input
						id="dpp-amount"
						type="number"
						min="1"
						class="kt-input"
						v-model="form.indicative_amount"
						data-testid="dpp-f-amount"
						:disabled="form.not_proceeding"
					/>
				</div>
			</div>

			<!-- PLN-AC-092 — a Need-origin entry the department will not proceed
			     with is accounted for with a reason instead of funding (§5.1). -->
			<div v-if="isNeed" class="pln-not-proceeding" data-testid="dpp-not-proceeding">
				<label class="pln-checkbox-row">
					<input
						type="checkbox"
						v-model="form.not_proceeding"
						data-testid="dpp-f-not-proceeding"
					/>
					This requirement will not proceed in this financial year
				</label>
				<div v-if="form.not_proceeding" class="pln-field">
					<label for="dpp-not-proceeding-reason">Reason</label>
					<textarea
						id="dpp-not-proceeding-reason"
						class="kt-input"
						rows="3"
						v-model="form.not_proceeding_reason"
						data-testid="dpp-f-not-proceeding-reason"
					></textarea>
				</div>
			</div>
		</div>

		<div v-if="errorSummary" class="pln-notice is-critical" role="alert" data-testid="dpp-editor-error">
			<p class="pln-notice-title">This could not be saved</p>
			<p>{{ errorSummary }}</p>
		</div>

		<div class="pln-footer-bar" style="justify-content: flex-end">
			<div class="pln-footer-actions">
				<button type="button" class="kt-btn kt-btn-secondary" @click="$emit('cancel')">Cancel</button>
				<button
					type="button"
					class="kt-btn kt-btn-primary"
					data-testid="dpp-editor-save"
					:disabled="pending"
					@click="save"
				>
					{{ isNeed ? "Save funding details" : isNew ? "Add requirement" : "Save changes" }}
				</button>
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

const emit = defineEmits(["save-funding", "save-direct", "cancel"]);

const entry = computed(() => props.editor.entry || {});
const context = computed(() => props.editor.context || {});
const units = computed(() => props.editor.units || []);
const budgetLines = computed(() => props.editor.budget_lines || []);
const currency = computed(() => props.editor.currency || "KES");
const isNew = computed(() => !props.editor.entry);
const isNeed = computed(
	() => entry.value.source_origin === "Accepted Departmental Need"
);

const form = reactive({
	title: "",
	description: "",
	expected_operational_result: "",
	quantity: 1,
	unit: "",
	required_by_date: "",
	budget_line: "",
	indicative_amount: null,
	not_proceeding: false,
	not_proceeding_reason: "",
});

watch(
	() => props.editor,
	(editor, previous) => {
		const row = editor?.entry || {};
		// An in-place refresh that returns the same entry at the same record
		// version carries nothing new — re-hydrating would discard what the
		// user has typed since.
		if (
			previous &&
			(previous.entry?.entry_id ?? null) === (row.entry_id ?? null) &&
			(previous.record_version ?? null) === (editor?.record_version ?? null)
		) {
			return;
		}
		form.title = row.title || "";
		form.description = row.description || "";
		form.expected_operational_result = row.expected_operational_result || "";
		form.quantity = row.quantity || 1;
		form.unit = row.unit || (editor?.units?.[0]?.id ?? "");
		form.required_by_date = row.required_by_date || "";
		form.budget_line = row.budget_line || "";
		form.indicative_amount = row.indicative_amount || null;
		form.not_proceeding_reason = row.not_proceeding_reason || "";
		form.not_proceeding = !!row.not_proceeding_reason;
	},
	{ immediate: true, deep: false }
);

function save() {
	if (isNeed.value) {
		if (form.not_proceeding) {
			emit("save-funding", {
				entry_id: entry.value.entry_id,
				not_proceeding_reason: form.not_proceeding_reason,
			});
			return;
		}
		emit("save-funding", {
			entry_id: entry.value.entry_id,
			budget_line: form.budget_line,
			indicative_amount: form.indicative_amount,
		});
		return;
	}
	emit("save-direct", {
		entry_id: isNew.value ? null : entry.value.entry_id,
		values: {
			title: form.title,
			description: form.description,
			expected_operational_result: form.expected_operational_result,
			quantity: form.quantity,
			unit: form.unit,
			required_by_date: form.required_by_date,
			budget_line: form.budget_line,
			indicative_amount: form.indicative_amount,
		},
	});
}
</script>
