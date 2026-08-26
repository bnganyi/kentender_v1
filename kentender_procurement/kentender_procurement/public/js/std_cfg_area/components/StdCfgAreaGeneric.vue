<script setup>
// Generic PCFG-03..09 editor: real items from get_std_configuration_area,
// grouped into tabs per areaRegistry.js's `groups`, edited via
// AreaItemDialog.vue, saved through the area's real save_std_* command.
import { ref, reactive, computed, onMounted, watch } from "vue";
import { AREA_REGISTRY } from "../../std_configuration_shared/areaRegistry.js";
import AreaItemDialog from "./AreaItemDialog.vue";

const props = defineProps({
	referenceDoctype: { type: String, required: true },
	referenceName: { type: String, required: true },
	areaCode: { type: String, required: true },
	readOnly: { type: Boolean, default: false },
});
const emit = defineEmits(["saved"]);

const area = computed(() => AREA_REGISTRY[props.areaCode]);
const itemsByDoctype = reactive({});
const loading = ref(true);
const activeGroupIdx = ref(0);

async function refresh() {
	loading.value = true;
	activeGroupIdx.value = 0;
	const res = await frappe.xcall(
		"kentender_procurement.std_configuration.api.std_configuration_api.get_std_configuration_area",
		{ reference_doctype: props.referenceDoctype, reference_name: props.referenceName, area: props.areaCode }
	);
	for (const g of area.value.groups) {
		itemsByDoctype[g.doctype] = res.items[g.doctype] || [];
	}
	loading.value = false;
}
watch(() => props.areaCode, refresh);
onMounted(refresh);

const activeGroup = computed(() => area.value.groups[activeGroupIdx.value]);

const dialogOpen = ref(false);
const dialogItem = ref(null);
const saving = ref(false);

function openAdd() {
	dialogItem.value = null;
	dialogOpen.value = true;
}
function openEdit(item) {
	dialogItem.value = item;
	dialogOpen.value = true;
}

async function confirmDialog(values) {
	const g = activeGroup.value;
	const payload = { ...values, ...(g.defaults || {}) };
	if (dialogItem.value) payload.name = dialogItem.value.name;
	const list = itemsByDoctype[g.doctype].filter((i) => i.name !== payload.name);
	list.push(payload);
	saving.value = true;
	try {
		const params = { draft_name: props.referenceName };
		params[g.savePayloadKey || area.value.savePayloadKey] = list;
		await frappe.xcall(area.value.saveMethod, params);
		dialogOpen.value = false;
		frappe.show_alert({ message: __("Saved"), indicator: "green" });
		await refresh();
		emit("saved");
	} finally {
		saving.value = false;
	}
}

function displayValue(item, col) {
	const v = item[col.key];
	if (col.boolean) return v ? __("Yes") : __("No");
	return v || "—";
}
</script>

<template>
	<div>
		<div v-if="area.groups.length > 1" class="kt-tabs">
			<div
				v-for="(g, i) in area.groups"
				:key="g.doctype"
				class="kt-tab"
				:aria-selected="activeGroupIdx === i"
				@click="activeGroupIdx = i"
			>
				{{ g.label }} <span class="kt-count">{{ (itemsByDoctype[g.doctype] || []).length }}</span>
			</div>
		</div>

		<div v-if="loading" class="kt-card kt-blueprint">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div v-for="i in 3" :key="i" class="kt-skel" style="height: 16px; margin-bottom: 10px"></div>
		</div>
		<template v-else>
			<div class="kt-card kt-blueprint" style="padding: 0; margin-bottom: 16px">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<table class="kt-table" style="border: none">
					<thead>
						<tr>
							<th v-for="c in activeGroup.columns" :key="c.key">{{ c.label }}</th>
							<th></th>
						</tr>
					</thead>
					<tbody>
						<tr v-for="item in itemsByDoctype[activeGroup.doctype]" :key="item.name">
							<td v-for="c in activeGroup.columns" :key="c.key">{{ displayValue(item, c) }}</td>
							<td><a v-if="!readOnly" href="#" class="kt-btn kt-btn-ghost" @click.prevent="openEdit(item)">{{ __("Edit") }}</a></td>
						</tr>
						<tr v-if="!itemsByDoctype[activeGroup.doctype] || !itemsByDoctype[activeGroup.doctype].length">
							<td :colspan="activeGroup.columns.length + 1" class="kt-muted">{{ __("Nothing configured yet.") }}</td>
						</tr>
					</tbody>
				</table>
			</div>
			<button v-if="!readOnly" type="button" class="kt-btn kt-btn-secondary" @click="openAdd">{{ __("Add") }} {{ activeGroup.label.toLowerCase() }}</button>
		</template>

		<AreaItemDialog
			v-if="!readOnly"
			:open="dialogOpen"
			:title="dialogItem ? __('Edit') + ' ' + activeGroup.label : __('Add') + ' ' + activeGroup.label"
			:fields="activeGroup ? activeGroup.fields : []"
			:item="dialogItem"
			:saving="saving"
			@confirm="confirmDialog"
			@cancel="dialogOpen = false"
		/>
	</div>
</template>
