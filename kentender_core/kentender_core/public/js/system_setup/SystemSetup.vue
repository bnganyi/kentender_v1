<script setup>
// CFG-CHG-002 v0.6 §9–§11 — the one System setup page: shared header, four
// horizontal tabs, hash-anchor tab state. Frappe supplies the Desk header and
// breadcrumb (KT-STD-001 §2.5); this component renders only the content
// column below it, ported from CFG-DES-01…07 and AUTH-DES-01…08.
//
// The hash selects the tab; refresh, direct load and browser back/forward
// preserve it (CFG-AC-024). Tab changes update the hash without a full route
// change (§9). No remembered browser context is required or authoritative.
import { computed, onMounted, onUnmounted, ref } from "vue";
import ProcuringEntityTab from "./tabs/ProcuringEntityTab.vue";
import FiscalYearsTab from "./tabs/FiscalYearsTab.vue";
import OrganisationStructureTab from "./tabs/OrganisationStructureTab.vue";
import UserResponsibilitiesTab from "./tabs/UserResponsibilitiesTab.vue";
import { siteConfigApi } from "./data/siteConfigApi.js";

const TABS = [
	{ key: "procuring-entity", label: __("Procuring entity") },
	{ key: "fiscal-years", label: __("Fiscal years") },
	{ key: "organisation-structure", label: __("Organisation structure") },
	{ key: "users-and-responsibilities", label: __("Users and responsibilities") },
];

const loading = ref(true);
const forbidden = ref(false);
const loadError = ref("");
const site = ref(null);
const activeTab = ref("procuring-entity");
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

function tabFromHash() {
	const hash = (window.location.hash || "").replace(/^#/, "");
	return TABS.some((tab) => tab.key === hash) ? hash : "";
}

function selectTab(key, { push = true } = {}) {
	if (tabDisabled(key)) return;
	activeTab.value = key;
	if (push && tabFromHash() !== key) {
		window.location.hash = key;
	}
}

let active = true;
function onHashChange() {
	if (!active) return;
	const key = tabFromHash();
	if (key && key !== activeTab.value && !tabDisabled(key)) {
		activeTab.value = key;
	}
}

async function load() {
	loading.value = true;
	loadError.value = "";
	forbidden.value = false;
	try {
		site.value = await siteConfigApi.getConfiguration();
		const wanted = tabFromHash();
		if (!configured.value) selectTab("procuring-entity", { push: false });
		else if (wanted && !tabDisabled(wanted)) selectTab(wanted, { push: false });
		else selectTab(activeTab.value && !tabDisabled(activeTab.value) ? activeTab.value : "procuring-entity", { push: false });
	} catch (error) {
		if (error.httpStatus === 403) forbidden.value = true;
		else loadError.value = error.message;
	} finally {
		loading.value = false;
	}
}

async function refreshSite() {
	// After a state-changing command the page re-reads authoritative data
	// (KT-STD §3); tab availability follows the fresh projection.
	site.value = await siteConfigApi.getConfiguration();
}

function viewAffected(unitId) {
	uraUnitFilter.value = unitId;
	selectTab("users-and-responsibilities");
}

function backToConfiguration() {
	frappe.set_route("Workspaces", "Platform Configuration & Governance");
}

onMounted(() => {
	window.addEventListener("hashchange", onHashChange);
	load();
});
onUnmounted(() => {
	// frappe.router.off() is a framework no-op; the DOM listener here is our
	// own, but the active flag also guards any late async callback.
	active = false;
	window.removeEventListener("hashchange", onHashChange);
});
</script>

<template>
	<div class="kt-industry kt-setup-root" data-testid="kt-setup-root">
		<div class="kt-setup-shell">
			<a
				href="#"
				class="kt-back-link"
				data-testid="back-to-workbench"
				@click.prevent="backToConfiguration"
			>← {{ __("Configuration and Governance") }}</a>

			<header class="kt-setup-header">
				<span class="kt-eyebrow">{{ __("Configuration and Governance") }}</span>
				<h1 class="kt-setup-title">{{ __("System setup") }}</h1>
				<p class="kt-setup-lede">
					{{ __("Configure this KenTender site, its financial years, organisational structure and user responsibilities.") }}
				</p>
			</header>

			<!-- CFG-DES-07 forbidden/error/loading — never an empty success -->
			<div v-if="forbidden" class="kt-card kt-blueprint kt-empty" data-testid="kt-setup-forbidden">
				<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
				<h2>{{ __("System setup is not available") }}</h2>
				<p>{{ __("You do not have the technical access required to configure this site.") }}</p>
			</div>

			<div v-else-if="loadError" class="kt-card kt-blueprint kt-empty" data-testid="kt-setup-error">
				<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
				<h2>{{ __("System setup could not be loaded") }}</h2>
				<p>{{ __("Try again. If the problem continues, contact support.") }}</p>
				<button type="button" class="kt-btn kt-btn-secondary" data-testid="kt-setup-retry" @click="load">
					{{ __("Try again") }}
				</button>
			</div>

			<div v-else-if="loading" class="kt-card kt-blueprint" data-testid="kt-setup-loading">
				<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
				<span class="kt-eyebrow">{{ __("Loading") }}</span>
				<div class="kt-skel" style="width:88%" />
				<div class="kt-skel" style="width:64%" />
				<div class="kt-skel" style="width:76%" />
			</div>

			<template v-else>
				<nav class="kt-setup-tabs" role="tablist" data-testid="kt-setup-tabs">
					<button
						v-for="tab in TABS"
						:key="tab.key"
						type="button"
						role="tab"
						class="kt-setup-tab"
						:class="{ 'is-active': activeTab === tab.key, 'is-disabled': tabDisabled(tab.key) }"
						:aria-selected="activeTab === tab.key"
						:disabled="tabDisabled(tab.key)"
						:data-testid="'kt-setup-tab-' + tab.key"
						@click="selectTab(tab.key)"
					>{{ tab.label }}</button>
				</nav>

				<ProcuringEntityTab
					v-if="activeTab === 'procuring-entity'"
					:site="site"
					@configured="refreshSite"
					@updated="refreshSite"
				/>
				<FiscalYearsTab v-else-if="activeTab === 'fiscal-years'" @changed="refreshSite" />
				<OrganisationStructureTab
					v-else-if="activeTab === 'organisation-structure'"
					@repaired="refreshSite"
					@view-affected="viewAffected"
				/>
				<UserResponsibilitiesTab
					v-else-if="activeTab === 'users-and-responsibilities'"
					:initial-unit="uraUnitFilter"
				/>
			</template>
		</div>
	</div>
</template>
