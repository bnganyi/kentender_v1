<!-- Procurement Planning — PLN-CHG-001 v1.2 §10.
     One bundle, several Pages: "procurement-planning" (workspace + task deep
     links) and "departmental-procurement-plan" (PLN-UI-02..05). This root
     reads the full route (page slug included) and picks the screen; further
     record pages join with their slices. -->
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

			<template v-else-if="screen === 'dpp'">
				<div v-if="loading" class="kt-card kt-blueprint" style="padding: 24px">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
					<i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<div v-for="row in 3" :key="row" class="pln-skel-row">
						<div class="kt-skel" style="width: 72%"></div>
						<div class="kt-skel" style="width: 52%"></div>
						<div class="kt-skel" style="width: 52%"></div>
						<div class="kt-skel" style="width: 44%"></div>
					</div>
				</div>
				<div v-else-if="error" class="kt-card kt-blueprint pln-state-card" data-testid="pln-error">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
					<i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<h3>Procurement Planning could not be loaded</h3>
					<p>Try again. If the problem continues, quote the support reference shown below.</p>
					<button class="kt-btn kt-btn-secondary" @click="load">Try again</button>
					<p class="pln-support-ref">Support reference: {{ supportRef }}</p>
				</div>
				<DppPlanScreen
					v-else
					:plan="dpp"
					:pending="pending"
					:certified="certified"
					:error-summary="errorSummary"
					@update:certified="certified = $event"
					@view-accepted-needs="onViewAcceptedNeeds"
					@add-direct="go(dppReference, 'add-direct')"
					@open-entry="onOpenEntry"
					@back="frappe.set_route('procurement-planning')"
					@save-draft="load"
					@submit="onSubmit"
				/>
			</template>

			<template v-else-if="screen === 'dpp-entry'">
				<div v-if="loading" class="kt-card kt-blueprint" style="padding: 24px">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
					<i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<div v-for="row in 3" :key="row" class="pln-skel-row">
						<div class="kt-skel" style="width: 72%"></div>
						<div class="kt-skel" style="width: 52%"></div>
						<div class="kt-skel" style="width: 52%"></div>
						<div class="kt-skel" style="width: 44%"></div>
					</div>
				</div>
				<DppEntryEditorScreen
					v-else
					:editor="editor"
					:pending="pending"
					:error-summary="errorSummary"
					@save-funding="onSaveFunding"
					@save-direct="onSaveDirect"
					@cancel="go(dppReference)"
				/>
			</template>
		</div>
	</div>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { useRouteState } from "../pln_shared/composables/useRouteState.js";
import { usePageRail } from "../pln_shared/composables/usePageRail.js";
import * as api from "./data/planningApi.js";
import WorkspaceScreen from "./components/WorkspaceScreen.vue";
import DppPlanScreen from "./components/DppPlanScreen.vue";
import DppEntryEditorScreen from "./components/DppEntryEditorScreen.vue";

const WORKSPACE_PAGE = "procurement-planning";
const DPP_PAGE = "departmental-procurement-plan";
const { route } = useRouteState(WORKSPACE_PAGE);

const railEl = ref(null);
const loading = ref(true);
const pending = ref(false);
const error = ref("");
const errorSummary = ref("");
const supportRef = ref("");
const workspace = ref({});
const dpp = ref({});
const editor = ref({});
const certified = ref(false);

// §10/§12.1 — explicit PE/FY are visible filters only; the server resolves
// the remembered server-side preference on a bare load.
const procuringEntity = ref("");
const financialYear = ref("");

const pageSlug = computed(() => route.value[0] || WORKSPACE_PAGE);
const segments = computed(() => route.value.slice(1).filter(Boolean));

const dppReference = computed(() =>
	pageSlug.value === DPP_PAGE ? segments.value[0] || "" : ""
);

const screen = computed(() => {
	if (pageSlug.value === DPP_PAGE && dppReference.value) {
		const second = segments.value[1];
		if (second === "add-direct" || second === "entry") return "dpp-entry";
		return "dpp";
	}
	return "workspace";
});

const entryId = computed(() =>
	segments.value[1] === "entry" ? segments.value[2] || "" : ""
);

function go(...parts) {
	frappe.set_route(DPP_PAGE, ...parts.filter(Boolean));
}

let loadSeq = 0;

async function load() {
	const seq = ++loadSeq;
	loading.value = true;
	error.value = "";
	errorSummary.value = "";
	try {
		if (screen.value === "workspace") {
			const loaded = await api.getPlanningWorkspace({
				procuring_entity: procuringEntity.value || undefined,
				financial_year: financialYear.value || undefined,
			});
			if (seq !== loadSeq) return;
			workspace.value = loaded;
			const context = loaded.context || {};
			if (context.procuring_entity) procuringEntity.value = context.procuring_entity;
			if (context.financial_year) financialYear.value = context.financial_year;
		} else if (screen.value === "dpp") {
			const loaded = await api.getDepartmentalPlan(dppReference.value);
			if (seq !== loadSeq) return;
			dpp.value = loaded;
			certified.value = false;
		} else if (screen.value === "dpp-entry") {
			const loaded = await api.getDppEntryEditor(
				dppReference.value, entryId.value || undefined
			);
			if (seq !== loadSeq) return;
			editor.value = loaded;
		}
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
	try {
		await api.selectPlanningContext({
			procuring_entity: procuringEntity.value,
			financial_year: financialYear.value,
		});
	} catch (e) {
		// a refused selection simply does not persist
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

async function run(action, fn) {
	if (pending.value) return null;
	pending.value = true;
	errorSummary.value = "";
	try {
		return await fn(api.newIdempotencyKey(action));
	} catch (e) {
		errorSummary.value = e.message;
		return null;
	} finally {
		pending.value = false;
	}
}

async function onOpenDepartmentalPlan(organisationUnit) {
	const result = await run("open-dpp", (key) =>
		api.openDepartmentalPlan({
			procuring_entity: procuringEntity.value,
			organisation_unit: organisationUnit,
			financial_year: financialYear.value,
			idempotency_key: key,
		})
	);
	if (result) await load();
}

function onOpenEntry(row) {
	go(dppReference.value, "entry", row.entry_id);
}

function onViewAcceptedNeeds() {
	frappe.set_route("departmental-needs");
}

async function onSubmit() {
	const result = await run("submit-dpp", (key) =>
		api.submitDepartmentalPlan({
			dpp_version: dpp.value.version?.name,
			certification_confirmed: certified.value,
			expected_record_version: dpp.value.record_version,
			idempotency_key: key,
		})
	);
	if (result) await load();
}

async function onSaveFunding(payload) {
	const result = await run("save-need-funding", (key) =>
		api.saveNeedFunding({
			dpp_version: editor.value.dpp_version,
			entry_id: payload.entry_id,
			budget_line: payload.budget_line,
			indicative_amount: payload.indicative_amount,
			expected_record_version: editor.value.record_version,
			idempotency_key: key,
		})
	);
	if (result) go(dppReference.value);
}

async function onSaveDirect(payload) {
	const result = await run("save-direct", (key) =>
		api.saveDirectRequirement({
			dpp_version: editor.value.dpp_version,
			entry_values: JSON.stringify(payload.values),
			entry_id: payload.entry_id || undefined,
			expected_record_version: editor.value.record_version,
			idempotency_key: key,
		})
	);
	if (result) go(dppReference.value);
}

function onNavigate(routeSegments) {
	if (!routeSegments || !routeSegments.length) return;
	frappe.set_route(...routeSegments);
}

watch([pageSlug, segments], () => load(), { immediate: true, deep: true });

const railTrail = computed(() => {
	const trail = [{ label: "Procurement Planning", route: [WORKSPACE_PAGE] }];
	if (dppReference.value) {
		trail.push({ label: dppReference.value, route: [DPP_PAGE, dppReference.value] });
		if (screen.value === "dpp-entry") {
			trail.push({
				label:
					segments.value[1] === "add-direct"
						? "Add direct requirement"
						: (editor.value.entry || {}).need_reference_line?.split(" · ")[0] ||
						  entryId.value,
			});
		}
	}
	return trail;
});

usePageRail(railEl, railTrail, {
	showPeSwitcher: true,
	onPeChange: () => {
		procuringEntity.value = "";
		financialYear.value = "";
		if (screen.value === "workspace") load();
		else frappe.set_route(WORKSPACE_PAGE);
	},
});
</script>
