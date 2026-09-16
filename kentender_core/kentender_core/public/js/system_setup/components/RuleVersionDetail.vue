<script setup>
// C03-detail — one referenced rule Version, read-only: a method eligibility
// profile or a regulator reference ("Reservation rules"). "Create new
// version" is the only write (never edit-in-place); the new-version dialog
// copies the current rule values for correction (§11.6).
import { computed, onMounted, ref } from "vue";
import NewVersionDialog from "./NewVersionDialog.vue";
import { procurementSettingsApi } from "../data/procurementSettingsApi.js";
import { applicabilityBasisLabel, dash, fmtDate, sourceCheckClass, sourceCheckLabel } from "../data/format.js";

const props = defineProps({
	name: { type: String, required: true },
	kind: { type: String, default: "method" }, // "method" | "reference"
	verificationStatuses: { type: Array, default: () => [] },
});
const emit = defineEmits(["back", "registered", "new-version", "check-sources"]);

const loading = ref(true);
const loadError = ref("");
const rule = ref(null);
const dialogOpen = ref(false);
const renaming = ref(false);
const renameValue = ref("");
const renameBusy = ref(false);
const renameError = ref("");

async function saveName() {
	renameBusy.value = true;
	renameError.value = "";
	try {
		await procurementSettingsApi.renameRegulatoryReference(
			rule.value.reference_set,
			renameValue.value.trim(),
			""
		);
		renaming.value = false;
		emit("registered");
	} catch (error) {
		renameError.value = error.message;
	} finally {
		renameBusy.value = false;
	}
}

async function load() {
	loading.value = true;
	loadError.value = "";
	try {
		rule.value =
			props.kind === "reference"
				? await procurementSettingsApi.getRegulatoryReferenceVersion(props.name)
				: await procurementSettingsApi.getMethodProfile(props.name);
		renameValue.value = rule.value?.display_name || rule.value?.reference_kind || "";
	} catch (error) {
		loadError.value = error.message;
	} finally {
		loading.value = false;
	}
}
onMounted(load);

// CFG-CHG-002 v0.11 §10.6 — the version record now carries its own kind and
// number, so neither is inferred from the record id any more (version ids are
// hashes under the new envelope; the old suffix-parsing produced "1" for
// every reference version).
const referenceSet = computed(() =>
	props.kind === "reference"
		? rule.value?.reference_kind || __("Procurement rule")
		: `${__("Method eligibility")} — ${rule.value?.procurement_method || ""}`
);
const versionNumber = computed(() => rule.value?.version_number || "");
const title = computed(() => `${referenceSet.value} — ${__("Version {0}", [versionNumber.value])}`);
const verification = computed(() => rule.value?.verification_status || "Production verification pending");
const verificationShort = computed(() => __(sourceCheckLabel(verification.value)));
const conditions = computed(() => rule.value?.conditions || []);
// C04-eligibility-reminder — an eligibility profile whose conditions are
// not verified cannot be reported complete.
const conditionsComplete = computed(() => props.kind === "method" && conditions.value.length > 0 && verification.value !== "Production verification pending");
// §10.7 — the validated payload rendered as labelled facts and row tables,
// derived from the shape the server actually returned for this kind. A field
// the payload does not carry is simply absent, never invented.
function humanise(key) {
	const text = String(key).replace(/_/g, " ").trim();
	return text.charAt(0).toUpperCase() + text.slice(1);
}
function cellText(value) {
	if (value === true) return __("Yes");
	if (value === false) return __("No");
	if (Array.isArray(value)) return value.length ? value.join(", ") : "—";
	return dash(value);
}
const payloadFacts = computed(() => {
	const payload = rule.value?.payload || {};
	return Object.entries(payload)
		.filter(([, value]) => !(Array.isArray(value) && value.some((row) => row && typeof row === "object")))
		.map(([key, value]) => ({ key, label: humanise(key), value: cellText(value) }));
});
const payloadTables = computed(() => {
	const payload = rule.value?.payload || {};
	return Object.entries(payload)
		.filter(([, value]) => Array.isArray(value) && value.some((row) => row && typeof row === "object"))
		.map(([key, rows]) => {
			const columns = [];
			for (const row of rows) {
				for (const column of Object.keys(row || {})) {
					if (!columns.some((existing) => existing.key === column)) {
						columns.push({ key: column, label: humanise(column) });
					}
				}
			}
			return { key, label: humanise(key), rows, columns };
		});
});
// §10.6 — "Details" is about the rule's own content, and is deliberately
// separate from the source check: a rule can be fully written and still
// unverified, or verified in principle with its details still outstanding.
const detailsComplete = computed(() => {
	if (props.kind === "method") return conditions.value.length > 0;
	const payload = rule.value?.payload || {};
	return Object.values(payload).some((value) =>
		Array.isArray(value) ? value.length > 0 : value !== "" && value !== null && value !== undefined
	);
});

const applicabilityBasis = computed(
	() =>
		applicabilityBasisLabel(rule.value?.applicability_basis) ||
		(props.kind === "reference" ? __("Not yet established") : __("Category / value / circumstance"))
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
					<div class="kt-fact"><span class="kt-label">{{ __("Rule kind") }}</span><span class="kt-fact-val" data-testid="kt-procset-rule-kind">{{ kind === "method" ? __("Method eligibility") : dash(rule.reference_kind) }}</span></div>
					<div class="kt-fact"><span class="kt-label">{{ __("Version") }}</span><span class="kt-fact-val">{{ versionNumber }}</span></div>
					<div class="kt-fact"><span class="kt-label">{{ __("Which date determines the rule to use?") }}</span><span class="kt-fact-val">{{ applicabilityBasis }}</span></div>
				</div>
				<div class="kt-facts-row">
					<div class="kt-fact"><span class="kt-label">{{ __("Applies from") }}</span><span class="kt-fact-val">{{ fmtDate(rule.effective_from) }}</span></div>
					<div class="kt-fact"><span class="kt-label">{{ __("Applies until") }}</span><span class="kt-fact-val">{{ fmtDate(rule.effective_until) }}</span></div>
				</div>
				<div class="kt-facts-row">
					<div class="kt-fact"><span class="kt-label">{{ __("Source check") }}</span><span :class="sourceCheckClass(verification)" data-testid="kt-procset-rule-verification">{{ verificationShort }}</span></div>
					<div class="kt-fact"><span class="kt-label">{{ __("Details") }}</span><span :class="detailsComplete ? 'kt-status is-live' : 'kt-status is-pending'" data-testid="kt-procset-rule-details">{{ detailsComplete ? __("Complete") : __("Details missing") }}</span></div>
				</div>

				<div v-if="!detailsComplete || verification !== 'Verified'" class="kt-notice is-warning" data-testid="kt-procset-rule-incomplete-notice">
					<div class="kt-notice-body">{{ __("Complete the rule details and source checks before using this version.") }}</div>
				</div>

				<!-- §10.6's four supporting groups. "Rule details" is the kind's
				     own content; the rest are shared by every kind. -->
				<div class="kt-section" data-testid="kt-procset-rule-details-group">
					<h6 class="kt-card-title">{{ __("Rule details") }}</h6>
					<div class="kt-panel">
						<div v-if="kind === 'method'" class="kt-meta-row">
							<div><span class="kt-label">{{ __("Method") }}</span><span class="kt-meta-value">{{ dash(rule.procurement_method) }}</span></div>
							<div><span class="kt-label">{{ __("Currency") }}</span><span class="kt-meta-value">{{ dash(rule.applicability_currency || "KES") }}</span></div>
						</div>
						<div v-else-if="payloadFacts.length" class="kt-meta-row">
							<div v-for="fact in payloadFacts" :key="fact.key">
								<span class="kt-label">{{ fact.label }}</span>
								<span class="kt-meta-value" :data-testid="'kt-procset-rule-fact-' + fact.key">{{ fact.value }}</span>
							</div>
						</div>
						<span v-else class="kt-meta-value" data-testid="kt-procset-rule-values-empty">{{ __("Not yet established") }}</span>
					</div>
				</div>

				<div class="kt-section">
					<h6 class="kt-card-title">{{ __("When this rule applies") }}</h6>
					<div class="kt-panel">
						<div class="kt-meta-row">
							<div><span class="kt-label">{{ __("Which date determines the rule to use?") }}</span><span class="kt-meta-value">{{ applicabilityBasis || __("Not yet established") }}</span></div>
							<div><span class="kt-label">{{ __("Entity applicability") }}</span><span class="kt-meta-value">{{ (rule.applicability_entity_types || []).join(", ") || __("Not yet established") }}</span></div>
							<div><span class="kt-label">{{ __("County applicability") }}</span><span class="kt-meta-value">{{ dash(rule.applicability_county) }}</span></div>
						</div>
					</div>
				</div>

				<div class="kt-section">
					<h6 class="kt-card-title">{{ __("Sources and interpretation") }}</h6>
					<div class="kt-panel">
						<div class="kt-meta-row">
							<div><span class="kt-label">{{ __("Source instrument") }}</span><span class="kt-meta-value">{{ rule.source_instrument || __("Not yet established") }}</span></div>
							<!-- §4.6 — the edition is verification evidence, appended by a
							     source check rather than carried on the immutable version. -->
							<div><span class="kt-label">{{ __("Edition") }}</span><span class="kt-meta-value" data-testid="kt-procset-rule-edition">{{ __("Recorded with the source check") }}</span></div>
							<div><span class="kt-label">{{ __("Provisions") }}</span><span class="kt-meta-value">{{ rule.provision || __("Not yet established") }}</span></div>
							<div><span class="kt-label">{{ __("Source document") }}</span><span class="kt-meta-value"><a v-if="rule.source_document" :href="rule.source_document" target="_blank" rel="noopener">{{ __("View document") }}</a><template v-else>{{ __("Not attached") }}</template></span></div>
							<div><span class="kt-label">{{ __("Interpretation") }}</span><span class="kt-meta-value">{{ rule.interpretation || __("Not yet established") }}</span></div>
						</div>
					</div>
				</div>

				<div class="kt-section">
					<h6 class="kt-card-title">{{ __("Usage and history") }}</h6>
					<div class="kt-panel">
						<span class="kt-meta-value">{{ __("Version history and source-check history are shown with this rule's source checks.") }}</span>
					</div>
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
			<!-- CFG-CHG-002 v0.11 §10.7 — the version's own typed payload. Each
			     of the six reference kinds carries a different validated shape,
			     so scalars render as separately labelled facts and row sets as
			     their own tables; the raw JSON is never shown. -->
			<div v-else-if="payloadTables.length" class="kt-card kt-blueprint kt-table-card kt-procset-wide" data-testid="kt-procset-rule-values">
				<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
				<h3 class="kt-card-title">{{ __("Rule values") }}</h3>
				<template v-for="table in payloadTables" :key="table.key">
					<h6 class="kt-card-title" style="margin-top:16px">{{ table.label }}</h6>
					<table class="kt-table" :data-testid="'kt-procset-rule-rows-' + table.key">
						<thead><tr><th v-for="column in table.columns" :key="column.key">{{ column.label }}</th></tr></thead>
						<tbody>
							<tr v-for="(row, index) in table.rows" :key="index">
								<td v-for="column in table.columns" :key="column.key">{{ cellText(row[column.key]) }}</td>
							</tr>
						</tbody>
					</table>
				</template>
			</div>

			<!-- §10.6 saved-detail actions. A reference rule's new version and
			     its source check are full screens (the form is far too large
			     for a dialog); a method profile keeps its existing dialog. -->
			<div class="kt-procset-card-actions">
				<button v-if="kind === 'method'" type="button" class="kt-btn kt-btn-secondary" data-testid="kt-procset-rule-new-version" @click="dialogOpen = true">{{ __("Create new version") }}</button>
				<template v-else>
					<button type="button" class="kt-btn kt-btn-secondary" data-testid="kt-procset-rule-new-version" @click="emit('new-version')">{{ __("Create new version") }}</button>
					<button type="button" class="kt-btn kt-btn-secondary" data-testid="kt-procset-rule-check-sources" @click="emit('check-sources')">{{ __("Check sources") }}</button>
					<button type="button" class="kt-btn kt-btn-ghost" data-testid="kt-procset-rule-usage" @click="emit('check-sources')">{{ __("View usage and history") }}</button>
					<button type="button" class="kt-btn kt-btn-ghost" data-testid="kt-procset-rule-rename" @click="renaming = true">{{ __("Edit rule name") }}</button>
				</template>
			</div>

			<!-- §10.6 — identifier and kind are separately labelled read-only
			     facts on the saved detail, for a method profile as much as for a
			     reference rule. -->
			<div class="kt-meta-row" style="margin-top:16px">
				<div><span class="kt-label">{{ __("Rule identifier") }}</span><span class="kt-meta-value" data-testid="kt-procset-rule-identifier">{{ dash(rule.reference_key || rule.profile || name) }}</span></div>
			</div>

			<!-- C03-B "rename" — the display name only. -->
			<div v-if="renaming" class="kt-dialog-backdrop" @click.self="renaming = false">
				<div class="kt-dialog kt-blueprint kt-narrow" role="dialog" aria-modal="true" :aria-label="__('Edit rule name')" data-testid="kt-procset-rule-rename-dialog" @keydown.esc="renaming = false">
					<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
					<h2 class="kt-dialog-title">{{ __("Edit rule name") }}</h2>
					<div class="kt-dialog-fields">
						<div class="kt-field">
							<label for="kt-rule-rename">{{ __("Rule name") }}</label>
							<input id="kt-rule-rename" v-model="renameValue" class="kt-input" data-testid="kt-procset-rule-rename-input">
						</div>
						<p v-if="renameError" class="kt-inline-error" role="alert" data-testid="kt-procset-rule-rename-error">{{ renameError }}</p>
					</div>
					<div class="kt-dialog-actions">
						<button type="button" class="kt-btn kt-btn-secondary" :disabled="renameBusy" @click="renaming = false">{{ __("Cancel") }}</button>
						<button type="button" class="kt-btn kt-btn-primary" :disabled="renameBusy || !renameValue.trim()" data-testid="kt-procset-rule-rename-save" @click="saveName">{{ __("Save changes") }}</button>
					</div>
				</div>
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
