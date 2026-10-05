<!-- STD-DES-01 Installed template list, with 01F (filtered empty), 01E
     (installed empty) and 01R (read failure) — ported class-for-class from
     "STD Templates Artboards.dc.html" (DS .field/.input/.table/.btn ->
     .field/.input/.table/.btn). At 390 px or 200% zoom the table
     becomes labelled cards (std_templates.bundle.css; STD-TPL-001 §11.4). -->
<template>
	<div class="kt-page stdt-page" data-testid="stdt-list" data-screen-label="STD-DES-01 Installed template list">
		<div class="kt-page-head">
			<div>
				<p class="stdt-eyebrow">TENDER DOCUMENT STANDARDS</p>
				<h1 class="kt-page-title">STD Templates</h1>
				<p class="kt-page-desc">Review the Tender formats installed on this site, what they support and whether they are ready to use.</p>
			</div>
		</div>

		<div v-if="failed" class="kt-notice is-critical" style="align-items: center" role="alert" data-testid="stdt-list-failure">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" x2="12" y1="8" y2="12"></line><line x1="12" x2="12.01" y1="16" y2="16"></line></svg>
			<div class="kt-notice-body" style="flex: 1"><strong>STD Templates could not be loaded. Try again.</strong></div>
			<button type="button" class="btn btn-secondary" data-testid="stdt-list-retry" @click="$emit('retry')">Try again</button>
		</div>

		<div v-else-if="loading" data-testid="stdt-list-loading">
			<div class="kt-filter-bar"><div class="is-wide"><div class="kt-skel" style="height: 40px"></div></div><div><div class="kt-skel" style="height: 40px"></div></div><div></div></div>
			<div v-for="row in 3" :key="row" class="kt-skel" style="height: 44px; margin-bottom: 8px"></div>
		</div>

		<div v-else-if="data.empty_kind === 'installed'" class="kt-empty" data-testid="stdt-list-installed-empty">
			<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="m7.5 4.27 9 5.15"></path><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"></path><path d="m3.3 7 8.7 5 8.7-5"></path><path d="M12 22V12"></path></svg>
			<p style="margin: 0 auto; font-size: 15px; max-width: 520px">{{ data.empty }}</p>
		</div>

		<div v-else>
			<div class="kt-filter-bar" role="search">
				<div class="field is-wide">
					<label for="stdt-q">Search Tender format</label>
					<input id="stdt-q" v-model="draftSearch" class="input" type="search" data-testid="stdt-filter-search" @keydown.enter.prevent="emitFilter" />
				</div>
				<div class="field">
					<label for="stdt-s">Status</label>
					<select id="stdt-s" v-model="draftStatus" class="input" data-testid="stdt-filter-status" @change="emitFilter">
						<option value="">All statuses</option>
						<option v-for="s in statuses" :key="s" :value="s">{{ s }}</option>
					</select>
				</div>
				<div class="stdt-filter-actions">
					<button v-if="filtersActive" type="button" class="btn btn-secondary" data-testid="stdt-clear-filters" @click="clear">Clear filters</button>
				</div>
			</div>

			<div v-if="data.empty_kind === 'filtered'" class="kt-empty" data-testid="stdt-list-filtered-empty">
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="m13.5 8.5-5 5"></path><path d="m8.5 8.5 5 5"></path><circle cx="11" cy="11" r="8"></circle><path d="m21 21-4.3-4.3"></path></svg>
				<p style="margin: 0 0 16px; font-size: 15px">{{ data.empty }}</p>
				<button type="button" class="btn btn-secondary" @click="clear">Clear filters</button>
			</div>

			<table v-else class="table stdt-table" style="width: 100%" data-testid="stdt-list-table">
				<thead>
					<tr>
						<th style="text-transform: none; letter-spacing: 0">Tender format</th>
						<th style="text-transform: none; letter-spacing: 0">Release</th>
						<th style="text-transform: none; letter-spacing: 0">Supported use</th>
						<th style="text-transform: none; letter-spacing: 0">Status</th>
						<th style="text-transform: none; letter-spacing: 0">Official source</th>
						<th style="text-transform: none; letter-spacing: 0">Last verified</th>
						<th style="text-transform: none; letter-spacing: 0"><span class="stdt-sr-only">Action</span></th>
					</tr>
				</thead>
				<tbody v-for="row in data.releases" :key="row.release_id" :data-testid="`stdt-row-${row.template_key}-${row.template_release}`">
					<tr>
						<td data-label="Tender format" :style="cellStyle(row)"><div style="font-weight: 600">{{ row.display_name }}</div><div style="font-size: 12px; color: var(--kt-color-neutral-700); margin-top: 2px">{{ row.template_key }}</div></td>
						<td data-label="Release" :style="cellStyle(row)">{{ row.template_release }}</td>
						<td data-label="Supported use" :style="[cellStyle(row), { maxWidth: '300px' }]" :aria-label="row.supported_use.label"><div>{{ row.supported_use.line }}</div><div style="font-size: 13px; color: var(--kt-color-neutral-800); margin-top: 2px">{{ row.supported_use.detail }}</div></td>
						<td data-label="Status" :style="cellStyle(row)"><span class="kt-status" :class="row.status_class">{{ row.status }}</span></td>
						<td data-label="Official source" :style="[cellStyle(row), { maxWidth: '220px' }]">{{ row.official_source }}</td>
						<td data-label="Last verified" :style="[cellStyle(row), { whiteSpace: 'nowrap' }]">{{ row.last_verified }}</td>
						<td :style="cellStyle(row)" class="stdt-action-cell">
							<a :href="`/app/std-templates/${encodeURIComponent(row.release_id)}`" style="font-weight: 600" :data-testid="`stdt-view-${row.template_key}-${row.template_release}`" :aria-label="`View ${row.display_name} release ${row.template_release}`" @click.prevent.stop="$emit('view', row.release_id)">View</a>
						</td>
					</tr>
					<tr v-if="row.consequence" class="stdt-consequence-row">
						<td colspan="7" style="padding-top: 0">
							<div style="display: flex; gap: 8px; align-items: center; font-size: 13px">
								<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--kt-status-attention)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"></path><path d="M12 9v4"></path><path d="M12 17h.01"></path></svg>
								{{ row.consequence }}
							</div>
						</td>
					</tr>
				</tbody>
			</table>
		</div>
	</div>
</template>

<script setup>
import { computed, ref, watch } from "vue";

const props = defineProps({
	data: { type: Object, required: true },
	loading: { type: Boolean, default: false },
	failed: { type: Boolean, default: false },
	search: { type: String, default: "" },
	status: { type: String, default: "" },
});
const emit = defineEmits(["filter", "clear", "retry", "view"]);

// The caller's own selection drives the controls (AGENTS.md §6.4).
const draftSearch = ref(props.search);
const draftStatus = ref(props.status);
watch(
	() => [props.search, props.status],
	([search, status]) => {
		if (search !== draftSearch.value.trim()) draftSearch.value = search;
		if (status !== draftStatus.value) draftStatus.value = status;
	}
);
let timer = null;
watch(draftSearch, () => {
	clearTimeout(timer);
	timer = setTimeout(emitFilter, 350);
});

const statuses = computed(() => ((props.data.filters && props.data.filters.statuses) || []).filter((s) => s !== "All statuses"));
const filtersActive = computed(() => !!(props.search || props.status));

function emitFilter() {
	clearTimeout(timer);
	emit("filter", { search: draftSearch.value, status: draftStatus.value });
}
function clear() {
	clearTimeout(timer);
	draftSearch.value = "";
	draftStatus.value = "";
	emit("clear");
}
function cellStyle(row) {
	return { borderBottom: row.consequence ? "0" : undefined, verticalAlign: "top" };
}
</script>
