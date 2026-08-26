<script setup>
// STD-UI-01 Package home (§15.5) + STD-UI-M01 Create new package version
// (§15.4). Handles both real system states: an in-progress Draft (the
// artboard's own scenario) and Active-only with no Draft (the golden seed's
// actual current state) — the artboard only draws the former, but the M01
// modal's own purpose IS the transition out of the latter, so both states
// are real and both must render honestly rather than only matching the
// static mockup's one scenario.
import { ref, reactive, computed, onMounted } from "vue";
import { useRouteState } from "../std_configuration_shared/composables/useRouteState.js";
import { usePageRail } from "../std_configuration_shared/composables/usePageRail.js";
import CreateVersionModal from "./components/CreateVersionModal.vue";
import DraftAssistanceModal from "./components/DraftAssistanceModal.vue";
import ProposalDrawer from "./components/ProposalDrawer.vue";

const { route } = useRouteState("std-cfg-package-home");
const packageId = computed(() => route.value[1]);

const railEl = ref(null);

const PCFG_AREAS = [
	{ code: "PCFG-01", title: __("Source and Profile"), purpose: __("Official package identity and source") },
	{ code: "PCFG-02", title: __("Coverage and Document Structure"), purpose: __("Sixteen coverage areas, required sections and ordered content") },
	{ code: "PCFG-03", title: __("Tender Parameters"), purpose: __("Configurable and system-derived tender values") },
	{ code: "PCFG-04", title: __("IT Requirements"), purpose: __("Requirement composer and downstream response structure") },
	{ code: "PCFG-05", title: __("Schedule, Inventory and Background"), purpose: __("Delivery structure and bidder-relevant context") },
	{ code: "PCFG-06", title: __("Price Schedules"), purpose: __("Four bidder price-table structures") },
	{ code: "PCFG-07", title: __("Evaluation and Qualification"), purpose: __("Four evaluation stages and permitted criteria") },
	{ code: "PCFG-08", title: __("Forms and Evidence"), purpose: __("Eighteen field-level bidder forms") },
	{ code: "PCFG-09", title: __("Contract and Outputs"), purpose: __("SCC values, forms and downstream mappings") },
];

const loading = ref(true);
const error = ref(null);
const pkg = ref(null);
const draft = ref(null);
const activeVersion = ref(null);
const readiness = ref(null);
const areaStatus = reactive({});
const activeAreaStatus = reactive({});
const runtimeManifests = ref([]);

const railTrail = computed(() => [
	{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
	{ label: __("Standard Tender Documents"), route: ["std-cfg-documents"] },
	{ label: pkg.value ? pkg.value.package_code : "" },
]);
usePageRail(railEl, railTrail);

async function refresh() {
	loading.value = true;
	error.value = null;
	try {
		pkg.value = await frappe.xcall(
			"kentender_procurement.std_configuration.api.std_configuration_api.get_std_package_home",
			{ package_id: packageId.value }
		);
		draft.value = null;
		activeVersion.value = null;
		readiness.value = null;

		if (pkg.value.current_draft_id) {
			draft.value = await frappe.db.get_doc("STD Cfg Draft", pkg.value.current_draft_id);
			readiness.value = await frappe.xcall(
				"kentender_procurement.std_configuration.api.std_configuration_api.get_std_readiness_report",
				{ reference_doctype: "STD Cfg Draft", reference_name: draft.value.name }
			);
			areaStatus["PCFG-01"] = draft.value.official_issue_label && draft.value.official_source_file_id ? "Complete" : "Incomplete";
			await Promise.all(
				PCFG_AREAS.filter((a) => a.code !== "PCFG-01").map(async (a) => {
					const res = await frappe.xcall(
						"kentender_procurement.std_configuration.api.std_configuration_api.get_std_configuration_area",
						{ reference_doctype: "STD Cfg Draft", reference_name: draft.value.name, area: a.code }
					);
					const hasItems = Object.values(res.items).some((rows) => rows.length > 0);
					areaStatus[a.code] = hasItems ? "Complete" : "Not started";
				})
			);
		} else if (pkg.value.current_active_version_id) {
			activeVersion.value = await frappe.db.get_doc("STD Cfg Version", pkg.value.current_active_version_id);
			Object.keys(activeAreaStatus).forEach((k) => delete activeAreaStatus[k]);
			await Promise.all(
				PCFG_AREAS.map(async (a) => {
					if (a.code === "PCFG-01") {
						activeAreaStatus[a.code] = activeVersion.value.official_issue_label && activeVersion.value.official_source_file_id ? "Complete" : "Incomplete";
						return;
					}
					const res = await frappe.xcall(
						"kentender_procurement.std_configuration.api.std_configuration_api.get_std_configuration_area",
						{ reference_doctype: "STD Cfg Version", reference_name: activeVersion.value.name, area: a.code }
					);
					const hasItems = Object.values(res.items).some((rows) => rows.length > 0);
					activeAreaStatus[a.code] = hasItems ? "Complete" : "Not started";
				})
			);
			runtimeManifests.value = await frappe.db.get_list("STD Cfg Tender Manifest", {
				filters: { std_version_id: activeVersion.value.name },
				fields: ["name", "manifest_type"],
				limit: 20,
			});
		}
	} catch (e) {
		error.value = e;
	} finally {
		loading.value = false;
	}
}
onMounted(refresh);

function openArea(area) {
	frappe.set_route("std-cfg-area", draft.value.name, area.code);
}

// --- STD-UI-M01 ---
const modalOpen = ref(false);
const modalSaving = ref(false);
const modalError = ref("");

function openCreateVersionModal() {
	modalError.value = "";
	modalOpen.value = true;
}

async function submitCreateVersion(payload) {
	modalSaving.value = true;
	modalError.value = "";
	try {
		// official_source_file_id links to STD Cfg Source Document, not a raw
		// File — create_next_std_draft can't wrap the picked File until the
		// Draft it belongs to actually exists, so the Draft is created first
		// (without a source), then the source is attached via PCFG-01's own
		// save_std_source_document/save_std_source_and_profile commands.
		const created = await frappe.xcall(
			"kentender_procurement.std_configuration.api.std_configuration_api.create_next_std_draft",
			{ package_id: packageId.value, official_issue_label: payload.official_issue_label }
		);
		if (payload.official_source_file_id) {
			const sourceDoc = await frappe.xcall(
				"kentender_procurement.std_configuration.api.std_configuration_api.save_std_source_document",
				{
					draft_name: created.draft_id,
					file_id: payload.official_source_file_id,
					official_title: pkg.value.official_title,
					official_issue_label: payload.official_issue_label,
				}
			);
			await frappe.xcall(
				"kentender_procurement.std_configuration.api.std_configuration_api.save_std_source_and_profile",
				{ draft_name: created.draft_id, official_source_file_id: sourceDoc.source_document_id }
			);
		}
		modalOpen.value = false;
		frappe.show_alert({ message: __("Draft version created"), indicator: "green" });
		await refresh();
	} catch (e) {
		modalError.value = (e && e.message) || __("Could not create the draft version.");
	} finally {
		modalSaving.value = false;
	}
}

// --- STD-WF footer actions ---
const checking = ref(false);
async function runCompleteCheck() {
	checking.value = true;
	try {
		await frappe.xcall(
			"kentender_procurement.std_configuration.api.std_configuration_api.run_std_complete_check",
			{ draft_name: draft.value.name }
		);
		frappe.show_alert({ message: __("Complete check finished"), indicator: "blue" });
		await refresh();
	} finally {
		checking.value = false;
	}
}

const submitting = ref(false);
async function submitForReview() {
	submitting.value = true;
	try {
		const reviewers = await frappe.xcall(
			"kentender_procurement.std_configuration.api.std_configuration_api.list_std_reviewers"
		);
		if (!reviewers.length) {
			frappe.show_alert({ message: __("No STD Reviewer is available."), indicator: "red" });
			return;
		}
		await frappe.xcall(
			"kentender_procurement.std_configuration.api.std_configuration_api.submit_std_for_review",
			{ draft_name: draft.value.name, reviewer: reviewers[0].name, expected_record_version: draft.value.record_version }
		);
		frappe.show_alert({ message: __("Submitted for review"), indicator: "green" });
		await refresh();
	} finally {
		submitting.value = false;
	}
}

function openReadiness() {
	frappe.set_route("std-cfg-readiness", draft.value.name);
}
function openPreview() {
	frappe.show_alert({ message: __("Complete preview is not available yet."), indicator: "orange" });
}
// --- STD-UI-M02 ---
const assistanceModalOpen = ref(false);
const assistanceSaving = ref(false);
const assistanceError = ref("");
const drawerOpen = ref(false);
const drawerBatchIds = ref([]);

function openDraftAssistance() {
	assistanceError.value = "";
	assistanceModalOpen.value = true;
}

async function confirmDraftAssistance() {
	assistanceSaving.value = true;
	assistanceError.value = "";
	try {
		const result = await frappe.xcall(
			"kentender_procurement.std_configuration.api.std_configuration_api.run_std_reuse_transformation",
			{ draft_name: draft.value.name }
		);
		drawerBatchIds.value = result.register.map((r) => r.assistance_batch_id).filter(Boolean);
		assistanceModalOpen.value = false;
		if (!drawerBatchIds.value.length) {
			frappe.show_alert({ message: __("No proposals were produced."), indicator: "orange" });
			return;
		}
		drawerOpen.value = true;
	} catch (e) {
		assistanceError.value = (e && e.message) || __("Could not prepare proposals.");
	} finally {
		assistanceSaving.value = false;
	}
}

async function closeDrawer() {
	drawerOpen.value = false;
	await refresh();
}
</script>

<template>
	<div class="kt-industry">
		<div ref="railEl" class="kt-rail-mount"></div>
		<div class="kt-shell">
			<div v-if="error" class="kt-card kt-empty">
				<h2>{{ __("Could not load this package.") }}</h2>
				<p>{{ error.message }}</p>
			</div>

			<template v-else-if="loading">
				<div class="kt-card kt-blueprint">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<div v-for="i in 4" :key="i" class="kt-skel" style="height: 16px; margin-bottom: 10px"></div>
				</div>
			</template>

			<template v-else-if="draft">
				<header style="display: flex; justify-content: space-between; align-items: flex-end; gap: 16px">
					<div>
						<div class="kt-eyebrow">{{ __("Standard Tender Document") }}</div>
						<h1 style="font-size: 32px">{{ pkg.official_title }}</h1>
						<p class="kt-muted" style="margin: 4px 0 0">
							{{ pkg.package_code }} · {{ __("Proposed Version") }} {{ draft.proposed_version_number }}
							<span class="kt-status is-draft" style="margin-left: 8px">{{ draft.state }}</span>
						</p>
					</div>
					<button type="button" class="kt-btn kt-btn-secondary" @click="openDraftAssistance">
						{{ __("Draft assistance") }}
					</button>
				</header>

				<div class="kt-card" style="padding: 16px">
					<table class="kt-table" style="border: none">
						<tbody>
							<tr>
								<td class="kt-muted">{{ __("Official title") }}</td>
								<td>{{ pkg.official_title }}</td>
							</tr>
							<tr>
								<td class="kt-muted">{{ __("Official issue") }}</td>
								<td>{{ draft.official_issue_label || "—" }}</td>
							</tr>
							<tr>
								<td class="kt-muted">{{ __("Official source") }}</td>
								<td>{{ draft.official_source_file_id || "—" }}</td>
							</tr>
						</tbody>
					</table>
				</div>

				<table class="kt-table">
					<thead>
						<tr>
							<th>{{ __("Area") }}</th>
							<th>{{ __("Exact purpose") }}</th>
							<th>{{ __("Status") }}</th>
							<th></th>
						</tr>
					</thead>
					<tbody>
						<tr v-for="a in PCFG_AREAS" :key="a.code">
							<td>{{ a.title }}</td>
							<td class="kt-muted">{{ a.purpose }}</td>
							<td>
								<span class="kt-status" :class="areaStatus[a.code] === 'Complete' ? 'is-live' : 'is-pending'">
									{{ areaStatus[a.code] || __("Not started") }}
								</span>
							</td>
							<td><a href="#" @click.prevent="openArea(a)">{{ __("Review") }}</a></td>
						</tr>
					</tbody>
				</table>

				<div v-if="readiness" class="kt-card" style="padding: 16px">
					<table class="kt-table" style="border: none">
						<tbody>
							<tr>
								<td class="kt-muted">{{ __("Coverage") }}</td>
								<td>{{ readiness.coverage_pass_count }} {{ __("of") }} {{ readiness.coverage.length }} {{ __("areas complete") }}</td>
								<td><a href="#" @click.prevent="openReadiness">{{ __("View report") }}</a></td>
							</tr>
							<tr>
								<td class="kt-muted">{{ __("Blocking findings") }}</td>
								<td>{{ readiness.blocking_count }}</td>
								<td><a href="#" @click.prevent="openReadiness">{{ __("View readiness") }}</a></td>
							</tr>
							<tr>
								<td class="kt-muted">{{ __("Warnings") }}</td>
								<td>{{ readiness.warning_count }}</td>
								<td><a href="#" @click.prevent="openReadiness">{{ __("View readiness") }}</a></td>
							</tr>
							<tr>
								<td class="kt-muted">{{ __("Complete preview") }}</td>
								<td><span class="kt-status is-pending">{{ __("Not available yet") }}</span></td>
								<td><a href="#" @click.prevent="openPreview">{{ __("Open preview") }}</a></td>
							</tr>
						</tbody>
					</table>
				</div>

				<div style="display: flex; justify-content: flex-end; gap: 10px">
					<button type="button" class="kt-btn kt-btn-secondary" :disabled="checking" @click="runCompleteCheck">
						{{ __("Run complete check") }}
					</button>
					<button type="button" class="kt-btn kt-btn-primary" :disabled="submitting" @click="submitForReview">
						{{ __("Submit for review") }}
					</button>
				</div>
			</template>

			<template v-else>
				<header>
					<div class="kt-eyebrow">{{ __("Standard Tender Document") }}</div>
					<h1 style="font-size: 32px">{{ pkg.official_title }}</h1>
					<p class="kt-muted" style="margin: 4px 0 0" v-if="activeVersion">
						{{ pkg.package_code }} · {{ __("Version") }} {{ activeVersion.version_number }}
						<span class="kt-status is-live" style="margin-left: 8px">{{ __("Active") }}</span>
					</p>
					<p class="kt-muted" style="margin: 4px 0 0" v-else>{{ pkg.package_code }}</p>
				</header>

				<template v-if="activeVersion">
					<div class="kt-card" style="padding: 12px 16px; border-left: 3px solid #10b981">
						{{ __("Version {0} is available to Procurement Requisitions and Tender Preparation.", [activeVersion.version_number]) }}
					</div>

					<table class="kt-table">
						<thead>
							<tr>
								<th>{{ __("Area") }}</th>
								<th>{{ __("Exact purpose") }}</th>
								<th>{{ __("Status") }}</th>
								<th></th>
							</tr>
						</thead>
						<tbody>
							<tr v-for="a in PCFG_AREAS" :key="a.code">
								<td>{{ a.title }}</td>
								<td class="kt-muted">{{ a.purpose }}</td>
								<td>
									<span class="kt-status" :class="activeAreaStatus[a.code] === 'Complete' ? 'is-live' : 'is-pending'">
										{{ activeAreaStatus[a.code] || __("Not started") }}
									</span>
								</td>
								<td>—</td>
							</tr>
						</tbody>
					</table>

					<div class="kt-card" style="padding: 16px">
						<h2 style="font-size: 16px; margin: 0 0 10px">{{ __("Runtime Outputs") }}</h2>
						<table class="kt-table" style="border: none">
							<thead>
								<tr><th>{{ __("Output") }}</th><th>{{ __("Status") }}</th><th></th></tr>
							</thead>
							<tbody>
								<tr v-for="m in runtimeManifests" :key="m.name">
									<td>{{ m.manifest_type }}</td>
									<td><span class="kt-status is-live">{{ __("Available") }}</span></td>
									<td><a href="#" @click.prevent="openPreview">{{ __("Preview") }}</a></td>
								</tr>
								<tr v-if="!runtimeManifests.length"><td colspan="3" class="kt-muted">{{ __("No runtime outputs generated yet.") }}</td></tr>
							</tbody>
						</table>
					</div>

					<div style="display: flex; justify-content: flex-end; gap: 10px">
						<button type="button" class="kt-btn kt-btn-secondary" @click="openPreview">
							{{ __("Open complete preview") }}
						</button>
						<button type="button" class="kt-btn kt-btn-primary" @click="openCreateVersionModal">
							{{ __("Create new version") }}
						</button>
					</div>
				</template>
				<div v-else style="display: flex; justify-content: flex-end">
					<button type="button" class="kt-btn kt-btn-primary" @click="openCreateVersionModal">
						{{ __("Create new package version") }}
					</button>
				</div>
			</template>
		</div>

		<CreateVersionModal
			:open="modalOpen"
			:based-on-label="activeVersion ? `Version ${activeVersion.version_number} · ${activeVersion.official_issue_label}` : ''"
			:saving="modalSaving"
			:error="modalError"
			@confirm="submitCreateVersion"
			@cancel="modalOpen = false"
		/>

		<DraftAssistanceModal
			:open="assistanceModalOpen"
			:saving="assistanceSaving"
			:error="assistanceError"
			@confirm="confirmDraftAssistance"
			@cancel="assistanceModalOpen = false"
		/>
		<ProposalDrawer
			:open="drawerOpen"
			source-name="Prior configuration"
			:batch-ids="drawerBatchIds"
			@close="closeDrawer"
		/>
	</div>
</template>
