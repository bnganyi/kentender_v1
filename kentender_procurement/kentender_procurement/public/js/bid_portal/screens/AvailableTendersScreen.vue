<script setup>
// BDS-CHG-001 v0.8 §10.2 BDS-DES-01 — Available Tenders, ported from the
// "Bid Board v3 - A" artboard (1440 table; 390 labelled cards). Public: a
// guest and a signed-in supplier see the same list. The filters are the
// caller's own selection and live in the URL query, so direct load, refresh
// and back/forward keep them (AGENTS.md §6.4); the server filters and words
// every row. No Start bid, account status, value or document count here.
import { computed, inject, onMounted, onUnmounted, ref, watch } from "vue";
import { useNarrow } from "../composables/useNarrow.js";
import TablePagerHost from "../../pager_shared/TablePagerHost.vue";
import { usePagedRows } from "../../pager_shared/usePagedRows.js";

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
const filtersOpen = ref(false);

function fromQuery(query) {
	const q = query || {};
	return {
		search: q.search || "",
		method: q.method || "",
		reservation: q.reservation || "",
		closing: q.closing || "open",
		reference: q.reference || "",
		exact: q.exact || "",
		created_from: q.created_from || "",
		created_to: q.created_to || "",
		expiry_from: q.expiry_from || "",
		expiry_to: q.expiry_to || "",
	};
}
function toQuery(filters) {
	return {
		search: filters.search,
		method: filters.method,
		reservation: filters.reservation,
		closing: filters.closing === "open" ? "" : filters.closing,
		reference: filters.reference,
		exact: filters.exact,
		created_from: filters.created_from,
		created_to: filters.created_to,
		expiry_from: filters.expiry_from,
		expiry_to: filters.expiry_to,
	};
}
function same(a, b) {
	return JSON.stringify(a) === JSON.stringify(b);
}

const filters = ref(fromQuery(route.value.query));
const data = ref(props.initial);
const failure = ref("");
const guard = portal.createSequenceGuard();

const rows = computed(() => (data.value && data.value.rows) || []);
// The table-pagination standard (AGENTS.md §6.11): the wide table and the narrow cards draw the same page.
const { pagedRows, total, page, pageSize, setPage, setPageSize, reset } = usePagedRows(
	rows,
	"portal-tenders",
);
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
	reset();
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
			reset();
			load();
		}
	},
);
// Restored from the back/forward cache: revalidate in place.
watch(epoch, () => load());

onMounted(() => {
	portal.setTitle(__("All Tenders"));
	if (!data.value) load();
});
</script>

<template>
	<div class="kt-page" data-testid="bds-available-tenders">
		<div class="kt-page-head">
			<div class="bds-head-main">
				<div class="bds-title-row">
					<h1 class="kt-page-title">
						All <span class="bds-title-accent">Tenders</span>
					</h1>
				</div>
				<p class="kt-page-desc">
					{{
						__(
							"Browse published opportunities and review tender details across Kenya.",
						)
					}}
				</p>
			</div>
		</div>
		<div>
			<div class="bds-awarded-filter-heading">
				<h2>{{ __("All Tenders Filters") }}</h2>
				<button
					type="button"
					class="bds-filter-toggle"
					:aria-expanded="filtersOpen"
					aria-controls="bds-tender-filter-panel"
					data-testid="bds-filter-toggle"
					@click="filtersOpen = !filtersOpen"
				>
					{{ filtersOpen ? __("Hide Filters") : __("Show Filters")
					}}<span class="bds-filter-chevron" aria-hidden="true"></span>
				</button>
			</div>
			<div
				id="bds-tender-filter-panel"
				v-show="filtersOpen"
				class="bds-awarded-filter-panel"
				data-testid="bds-tender-filter-panel"
			>
				<form
					class="bds-awarded-form"
					role="search"
					:aria-label="__('Filter Tenders')"
					@submit.prevent="apply"
				>
					<div class="bds-awarded-fields bds-awarded-primary-fields">
						<div class="field">
							<label for="bds-filter-reference">{{ __("Ref. No.") }}</label>
							<input
								id="bds-filter-reference"
								v-model="filters.reference"
								class="input"
								type="search"
								:placeholder="__('Enter KET reference')"
								data-testid="bds-filter-reference"
								@input="onSearch"
							/>
						</div>
						<div class="field">
							<label for="bds-filter-location">{{ __("Location") }}</label>
							<select
								id="bds-filter-location"
								class="input"
								data-testid="bds-filter-location"
							>
								<option>{{ __("All Locations") }}</option>
								<option>Nairobi County</option>
								<option>Mombasa County</option>
								<option>Kisumu County</option>
								<option>Kiambu County</option>
								<option>Nakuru County</option>
							</select>
						</div>
						<div class="field">
							<label for="bds-filter-financier">{{ __("Financier") }}</label>
							<select
								id="bds-filter-financier"
								class="input"
								data-testid="bds-filter-financier"
							>
								<option>{{ __("All Financiers") }}</option>
								<option>World Bank</option>
								<option>African Development Bank</option>
								<option>European Union</option>
								<option>Government of Kenya</option>
								<option>USAID</option>
							</select>
						</div>
						<div class="field bds-keyword-field">
							<label for="bds-filter-search">{{ __("Search Keywords") }}</label>
							<input
								id="bds-filter-search"
								v-model="filters.search"
								class="input"
								type="search"
								:placeholder="__('Enter keywords')"
								data-testid="bds-filter-search"
								@input="onSearch"
								@keydown.enter.prevent="apply"
							/>
						</div>
					</div>
					<div class="bds-awarded-fields bds-awarded-date-fields">
						<div class="field">
							<label for="bds-filter-created-from">{{
								__("Tender Creation Date From")
							}}</label>
							<input
								id="bds-filter-created-from"
								v-model="filters.created_from"
								class="input"
								type="date"
								data-testid="bds-filter-created-from"
								@change="apply"
							/>
						</div>
						<div class="field">
							<label for="bds-filter-created-to">{{
								__("Tender Creation Date To")
							}}</label>
							<input
								id="bds-filter-created-to"
								v-model="filters.created_to"
								class="input"
								type="date"
								data-testid="bds-filter-created-to"
								@change="apply"
							/>
						</div>
						<div class="field">
							<label for="bds-filter-expiry-from">{{
								__("Tender Expiry Date From")
							}}</label>
							<input
								id="bds-filter-expiry-from"
								v-model="filters.expiry_from"
								class="input"
								type="date"
								data-testid="bds-filter-expiry-from"
								@change="apply"
							/>
						</div>
						<div class="field">
							<label for="bds-filter-expiry-to">{{
								__("Tender Expiry Date To")
							}}</label>
							<input
								id="bds-filter-expiry-to"
								v-model="filters.expiry_to"
								class="input"
								type="date"
								data-testid="bds-filter-expiry-to"
								@change="apply"
							/>
						</div>
					</div>
					<div class="bds-awarded-fields bds-awarded-live-fields">
						<div class="field">
							<label for="bds-filter-method">{{ __("Method") }}</label>
							<select
								id="bds-filter-method"
								v-model="filters.method"
								class="input"
								data-testid="bds-filter-method"
								@change="apply"
							>
								<option
									v-for="o in options.method"
									:key="'m' + o.value"
									:value="o.value"
								>
									{{ __(o.label) }}
								</option>
							</select>
						</div>
						<div class="field">
							<label for="bds-filter-reservation">{{ __("Reservation") }}</label>
							<select
								id="bds-filter-reservation"
								v-model="filters.reservation"
								class="input"
								data-testid="bds-filter-reservation"
								@change="apply"
							>
								<option
									v-for="o in options.reservation"
									:key="'r' + o.value"
									:value="o.value"
								>
									{{ __(o.label) }}
								</option>
							</select>
						</div>
						<div class="field">
							<label for="bds-filter-closing">{{ __("Closing") }}</label>
							<select
								id="bds-filter-closing"
								v-model="filters.closing"
								class="input"
								data-testid="bds-filter-closing"
								@change="apply"
							>
								<option
									v-for="o in options.closing"
									:key="'c' + o.value"
									:value="o.value"
								>
									{{ __(o.label) }}
								</option>
							</select>
						</div>
					</div>
					<div class="bds-awarded-actions">
						<button type="submit" class="btn btn-primary">
							{{ __("Search Available Tenders") }}
						</button>
						<button
							type="button"
							class="btn btn-secondary"
							data-testid="bds-filter-clear"
							@click="clearFilters"
						>
							{{ __("Reset Filters") }}
						</button>
					</div>
				</form>
			</div>

			<div
				v-if="failure"
				class="kt-notice is-critical bds-load-failure"
				role="alert"
				data-testid="bds-load-failure"
			>
				<div class="kt-notice-body">{{ failure }}</div>
				<button type="button" class="btn btn-secondary" @click="load">
					{{ __("Try again") }}
				</button>
			</div>

			<template v-if="rows.length">
				<div class="bds-tender-card-list" data-testid="bds-tenders-cards">
					<article
						v-for="row in pagedRows"
						:key="row.reference"
						class="bds-card"
						:data-testid="'bds-tender-row-' + row.reference"
					>
						<div class="bds-card-top">
							<div class="bds-card-badges">
								<span class="bds-badge bds-badge-category">{{
									row.reservation === "None"
										? __("No reservation")
										: row.reservation
								}}</span>
								<span class="bds-badge bds-badge-published">{{
									__("Published")
								}}</span>
							</div>
							<div class="bds-card-deadline">
								<span>{{ __("Submission Deadline:") }}</span>
								<strong>{{ row.submission_deadline_label }}</strong>
							</div>
						</div>
						<h3 class="bds-card-title">{{ row.title }}</h3>
						<div class="bds-card-meta">
							<div class="bds-card-facts">
								<div class="bds-card-fact">
									<span>{{ __("Procuring entity") }}</span
									><strong>{{ row.procuring_entity }}</strong>
								</div>
								<div class="bds-card-fact">
									<span>{{ __("Method") }}</span
									><strong>{{ row.method }}</strong>
								</div>
								<div class="bds-card-fact">
									<span>{{ __("Reservation") }}</span
									><strong>{{
										row.reservation === "None"
											? __("No reservation")
											: row.reservation
									}}</strong>
								</div>
								<div class="bds-card-fact">
									<span>{{ __("Reference") }}</span
									><strong>{{ row.reference }}</strong>
								</div>
							</div>
							<div class="bds-card-actions">
								<a :href="row.href"
									>{{ __("View Details") }} <span aria-hidden="true">→</span></a
								>
							</div>
						</div>
					</article>
				</div>
				<TablePagerHost
					:total="total"
					:page="page"
					:page-size="pageSize"
					noun="available Tender"
					@update:page="setPage"
					@update:page-size="setPageSize"
				/>
			</template>
			<div v-else-if="data" class="kt-empty" data-testid="bds-tenders-empty">
				<svg
					width="30"
					height="30"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="1.5"
					stroke-linecap="round"
					stroke-linejoin="round"
					aria-hidden="true"
				>
					<circle cx="11" cy="11" r="8" />
					<path d="m21 21-4.3-4.3" />
				</svg>
				<p class="bds-empty-text">
					{{ data.empty_text || __("No Tenders match these filters.") }}
				</p>
				<button
					type="button"
					class="btn btn-secondary"
					:class="{ 'bds-btn-touch': narrow }"
					@click="clearFilters"
				>
					{{ __("Clear filters") }}
				</button>
			</div>
			<div
				v-else-if="!failure"
				class="bds-skeleton"
				aria-hidden="true"
				data-testid="bds-tenders-loading"
			></div>
		</div>
	</div>
</template>
