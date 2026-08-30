<!-- Procurement Planning — PLN-CHG-001 v1.2 §10.
     One Frappe Page ("procurement-planning") for the workspace and the task
     deep links under its prefix (§10: dpp-review/finance/review/publication).
     Record pages (departmental-procurement-plan, annual-procurement-plan,
     procurement-plan-item) are their own Pages, added by their slices. -->
<template>
	<div class="kt-industry kt-pln">
		<div ref="railEl" class="kt-rail-mount"></div>
		<!-- One stable page-ready hook (§16.2): specs wait for
		     [data-testid="pln-shell"][data-loading="false"]. -->
		<div
			class="kt-shell"
			data-testid="pln-shell"
			:data-screen="screen"
			:data-loading="loading ? 'true' : 'false'"
		>
			<WorkspaceScreen
				v-if="screen === 'workspace'"
				:loading="loading"
				:error="error"
				:support-ref="supportRef"
				:workspace="workspace"
				:pending="pending"
				@reload="load"
				@select-procuring-entity="onSelectPe"
				@select-financial-year="onSelectFy"
				@open-departmental-plan="onOpenDepartmentalPlan"
				@navigate="onNavigate"
			/>
		</div>
	</div>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { useRouteState } from "../pln_shared/composables/useRouteState.js";
import { usePageRail } from "../pln_shared/composables/usePageRail.js";
import * as api from "./data/planningApi.js";
import WorkspaceScreen from "./components/WorkspaceScreen.vue";

const PAGE = "procurement-planning";
const { route, go } = useRouteState(PAGE);

const railEl = ref(null);
const loading = ref(true);
const pending = ref(false);
const error = ref("");
const supportRef = ref("");
const workspace = ref({});

// §10/§12.1 — explicit PE/FY are visible filters only; a bare load lets the
// server resolve the remembered server-side preference.
const procuringEntity = ref("");
const financialYear = ref("");

const segments = computed(() => route.value.slice(1).filter(Boolean));

const screen = computed(() => {
	// dpp-review/{task}, finance/{task}, review/{task}, publication/{id} are
	// §10 deep links under this prefix; their screens arrive with their
	// slices. Anything unknown lands on the workspace rather than a dead end.
	return "workspace";
});

let loadSeq = 0;

async function load() {
	const seq = ++loadSeq;
	loading.value = true;
	error.value = "";
	try {
		const loaded = await api.getPlanningWorkspace({
			procuring_entity: procuringEntity.value || undefined,
			financial_year: financialYear.value || undefined,
		});
		if (seq !== loadSeq) return;
		workspace.value = loaded;
		const context = loaded.context || {};
		if (context.procuring_entity) procuringEntity.value = context.procuring_entity;
		if (context.financial_year) financialYear.value = context.financial_year;
	} catch (e) {
		if (seq !== loadSeq) return;
		error.value = e.message;
		supportRef.value = newSupportRef();
	} finally {
		if (seq === loadSeq) loading.value = false;
	}
}

function newSupportRef() {
	const now = new Date();
	const pad = (n) => String(n).padStart(2, "0");
	return (
		`PLN-ERR-${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}` +
		`-${pad(now.getHours())}${pad(now.getMinutes())}`
	);
}

async function persistSelection() {
	// §10 — the last valid selection is a server-side preference only.
	try {
		await api.selectPlanningContext({
			procuring_entity: procuringEntity.value,
			financial_year: financialYear.value,
		});
	} catch (e) {
		// A selection the server refuses simply does not persist.
	}
}

function onSelectPe(value) {
	procuringEntity.value = value;
	financialYear.value = "";
	load().then(persistSelection);
}

function onSelectFy(value) {
	financialYear.value = value;
	load().then(persistSelection);
}

async function onOpenDepartmentalPlan(organisationUnit) {
	if (pending.value) return;
	pending.value = true;
	try {
		await api.openDepartmentalPlan({
			procuring_entity: procuringEntity.value,
			organisation_unit: organisationUnit,
			financial_year: financialYear.value,
			idempotency_key: api.newIdempotencyKey("open-dpp"),
		});
		await load();
	} catch (e) {
		error.value = e.message;
	} finally {
		pending.value = false;
	}
}

function onNavigate(routeSegments) {
	if (!routeSegments || !routeSegments.length) return;
	frappe.set_route(...routeSegments);
}

watch(segments, () => load(), { immediate: true });

usePageRail(
	railEl,
	computed(() => [{ label: "Procurement Planning", route: [PAGE] }]),
	{
		// CTX-CHG-001 — the rail hosts the global PE switcher; a switch clears
		// this module's transient selection and the server re-resolves.
		showPeSwitcher: true,
		onPeChange: () => {
			procuringEntity.value = "";
			financialYear.value = "";
			load();
		},
	}
);
</script>
