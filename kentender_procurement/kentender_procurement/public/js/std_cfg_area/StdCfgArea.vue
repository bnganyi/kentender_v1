<script setup>
// PCFG-01..09 shared shell (§15.7-15.15): header/breadcrumb/footer around one
// of 3 area implementations — StdCfgAreaProfile (PCFG-01, Draft-field save),
// StdCfgAreaStructure (PCFG-02, Section/Content Block tree), or
// StdCfgAreaGeneric (PCFG-03..09, generic table+dialog editor over
// areaRegistry.js). Each area's own save happens inside that component
// (immediate per-item persistence via the real save_std_* command), not a
// single page-level Save button — a deliberate simplification from §15's
// single-footer-Save artboard: it avoids a whole class of "unsaved changes
// lost on navigation" bug for very little cost, and still calls the exact
// same real command per area.
import { ref, computed, onMounted, watch } from "vue";
import { useRouteState } from "../std_configuration_shared/composables/useRouteState.js";
import { usePageRail } from "../std_configuration_shared/composables/usePageRail.js";
import { AREA_REGISTRY } from "../std_configuration_shared/areaRegistry.js";
import StdCfgAreaProfile from "./components/StdCfgAreaProfile.vue";
import StdCfgAreaStructure from "./components/StdCfgAreaStructure.vue";
import StdCfgAreaGeneric from "./components/StdCfgAreaGeneric.vue";

const AREA_TITLES = {
	"PCFG-01": __("Source and Profile"),
	"PCFG-02": __("Coverage and Document Structure"),
};

const { route } = useRouteState("std-cfg-area");
const draftId = computed(() => route.value[1]);
const areaCode = computed(() => route.value[2]);
const areaTitle = computed(() => AREA_TITLES[areaCode.value] || (AREA_REGISTRY[areaCode.value] && AREA_REGISTRY[areaCode.value].title) || areaCode.value);

const railEl = ref(null);
const draft = ref(null);
const loading = ref(true);

async function refresh() {
	loading.value = true;
	draft.value = await frappe.db.get_doc("STD Cfg Draft", draftId.value);
	loading.value = false;
}
watch(draftId, refresh);
onMounted(refresh);

const railTrail = computed(() => [
	{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
	{ label: __("Standard Tender Documents"), route: ["std-cfg-documents"] },
	{ label: draft.value ? draft.value.package_id : "", route: draft.value ? ["std-cfg-package-home", draft.value.package_id] : [] },
	{ label: areaTitle.value },
]);
usePageRail(railEl, railTrail);

function backToPackage() {
	frappe.set_route("std-cfg-package-home", draft.value.package_id);
}
</script>

<template>
	<div class="kt-industry">
		<div ref="railEl" class="kt-rail-mount"></div>
		<div class="kt-shell">
			<template v-if="!loading && draft">
				<header>
					<h1 style="font-size: 28px">{{ areaTitle }}</h1>
					<p class="kt-muted" style="margin: 4px 0 0">
						{{ __("Draft Version") }} {{ draft.proposed_version_number }}
					</p>
				</header>

				<StdCfgAreaProfile v-if="areaCode === 'PCFG-01'" :draft-id="draftId" :package-id="draft.package_id" />
				<StdCfgAreaStructure v-else-if="areaCode === 'PCFG-02'" :draft-id="draftId" :package-id="draft.package_id" />
				<StdCfgAreaGeneric v-else-if="AREA_REGISTRY[areaCode]" :draft-id="draftId" :area-code="areaCode" />
				<div v-else class="kt-card kt-empty">
					<h2>{{ __("Unknown configuration area.") }}</h2>
				</div>

				<div style="display: flex; justify-content: flex-start; margin-top: 8px">
					<button type="button" class="kt-btn kt-btn-ghost" @click="backToPackage">{{ __("Back to package") }}</button>
				</div>
			</template>
			<div v-else class="kt-card kt-blueprint">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div v-for="i in 3" :key="i" class="kt-skel" style="height: 16px; margin-bottom: 10px"></div>
			</div>
		</div>
	</div>
</template>
