<!-- REQ-DES-06's "Add supporting material" dialog (§5.10). Not in the
     artboard file itself, same as ItemDialog.vue — built on
     kt_industry_tokens.css's shared .kt-dialog chrome. The file picker
     itself uses frappe.ui.FileUploader — the same precedent
     BudgetVersionEditorScreen.vue already established for a metadata dialog
     that needs a real OS file-open dialog, which no Vue-owned control can
     replace; the metadata form around it stays a proper in-Vue dialog
     (AGENTS.md §6.3). §5.10: a supporting file can never be the only
     statement of an obligation — Forms-part-of-requirement requires at
     least one linked structured row, checked again server-side. -->
<template>
	<div class="kt-dialog-backdrop" data-testid="req-material-dialog" @keydown.esc="$emit('cancel')">
		<div class="kt-dialog" role="dialog" aria-modal="true" ref="dialogEl" tabindex="-1">
			<div class="kt-dialog-title">Add supporting material</div>

			<div class="kt-field">
				<label for="mat-title">Title</label>
				<input id="mat-title" class="kt-input" maxlength="160" :value="fields.title" @input="fields.title = $event.target.value" />
				<p v-if="errors.title" class="req-field-error">{{ errors.title }}</p>
			</div>

			<div class="kt-field">
				<label for="mat-type">Document type</label>
				<select id="mat-type" class="kt-input" v-model="fields.document_type">
					<option value="" disabled>Select a type</option>
					<option v-for="t in materialTypes" :key="t" :value="t">{{ t }}</option>
				</select>
				<p v-if="errors.document_type" class="req-field-error">{{ errors.document_type }}</p>
			</div>
			<div class="kt-field" v-if="fields.document_type === 'Other supporting material'">
				<label for="mat-other-type">Other document type</label>
				<input id="mat-other-type" class="kt-input" maxlength="80" :value="fields.other_document_type" @input="fields.other_document_type = $event.target.value" />
				<p v-if="errors.other_document_type" class="req-field-error">{{ errors.other_document_type }}</p>
			</div>

			<div class="kt-field">
				<label for="mat-purpose">Purpose</label>
				<textarea id="mat-purpose" class="kt-input" rows="2" minlength="10" maxlength="300" :value="fields.purpose" @input="fields.purpose = $event.target.value"></textarea>
				<p v-if="errors.purpose" class="req-field-error">{{ errors.purpose }}</p>
			</div>

			<div class="kt-field">
				<label>File</label>
				<div class="req-file-picker">
					<button type="button" class="kt-btn kt-btn-secondary" @click="openFileUploader">{{ fileName ? "Replace file" : "Choose file" }}</button>
					<span v-if="fileName" class="req-file-name" data-testid="req-material-filename">{{ fileName }}</span>
				</div>
				<p class="req-table-caption">PDF, PNG, JPG or JPEG, maximum 20 MB.</p>
				<p v-if="errors.file" class="req-field-error">{{ errors.file }}</p>
			</div>

			<div class="req-field-grid">
				<div class="kt-field">
					<label id="mat-treatment-lbl">Treatment</label>
					<div class="req-seg" role="radiogroup" aria-labelledby="mat-treatment-lbl">
						<label class="req-seg-opt"><input type="radio" :checked="fields.treatment === 'Informational'" @change="fields.treatment = 'Informational'" />Informational</label>
						<label class="req-seg-opt"><input type="radio" :checked="fields.treatment === 'Forms part of requirement'" @change="fields.treatment = 'Forms part of requirement'" />Forms part of requirement</label>
					</div>
				</div>
				<div class="kt-field">
					<label for="mat-version">Document version</label>
					<input id="mat-version" class="kt-input" maxlength="40" :value="fields.document_version" @input="fields.document_version = $event.target.value" />
				</div>
			</div>

			<div class="kt-field" v-if="fields.treatment === 'Forms part of requirement'">
				<label id="mat-linked-lbl">Linked requirements</label>
				<div class="req-check-list" aria-labelledby="mat-linked-lbl">
					<label v-for="row in linkableRows" :key="row.id" class="req-check-opt">
						<input type="checkbox" :value="row.id" v-model="fields.linked_requirement_ids" />{{ row.label }}
					</label>
				</div>
				<p v-if="errors.linked_requirement_ids" class="req-field-error">{{ errors.linked_requirement_ids }}</p>
			</div>

			<p v-if="error" class="req-field-error" role="alert">{{ error }}</p>

			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" @click="$emit('cancel')">Cancel</button>
				<button type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="req-material-dialog-confirm" @click="confirm">Add material</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref } from "vue";

const props = defineProps({
	editor: { type: Object, required: true },
	pending: Boolean,
	error: { type: String, default: "" },
});

const emit = defineEmits(["confirm", "cancel"]);

const dialogEl = ref(null);
const pkg = computed(() => props.editor.package || {});
const materialTypes = computed(() => (props.editor.catalogue || {}).supporting_material_types || []);
const catalogueByKey = computed(() => {
	const map = {};
	for (const c of (props.editor.catalogue || {}).characteristics || []) map[c.key] = c;
	return map;
});

const linkableRows = computed(() => [
	...(pkg.value.technical_requirements || []).map((r) => ({ id: r.technical_requirement_id, label: `Technical — ${(catalogueByKey.value[r.characteristic_key] || {}).label || r.characteristic_key}` })),
	...(pkg.value.related_services || []).map((r) => ({ id: r.service_requirement_id, label: `Service — ${r.service_type}` })),
	...(pkg.value.acceptance_requirements || []).map((r) => ({ id: r.acceptance_requirement_id, label: `Acceptance — ${r.check_type}` })),
]);

const fileValue = ref("");
const fileName = ref("");
const fields = reactive({
	title: "",
	document_type: "",
	other_document_type: "",
	purpose: "",
	treatment: "Informational",
	document_version: "",
	linked_requirement_ids: [],
});
const errors = reactive({});

function openFileUploader() {
	new frappe.ui.FileUploader({
		allow_multiple: false,
		restrictions: { max_number_of_files: 1, allowed_file_types: [".pdf", ".png", ".jpg", ".jpeg"] },
		on_success: (file) => {
			fileValue.value = file.name;
			fileName.value = file.file_name || file.name;
		},
	});
}

function validate() {
	const next = {};
	if (!fields.title.trim()) next.title = "A title is required.";
	if (!fields.document_type) next.document_type = "A document type is required.";
	if (fields.document_type === "Other supporting material" && !fields.other_document_type.trim()) next.other_document_type = "Other document type is required.";
	if (fields.purpose.trim().length < 10) next.purpose = "10-300 characters stating the purpose is required.";
	if (!fileValue.value) next.file = "A file is required.";
	if (fields.treatment === "Forms part of requirement" && !fields.linked_requirement_ids.length) next.linked_requirement_ids = "At least one linked structured row is required.";
	Object.keys(errors).forEach((k) => delete errors[k]);
	Object.assign(errors, next);
	return Object.keys(next).length === 0;
}

function confirm() {
	if (!validate()) return;
	// The doctype's own field is `linked_requirement_ids_json` (Small Text,
	// §5.10) — the checkbox list's plain array is only this dialog's own
	// working state.
	const { linked_requirement_ids, ...rest } = fields;
	emit("confirm", { ...rest, linked_requirement_ids_json: JSON.stringify(linked_requirement_ids), file: fileValue.value });
}

onMounted(() => {
	nextTick(() => dialogEl.value && dialogEl.value.focus());
});
</script>
