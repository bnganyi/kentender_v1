<script setup>
// BDS-CHG-001 v0.8 §10.6 BDS-DES-05 — My bids, ported from "Bid Board v3 - A"
// (1440 table; 390 labelled cards). `GetMyBids` gives the active
// organisation's bids with their status, deadline, last update and the
// actions this person may take; nothing here derives a status or an action.
// A list, not a tracker (§10.19): no journey or next step in the rows. The
// filters are the caller's own selection and live in the URL query.
import { computed, inject, onMounted, onUnmounted, ref, watch } from "vue";
import { useNarrow } from "../composables/useNarrow.js";
import TablePagerHost from "../../pager_shared/TablePagerHost.vue";
import { usePagedRows } from "../../pager_shared/usePagedRows.js";

const METHOD = "kentender_procurement.bid_submission.api.get_my_bids";
// Row commands the read may offer; each then opens the bid it changed.
const COMMANDS = { prepare_replacement: "kentender_procurement.bid_submission.api.prepare_replacement_bid" };
const DEFAULT_OPTIONS = { status: [{ value: "", label: "All statuses" }] };

const props = defineProps({ initial: { type: Object, default: null } });
const portal = inject("portal");
const { route, go, epoch } = portal.useRoute({ ref, onMounted, onUnmounted });
const narrow = useNarrow();

function fromQuery(query) {
	const q = query || {};
	return { search: q.search || "", status: q.status || "", organisation: q.organisation || "" };
}
function same(a, b) {
	return JSON.stringify(a) === JSON.stringify(b);
}

const filters = ref(fromQuery(route.value.query));
const data = ref(props.initial);
const failure = ref("");
const guard = portal.createSequenceGuard();
const runner = portal.createCommandRunner({ ref }, { onError: (e) => (failure.value = e.message) });
const pending = computed(() => runner.pending.value);

const rows = computed(() => (data.value && data.value.rows) || []);
// The table-pagination standard (AGENTS.md §6.11): the wide table and the narrow cards draw the same page.
const { pagedRows, total, page, pageSize, setPage, setPageSize, reset } = usePagedRows(rows, "portal-my-bids");
const options = computed(() => (data.value && data.value.options) || DEFAULT_OPTIONS);
const filtered = computed(() => !!(filters.value.search || filters.value.status));

function tone(row) {
	return row.status_tone ? `is-${row.status_tone}` : "";
}
async function load() {
	const token = guard.next();
	try {
		const result = await portal.call(METHOD, { ...filters.value });
		if (!guard.isCurrent(token)) return;
		data.value = result;
		failure.value = "";
	} catch (e) {
		if (guard.isCurrent(token)) failure.value = e.message;
	}
}
function apply() {
	reset();
	go("/my-bids", { replace: true, query: { ...filters.value }, keepFocus: true });
	return load();
}
let searchTimer = null;
function onSearch() {
	clearTimeout(searchTimer);
	searchTimer = setTimeout(apply, 300);
}
onUnmounted(() => clearTimeout(searchTimer));
function runAction(row, action) {
	failure.value = "";
	return runner.run(async () => {
		const key = `bds-${action.command}-${row.bid_reference}-${Date.now().toString(36)}`;
		await portal.call(COMMANDS[action.command], { bid_reference: row.bid_reference, expected_record_version: action.record_version, idempotency_key: key }, { type: "POST" });
		go(action.href);
	}, action.label);
}
function clearFilters() {
	filters.value = { ...fromQuery({}), organisation: filters.value.organisation };
	return apply();
}
watch(
	() => route.value.query,
	(query) => {
		if (route.value.path !== "/my-bids") return;
		const next = fromQuery(query);
		if (!same(next, filters.value)) {
			filters.value = next;
			reset();
			load();
		}
	},
);
watch(epoch, () => load());
onMounted(() => {
	portal.setTitle(__("My bids"));
	if (!data.value) load();
});
</script>

<template>
	<div class="kt-page" data-testid="bds-my-bids">
		<div class="kt-page-head" :class="{ 'bds-head-stack': narrow }">
			<div class="bds-head-main">
				<div class="bds-title-row"><h1 class="kt-page-title">{{ __("My bids") }}</h1></div>
				<p class="kt-page-desc">{{ __("Continue your organisation's bids and view submission receipts.") }}</p>
			</div>
		</div>
		<div>
			<div class="kt-filter-bar" :class="{ 'bds-filter-stack': narrow }" role="search" :aria-label="__('Filter bids')">
				<div class="field">
					<label for="bds-bids-search">{{ __("Search Tender or bid") }}</label>
					<input id="bds-bids-search" v-model="filters.search" class="input" type="search" :placeholder="__('Tender or bid')" data-testid="bds-bids-search" @input="onSearch" @keydown.enter.prevent="apply">
				</div>
				<div class="field">
					<label for="bds-bids-status">{{ __("Status") }}</label>
					<select id="bds-bids-status" v-model="filters.status" class="input" data-testid="bds-bids-status" @change="apply">
						<option v-for="o in options.status" :key="'s' + o.value" :value="o.value">{{ __(o.label) }}</option>
					</select>
				</div>
				<div>
					<button type="button" class="btn btn-ghost" :class="{ 'bds-btn-block': narrow }" data-testid="bds-bids-clear" @click="clearFilters">{{ __("Clear filters") }}</button>
				</div>
			</div>

			<div v-if="failure" class="kt-notice is-critical bds-load-failure" role="alert" data-testid="bds-load-failure">
				<div class="kt-notice-body">{{ failure }}</div>
				<button type="button" class="btn btn-secondary" @click="load">{{ __("Try again") }}</button>
			</div>

			<template v-if="rows.length">
				<table v-if="!narrow" class="table" data-testid="bds-bids-table">
					<thead>
						<tr>
							<th>{{ __("Tender") }}</th>
							<th>{{ __("Bid") }}</th>
							<th>{{ __("Status") }}</th>
							<th>{{ __("Submission deadline") }}</th>
							<th>{{ __("Last updated") }}</th>
							<th>{{ __("Action") }}</th>
						</tr>
					</thead>
					<tbody>
						<tr v-for="row in pagedRows" :key="row.bid_reference" :data-testid="'bds-bid-row-' + row.bid_reference">
							<td class="bds-tender-cell">{{ row.tender_title }}<div class="kt-label bds-tender-ref">{{ row.tender_reference }}</div><div v-for="a in row.alerts" :key="a.title" class="bds-row-alert"><a :href="a.href" data-testid="bds-bid-alert">{{ __(a.title) }}</a></div></td>
							<td><span class="bds-nowrap">{{ row.bid_reference }}</span><div v-if="row.version_label" class="kt-label">{{ row.version_label }}</div></td>
							<td><span class="kt-status" :class="tone(row)">{{ row.status_label }}</span></td>
							<td>{{ row.deadline_label }}</td>
							<td>{{ row.updated_label }}</td>
							<td>
								<div class="bds-row-actions">
									<template v-for="(a, i) in row.actions" :key="a.label">
										<button v-if="a.command" type="button" class="btn" :class="i === 0 ? 'btn-primary' : 'btn-secondary'" :disabled="pending" :data-testid="'bds-bid-action-' + i" @click="runAction(row, a)">{{ __(a.label) }}</button>
										<a v-else :href="a.href" class="btn" :class="i === 0 ? 'btn-primary' : 'btn-secondary'" :data-testid="'bds-bid-action-' + i">{{ __(a.label) }}</a>
									</template>
								</div>
							</td>
						</tr>
					</tbody>
				</table>
				<div v-else data-testid="bds-bids-cards">
					<div v-for="row in pagedRows" :key="row.bid_reference" class="bds-card" :data-testid="'bds-bid-row-' + row.bid_reference">
						<div class="bds-card-title">{{ row.tender_title }}<div class="kt-label bds-tender-ref">{{ row.tender_reference }}</div><div v-for="a in row.alerts" :key="a.title" class="bds-row-alert"><a :href="a.href" data-testid="bds-bid-alert">{{ __(a.title) }}</a></div></div>
						<div class="bds-card-fact"><span class="kt-label">{{ __("Bid") }}</span><span>{{ row.bid_reference }}</span></div>
						<div class="bds-card-fact"><span class="kt-label">{{ __("Status") }}</span><span><span class="kt-status" :class="tone(row)">{{ row.status_label }}</span></span></div>
						<div class="bds-card-fact"><span class="kt-label">{{ __("Submission deadline") }}</span><span>{{ row.deadline_label }}</span></div>
						<div class="bds-card-fact"><span class="kt-label">{{ __("Last updated") }}</span><span>{{ row.updated_label }}</span></div>
						<div class="bds-card-actions">
							<div class="bds-row-actions">
								<template v-for="(a, i) in row.actions" :key="a.label">
									<button v-if="a.command" type="button" class="btn bds-btn-touch" :class="i === 0 ? 'btn-primary' : 'btn-secondary'" :disabled="pending" :data-testid="'bds-bid-action-' + i" @click="runAction(row, a)">{{ __(a.label) }}</button>
									<a v-else :href="a.href" class="btn bds-btn-touch" :class="i === 0 ? 'btn-primary' : 'btn-secondary'" :data-testid="'bds-bid-action-' + i">{{ __(a.label) }}</a>
								</template>
							</div>
						</div>
					</div>
				</div>
				<TablePagerHost :total="total" :page="page" :page-size="pageSize" noun="bid" @update:page="setPage" @update:page-size="setPageSize" />
			</template>
			<div v-else-if="data" class="kt-empty" data-testid="bds-bids-empty">
				<p class="bds-empty-text">{{ filtered ? __("No bids match these filters.") : data.empty_text }}</p>
				<button v-if="filtered" type="button" class="btn btn-secondary" :class="{ 'bds-btn-touch': narrow }" @click="clearFilters">{{ __("Clear filters") }}</button>
				<a v-else href="/tenders" class="btn btn-primary" :class="{ 'bds-btn-touch': narrow }" data-testid="bds-bids-view-tenders">{{ __("View Tenders") }}</a>
			</div>
			<div v-else-if="!failure" class="bds-skeleton" aria-hidden="true" data-testid="bds-bids-loading"></div>
		</div>
	</div>
</template>
