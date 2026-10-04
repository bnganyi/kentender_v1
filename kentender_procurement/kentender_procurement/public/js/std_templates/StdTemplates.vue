<!-- STD Templates — STD-TPL-001 v0.10 §11; STD-TPL-IMP-001 v1.0 §11.
       /app/std-templates                  installed template list (STD-DES-01, 01F, 01E, 01R)
       /app/std-templates/{release_id}     release detail (STD-DES-02, 02A, 02F, 02S, 02W, 02R)
     Filters, the selected section and open disclosures live in the URL
     fragment so refresh and Back keep them. One payload cache per screen
     identity and one sequence guard per loader (AGENTS.md §6.4); every value
     shown comes from the owner projection. -->
<template>
	<div class="kt-industry kt-stdt">
		<div ref="railEl" class="kt-rail-mount"></div>
		<div class="kt-shell" data-testid="stdt-shell" :data-screen="screen" :data-loading="loading ? 'true' : 'false'" :data-refreshing="refreshing ? 'true' : 'false'">
			<CommonState v-if="state" :kind="state.kind" :heading="state.heading" :text="state.text" @back="go()" />
			<ReleaseList
				v-else-if="kind === 'list'"
				:data="listData"
				:loading="loading && !listData.outcome"
				:failed="!!error"
				:search="listSearch"
				:status="listStatus"
				@filter="onFilter"
				@clear="onFilter({ search: '', status: '' })"
				@retry="retry"
				@view="(id) => go(id)"
			/>
			<ReleaseDetail
				v-else
				:data="detail"
				:loading="loading && !detail.outcome"
				:failed="!!error"
				:hash-state="hashState"
				@back="go()"
				@retry="retry"
				@hash="onHash"
				@report="concernOpen = true"
			/>
			<ReportConcernDialog
				v-if="concernOpen && detail.outcome === 'OK'"
				:release="detail.release"
				:categories="(detail.concerns && detail.concerns.categories) || []"
				:pending="pending"
				:errors="concernErrors"
				:error="concernError"
				@submit="onReportConcern"
				@cancel="closeConcern"
			/>
			<div v-if="notice" class="stdt-toast kt-notice is-success" role="status" data-testid="stdt-concern-reported">
				<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"></path></svg>
				<div class="kt-notice-body">{{ notice }}</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { useRouteState } from "./composables/useRouteState.js";
import { usePageRail } from "../tnd_shared/composables/usePageRail.js";
import * as api from "./data/api.js";
import { buildHash, parseHash } from "./data/hashState.js";
import CommonState from "./components/CommonState.vue";
import ReleaseList from "./components/ReleaseList.vue";
import ReleaseDetail from "./components/ReleaseDetail.vue";
import ReportConcernDialog from "./components/ReportConcernDialog.vue";

const PAGE = "std-templates";
const { route, epoch, hash, goHash } = useRouteState(PAGE);
const cache = kentender_core.desk_page.createScreenCache();
const loadGuard = kentender_core.desk_page.createSequenceGuard();

const railEl = ref(null);
const loading = ref(true);
const refreshing = ref(false);
const pending = ref(false);
const error = ref("");
const listData = ref({});
const detail = ref({});
const concernOpen = ref(false);
const concernErrors = ref({});
const concernError = ref("");
const notice = ref("");

const segments = computed(() => route.value.slice(1).filter(Boolean));
const releaseId = computed(() => segments.value[0] || "");
const kind = computed(() => (releaseId.value ? "detail" : "list"));
const screenKey = computed(() => (kind.value === "list" ? `list:${listSearch.value}|${listStatus.value}` : `detail:${releaseId.value}`));
const hashState = computed(() => parseHash(hash.value));
// Controlled inputs bind to the caller's own selection (AGENTS.md §6.4): the
// fragment is that selection, never the server echo.
const listSearch = computed(() => (kind.value === "list" ? hashState.value.search || "" : ""));
const listStatus = computed(() => (kind.value === "list" ? hashState.value.status || "" : ""));

const state = computed(() => {
	if (kind.value === "list" && listData.value.outcome === "FORBIDDEN") return { kind: "forbidden", heading: listData.value.heading, text: listData.value.text };
	if (kind.value === "detail" && detail.value.outcome === "NOT_FOUND") return { kind: "not-found", heading: detail.value.heading, text: detail.value.text };
	return null;
});
const screen = computed(() => {
	if (state.value) return state.value.kind;
	if (kind.value === "list") return "list";
	return detail.value.release ? `detail-${String(detail.value.release.status || "").toLowerCase()}` : "detail";
});

function go(...parts) {
	frappe.set_route(PAGE, ...parts.filter(Boolean));
}

async function fetchFor() {
	if (kind.value === "list") return { listData: await api.getReleases({ search: listSearch.value, status: listStatus.value }) };
	return { detail: await api.getRelease(releaseId.value) };
}
function applyLoaded(loaded) {
	if (loaded.listData) listData.value = loaded.listData;
	if (loaded.detail) detail.value = loaded.detail;
}
let inFlightKey = "";
async function load(opts) {
	const key = screenKey.value;
	const cached = cache.get(key);
	if (opts && opts.entering && cached) applyLoaded(cached);
	const quiet = !!(opts && opts.quiet === true) || !!cached;
	if (quiet && inFlightKey === key) return;
	const token = loadGuard.next();
	inFlightKey = key;
	if (quiet) refreshing.value = true;
	else loading.value = true;
	error.value = "";
	try {
		const loaded = await fetchFor();
		if (!loadGuard.isCurrent(token)) return;
		cache.set(key, loaded);
		applyLoaded(loaded);
	} catch (e) {
		if (!loadGuard.isCurrent(token)) return;
		error.value = e.message || "failed";
	} finally {
		if (loadGuard.isCurrent(token)) {
			loading.value = false;
			refreshing.value = false;
			inFlightKey = "";
		}
	}
}
function retry() {
	error.value = "";
	load({ quiet: !!cache.get(screenKey.value) });
}

function onFilter(next) {
	goHash(buildHash({ search: (next.search || "").trim(), status: next.status || "" }), { replace: true });
}
function onHash(next) {
	const { __replace: replace, ...changes } = next;
	const merged = { ...hashState.value, ...changes };
	delete merged.__replace;
	goHash(buildHash(merged), { replace: !!replace });
}

function closeConcern() {
	concernOpen.value = false;
	concernErrors.value = {};
	concernError.value = "";
}
async function onReportConcern({ values, file }) {
	if (pending.value) return;
	pending.value = true;
	concernErrors.value = {};
	concernError.value = "";
	try {
		let evidenceId = "";
		if (file) {
			try {
				evidenceId = await api.uploadEvidence(file);
			} catch (e) {
				concernErrors.value = { evidence_file_id: e.message };
				return;
			}
		}
		const result = await api.reportConcern(releaseId.value, { ...values, evidence_file_id: evidenceId });
		if (result && result.ok) {
			concernOpen.value = false;
			notice.value = result.message;
			setTimeout(() => (notice.value = ""), 6000);
			await load({ quiet: true });
			return;
		}
		if (result && result.errors) concernErrors.value = result.errors;
		else concernError.value = (result && result.message) || "The concern could not be reported. Try again.";
	} catch (e) {
		concernError.value = e.message || "The concern could not be reported. Try again.";
	} finally {
		pending.value = false;
	}
}

watch(
	screenKey,
	() => {
		concernOpen.value = false;
		load({ entering: true });
	},
	{ immediate: true }
);
watch(epoch, () => load({ quiet: true }));

const railTrail = computed(() => {
	if (kind.value === "list") return [{ label: __("Home"), route: ["Workspaces", "Procurement Home"] }, { label: "STD Templates" }];
	const name = (detail.value.release && detail.value.release.display_name) || releaseId.value;
	return [{ label: "STD Templates", route: [PAGE] }, { label: name }];
});
usePageRail(railEl, railTrail, { showPeSwitcher: false });
</script>
