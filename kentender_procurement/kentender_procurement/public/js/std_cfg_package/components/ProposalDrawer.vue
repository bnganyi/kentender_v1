<script setup>
// STD-UI-M02 — Draft assistance proposals drawer (§15.6, second half). Real
// STD Cfg Assistance Batch/Proposal Item rows from the reuse-transformation
// run just triggered — tabs grouped by owning_area (the closest real
// grouping to the artboard's "Document content / Fields and schemas /
// Mappings" split, since content_class in the register isn't itself stored
// per proposal item).
import { ref, computed, watch } from "vue";

const props = defineProps({
	open: { type: Boolean, default: false },
	sourceName: { type: String, default: "" },
	batchIds: { type: Array, default: () => [] },
});
const emit = defineEmits(["close"]);

const loading = ref(true);
const batches = ref([]);
const activeArea = ref(null);

async function refresh() {
	loading.value = true;
	batches.value = await Promise.all(
		props.batchIds.map((id) =>
			frappe.xcall("kentender_procurement.std_configuration.api.std_configuration_api.get_assistance_proposal", { batch_id: id })
		)
	);
	const firstArea = allItems.value[0]?.owning_area;
	activeArea.value = firstArea || null;
	loading.value = false;
}
watch(
	() => props.open,
	(isOpen) => {
		if (isOpen) refresh();
	}
);

const allItems = computed(() => {
	const items = [];
	for (const b of batches.value) {
		for (const p of b.proposals || []) items.push({ ...p, batch_id: b.name });
	}
	return items;
});
const areas = computed(() => [...new Set(allItems.value.map((i) => i.owning_area))]);
const visibleItems = computed(() => allItems.value.filter((i) => i.owning_area === activeArea.value));
const totalProposed = computed(() => allItems.value.length);

const busy = ref(false);
async function acceptItem(item) {
	busy.value = true;
	try {
		await frappe.xcall("kentender_procurement.std_configuration.api.std_configuration_api.accept_assistance_items", {
			batch_id: item.batch_id,
			item_names: [item.name],
		});
		frappe.show_alert({ message: __("Accepted"), indicator: "green" });
		await refresh();
	} catch (e) {
		frappe.show_alert({ message: (e && e.message) || __("Could not accept this item."), indicator: "red" });
	} finally {
		busy.value = false;
	}
}

async function rejectRemaining() {
	busy.value = true;
	try {
		for (const b of batches.value) {
			const proposed = (b.proposals || []).filter((p) => p.status === "Proposed").map((p) => p.name);
			if (proposed.length) {
				await frappe.xcall("kentender_procurement.std_configuration.api.std_configuration_api.reject_assistance_items", {
					batch_id: b.name,
					item_names: proposed,
				});
			}
		}
		frappe.show_alert({ message: __("Remaining proposals rejected"), indicator: "blue" });
		await refresh();
	} finally {
		busy.value = false;
	}
}
</script>

<template>
	<div v-if="open" class="kt-dialog-backdrop" tabindex="-1">
		<div class="kt-dialog kt-blueprint" style="width: 760px; max-height: 82vh; overflow-y: auto">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<h2 class="kt-dialog-title">{{ __("Draft assistance proposals") }}</h2>
			<p class="kt-muted" style="font-size: 13px; margin: 0 0 14px">
				{{ sourceName }} · {{ totalProposed }} {{ __("proposed items") }}
			</p>

			<div v-if="loading" class="kt-skel" style="height: 16px; margin-bottom: 10px"></div>
			<template v-else>
				<div class="kt-tabs">
					<div v-for="a in areas" :key="a" class="kt-tab" :aria-selected="activeArea === a" @click="activeArea = a">
						{{ a }} <span class="kt-count">{{ allItems.filter((i) => i.owning_area === a).length }}</span>
					</div>
				</div>
				<table class="kt-table">
					<thead>
						<tr><th>{{ __("Proposed item") }}</th><th>{{ __("Owning area") }}</th><th>{{ __("Current Draft") }}</th><th></th></tr>
					</thead>
					<tbody>
						<tr v-for="item in visibleItems" :key="item.name">
							<td>{{ item.proposed_item_label }}</td>
							<td>{{ item.owning_area }}</td>
							<td>{{ item.current_draft_state }}</td>
							<td>
								<span v-if="item.status !== 'Proposed'" class="kt-status" :class="item.status === 'Accepted' ? 'is-live' : 'is-pending'">{{ item.status }}</span>
								<a v-else href="#" :aria-disabled="busy" @click.prevent="!busy && acceptItem(item)">{{ __("Review") }}</a>
							</td>
						</tr>
						<tr v-if="!visibleItems.length"><td colspan="4" class="kt-muted">{{ __("No items in this group.") }}</td></tr>
					</tbody>
				</table>
			</template>

			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-ghost" :disabled="busy" @click="rejectRemaining">{{ __("Reject remaining proposals") }}</button>
				<button type="button" class="kt-btn kt-btn-primary" @click="$emit('close')">{{ __("Close") }}</button>
			</div>
		</div>
	</div>
</template>
