<!-- Procurement Requisitions — REQ-CHG-001 v1.11 §12 route table.
     One Page ("procurement-requisitions") owns every route; this root reads
     the route, loads the one read that route needs and hands its payload to
     the screen the server chose. It holds no business rule: whether a record
     opens as an editor, a locked Version, an authorised record or a stopped
     page is the server's `kind` (§14.6). -->
<template>
	<div class="kt-industry kt-req">
		<div ref="railEl" class="kt-rail-mount"></div>
		<!-- One stable page-ready hook (AGENTS.md §6.4/§6.7): specs wait for
		     [data-testid="req-shell"][data-loading="false"]. -->
		<div
			class="kt-shell"
			data-testid="req-shell"
			:data-screen="screen"
			:data-kind="payload.kind || ''"
			:data-loading="loading ? 'true' : 'false'"
			:data-refreshing="refreshing ? 'true' : 'false'"
		>
			<div v-if="refreshFailed && !loading && !error" class="req-refresh-failed" data-testid="req-refresh-failed">
				<Notice tone="warning">The latest state could not be loaded. What is shown may be out of date.</Notice>
				<button type="button" class="btn btn-secondary" @click="load({ quiet: true })">Try again</button>
			</div>
			<CommonState v-if="loading" kind="loading" />
			<CommonState v-else-if="error" kind="error" @retry="load()" />
			<CommonState v-else-if="payload.outcome === 'FORBIDDEN'" kind="forbidden" :message="payload.message" />
			<CommonState v-else-if="payload.outcome === 'NOT_FOUND'" kind="not-found" @back="go()" />
			<template v-else-if="screen === 'workspace' || screen === 'start'">
				<WorkspaceScreen :workspace="payload" :filters="workspaceFilters" @filters="onFilters" />
				<StartDialog v-if="screen === 'start' && start" :preview="start" @close="go()" />
			</template>
			<EditorScreen v-else-if="payload.kind === 'editor'" :key="payload.header.requisition" :view="payload" />
			<LockedScreen v-else-if="payload.kind === 'locked'" :view="payload" />
			<VersionScreen v-else-if="payload.kind === 'version'" :view="payload" />
			<AuthorisedScreen v-else-if="payload.kind === 'authorised'" :view="payload" />
			<StoppedScreen v-else-if="payload.kind === 'stopped'" :view="payload" />
			<DepartmentTaskScreen v-else-if="payload.kind === 'department_task'" :view="payload" />
			<ProcurementTaskScreen v-else-if="payload.kind === 'procurement_task'" :view="payload" />
		</div>
	</div>
</template>

<script setup>
import { computed, provide, ref, watch } from "vue";
import { useRouteState } from "../req_shared/composables/useRouteState.js";
import { usePageRail } from "../req_shared/composables/usePageRail.js";
import * as api from "./data/requisitionsApi.js";
import { key as mintKey } from "./data/format.js";
import { REQ_CONTEXT } from "./data/context.js";
import CommonState from "./components/shared/CommonState.vue";
import Notice from "./components/shared/Notice.vue";
import WorkspaceScreen from "./components/WorkspaceScreen.vue";
import StartDialog from "./components/StartDialog.vue";
import EditorScreen from "./components/EditorScreen.vue";
import LockedScreen from "./components/LockedScreen.vue";
import VersionScreen from "./components/VersionScreen.vue";
import AuthorisedScreen from "./components/AuthorisedScreen.vue";
import StoppedScreen from "./components/StoppedScreen.vue";
import DepartmentTaskScreen from "./components/DepartmentTaskScreen.vue";
import ProcurementTaskScreen from "./components/ProcurementTaskScreen.vue";

const PAGE = "procurement-requisitions";
const RESERVED = new Set(["new", "department-task", "procurement-task"]);
const { route, epoch } = useRouteState(PAGE);
const desk = kentender_core.desk_page;
// Last payload per screen identity: a revisited screen renders from here at
// once and revalidates in place; the skeleton is only for a screen never
// loaded in this session (AGENTS.md §6.4).
const cache = desk.createScreenCache();
const guard = desk.createSequenceGuard();

const railEl = ref(null);
const loading = ref(true);
const refreshing = ref(false);
const error = ref("");
const payload = ref({});
const start = ref(null);
const refreshFailed = ref(false);
// The caller's own filter selection — the inputs bind to this, never to the
// server's echo of it (AGENTS.md §6.4).
const workspaceFilters = ref({ search: "", status: "", department: "", fiscal_year: "" });

const segments = computed(() => route.value.slice(1).filter(Boolean));
const parsed = computed(() => {
	const [first, second, third] = segments.value;
	if (!first) return { screen: "workspace" };
	if (first === "new" && second) return { screen: "start", planItem: second };
	if (first === "department-task" && second) return { screen: "department-task", task: second };
	if (first === "procurement-task" && second) return { screen: "procurement-task", task: second };
	if (!RESERVED.has(first)) {
		if (second === "version" && third) return { screen: "record", requisition: first, version: third };
		return { screen: "record", requisition: first, version: "" };
	}
	return { screen: "workspace" };
});
const screen = computed(() => parsed.value.screen);

function screenKey(p) {
	switch (p.screen) {
		case "workspace":
		case "start":
			return `workspace:${JSON.stringify(workspaceFilters.value)}`;
		case "record":
			return `record:${p.requisition}:${p.version}`;
		default:
			return `${p.screen}:${p.task}`;
	}
}

function fetchFor(p) {
	switch (p.screen) {
		case "workspace":
		case "start":
			return api.getWorkspace(workspaceFilters.value);
		case "record":
			return api.getRecord(p.requisition, p.version);
		case "department-task":
			return api.getDepartmentTask(p.task);
		case "procurement-task":
			return api.getProcurementTask(p.task);
		default:
			return Promise.resolve({});
	}
}

// The skeleton shows only for a screen with nothing to show yet; one already
// loaded this session renders its last payload at once and refreshes in
// place. A slower, older response never overwrites a newer one.
async function load(opts) {
	const p = parsed.value;
	const k = screenKey(p);
	const cached = cache.get(k);
	if (cached) payload.value = cached;
	const quiet = !!cached || !!(opts && opts.quiet);
	const token = guard.next();
	if (quiet) refreshing.value = true;
	else loading.value = true;
	error.value = "";
	refreshFailed.value = false;
	try {
		const [loaded, preview] = await Promise.all([
			fetchFor(p),
			p.screen === "start" ? api.getStartPreview(p.planItem) : Promise.resolve(null),
		]);
		if (!guard.isCurrent(token)) return;
		cache.set(k, loaded);
		payload.value = loaded || {};
		start.value = preview;
	} catch (e) {
		if (!guard.isCurrent(token)) return;
		// A failed refresh keeps what is on screen (AGENTS.md §6.4): only a
		// screen with nothing to show yet falls back to the load-failure state.
		if (quiet && payload.value && payload.value.outcome) refreshFailed.value = true;
		else error.value = e.message || "error";
	} finally {
		if (guard.isCurrent(token)) {
			loading.value = false;
			refreshing.value = false;
		}
	}
}

watch(
	parsed,
	(next, prev) => {
		// Opening or closing the start dialog keeps the workspace on screen.
		if (prev && next.screen !== "start" && prev.screen !== "start") start.value = null;
		load();
	},
	{ immediate: true, deep: true }
);
// The page came back into view on the same route: revalidate what is shown.
watch(epoch, () => load({ quiet: true }));

function onFilters(next) {
	workspaceFilters.value = { ...workspaceFilters.value, ...next };
	load({ quiet: true });
}

function go(...args) {
	frappe.set_route(PAGE, ...args.filter((a) => a !== undefined && a !== null && a !== ""));
}

function goPath(path) {
	// Server-built routes are "/app/procurement-requisitions/..." strings.
	const parts = String(path || "").replace(/^\/app\//, "").split("/").filter(Boolean);
	if (parts.length) frappe.set_route(...parts);
}

// Every mutation runs through the shared runner: one in flight at a time, a
// fresh idempotency key per attempt, the refusal surfaced inline (never a
// Frappe modal — AGENTS.md §6.10). The post-command reload is awaited inside
// the runner so `pending` stays true until the page shows the new state.
const commandError = ref(null);
const runner = desk.createCommandRunner({ ref }, {
	mintKey: () => mintKey(),
	onStart: () => {
		commandError.value = null;
	},
	onError: (e, label) => {
		commandError.value = { code: e.code || "", message: e.message || "", detail: e.detail || {}, label: label || "", httpStatus: e.httpStatus || 0 };
	},
});

async function run(label, fn, opts) {
	return runner.run(async (idempotencyKey) => {
		const result = await fn(idempotencyKey);
		if (!(opts && opts.noReload)) await load({ quiet: true });
		return result === undefined ? true : result;
	}, label);
}

provide(REQ_CONTEXT, {
	pending: runner.pending,
	commandError,
	clearError: () => {
		commandError.value = null;
	},
	run,
	reload: () => load({ quiet: true }),
	go,
	goPath,
	api,
	refreshing,
});

const railTrail = computed(() => {
	const trail = [
		{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
		{ label: "Procurement Requisitions", route: [PAGE] },
	];
	const reference = (payload.value.header || {}).reference;
	if (screen.value === "start") trail.push({ label: "Start requisition" });
	else if (screen.value !== "workspace" && reference) trail.push({ label: reference });
	return trail;
});

// §1.1 — no Procuring Entity switcher anywhere in Requisitions.
usePageRail(railEl, railTrail, { showPeSwitcher: false });
</script>
