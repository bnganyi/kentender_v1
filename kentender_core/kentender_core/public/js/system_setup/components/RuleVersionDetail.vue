<script setup>
// C03-detail — one referenced rule Version, read-only: a method eligibility
// profile or a regulator reference ("Reservation rules"). "Create new
// version" is the only write (never edit-in-place); the new-version dialog
// copies the current rule values for correction (§11.6).
import { computed, onMounted, ref } from "vue";
import NewVersionDialog from "./NewVersionDialog.vue";
import { procurementSettingsApi } from "../data/procurementSettingsApi.js";
import { dash, fmtDate } from "../data/format.js";

const props = defineProps({
	name: { type: String, required: true },
	kind: { type: String, default: "method" }, // "method" | "reference"
	verificationStatuses: { type: Array, default: () => [] },
});
const emit = defineEmits(["back", "registered"]);

const loading = ref(true);
const loadError = ref("");
const rule = ref(null);
const dialogOpen = ref(false);

async function load() {
	loading.value = true;
	loadError.value = "";
	try {
		rule.value =
			props.kind === "reference"
				? await procurementSettingsApi.getRegulatoryReferenceVersion(props.name)
				: await procurementSettingsApi.getMethodProfile(props.name);
	} catch (error) {
		loadError.value = error.message;
	} finally {
		loading.value = false;
	}
}
onMounted(load);

const referenceSet = computed(() =>
	props.kind === "reference" ? __("Reservation rules") : `${__("Method eligibility")} — ${rule.value?.procurement_method || ""}`
);
const versionNumber = computed(() =>
	props.kind === "reference" ? (props.name.split("-").pop() || "").replace(/^0+/, "") || "1" : rule.value?.version_number
);
const title = computed(() => `${referenceSet.value} — ${__("Version {0}", [versionNumber.value])}`);
const verification = computed(() => rule.value?.verification_status || "Production verification pending");
const verificationShort = computed(() =>
	verification.value === "Verified" ? __("Verified") : verification.value.startsWith("Fixture") ? __("Fixture-verified") : __("Pending")
);
const conditions = computed(() => rule.value?.conditions || []);
// C04-eligibility-reminder — an eligibility profile whose conditions are
// not verified cannot be reported complete.
const conditionsComplete = computed(() => props.kind === "method" && conditions.value.length > 0 && verification.value !== "Production verification pending");
const applicabilityBasis = computed(() =>
	rule.value?.applicability_basis || (props.kind === "reference" ? __("Fiscal Year") : __("Category / value / circumstance"))
);
</script>

<template>
	<div class="kt-procset-view" data-testid="kt-procset-rule">
		<div class="kt-section-head">
			<div>
				<span class="kt-eyebrow">{{ __("Procurement settings") }}</span>
				<h2 class="kt-section-title" data-testid="kt-procset-rule-title">{{ loading ? __("Loading…") : title }}</h2>
			</div>
			<button type="button" class="kt-btn kt-btn-ghost" data-testid="kt-procset-rule-back" @click="emit('back')">← {{ __("Procurement settings") }}</button>
		</div>

		<div v-if="loading" class="kt-card kt-blueprint" data-testid="kt-procset-rule-loading">
			<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
			<div class="kt-skel" style="width:70%" /><div class="kt-skel" style="width:50%" />
		</div>
		<div v-else-if="loadError" class="kt-card kt-blueprint kt-empty" data-testid="kt-procset-rule-error">
			<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
			<h2>{{ __("This record isn't available to you") }}</h2>
			<p>{{ __("It may not exist, or you may not have access to it.") }}</p>
			<button type="button" class="kt-btn kt-btn-secondary" @click="emit('back')">{{ __("Back to Procurement settings") }}</button>
		</div>

		<template v-else>
			<div class="kt-card kt-blueprint kt-procset-wide" data-testid="kt-procset-rule-card">
				<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
				<div class="kt-facts-row">
					<div class="kt-fact"><span class="kt-label">{{ __("Reference set") }}</span><span class="kt-fact-val">{{ referenceSet }}</span></div>
					<div class="kt-fact"><span class="kt-label">{{ __("Version") }}</span><span class="kt-fact-val">{{ versionNumber }}</span></div>
					<div class="kt-fact"><span class="kt-label">{{ __("Applicability basis") }}</span><span class="kt-fact-val">{{ applicabilityBasis }}</span></div>
				</div>
				<div class="kt-facts-row">
					<div class="kt-fact"><span class="kt-label">{{ __("Effective from") }}</span><span class="kt-fact-val">{{ fmtDate(rule.effective_from) }}</span></div>
					<div class="kt-fact"><span class="kt-label">{{ __("Effective until") }}</span><span class="kt-fact-val">{{ fmtDate(rule.effective_until) }}</span></div>
				</div>
				<div class="kt-fact"><span class="kt-label">{{ __("Source instrument") }}</span><span class="kt-fact-val">{{ dash(rule.source_instrument) }}</span></div>
				<div class="kt-facts-row">
					<div class="kt-fact"><span class="kt-label">{{ __("Provision") }}</span><span class="kt-fact-val">{{ dash(rule.provision) }}</span></div>
					<div class="kt-fact"><span class="kt-label">{{ __("Source document") }}</span><span class="kt-fact-val"><a v-if="rule.source_document" :href="rule.source_document" target="_blank" rel="noopener">{{ __("View document") }}</a><template v-else>{{ __("Not attached") }}</template></span></div>
					<div class="kt-fact"><span class="kt-label">{{ __("Verification status") }}</span><span :class="verification === 'Verified' ? 'kt-status is-live' : 'kt-status is-attention'" data-testid="kt-procset-rule-verification">{{ verificationShort }}</span></div>
				</div>
			</div>

			<!-- Rule values -->
			<div v-if="kind === 'method'" class="kt-card kt-blueprint kt-table-card kt-procset-wide" data-testid="kt-procset-rule-values">
				<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
				<h3 class="kt-card-title">{{ __("Rule values") }}</h3>
				<span v-if="!conditionsComplete" class="kt-status is-attention" data-testid="kt-procset-rule-incomplete">{{ __("Required conditions not yet completed") }}</span>
				<table class="kt-table">
					<thead><tr><th>{{ __("Condition") }}</th><th>{{ __("Kind") }}</th><th>{{ __("Category") }}</th><th>{{ __("Limit") }}</th><th>{{ __("Evidence") }}</th><th>{{ __("Authorisation") }}</th></tr></thead>
					<tbody>
						<tr v-for="row in conditions" :key="row.condition_id">
							<td>{{ row.description }}</td>
							<td>{{ row.kind }}</td>
							<td>{{ row.procurement_category || __("All") }}</td>
							<td>{{ row.maximum_amount ? __("KES {0}", [Number(row.maximum_amount).toLocaleString("en-KE")]) : __("No fixed maximum") }}<span v-if="row.cumulative_basis && row.cumulative_basis !== 'None'" class="kt-muted"> · {{ row.cumulative_basis }}</span></td>
							<td>{{ dash(row.required_evidence) }}</td>
							<td>{{ row.authorisation_actor ? row.authorisation_actor + ' · ' + row.authorisation_stage : "—" }}</td>
						</tr>
					</tbody>
				</table>
			</div>
			<div v-else class="kt-card kt-blueprint kt-table-card kt-procset-wide" data-testid="kt-procset-rule-values">
				<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
				<h3 class="kt-card-title">{{ __("Rule values") }}</h3>
				<div class="kt-facts-row">
					<div class="kt-fact"><span class="kt-label">{{ __("Reservation target") }}</span><span class="kt-fact-val">{{ rule.reservation.published ? rule.reservation.target_percent + '%' : __("Not published") }}</span></div>
					<div class="kt-fact"><span class="kt-label">{{ __("County resident-tenderer minimum") }}</span><span class="kt-fact-val">{{ rule.reservation.county_target_percent ? rule.reservation.county_target_percent + '%' : __("Not published") }}</span></div>
					<div class="kt-fact"><span class="kt-label">{{ __("Gazette reference") }}</span><span class="kt-fact-val">{{ dash(rule.gazette_reference) }}</span></div>
				</div>
				<table class="kt-table">
					<thead><tr><th>{{ __("Reservation category") }}</th><th>{{ __("Regional") }}</th><th>{{ __("Statutory reference") }}</th></tr></thead>
					<tbody>
						<tr v-for="row in rule.reservation.categories" :key="row.category">
							<td>{{ row.category }}</td><td>{{ row.is_regional ? __("Yes") : __("No") }}</td><td>{{ dash(row.statutory_reference) }}</td>
						</tr>
					</tbody>
				</table>
			</div>

			<div class="kt-procset-card-actions">
				<button v-if="kind === 'method'" type="button" class="kt-btn kt-btn-secondary" data-testid="kt-procset-rule-new-version" @click="dialogOpen = true">{{ __("Create new version") }}</button>
			</div>

			<NewVersionDialog
				v-if="dialogOpen"
				mode="method"
				:current="rule"
				:verification-statuses="verificationStatuses"
				@registered="dialogOpen = false; emit('registered')"
				@cancel="dialogOpen = false"
			/>
		</template>
	</div>
</template>
