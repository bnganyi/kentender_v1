<!-- "View coverage details" (STD-TPL-001 v0.10 §11.3): an in-page, searchable,
     filterable, server-paged read-only table of every source row. Filters and
     page live in the URL fragment (cq/ct/cp) so refresh and Back keep them.
     Not drawn open on the artboard; a registered structural departure. -->
<template>
	<div data-testid="stdt-coverage-details">
		<div class="kt-filter-bar" role="search">
			<div class="field is-wide"><label for="stdt-cq">Search source rows</label><input id="stdt-cq" v-model="draft" class="input" type="search" data-testid="stdt-coverage-search" @keydown.enter.prevent="apply" /></div>
			<div class="field"><label for="stdt-ct">Treatment</label>
				<select id="stdt-ct" :value="treatment" class="input" data-testid="stdt-coverage-treatment" @change="(e) => emitHash({ ct: e.target.value, cp: '' })">
					<option value="">All treatments</option>
					<option v-for="t in treatments" :key="t" :value="t">{{ t }}</option>
				</select>
			</div>
			<div></div>
		</div>
		<div v-if="failed" class="kt-notice is-critical" role="alert"><div class="kt-notice-body"><strong>Coverage details could not be loaded. Try again.</strong></div><button type="button" class="btn btn-secondary" @click="load">Try again</button></div>
		<p v-else-if="!loading && !rows.length" style="margin: 0; font-size: 14px">No source rows match these filters.</p>
		<table v-else class="table stdt-sub-table" style="width: 100%" :aria-busy="loading ? 'true' : 'false'">
			<thead><tr><th style="text-transform: none; letter-spacing: 0">Source locator</th><th style="text-transform: none; letter-spacing: 0">Title</th><th style="text-transform: none; letter-spacing: 0">Treatment</th><th style="text-transform: none; letter-spacing: 0">Output anchor</th><th style="text-transform: none; letter-spacing: 0">Reason</th></tr></thead>
			<tbody>
				<tr v-for="r in rows" :key="r.coverage_id" :data-testid="`stdt-coverage-row-${r.coverage_id}`">
					<td data-label="Source locator"><div style="font-weight: 600">{{ r.coverage_id }}</div><div style="font-size: 13px; color: var(--kt-color-neutral-800)">{{ r.source_locator }}</div></td>
					<td data-label="Title">{{ r.title }}</td>
					<td data-label="Treatment">{{ r.treatment }}<div v-if="r.review_status !== 'Reviewed'" style="font-size: 12px; color: var(--kt-color-neutral-700)">Awaiting review</div></td>
					<td data-label="Output anchor" style="font-size: 13px">{{ r.output_anchor || "Not rendered" }}</td>
					<td data-label="Reason" style="font-size: 13px; color: var(--kt-color-neutral-800)">{{ r.reason || "—" }}</td>
				</tr>
			</tbody>
		</table>
		<div v-if="pages > 1" class="stdt-pager" data-testid="stdt-coverage-pager">
			<span style="font-size: 13px">Page {{ page }} of {{ pages }} · {{ total }} rows</span>
			<button type="button" class="btn btn-secondary" :disabled="page <= 1" @click="emitHash({ cp: String(page - 1) })">Previous</button>
			<button type="button" class="btn btn-secondary" :disabled="page >= pages" @click="emitHash({ cp: String(page + 1) })">Next</button>
		</div>
	</div>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { getCoverage } from "../data/api.js";

const props = defineProps({ releaseId: { type: String, required: true }, hashState: { type: Object, default: () => ({}) } });
const emit = defineEmits(["hash"]);
const guard = kentender_core.desk_page.createSequenceGuard();

const search = computed(() => props.hashState.cq || "");
const treatment = computed(() => props.hashState.ct || "");
const page = ref(1);
const pages = ref(1);
const total = ref(0);
const rows = ref([]);
const treatments = ref([]);
const loading = ref(true);
const failed = ref(false);
const draft = ref(search.value);
watch(search, (v) => { if (v !== draft.value.trim()) draft.value = v; });

function emitHash(next) {
	emit("hash", { ...next, __replace: true });
}
function apply() {
	emitHash({ cq: draft.value.trim(), cp: "" });
}
let timer = null;
watch(draft, () => { clearTimeout(timer); timer = setTimeout(apply, 350); });

async function load() {
	const token = guard.next();
	loading.value = true;
	failed.value = false;
	try {
		const result = await getCoverage(props.releaseId, { search: search.value, treatment: treatment.value, page: Number(props.hashState.cp || 1) });
		if (!guard.isCurrent(token)) return;
		rows.value = result.rows || [];
		page.value = result.page || 1;
		pages.value = result.pages || 1;
		total.value = result.total || 0;
		treatments.value = (result.filters && result.filters.treatments) || [];
	} catch (e) {
		if (guard.isCurrent(token)) failed.value = true;
	} finally {
		if (guard.isCurrent(token)) loading.value = false;
	}
}
watch(() => [props.releaseId, search.value, treatment.value, props.hashState.cp], load, { immediate: true });
</script>
