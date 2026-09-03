<script setup>
import { computed, onMounted, watch } from "vue";
import PageRail from "../kt_industry/components/PageRail.vue";
import SummaryCards from "./components/SummaryCards.vue";
import TabStrip from "./components/TabStrip.vue";
import PeList from "./components/pe/PeList.vue";
import PeDetail from "./components/pe/PeDetail.vue";
import PeNew from "./components/pe/PeNew.vue";
import FyList from "./components/fy/FyList.vue";
import FyDetail from "./components/fy/FyDetail.vue";
import FyNew from "./components/fy/FyNew.vue";
import ContextList from "./components/context/ContextList.vue";
import ContextDetail from "./components/context/ContextDetail.vue";
import ContextNew from "./components/context/ContextNew.vue";
import { useReferenceData } from "./composables/useReferenceData.js";
import { useRouteState } from "./composables/useRouteState.js";

const { pe, fy, context, peTypes, refreshPe, refreshFy, refreshContext, refreshAll, loadPeTypes } = useReferenceData();
onMounted(refreshAll);

const { state: route, goToTab, openRecord, openNew, openEdit, closeToList } = useRouteState();

// The registers and the summary cards above them are read once on mount, so a
// record created or activated on the New/Detail view stayed invisible here
// until the user reloaded the browser. Refetch whenever a register comes back
// into view; quiet, so the rows already on screen are not flashed away and
// back on every return.
watch(
	() => route.value.view,
	(view) => {
		if (view === "list") refreshAll({ quiet: true });
	}
);

const NEW_LABEL = { pe: "New procuring entity", fy: "New financial year", context: "New PE/FY context" };

function retryActive() {
	if (route.value.tab === "pe") refreshPe();
	else if (route.value.tab === "fy") refreshFy();
	else refreshContext();
}

function afterAction() {
	refreshAll();
}

// CFG-PEFY-DES-12 — same shape PageRail.vue expects: [{label, route?}], last item
// has no route (current, non-link crumb).
const TAB_LABELS = { pe: "Procuring Entities", fy: "Financial Years", context: "PE/FY Contexts" };
const railTrail = computed(() => {
	const items = [
		{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
		{ label: __("Reference Data"), route: ["reference-data"] },
	];
	const tabLabel = __(TAB_LABELS[route.value.tab]);
	if (route.value.view === "list") {
		items.push({ label: tabLabel });
	} else {
		items.push({ label: tabLabel, route: ["reference-data", route.value.tab] });
		items.push({ label: route.value.view === "new" ? __("New") : route.value.code });
	}
	return items;
});

const activePeTypes = computed(() => peTypes.value);
const activePeOptionsForContext = computed(() =>
	pe.value.rows.filter((r) => r.status === "Active").map((r) => ({ pe_id: r.pe_id, code: r.code, legal_name: r.legal_name }))
);
const availableFyOptionsForContext = computed(() =>
	fy.value.rows.filter((r) => r.record_status === "Available").map((r) => ({ financial_year_id: r.financial_year_id, label: r.label }))
);
</script>

<template>
	<div class="kt-industry" style="min-height:100vh;display:flex;flex-direction:column">
		<PageRail :trail="railTrail" />
		<template v-if="route.view === 'list'">
			<div style="padding:36px 48px 0;display:flex;align-items:flex-start;gap:32px">
				<div style="flex:1">
					<h1 style="margin:0;font-size:38px;line-height:1.05;letter-spacing:.005em">{{ __("Reference data") }}</h1>
					<p style="margin:10px 0 0;font-size:15px;max-width:760px;color:color-mix(in srgb, var(--kt-color-text) 72%, transparent)">
						{{ __("Maintain Procuring Entities, Financial Years and PE/FY Contexts used across KenTender.") }}
					</p>
				</div>
				<button type="button" class="kt-btn kt-btn-primary" style="margin-top:6px" @click="openNew(route.tab)">
					{{ __(NEW_LABEL[route.tab]) }}
				</button>
			</div>

			<SummaryCards :pe-rows="pe.rows" :fy-rows="fy.rows" :context-rows="context.rows" />

			<TabStrip :active-tab="route.tab" :pe-count="pe.rows.length" :fy-count="fy.rows.length" :context-count="context.rows.length" @select="goToTab" />

			<PeList v-if="route.tab === 'pe'" :rows="pe.rows" :loading="pe.loading" :error="pe.error" :pe-types="activePeTypes" @open="(code) => openRecord('pe', code)" @retry="retryActive" />
			<FyList v-else-if="route.tab === 'fy'" :rows="fy.rows" :loading="fy.loading" :error="fy.error" @open="(code) => openRecord('fy', code)" @retry="retryActive" />
			<ContextList
				v-else
				:rows="context.rows"
				:loading="context.loading"
				:error="context.error"
				:pe-options="pe.rows"
				:fy-options="fy.rows"
				@open="(code) => openRecord('context', code)"
				@retry="retryActive"
			/>
		</template>

		<template v-else-if="route.view === 'new'">
			<PeNew v-if="route.tab === 'pe'" :pe-types="activePeTypes" @created="(code) => openRecord('pe', code)" @cancel="closeToList('pe')" @pe-type-created="loadPeTypes" />
			<FyNew v-else-if="route.tab === 'fy'" @created="(code) => openRecord('fy', code)" @cancel="closeToList('fy')" />
			<ContextNew
				v-else
				:pe-options="activePeOptionsForContext"
				:fy-options="availableFyOptionsForContext"
				@created="(code) => openRecord('context', code)"
				@cancel="closeToList('context')"
			/>
		</template>

		<template v-else-if="route.view === 'edit'">
			<PeNew v-if="route.tab === 'pe'" :pe-types="activePeTypes" :edit-code="route.code" @created="(code) => openRecord('pe', code)" @cancel="openRecord('pe', route.code)" @pe-type-created="loadPeTypes" />
		</template>

		<template v-else-if="route.view === 'detail'">
			<PeDetail v-if="route.tab === 'pe'" :code="route.code" @after-action="afterAction" @edit="(code) => openEdit('pe', code)" />
			<FyDetail v-else-if="route.tab === 'fy'" :code="route.code" @after-action="afterAction" @open-context="(code) => openRecord('context', code)" />
			<ContextDetail v-else :code="route.code" @after-action="afterAction" />
		</template>
	</div>
</template>
