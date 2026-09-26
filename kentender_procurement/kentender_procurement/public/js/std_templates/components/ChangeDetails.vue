<!-- "View change details" (STD-TPL-001 v0.10 §11.3): the generated
     preceding-release comparison grouped by change type and consequence —
     never a raw JSON diff. Category and page live in the URL fragment
     (cc/chp). Not drawn open on the artboard; a registered departure. -->
<template>
	<div data-testid="stdt-change-details">
		<div class="kt-filter-bar">
			<div class="kt-field"><label for="stdt-cc">Change area</label>
				<select id="stdt-cc" :value="category" class="kt-input" data-testid="stdt-change-category" @change="(e) => emitHash({ cc: e.target.value, chp: '' })">
					<option value="">All change areas</option>
					<option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
				</select>
			</div>
			<div></div><div></div>
		</div>
		<div v-if="failed" class="kt-notice is-critical" role="alert"><div class="kt-notice-body"><strong>Change details could not be loaded. Try again.</strong></div><button type="button" class="kt-btn kt-btn-secondary" @click="load">Try again</button></div>
		<p v-else-if="!loading && !rows.length" style="margin: 0; font-size: 14px">No changes in this area.</p>
		<table v-else class="kt-table stdt-sub-table" style="width: 100%" :aria-busy="loading ? 'true' : 'false'">
			<thead><tr><th style="text-transform: none; letter-spacing: 0">Change area</th><th style="text-transform: none; letter-spacing: 0">Change</th><th style="text-transform: none; letter-spacing: 0">Identity</th><th style="text-transform: none; letter-spacing: 0">Summary</th><th style="text-transform: none; letter-spacing: 0">Consequence</th></tr></thead>
			<tbody>
				<tr v-for="(r, i) in rows" :key="`${r.category}-${r.identity}-${i}`">
					<td data-label="Change area">{{ r.category }}</td>
					<td data-label="Change">{{ r.change }}</td>
					<td data-label="Identity" style="font-size: 13px; overflow-wrap: anywhere">{{ r.identity }}</td>
					<td data-label="Summary" style="font-size: 13px">{{ r.summary }}</td>
					<td data-label="Consequence"><span class="kt-status" :class="r.effect === 'Breaking' ? 'is-attention' : 'is-live'">{{ r.effect === "Breaking" ? "Not interchangeable" : "Compatible" }}</span></td>
				</tr>
			</tbody>
		</table>
		<div v-if="pages > 1" class="stdt-pager" data-testid="stdt-change-pager">
			<span style="font-size: 13px">Page {{ page }} of {{ pages }} · {{ total }} changes</span>
			<button type="button" class="kt-btn kt-btn-secondary" :disabled="page <= 1" @click="emitHash({ chp: String(page - 1) })">Previous</button>
			<button type="button" class="kt-btn kt-btn-secondary" :disabled="page >= pages" @click="emitHash({ chp: String(page + 1) })">Next</button>
		</div>
	</div>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { getChanges } from "../data/api.js";

const props = defineProps({ releaseId: { type: String, required: true }, hashState: { type: Object, default: () => ({}) } });
const emit = defineEmits(["hash"]);
const guard = kentender_core.desk_page.createSequenceGuard();
const category = computed(() => props.hashState.cc || "");
const rows = ref([]);
const categories = ref([]);
const page = ref(1);
const pages = ref(1);
const total = ref(0);
const loading = ref(true);
const failed = ref(false);

function emitHash(next) {
	emit("hash", { ...next, __replace: true });
}
async function load() {
	const token = guard.next();
	loading.value = true;
	failed.value = false;
	try {
		const result = await getChanges(props.releaseId, { category: category.value, page: Number(props.hashState.chp || 1) });
		if (!guard.isCurrent(token)) return;
		rows.value = result.rows || [];
		categories.value = (result.filters && result.filters.categories) || [];
		page.value = result.page || 1;
		pages.value = result.pages || 1;
		total.value = result.total || 0;
	} catch (e) {
		if (guard.isCurrent(token)) failed.value = true;
	} finally {
		if (guard.isCurrent(token)) loading.value = false;
	}
}
watch(() => [props.releaseId, category.value, props.hashState.chp], load, { immediate: true });
</script>
