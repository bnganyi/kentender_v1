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

// Route: std-cfg-area/<draft|version>/<referenceName>/<areaCode>. A Draft is
// the real editing surface (save_std_* commands); a Version is read-only —
// there is no "edit an Active Version" operation, only viewing what was
// activated, since content changes go through a new Draft (§8).
const { route } = useRouteState("std-cfg-area");
const referenceKind = computed(() => route.value[1]);
const referenceName = computed(() => route.value[2]);
const areaCode = computed(() => route.value[3]);
const referenceDoctype = computed(() => (referenceKind.value === "version" ? "STD Cfg Version" : "STD Cfg Draft"));
const readOnly = computed(() => referenceKind.value === "version");
const areaTitle = computed(() => AREA_TITLES[areaCode.value] || (AREA_REGISTRY[areaCode.value] && AREA_REGISTRY[areaCode.value].title) || areaCode.value);

const railEl = ref(null);
const reference = ref(null);
const loading = ref(true);
const error = ref(null);

async function refresh() {
	loading.value = true;
	error.value = null;
	try {
		reference.value = await frappe.db.get_doc(referenceDoctype.value, referenceName.value);
	} catch (e) {
		error.value = e;
	} finally {
		loading.value = false;
	}
}
watch([referenceDoctype, referenceName], refresh);
onMounted(refresh);

const railTrail = computed(() => [
	{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
	{ label: __("Standard Tender Documents"), route: ["std-cfg-documents"] },
	{ label: reference.value ? reference.value.package_id : "", route: reference.value ? ["std-cfg-package-home", reference.value.package_id] : [] },
	{ label: areaTitle.value },
]);
usePageRail(railEl, railTrail);

function backToPackage() {
	frappe.set_route("std-cfg-package-home", reference.value.package_id);
}
</script>

<template>
	<div class="kt-industry">
		<div ref="railEl" class="kt-rail-mount"></div>
		<div class="kt-shell" style="padding-bottom: 88px">
			<div v-if="error" class="kt-card kt-empty">
				<h2>{{ __("Could not load this configuration area.") }}</h2>
				<p>{{ error.message }}</p>
			</div>
			<template v-else-if="!loading && reference">
				<header style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 20px">
					<h1 style="font-size: 28px; margin: 0">{{ areaTitle }}</h1>
					<div>
						<span class="kt-muted" style="font-size: 13px; margin-right: 10px">
							{{ readOnly ? __("Version") + " " + reference.version_number : __("Draft Version") + " " + reference.proposed_version_number }}
						</span>
						<span class="kt-status" :class="readOnly ? 'is-live' : 'is-draft'">{{ readOnly ? __("Read only") : reference.state }}</span>
					</div>
				</header>

				<StdCfgAreaProfile v-if="areaCode === 'PCFG-01'" :reference-doctype="referenceDoctype" :reference-name="referenceName" :package-id="reference.package_id" :read-only="readOnly" />
				<StdCfgAreaStructure v-else-if="areaCode === 'PCFG-02'" :reference-doctype="referenceDoctype" :reference-name="referenceName" :package-id="reference.package_id" :read-only="readOnly" />
				<StdCfgAreaGeneric v-else-if="AREA_REGISTRY[areaCode]" :reference-doctype="referenceDoctype" :reference-name="referenceName" :area-code="areaCode" :read-only="readOnly" />
				<div v-else class="kt-card kt-empty">
					<h2>{{ __("Unknown configuration area.") }}</h2>
				</div>

				<div class="kt-sticky-footer" style="justify-content: flex-start">
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
