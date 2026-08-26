<script setup>
// PCFG-02 — Coverage and Document Structure (§15.8). Three real tabs:
// Coverage (readiness engine's real 16-row register), Sections (real
// `STD Cfg Section` rows for this package, block counts from real
// `STD Cfg Content Block` rows), Selected section (that section's blocks,
// added/edited via save_std_document_structure).
import { ref, reactive, computed, onMounted, watch } from "vue";
import AreaItemDialog from "./AreaItemDialog.vue";

const props = defineProps({
	draftId: { type: String, required: true },
	packageId: { type: String, required: true },
});
const emit = defineEmits(["saved"]);

const TAB = { COVERAGE: 0, SECTIONS: 1, SELECTED: 2 };
const activeTab = ref(TAB.COVERAGE);

const loading = ref(true);
const coverage = ref([]);
const sections = ref([]);
const blocksBySection = reactive({});
const selectedSectionId = ref(null);

async function refresh() {
	loading.value = true;
	const [readiness, sectionRows, areaRes] = await Promise.all([
		frappe.xcall("kentender_procurement.std_configuration.api.std_configuration_api.get_std_readiness_report", {
			reference_doctype: "STD Cfg Draft",
			reference_name: props.draftId,
		}),
		frappe.db.get_list("STD Cfg Section", {
			filters: { package_id: props.packageId },
			fields: ["name", "section_code", "title", "coverage_area_number", "display_order", "is_required"],
			order_by: "display_order asc",
			limit: 100,
		}),
		frappe.xcall("kentender_procurement.std_configuration.api.std_configuration_api.get_std_configuration_area", {
			reference_doctype: "STD Cfg Draft",
			reference_name: props.draftId,
			area: "PCFG-02",
		}),
	]);
	coverage.value = readiness.coverage;
	sections.value = sectionRows;
	Object.keys(blocksBySection).forEach((k) => delete blocksBySection[k]);
	for (const s of sectionRows) blocksBySection[s.name] = [];
	for (const b of areaRes.items["STD Cfg Content Block"] || []) {
		if (blocksBySection[b.section_id]) blocksBySection[b.section_id].push(b);
	}
	for (const s of sectionRows) blocksBySection[s.name].sort((a, b) => (a.display_order || 0) - (b.display_order || 0));
	if (!selectedSectionId.value && sectionRows.length) selectedSectionId.value = sectionRows[0].name;
	loading.value = false;
}
watch(() => props.draftId, refresh);
onMounted(refresh);

const selectedSection = computed(() => sections.value.find((s) => s.name === selectedSectionId.value));
const selectedBlocks = computed(() => blocksBySection[selectedSectionId.value] || []);

const BLOCK_FIELDS = [
	{ key: "content_block_id", label: __("Content block id"), type: "text", required: true },
	{ key: "block_type", label: __("Treatment"), type: "select", options: ["Locked text", "Generated value", "Parameter", "Requirement table", "Schedule table", "Inventory table", "Price table", "Evaluation table", "Bidder form", "Contract value"] },
	{ key: "display_order", label: __("Order"), type: "int" },
	{ key: "locked_text", label: __("Locked content"), type: "textarea" },
	{ key: "binding_key", label: __("Binding"), type: "text" },
];
const dialogOpen = ref(false);
const dialogItem = ref(null);
const saving = ref(false);
function openAddBlock() {
	dialogItem.value = null;
	dialogOpen.value = true;
}
function openEditBlock(item) {
	dialogItem.value = item;
	dialogOpen.value = true;
}
async function confirmBlock(values) {
	const payload = { ...values, section_id: selectedSectionId.value };
	if (dialogItem.value) payload.name = dialogItem.value.name;
	const allBlocks = Object.values(blocksBySection).flat().filter((b) => b.name !== payload.name);
	allBlocks.push(payload);
	saving.value = true;
	try {
		await frappe.xcall("kentender_procurement.std_configuration.api.std_configuration_api.save_std_document_structure", {
			draft_name: props.draftId,
			content_blocks: allBlocks,
		});
		dialogOpen.value = false;
		frappe.show_alert({ message: __("Saved Document Structure"), indicator: "green" });
		await refresh();
		emit("saved");
	} finally {
		saving.value = false;
	}
}
</script>

<template>
	<div>
		<div class="kt-tabs">
			<div class="kt-tab" :aria-selected="activeTab === TAB.COVERAGE" @click="activeTab = TAB.COVERAGE">
				{{ __("Coverage") }} <span class="kt-count">{{ coverage.length }}</span>
			</div>
			<div class="kt-tab" :aria-selected="activeTab === TAB.SECTIONS" @click="activeTab = TAB.SECTIONS">
				{{ __("Sections") }} <span class="kt-count">{{ sections.length }}</span>
			</div>
			<div class="kt-tab" :aria-selected="activeTab === TAB.SELECTED" @click="activeTab = TAB.SELECTED">
				{{ __("Selected section") }}
			</div>
		</div>

		<div v-if="loading" class="kt-card kt-blueprint">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div v-for="i in 3" :key="i" class="kt-skel" style="height: 16px; margin-bottom: 10px"></div>
		</div>

		<table v-else-if="activeTab === TAB.COVERAGE" class="kt-table">
			<thead>
				<tr><th>{{ __("No.") }}</th><th>{{ __("STD area") }}</th><th>{{ __("Result") }}</th></tr>
			</thead>
			<tbody>
				<tr v-for="row in coverage" :key="row.number">
					<td>{{ row.number }}</td>
					<td>{{ row.official_area }}</td>
					<td><span class="kt-status" :class="row.result === 'Pass' ? 'is-live' : 'is-pending'">{{ row.result === 'Pass' ? __('Complete') : __('Incomplete') }}</span></td>
				</tr>
			</tbody>
		</table>

		<table v-else-if="activeTab === TAB.SECTIONS" class="kt-table">
			<thead>
				<tr><th>{{ __("Section") }}</th><th>{{ __("Blocks") }}</th><th></th></tr>
			</thead>
			<tbody>
				<tr v-for="s in sections" :key="s.name">
					<td>{{ s.title }}</td>
					<td>{{ (blocksBySection[s.name] || []).length }}</td>
					<td><a href="#" @click.prevent="selectedSectionId = s.name; activeTab = TAB.SELECTED">{{ __("Open") }}</a></td>
				</tr>
			</tbody>
		</table>

		<template v-else>
			<div class="kt-field" style="max-width: 360px">
				<label>{{ __("Section") }}</label>
				<select v-model="selectedSectionId" class="kt-input">
					<option v-for="s in sections" :key="s.name" :value="s.name">{{ s.title }}</option>
				</select>
			</div>
			<table class="kt-table">
				<thead>
					<tr><th>{{ __("Order") }}</th><th>{{ __("Content") }}</th><th>{{ __("Treatment") }}</th><th>{{ __("Binding") }}</th><th></th></tr>
				</thead>
				<tbody>
					<tr v-for="b in selectedBlocks" :key="b.name">
						<td>{{ b.display_order }}</td>
						<td>{{ b.content_block_id }}</td>
						<td>{{ b.block_type }}</td>
						<td>{{ b.binding_key || "—" }}</td>
						<td><a href="#" @click.prevent="openEditBlock(b)">{{ __("Edit") }}</a></td>
					</tr>
					<tr v-if="!selectedBlocks.length"><td colspan="5" class="kt-muted">{{ __("No content blocks yet.") }}</td></tr>
				</tbody>
			</table>
			<button type="button" class="kt-btn kt-btn-secondary" @click="openAddBlock">{{ __("Add content block") }}</button>
		</template>

		<AreaItemDialog
			:open="dialogOpen"
			:title="dialogItem ? __('Edit content block') : __('Add content block')"
			:fields="BLOCK_FIELDS"
			:item="dialogItem"
			:saving="saving"
			@confirm="confirmBlock"
			@cancel="dialogOpen = false"
		/>
	</div>
</template>
