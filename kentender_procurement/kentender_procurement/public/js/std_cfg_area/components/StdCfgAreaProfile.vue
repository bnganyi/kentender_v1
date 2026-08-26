<script setup>
// PCFG-01 — Source and Profile (§15.7). Updates the Draft's own fields
// directly via save_std_source_and_profile; Package code and Requirement
// profile are read-only (owned by the Package, not the Draft — §8).
import { ref, reactive, onMounted, watch } from "vue";

const props = defineProps({
	referenceDoctype: { type: String, required: true },
	referenceName: { type: String, required: true },
	packageId: { type: String, required: true },
	readOnly: { type: Boolean, default: false },
});
const emit = defineEmits(["saved"]);

const loading = ref(true);
const pkg = ref(null);
const form = reactive({ official_issue_label: "" });
const saving = ref(false);

async function refresh() {
	loading.value = true;
	pkg.value = await frappe.xcall(
		"kentender_procurement.std_configuration.api.std_configuration_api.get_std_package_home",
		{ package_id: props.packageId }
	);
	const reference = await frappe.db.get_doc(props.referenceDoctype, props.referenceName);
	form.official_issue_label = reference.official_issue_label || "";
	form.official_source_file_id = reference.official_source_file_id || "";
	form.official_source_file_name = "";
	if (reference.official_source_file_id) {
		const sourceDoc = await frappe.db.get_doc("STD Cfg Source Document", reference.official_source_file_id);
		const file = await frappe.db.get_doc("File", sourceDoc.file_id);
		form.official_source_file_name = file.file_name || sourceDoc.file_id;
	}
	loading.value = false;
}
watch(() => props.referenceName, refresh);
onMounted(refresh);

const uploadingSource = ref(false);
function pickSourceFile() {
	new frappe.ui.FileUploader({
		folder: "Home",
		on_success: async (file) => {
			// official_source_file_id links to STD Cfg Source Document, not a raw
			// Frappe File — save_std_source_document wraps the uploaded file as
			// that real record (confirmed live: passing the raw File name straight
			// through failed link validation at submission time, not at save time).
			uploadingSource.value = true;
			try {
				const result = await frappe.xcall(
					"kentender_procurement.std_configuration.api.std_configuration_api.save_std_source_document",
					{
						draft_name: props.referenceName,
						file_id: file.name,
						official_title: pkg.value.official_title,
						official_issue_label: form.official_issue_label,
					}
				);
				form.official_source_file_id = result.source_document_id;
				form.official_source_file_name = file.file_name;
			} finally {
				uploadingSource.value = false;
			}
		},
	});
}

async function save() {
	saving.value = true;
	try {
		await frappe.xcall(
			"kentender_procurement.std_configuration.api.std_configuration_api.save_std_source_and_profile",
			{
				draft_name: props.referenceName,
				official_issue_label: form.official_issue_label,
				official_source_file_id: form.official_source_file_id || null,
			}
		);
		frappe.show_alert({ message: __("Saved Source and Profile"), indicator: "green" });
		emit("saved");
	} finally {
		saving.value = false;
	}
}
</script>

<template>
	<div v-if="loading" class="kt-card kt-blueprint">
		<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
		<div v-for="i in 3" :key="i" class="kt-skel" style="height: 16px; margin-bottom: 10px"></div>
	</div>
	<div v-else class="kt-card" style="padding: 16px; display: flex; flex-direction: column; gap: 14px">
		<div class="kt-field" style="margin: 0">
			<label>{{ __("Package code") }}</label>
			<input class="kt-input" :value="pkg.package_code" disabled />
		</div>
		<div class="kt-field" style="margin: 0">
			<label>{{ __("Official title") }}</label>
			<input class="kt-input" :value="pkg.official_title" disabled />
		</div>
		<div class="kt-field" style="margin: 0">
			<label for="kt-cfg-profile-issue">{{ __("Official issue") }}</label>
			<input id="kt-cfg-profile-issue" v-model="form.official_issue_label" class="kt-input" type="text" :disabled="readOnly" />
		</div>
		<div class="kt-field" style="margin: 0">
			<label>{{ __("Requirement profile") }}</label>
			<input class="kt-input" :value="pkg.requirement_profile" disabled />
		</div>
		<div class="kt-field" style="margin: 0">
			<label>{{ __("Official source") }}</label>
			<div style="display: flex; align-items: center; gap: 10px">
				<span class="kt-muted">{{ form.official_source_file_name || __("No file selected") }}</span>
				<button v-if="!readOnly" type="button" class="kt-btn kt-btn-secondary" :disabled="uploadingSource" @click="pickSourceFile">{{ __("Replace") }}</button>
			</div>
		</div>
		<div v-if="!readOnly" style="display: flex; justify-content: flex-end">
			<button type="button" class="kt-btn kt-btn-primary" :disabled="saving" @click="save">
				{{ __("Save Source and Profile") }}
			</button>
		</div>
	</div>
</template>
