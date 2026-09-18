<script setup>
// CFG-CHG-002 v0.11 §9–§11 — the one System setup page. The top rail
// (breadcrumb, notifications, user identity) is the shared
// kentender_core.industry.mountPageRail every Industry module mounts; the
// artboard's own breadcrumb line documents that rail and is not rendered
// again here. Below it, the module's content area ported from the boards:
// one white blueprint card carrying the eyebrow, title, lede, the five tabs
// and the active tab's sections. The hash selects the tab; refresh, direct
// load and browser back/forward preserve it (CFG-AC-024).
import { computed, onMounted, onUnmounted, ref } from "vue";
import ProcuringEntityTab from "./tabs/ProcuringEntityTab.vue";
import FiscalYearsTab from "./tabs/FiscalYearsTab.vue";
import OrganisationStructureTab from "./tabs/OrganisationStructureTab.vue";
import UserResponsibilitiesTab from "./tabs/UserResponsibilitiesTab.vue";
import ProcurementSettingsTab from "./tabs/ProcurementSettingsTab.vue";
import { siteConfigApi } from "./data/siteConfigApi.js";
import { usePageRail } from "./composables/usePageRail.js";

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
	// PLN-CHG-001 v1.18 §10.11 — the fifth tab houses the agreed
	// catalogue/profile maintenance (C03/C04); a presentation addition, not a
	// governance module.
	{ key: "procurement-settings", label: __("Procurement settings") },
];

const loading = ref(true);
const forbidden = ref(null);
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

// The hash is `#<tab>` or `#<tab>/<sub-path>` (a detail or editor within
// the Procurement settings tab, e.g. `#procurement-settings/rule/MPR-…`);
// refresh, direct load and back/forward restore both (CFG-AC-024).
const subpath = ref("");

function parseHashString(hash) {
	let raw = (hash || "").replace(/^#/, "");
	try {
		raw = decodeURIComponent(raw);
	} catch (e) {
		// see parseHash
	}
	return raw;
}

function parseHash() {
	// The browser percent-encodes a sub-path with spaces (a funding source
	// name); read it back decoded so `source/Government of Kenya` resolves.
	let raw = (window.location.hash || "").replace(/^#/, "");
	try {
		raw = decodeURIComponent(raw);
	} catch (e) {
		// A malformed escape stays as typed; it simply matches nothing.
	}
	const [key, ...rest] = raw.split("/");
	return { key: TABS.some((tab) => tab.key === key) ? key : "", sub: rest.join("/") };
}

function tabFromHash() {
	return parseHash().key;
}

function selectTab(key, { push = true, sub = "" } = {}) {
	if (tabDisabled(key)) return;
	activeTab.value = key;
	subpath.value = sub;
	const wanted = sub ? `${key}/${sub}` : key;
	if (push && parseHashString(window.location.hash) !== wanted) {
		window.location.hash = wanted;
	}
}

function navigateWithin(sub) {
	selectTab(activeTab.value, { sub });
}

let active = true;
function onHashChange() {
	if (!active) return;
	const { key, sub } = parseHash();
	if (key && !tabDisabled(key)) {
		activeTab.value = key;
		subpath.value = sub;
	}
}

async function load() {
	loading.value = true;
	loadError.value = "";
	forbidden.value = null;
	try {
		const result = await siteConfigApi.getConfiguration();
		if (result && result.outcome === "FORBIDDEN") {
			forbidden.value = result.forbidden;
			return;
		}
		site.value = result;
		const { key: wanted, sub } = parseHash();
		if (!configured.value) selectTab("procuring-entity", { push: false });
		else if (wanted && !tabDisabled(wanted)) selectTab(wanted, { push: false, sub });
		else selectTab(activeTab.value && !tabDisabled(activeTab.value) ? activeTab.value : "procuring-entity", { push: false });
	} catch (error) {
		loadError.value = error.message;
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
		<div ref="railEl" class="kt-rail-mount"></div>
		<div class="kt-setup-shell">
		<div class="kt-setup-page kt-blueprint">
			<header class="kt-setup-head">
				<span class="kt-eyebrow">{{ __("Configuration and governance") }}</span>
				<h1 class="kt-setup-title">{{ __("System setup") }}</h1>
				<p class="kt-setup-lede">
					{{ __("Manage this site's details, financial years, responsibilities and procurement settings.") }}
				</p>
				<nav v-if="!forbidden && !loadError && !loading" class="kt-tabs" role="tablist" data-testid="kt-setup-tabs">
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

			<div v-else-if="loading" class="kt-card kt-blueprint" data-testid="kt-setup-loading">
				<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
				<span class="kt-eyebrow">{{ __("Loading") }}</span>
				<div class="kt-skel" style="width:88%" />
				<div class="kt-skel" style="width:64%" />
				<div class="kt-skel" style="width:76%" />
			</div>

			<template v-else>
				<ProcuringEntityTab
					v-if="activeTab === 'procuring-entity'"
					:site="site"
					:on-updated="refreshSite"
					@configured="refreshSite"
					@navigate="(sub) => selectTab('procurement-settings', { sub })"
				/>
				<FiscalYearsTab
					v-else-if="activeTab === 'fiscal-years'"
					:subpath="subpath"
					@changed="refreshSite"
					@navigate="navigateWithin"
				/>
				<ProcurementSettingsTab
					v-else-if="activeTab === 'procurement-settings'"
					:subpath="subpath"
					@navigate="navigateWithin"
				/>
				<OrganisationStructureTab
					v-else-if="activeTab === 'organisation-structure'"
					:can-repair="!!(site && site.capabilities && site.capabilities.repair_root)"
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
		</div>
	</div>
</template>
