<!-- Add supporting material (REQ-DES-05 "Add supporting material"). Not
     drawn on the board; built from the shared dialog and field primitives.
     The file is uploaded as a private File first; the server then checks its
     type, size, readability and digest before recording the row. -->
<template>
	<DialogFrame title="Add supporting material" :width="520" :busy="busy || uploading" testid="req-material-dialog" @close="$emit('close')">
		<p class="req-dialog-body kt-muted">Files may support a structured requirement but cannot replace it.</p>
		<div class="field">
			<label :for="`${id}-file`">File</label>
			<input :id="`${id}-file`" type="file" class="input" :class="{ 'is-invalid': uploadError }" data-testid="req-material-file" @change="pick" />
			<span v-if="uploadError" class="req-field-error">{{ uploadError }}</span>
		</div>
		<div class="req-grid-2-tight">
			<div class="field">
				<label :for="`${id}-title`">Title</label>
				<input :id="`${id}-title`" v-model="form.title" class="input" :class="{ 'is-invalid': fieldError('title') }" data-testid="req-material-title" />
				<span v-if="fieldError('title')" class="req-field-error">{{ fieldError("title") }}</span>
			</div>
			<div class="field">
				<label :for="`${id}-version`">Document version</label>
				<input :id="`${id}-version`" v-model="form.document_version" class="input" :class="{ 'is-invalid': fieldError('document_version') }" />
				<span v-if="fieldError('document_version')" class="req-field-error">{{ fieldError("document_version") }}</span>
			</div>
			<div class="field">
				<label :for="`${id}-type`">Document type</label>
				<select :id="`${id}-type`" v-model="form.document_type" class="input" :class="{ 'is-invalid': fieldError('document_type') }">
					<option value="">Select a type</option>
					<option v-for="t in (view.catalogue || {}).material_types || []" :key="t" :value="t">{{ t }}</option>
				</select>
				<span v-if="fieldError('document_type')" class="req-field-error">{{ fieldError("document_type") }}</span>
			</div>
			<div class="field">
				<label :for="`${id}-treatment`">Treatment</label>
				<select :id="`${id}-treatment`" v-model="form.treatment" class="input" :class="{ 'is-invalid': fieldError('treatment') }">
					<option value="Informational">Informational</option>
					<option value="Forms part of requirement">Forms part of requirement</option>
				</select>
			</div>
		</div>
		<div v-if="form.document_type === 'Other supporting material'" class="field">
			<label :for="`${id}-other`">Name the document type</label>
			<input :id="`${id}-other`" v-model="form.other_document_type" class="input" />
		</div>
		<div class="field">
			<label :for="`${id}-purpose`">Purpose</label>
			<textarea :id="`${id}-purpose`" v-model="form.purpose" class="input" rows="2" :class="{ 'is-invalid': fieldError('purpose') }"></textarea>
			<span v-if="fieldError('purpose')" class="req-field-error">{{ fieldError("purpose") }}</span>
		</div>
		<fieldset v-if="form.treatment === 'Forms part of requirement'" class="field req-fieldset">
			<legend>Structured requirements this file supports</legend>
			<label v-for="t in linkable" :key="t.id" class="kt-checkbox req-check-line"><input v-model="form.linked_requirement_ids" type="checkbox" :value="t.id" /><span class="box"></span>{{ t.label }}</label>
			<span v-if="fieldError('linked_requirement_ids')" class="req-field-error">{{ fieldError("linked_requirement_ids") }}</span>
		</fieldset>
		<Notice v-if="otherError" tone="critical">{{ otherError }}</Notice>
		<template #actions>
			<button type="button" class="btn btn-secondary" :disabled="busy || uploading" @click="$emit('close')">Cancel</button>
			<button type="button" class="btn btn-primary" :disabled="busy || uploading || !file" data-testid="req-material-confirm" @click="confirm">{{ uploading ? "Uploading…" : "Add supporting material" }}</button>
		</template>
	</DialogFrame>
</template>

<script setup>
import { computed, reactive, ref } from "vue";
import { useReq } from "../data/context.js";
import DialogFrame from "./shared/DialogFrame.vue";
import Notice from "./shared/Notice.vue";

const props = defineProps({ view: { type: Object, required: true } });
const emit = defineEmits(["close"]);
const ctx = useReq();
const busy = computed(() => ctx.pending.value);
const id = `req-mat-${Math.random().toString(36).slice(2, 8)}`;
const form = reactive({ title: "", document_type: "", other_document_type: "", purpose: "", treatment: "Informational", linked_requirement_ids: [], document_version: "1" });
const file = ref(null);
const uploading = ref(false);
const uploadError = ref("");

const linkable = computed(() => {
	const req = props.view.requirements || {};
	const out = [];
	for (const g of req.technical_groups || []) for (const r of g.rows) if (r.state !== "Proposed") out.push({ id: r.technical_requirement_id, label: r.label });
	for (const s of req.services || []) out.push({ id: s.service_requirement_id, label: s.service_type });
	for (const a of req.acceptance || []) if (a.state !== "Proposed") out.push({ id: a.acceptance_requirement_id, label: a.check_type });
	return out;
});

function pick(event) {
	file.value = (event.target.files || [])[0] || null;
	uploadError.value = "";
	if (file.value && !form.title) form.title = file.value.name.replace(/\.[^.]+$/, "");
}

async function upload() {
	const data = new FormData();
	data.append("file", file.value, file.value.name);
	data.append("is_private", "1");
	data.append("folder", "Home/Attachments");
	const response = await fetch("/api/method/upload_file", { method: "POST", body: data, headers: { "X-Frappe-CSRF-Token": window.frappe.csrf_token } });
	const body = await response.json().catch(() => ({}));
	if (!response.ok || !body.message || !body.message.name) throw new Error("The file could not be uploaded. Try again.");
	return body.message.name;
}

const error = computed(() => (ctx.commandError.value && ctx.commandError.value.label === "add-material" ? ctx.commandError.value : null));
function fieldError(field) {
	return (error.value && error.value.detail && error.value.detail.fields && error.value.detail.fields[field]) || "";
}
const otherError = computed(() => (error.value && !(error.value.detail && error.value.detail.fields) ? error.value.message : ""));

async function confirm() {
	uploadError.value = "";
	let name = "";
	uploading.value = true;
	try {
		name = await upload();
	} catch (e) {
		uploadError.value = e.message;
		return;
	} finally {
		uploading.value = false;
	}
	const done = await ctx.run("add-material", (key) =>
		ctx.api.addMaterial({ requisition: props.view.header.requisition, values: { ...form, file: name }, expected_record_version: props.view.package_record_version, idempotency_key: key })
	);
	if (done) emit("close");
}
</script>
