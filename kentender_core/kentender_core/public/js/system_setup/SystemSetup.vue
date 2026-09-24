<script setup>
// CFG-CHG-002 v0.14 §9–§11 — the one System setup page. The top rail
// (breadcrumb, notifications, user identity) is the shared
// kentender_core.industry.mountPageRail every Industry module mounts; the
// artboard's own breadcrumb line documents that rail and is not rendered
// again here. Below it, the module's content area ported from the boards.
//
// Routing (AGENTS.md §6.4, plan D12): the URL is read only through
// useRouteState, over kentender_core.desk_page.useRoute in hash mode — no
// page-owned listener. Links follow the §9 grammar (data/routes.js); visited
// tabs are kept alive, and the skeleton shows only while there is nothing to
// show yet.
import { KeepAlive, computed, onMounted, ref, watch } from "vue";
import ProcuringEntityTab from "./tabs/ProcuringEntityTab.vue";
import FiscalYearsTab from "./tabs/FiscalYearsTab.vue";
import OrganisationStructureTab from "./tabs/OrganisationStructureTab.vue";
import UserResponsibilitiesTab from "./tabs/UserResponsibilitiesTab.vue";
import ProcurementSettingsTab from "./tabs/ProcurementSettingsTab.vue";
import { siteConfigApi } from "./data/siteConfigApi.js";
import { SECTIONS, legacyToRoute, routeToLegacy } from "./data/routes.js";
import { usePageRail } from "./composables/usePageRail.js";
import { useRouteState } from "./composables/useRouteState.js";

const railEl = ref(null);
usePageRail(
	railEl,
	computed(() => [
		{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
		{ label: __("Configuration and Governance"), route: ["Workspaces", "Platform Configuration & Governance"] },
		{ label: __("System setup") },
	])
);

const TABS = [
	{ key: "procuring-entity", label: __("Procuring entity") },
	{ key: "fiscal-years", label: __("Financial years") },
	{ key: "organisation-structure", label: __("Organisation structure") },
	{ key: "users-and-responsibilities", label: __("Users and responsibilities") },
	{ key: "procurement-settings", label: __("Procurement settings") },
];
const COMPONENTS = {
	"procuring-entity": ProcuringEntityTab,
	"fiscal-years": FiscalYearsTab,
	"organisation-structure": OrganisationStructureTab,
	"users-and-responsibilities": UserResponsibilitiesTab,
	"procurement-settings": ProcurementSettingsTab,
};

const { state: route, go } = useRouteState();

const loading = ref(true);
const forbidden = ref(null);
const loadError = ref("");
const site = ref(null);
// Set when "View affected responsibilities" jumps from the structure tab to
// the register with that unit pre-filtered. A visible, clearable filter —
// never authority (§14.2).
const uraUnitFilter = ref("");

const configured = computed(() => !!site.value?.configured);
const rootMissing = computed(() => configured.value && !site.value?.root_unit);

function tabDisabled(key) {
	// §11.1 — with no PE, only the Procuring entity tab is available; with a
	// PE but no root, the responsibilities tab waits for the governed repair.
	if (!configured.value) return key !== "procuring-entity";
	if (rootMissing.value && key === "users-and-responsibilities") return true;
	return false;
}

// §9 — "Default is the first incomplete structural setup tab; once
// entity/root exist, honor the requested tab, otherwise entity."
const defaultTab = computed(() => {
	if (!configured.value) return "procuring-entity";
	if (rootMissing.value) return "organisation-structure";
	return "procuring-entity";
});
const activeTab = computed(() => {
	const wanted = route.value.tab;
	return wanted && !tabDisabled(wanted) ? wanted : defaultTab.value;
});

// The address always names the tab on screen: a missing or refused tab is
// corrected in place, without adding a Back step.
watch(
	() => [site.value, route.value.tab, activeTab.value],
	() => {
		if (!site.value) return;
		if (route.value.tab !== activeTab.value) go({ tab: activeTab.value }, { replace: true });
	}
);

// The older view names the tabs still switch on (until each is re-ported),
// derived from the §9 link. Procurement settings translates its own, because
// telling a method rule from a reference rule needs its data.
const legacySubpath = computed(() => (activeTab.value === route.value.tab ? routeToLegacy(route.value) : ""));

function selectTab(key, { sub = "" } = {}) {
	if (tabDisabled(key)) return;
	go(sub ? legacyToRoute(key, sub) : { tab: key });
}

function navigateWithin(sub) {
	// A Procurement settings section named from another tab crosses to it
	// (the Procuring entity's "View procurement rules").
	const first = String(sub || "").split("/")[0];
	const tab = SECTIONS.includes(first) ? "procurement-settings" : activeTab.value;
	selectTab(tab, { sub });
}

const tabProps = computed(() => {
	switch (activeTab.value) {
		case "procuring-entity":
			return { site: site.value, onUpdated: refreshSite };
		case "fiscal-years":
			return { subpath: legacySubpath.value };
		case "procurement-settings":
			return { route: route.value };
		case "organisation-structure":
			return { canRepair: !!site.value?.capabilities?.repair_root };
		case "users-and-responsibilities":
			return { initialUnit: uraUnitFilter.value };
		default:
			return {};
	}
});

// Every read carries a sequence token; only the newest may write (§6.4).
const sequence = kentender_core.desk_page.createSequenceGuard();

async function load() {
	const token = sequence.next();
	// The skeleton is for a page with nothing on it yet; a retry after an
	// error or a refresh keeps whatever is already shown.
	if (!site.value) loading.value = true;
	loadError.value = "";
	forbidden.value = null;
	try {
		const result = await siteConfigApi.getConfiguration();
		if (!sequence.isCurrent(token)) return;
		if (result && result.outcome === "FORBIDDEN") {
			forbidden.value = result.forbidden;
			return;
		}
		site.value = result;
	} catch (error) {
		if (sequence.isCurrent(token)) loadError.value = error.message;
	} finally {
		if (sequence.isCurrent(token)) loading.value = false;
	}
}

async function refreshSite() {
	// After a state-changing command the page re-reads authoritative data
	// (KT-STD §3); tab availability follows the fresh projection.
	const token = sequence.next();
	const result = await siteConfigApi.getConfiguration();
	if (sequence.isCurrent(token) && result && result.outcome !== "FORBIDDEN") site.value = result;
}

function viewAffected(unitId) {
	uraUnitFilter.value = unitId;
	selectTab("users-and-responsibilities");
}

onMounted(load);
</script>

<template>
	<div class="kt-industry kt-setup-root" data-testid="kt-setup-root">
		<div ref="railEl" class="kt-rail-mount"></div>
		<div class="kt-setup-shell">
		<div class="kt-setup-page kt-blueprint">
			<header class="kt-setup-head">
				<span class="kt-eyebrow">{{ __("Configuration and governance") }}</span>
				<h1 class="kt-setup-title">{{ __("System setup") }}</h1>
				<p class="kt-setup-lede">
					{{ __("Manage this site's details, financial years, responsibilities and procurement settings.") }}
				</p>
				<nav v-if="!forbidden && !loadError && site" class="kt-tabs" role="tablist" data-testid="kt-setup-tabs">
					<button
						v-for="tab in TABS"
						:key="tab.key"
						type="button"
						role="tab"
						class="kt-tab"
						:aria-selected="activeTab === tab.key"
						:disabled="tabDisabled(tab.key)"
						:data-testid="'kt-setup-tab-' + tab.key"
						@click="selectTab(tab.key)"
					>{{ tab.label }}</button>
				</nav>
			</header>

			<div class="kt-setup-panel">
			<!-- CFG-DES-07 forbidden/error/loading — never an empty success -->
			<div v-if="forbidden" class="kt-card kt-blueprint kt-empty" data-testid="kt-setup-forbidden">
				<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
				<h2>{{ __(forbidden.heading) }}</h2>
				<p>{{ __(forbidden.text) }}</p>
			</div>

			<div v-else-if="loadError" class="kt-card kt-blueprint kt-empty" data-testid="kt-setup-error">
				<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
				<h2>{{ __("System setup could not be loaded") }}</h2>
				<p>{{ __("Try again. If the problem continues, contact support.") }}</p>
				<button type="button" class="kt-btn kt-btn-secondary" data-testid="kt-setup-retry" @click="load">
					{{ __("Try again") }}
				</button>
			</div>

			<div v-else-if="loading && !site" class="kt-card kt-blueprint" data-testid="kt-setup-loading">
				<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
				<span class="kt-eyebrow">{{ __("Loading") }}</span>
				<div class="kt-skel" style="width:88%" />
				<div class="kt-skel" style="width:64%" />
				<div class="kt-skel" style="width:76%" />
			</div>

			<KeepAlive v-else>
				<component
					:is="COMPONENTS[activeTab]"
					:key="activeTab"
					v-bind="tabProps"
					@configured="refreshSite"
					@changed="refreshSite"
					@repaired="refreshSite"
					@view-affected="viewAffected"
					@navigate="navigateWithin"
				/>
			</KeepAlive>
			</div>
		</div>
		</div>
	</div>
</template>
