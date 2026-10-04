<script setup>
// BDS-CHG-001 v0.8 §10.2 BDS-DES-01 — Available Tenders, ported from the
// "Bid Board v3 - A" artboard (1440 table; 390 labelled cards). Public: a
// guest and a signed-in supplier see the same list. The filters are the
// caller's own selection and live in the URL query, so direct load, refresh
// and back/forward keep them (AGENTS.md §6.4); the server filters and words
// every row. No Start bid, account status, value or document count here.
import { computed, inject, onMounted, onUnmounted, ref, watch } from "vue";
import { useNarrow } from "../composables/useNarrow.js";

const METHOD = "kentender_procurement.bid_submission.api.get_available_tenders";
const DEFAULT_OPTIONS = {
	method: [{ value: "", label: "All methods" }],
	reservation: [{ value: "", label: "All categories" }],
	closing: [{ value: "open", label: "Open Tenders" }],
};

const props = defineProps({
	initial: { type: Object, default: null },
});
const portal = inject("portal");
const { route, go, epoch } = portal.useRoute({ ref, onMounted, onUnmounted });
const narrow = useNarrow();

function fromQuery(query) {
	const q = query || {};
	return { search: q.search || "", method: q.method || "", reservation: q.reservation || "", closing: q.closing || "open" };
}
function toQuery(filters) {
	return { search: filters.search, method: filters.method, reservation: filters.reservation, closing: filters.closing === "open" ? "" : filters.closing };
}
function same(a, b) {
	return JSON.stringify(a) === JSON.stringify(b);
}

const filters = ref(fromQuery(route.value.query));
const data = ref(props.initial);
const failure = ref("");
const guard = portal.createSequenceGuard();

const rows = computed(() => (data.value && data.value.rows) || []);
const options = computed(() => (data.value && data.value.options) || DEFAULT_OPTIONS);

async function load() {
	const token = guard.next();
	const asked = { ...filters.value };
	try {
		const result = await portal.call(METHOD, asked);
		if (!guard.isCurrent(token)) return;
		data.value = result;
		failure.value = "";
	} catch (e) {
		if (guard.isCurrent(token)) failure.value = e.message;
	}
}

function apply() {
	go("/tenders", { replace: true, query: toQuery(filters.value), keepFocus: true });
	return load();
}

let searchTimer = null;
function onSearch() {
	clearTimeout(searchTimer);
	searchTimer = setTimeout(apply, 300);
}
onUnmounted(() => clearTimeout(searchTimer));

function clearFilters() {
	filters.value = fromQuery({});
	return apply();
}

// Back/forward to another filtered URL: take that selection and reload.
watch(
	() => route.value.query,
	(query) => {
		if (route.value.path !== "/tenders") return;
		const next = fromQuery(query);
		if (!same(next, filters.value)) {
			filters.value = next;
			load();
		}
	},
);
// Restored from the back/forward cache: revalidate in place.
watch(epoch, () => load());

onMounted(() => {
	portal.setTitle(__("Available Tenders"));
	if (!data.value) load();
});
</script>

<template>
	<div class="kt-page" data-testid="bds-available-tenders">
		<div class="kt-page-head">
			<div class="bds-head-main">
				<div class="bds-title-row">
					<h1 class="kt-page-title">{{ __("Available Tenders") }}</h1>
				</div>
				<p class="kt-page-desc">{{ __("Find current opportunities and review the full Tender before deciding to bid.") }}</p>
			</div>
		</div>
		<div>
			<div class="kt-filter-bar" :class="{ 'bds-filter-stack': narrow }" role="search" :aria-label="__('Filter Tenders')">
				<div class="kt-field">
					<label for="bds-filter-search">{{ __("Search title or reference") }}</label>
					<input id="bds-filter-search" v-model="filters.search" class="kt-input" type="search" :placeholder="__('Title or reference')" data-testid="bds-filter-search" @input="onSearch" @keydown.enter.prevent="apply">
				</div>
				<div class="kt-field">
					<label for="bds-filter-method">{{ __("Method") }}</label>
					<select id="bds-filter-method" v-model="filters.method" class="kt-input" data-testid="bds-filter-method" @change="apply">
						<option v-for="o in options.method" :key="'m' + o.value" :value="o.value">{{ __(o.label) }}</option>
					</select>
				</div>
				<div class="kt-field">
					<label for="bds-filter-reservation">{{ __("Reservation") }}</label>
					<select id="bds-filter-reservation" v-model="filters.reservation" class="kt-input" data-testid="bds-filter-reservation" @change="apply">
						<option v-for="o in options.reservation" :key="'r' + o.value" :value="o.value">{{ __(o.label) }}</option>
					</select>
				</div>
				<div class="kt-field">
					<label for="bds-filter-closing">{{ __("Closing") }}</label>
					<select id="bds-filter-closing" v-model="filters.closing" class="kt-input" data-testid="bds-filter-closing" @change="apply">
						<option v-for="o in options.closing" :key="'c' + o.value" :value="o.value">{{ __(o.label) }}</option>
					</select>
				</div>
				<div>
					<button type="button" class="kt-btn kt-btn-ghost" :class="{ 'bds-btn-block': narrow }" data-testid="bds-filter-clear" @click="clearFilters">{{ __("Clear filters") }}</button>
				</div>
			</div>

			<div v-if="failure" class="kt-notice is-critical bds-load-failure" role="alert" data-testid="bds-load-failure">
				<div class="kt-notice-body">{{ failure }}</div>
				<button type="button" class="kt-btn kt-btn-secondary" @click="load">{{ __("Try again") }}</button>
			</div>

			<template v-if="rows.length">
				<table v-if="!narrow" class="kt-table" data-testid="bds-tenders-table">
					<thead>
						<tr>
							<th>{{ __("Tender") }}</th>
							<th>{{ __("Procuring Entity") }}</th>
							<th>{{ __("Method") }}</th>
							<th>{{ __("Reservation") }}</th>
							<th>{{ __("Submission deadline") }}</th>
							<th>{{ __("Action") }}</th>
						</tr>
					</thead>
					<tbody>
						<tr v-for="row in rows" :key="row.reference" :data-testid="'bds-tender-row-' + row.reference">
							<td class="bds-tender-cell">{{ row.title }}<div class="kt-label bds-tender-ref">{{ row.reference }}</div></td>
							<td>{{ row.procuring_entity }}</td>
							<td>{{ row.method }}</td>
							<td>{{ row.reservation }}</td>
							<td>{{ row.submission_deadline_label }}</td>
							<td><a :href="row.href">{{ __("View Tender") }}</a></td>
						</tr>
					</tbody>
				</table>
				<div v-else data-testid="bds-tenders-cards">
					<div v-for="row in rows" :key="row.reference" class="bds-card" :data-testid="'bds-tender-row-' + row.reference">
						<div class="bds-card-title">{{ row.title }}<div class="kt-label bds-tender-ref">{{ row.reference }}</div></div>
						<div class="bds-card-fact"><span class="kt-label">{{ __("Procuring Entity") }}</span><span>{{ row.procuring_entity }}</span></div>
						<div class="bds-card-fact"><span class="kt-label">{{ __("Method") }}</span><span>{{ row.method }}</span></div>
						<div class="bds-card-fact"><span class="kt-label">{{ __("Reservation") }}</span><span>{{ row.reservation }}</span></div>
						<div class="bds-card-fact"><span class="kt-label">{{ __("Submission deadline") }}</span><span>{{ row.submission_deadline_label }}</span></div>
						<div class="bds-card-actions"><a :href="row.href">{{ __("View Tender") }}</a></div>
					</div>
				</div>
				<p class="bds-count" data-testid="bds-tenders-count">{{ data.count_text }}</p>
			</template>
			<div v-else-if="data" class="kt-empty" data-testid="bds-tenders-empty">
				<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="8" /><path d="m21 21-4.3-4.3" /></svg>
				<p class="bds-empty-text">{{ data.empty_text || __("No Tenders match these filters.") }}</p>
				<button type="button" class="kt-btn kt-btn-secondary" :class="{ 'bds-btn-touch': narrow }" @click="clearFilters">{{ __("Clear filters") }}</button>
			</div>
			<div v-else-if="!failure" class="bds-skeleton" aria-hidden="true" data-testid="bds-tenders-loading"></div>
		</div>
	</div>
</template>
