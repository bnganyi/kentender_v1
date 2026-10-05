<script setup>
// ANL-CHG-001 v0.8 — Procurement Analytics. Ported from design/Analytics/*.dc.html (ANL-DES-21 to 31J); the
// boards' markup is the build source. A read-only page: tabs, filters, links and the disclosure are the only
// controls, and there is no next-step block and no journey tracker. Everything it says is made by the
// server (counts, percentages, labels, bands, dates, amounts, order, paging); nothing here computes work.
//
// The URL is the state (§9.1, route_spike.md): the tab is a path segment and the applied filters are the query
// string, read through the app's own `useRouteState()` on every route change. Search text and the paging cursor
// stay here, in component state. The Financial year and Department selects are the caller's own pending
// selection until Apply filters is pressed; they never follow the server's echo (AGENTS.md 6.4).
import { computed, ref, watch } from "vue";
import AnalyticsHeader from "./components/AnalyticsHeader.vue";
import AnalyticsFilters from "./components/AnalyticsFilters.vue";
import AnalyticsIcon from "./components/AnalyticsIcon.vue";
import AnalyticsTabs from "./components/AnalyticsTabs.vue";
import AreaCharts from "./components/AreaCharts.vue";
import AreaResult from "./components/AreaResult.vue";
import CoverageRegion from "./components/CoverageRegion.vue";
import DefinitionsDisclosure from "./components/DefinitionsDisclosure.vue";
import FundingRegion from "./components/FundingRegion.vue";
import OutstandingRows from "./components/OutstandingRows.vue";
import RegionMessage from "./components/RegionMessage.vue";
import RegisterRegion from "./components/RegisterRegion.vue";
import StatePanel from "./components/StatePanel.vue";
import StepsRegion from "./components/StepsRegion.vue";
import SummaryStrip from "./components/SummaryStrip.vue";
import WaitingRegion from "./components/WaitingRegion.vue";
import { regionId, useAnalytics } from "./composables/useAnalytics.js";
import { buildUrl, useRouteState } from "./composables/useRouteState.js";

const { url, route, epoch, go, sync } = useRouteState();
const analytics = useAnalytics({ getUrl: () => url.value });
const { phase, data, refreshing, busy, retryFailed, search } = analytics;

// The pending selections of the two filter selects and the search box: the caller's own, bound by v-model.
const fyDraft = ref(url.value.fy);
const deptDraft = ref(url.value.dept);
const searchDraft = ref("");

// Words the page owns while there is no payload yet (the board's loading and failed states): its title, its
// description and the six peer tabs of §9.1. Once a payload arrives the server's own are drawn.
const FALLBACK_TABS = [
	{ key: "overview", label: __("Overview"), icon: "" },
	{ key: "needs", label: __("Needs"), icon: "needs" },
	{ key: "departmental-planning", label: __("Departmental planning"), icon: "departmental-planning" },
	{ key: "annual-planning", label: __("Annual planning"), icon: "annual-planning" },
	{ key: "requisitions", label: __("Requisitions"), icon: "requisitions" },
	{ key: "tender-proceedings", label: __("Tender proceedings"), icon: "tender-proceedings" },
];
const TITLE = __("Procurement Analytics");
const DESCRIPTION = __("See where procurement work stands, how long key steps take and how much planned value is covered.");

// Which of the board's states is drawn.
const view = computed(() => {
	if (phase.value === "failed") return "failed";
	const payload = data.value;
	if (!payload) return "loading";
	if (payload.verdict === "denied" || payload.verdict === "no_area") return "denied";
	if (payload.verdict === "failed") return "failed";
	// ANL §8 / AC-13: an invalid or unpermitted filter value never widens the selection. The server then sends
	// the message(s), the valid parts and the option lists, and no regions: the page draws only the header, tabs,
	// filter row and messages.
	if (payload.filters && payload.filters.invalid) return "invalid";
	if (payload.empty) return "empty";
	return "ready";
});
const tabs = computed(() => (data.value && data.value.tabs && data.value.tabs.length ? data.value.tabs : FALLBACK_TABS));
const filters = computed(() => (data.value && data.value.filters) || { fy_options: [], dept_options: [], messages: [] });
const overview = computed(() => (data.value && data.value.overview) || null);
const area = computed(() => (data.value && data.value.area) || null);
const title = computed(() => (data.value && data.value.title) || TITLE);
const description = computed(() => (data.value && data.value.description) || DESCRIPTION);

// ----- the route is the state ----------------------------------------------------------------------------

let previousTab = url.value.tab;
watch(
	() => url.value.key,
	(key, previous) => {
		// A new tab starts clean; a changed filter or state keeps the search text and starts at the first page.
		analytics.routeChanged(previous === undefined ? null : { tab: previousTab }, url.value);
		previousTab = url.value.tab;
		fyDraft.value = url.value.fy;
		deptDraft.value = url.value.dept;
		searchDraft.value = search.value;
		analytics.load();
	},
	{ immediate: true },
);
// Frappe's router moved to another path of this page (a sidebar link, set_route): read the address again.
watch(route, () => sync(), { deep: true });
// The page was shown again on the same route: revalidate in place, no skeleton (AGENTS.md 6.4).
watch(epoch, () => {
	if (!sync()) analytics.load();
});

// ----- navigation: every one pushes a history entry (§9.1) -----------------------------------------------

function sameAddress(change) {
	return !go(change);
}
// Changing tab keeps the applied fy and dept and drops state, search and cursor.
function openTab(tab) {
	if (tab === url.value.tab) return;
	go({ tab, state: "" });
}
function applyFilters() {
	const reread = sameAddress({ fy: fyDraft.value, dept: deptDraft.value });
	if (reread) {
		analytics.routeChanged({ tab: url.value.tab }, url.value);
		analytics.load();
	}
}
function clearFilters() {
	fyDraft.value = "";
	deptDraft.value = "";
	searchDraft.value = "";
	search.value = "";
	if (sameAddress({ fy: "", dept: "", state: "" })) {
		analytics.routeChanged({ tab: url.value.tab }, url.value);
		analytics.load();
	}
}
function selectState(key) {
	go({ state: key || "" });
}
function clearRegister(kind) {
	if (kind === "state") selectState("");
	else {
		searchDraft.value = "";
		analytics.clearSearch();
	}
}
function submitSearch() {
	analytics.submitSearch(searchDraft.value);
}
function openRecord(routeArray) {
	frappe.set_route(...routeArray);
}
const hrefFor = (tab) => buildUrl({ tab, fy: url.value.fy, dept: url.value.dept });
const clearHref = computed(() => buildUrl({ tab: url.value.tab }));
const retryFailedFor = (id) => !!retryFailed[id];
</script>

<template>
	<div class="kt-industry kt-analytics" data-testid="kt-anl-root">
		<div class="kt-ap-frame">
			<main class="kt-ap-sheet" :aria-busy="view === 'loading' ? 'true' : 'false'" :data-refreshing="refreshing ? 'true' : null">
				<!-- ANL-DES-31G: loading. Title, description, tabs and one line; no counts, filter values, update time, charts or actions. -->
				<template v-if="view === 'loading'">
					<AnalyticsHeader :title="title" :description="description" :refresh="false" />
					<AnalyticsTabs :tabs="tabs" :selected="url.tab" @select="openTab" />
					<p class="kt-ap-loading" role="status" data-testid="kt-anl-loading">{{ __("Loading Analytics…") }}</p>
				</template>

				<!-- ANL-DES-31H: no permitted area (and a user who may not open Analytics at all): the title and one line, nothing else. -->
				<template v-else-if="view === 'denied'">
					<h1 class="kt-ap-title" data-testid="kt-anl-title">{{ title }}</h1>
					<StatePanel :text="data.message" spot="neutral" icon="lock" data-testid="kt-anl-denied" />
				</template>

				<template v-else>
					<AnalyticsHeader
						:title="title"
						:description="description"
						:updated="view === 'failed' ? '' : data && data.updated"
						:scope="(data && data.scope) || ''"
						@refresh="analytics.load()"
					/>
					<AnalyticsTabs :tabs="tabs" :selected="url.tab" @select="openTab" />
					<AnalyticsFilters
						v-model:fy="fyDraft"
						v-model:dept="deptDraft"
						:fy-options="filters.fy_options"
						:dept-options="filters.dept_options"
						:messages="filters.messages"
						:clear-href="clearHref"
						@apply="applyFilters"
						@clear="clearFilters"
					/>

					<!-- ANL-DES-31D: all reads failed. -->
					<StatePanel v-if="view === 'failed'" :text="(data && data.message) || __('Analytics could not be loaded.')" spot="error" icon="circle-x" data-testid="kt-anl-failed">
						<button type="button" class="btn btn-primary" data-testid="kt-anl-retry-all" @click="analytics.load()">
							<AnalyticsIcon name="refresh-cw" />{{ __("Try again") }}
						</button>
					</StatePanel>

					<!-- An invalid or unpermitted filter value: the filter row carries the messages and Clear filters; no region is drawn. -->
					<template v-else-if="view === 'invalid'" />

					<!-- ANL-DES-31B: a permitted selection with no records. -->
					<StatePanel v-else-if="view === 'empty'" :text="data.message" icon="inbox" data-testid="kt-anl-empty">
						<a :href="clearHref" class="kt-ap-panel-link" data-testid="kt-anl-empty-clear" @click.prevent="clearFilters">{{ __("Clear filters") }}</a>
					</StatePanel>

					<div v-else :key="url.tab" class="kt-ap-content" :data-tab="url.tab">
						<!-- Overview (ANL-DES-21, 28, 29, 29F, 31C, 31E, 31J) -->
						<template v-if="overview">
							<SummaryStrip
								:strip="overview.strip"
								:href-for="hrefFor"
								:busy="busy"
								:failed="retryFailed"
								@open="openTab"
								@retry="analytics.retry($event)"
							/>
							<section v-if="overview.coverage" class="kt-ap-split is-3-2">
								<div><WaitingRegion :waiting="overview.waiting" /></div>
								<div>
									<CoverageRegion
										:coverage="overview.coverage"
										:href-for="hrefFor"
										:busy="!!busy[regionId.coverage]"
										:failed="retryFailedFor(regionId.coverage)"
										@open="openTab"
										@retry="analytics.retry(regionId.coverage)"
									/>
								</div>
							</section>
							<section v-else class="kt-ap-section is-ruled"><WaitingRegion :waiting="overview.waiting" /></section>
							<StepsRegion v-if="overview.steps" :steps="overview.steps" />
							<FundingRegion
								v-if="overview.funding"
								:funding="overview.funding"
								:busy="!!busy[regionId.funding]"
								:failed="retryFailedFor(regionId.funding)"
								@retry="analytics.retry(regionId.funding)"
							/>
						</template>

						<!-- An area tab (ANL-DES-22 to 27, 30, 30B, 31A, 31F) -->
						<template v-else-if="area">
							<section v-if="area.status === 'unavailable'" class="kt-ap-section is-ruled">
								<RegionMessage
									:message="area.message"
									:busy="!!busy[regionId.area]"
									:failed="retryFailedFor(regionId.area)"
									@retry="analytics.retry(regionId.area)"
								/>
							</section>
							<template v-else>
								<AreaResult :area="area" />
								<section v-if="area.figures && area.figures.length" class="kt-ap-figures" data-testid="kt-anl-figures">
									<div v-for="figure in area.figures" :key="figure.label" class="kt-kpi-card kt-ap-figure">
										<span class="kt-kpi-head">{{ figure.label }}</span>
										<span class="kt-kpi-value">{{ figure.value }}</span>
									</div>
								</section>
								<OutstandingRows v-if="area.outstanding && area.outstanding.rows.length" :outstanding="area.outstanding" />
								<AreaCharts :area="area" :selected-state="url.state" @select-state="selectState" />
								<StepsRegion v-if="area.steps" :steps="area.steps" />
								<RegisterRegion
									v-if="area.register"
									v-model:search-text="searchDraft"
									:area="area"
									:selected-state="url.state"
									:has-previous="analytics.cursorStack.value.length > 0"
									@submit-search="submitSearch"
									@select-state="selectState"
									@clear="clearRegister"
									@next="analytics.nextPage()"
									@previous="analytics.previousPage()"
									@open-record="openRecord"
								/>
							</template>
						</template>

						<DefinitionsDisclosure :text="data.definitions" />
					</div>
				</template>
			</main>
		</div>
	</div>
</template>
