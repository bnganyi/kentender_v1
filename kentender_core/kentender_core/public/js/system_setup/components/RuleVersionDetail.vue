<script setup>
// CFG-CHG-002 v0.14 §10.6 (C03BC #detail; tracker CFG14-5D) — one saved rule
// version, read-only, ported from the board: the heading, the six facts in
// one row, the one visible issue, the four supporting groups, the actions
// and the identifier. "Source check" and "Details" are separate statuses,
// both from the server. Kept beyond the board, each a recorded decision:
// "Edit rule" for a version nothing uses yet (D15), "Mark as valid" on a
// method rule (owner, 23 Sep 2026, D20) and the method rule's conditions,
// which are what the rule says.
import { computed, onMounted, ref } from "vue";
import RuleRenameDialog from "./RuleRenameDialog.vue";
import { procurementSettingsApi } from "../data/procurementSettingsApi.js";
import { applicabilityBasisLabel, dash, fmtDate, sourceCheckClass, sourceCheckLabel } from "../data/format.js";

const props = defineProps({
	name: { type: String, required: true },
	kind: { type: String, default: "method" }, // "method" | "reference"
	verificationStatuses: { type: Array, default: () => [] },
});
const emit = defineEmits(["back", "registered", "renamed", "new-version", "edit-rule", "check-sources"]);

const loading = ref(true);
const loadError = ref("");
const rule = ref(null);
const renaming = ref(false);

const validityBusy = ref(false);
const validityError = ref("");

async function setValidity(valid) {
	validityBusy.value = true;
	validityError.value = "";
	try {
		await procurementSettingsApi.setVersionValidity({
			doctype: "Procurement Method Profile",
			name: props.name,
			valid,
		});
		await load();
	} catch (error) {
		validityError.value = error.message;
	} finally {
		validityBusy.value = false;
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
const versionNumber = computed(() => rule.value?.version_number || "");
const verification = computed(() => rule.value?.verification_status || "Production verification pending");
const verificationShort = computed(() => __(sourceCheckLabel(verification.value)));
const conditions = computed(() => rule.value?.conditions || []);
// Whether an administrator has said this version is valid. The one fact that
// governs whether a plan using it can be submitted, stated once.
const valid = computed(() => !!rule.value?.valid || verification.value === "Verified");
const canSetValidity = computed(() => !!rule.value?.can_set_validity);
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
// §10.6 — "Details" is the rule's own content, separate from the source
// check; which details are missing is the server's answer.
const detailsMissing = computed(() => rule.value?.details_missing || []);
const detailsComplete = computed(() => !detailsMissing.value.length);
// §10.6's one visible issue. Under the owner's 23 Sep wording (D20) a method
// rule that is complete but not marked valid says exactly that.
const issue = computed(() => {
	if (detailsComplete.value && valid.value) return "";
	if (props.kind === "method" && detailsComplete.value) return __("This rule is not marked valid, so a plan using it cannot be submitted.");
	return __("Complete the rule details and source checks before using this version.");
});
const hasValues = computed(() => (props.kind === "method" ? conditions.value.length > 0 : payloadTables.value.length > 0));
const issueText = computed(() =>
	detailsMissing.value.length ? `${issue.value} ${__("Missing: {0}.", [detailsMissing.value.join(", ")])}` : issue.value
);
const heading = computed(() =>
	props.kind === "reference"
		? rule.value?.display_name || rule.value?.reference_kind || __("Procurement rule")
		: `${__("Method eligibility")} — ${rule.value?.procurement_method || ""}`
);
const categories = computed(() => {
	const found = [...new Set(conditions.value.map((row) => row.procurement_category).filter(Boolean))];
	return found.length ? found.join(", ") : __("All categories");
});

const applicabilityBasis = computed(
	() =>
		applicabilityBasisLabel(rule.value?.applicability_basis) ||
		(props.kind === "reference" ? __("Not yet established") : __("Category / value / circumstance"))
);
</script>

<template>
	<div class="kt-procset-rule" data-testid="kt-procset-rule">
		<div v-if="loading" data-testid="kt-procset-rule-loading">
			<div class="kt-skel" style="width:40%" /><div class="kt-skel" style="width:70%" /><div class="kt-skel" style="width:55%" />
		</div>
		<div v-else-if="loadError" class="kt-notice is-critical" role="alert" data-testid="kt-procset-rule-error">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12" /></svg>
			<div class="kt-notice-body"><strong>{{ __("This record isn't available to you.") }}</strong> {{ __("It may not exist, or you may not have access to it.") }}</div>
		</div>

		<div v-else data-testid="kt-procset-rule-card">
			<h3 style="margin-bottom:4px" data-testid="kt-procset-rule-title">{{ heading }}</h3>
			<div class="kt-meta-row" style="margin-bottom:12px">
				<div><span class="kt-label">{{ __("Rule kind") }}</span><span class="kt-meta-value" data-testid="kt-procset-rule-kind">{{ kind === "method" ? __("Method eligibility") : dash(rule.reference_kind) }}</span></div>
				<div><span class="kt-label">{{ __("Version") }}</span><span class="kt-meta-value" data-testid="kt-procset-rule-version">{{ versionNumber }}</span></div>
				<div><span class="kt-label">{{ __("Applies from") }}</span><span class="kt-meta-value">{{ fmtDate(rule.effective_from) }}</span></div>
				<div><span class="kt-label">{{ __("Applies until") }}</span><span class="kt-meta-value">{{ fmtDate(rule.effective_until) }}</span></div>
				<div><span class="kt-label">{{ __("Source check") }}</span><span class="kt-meta-value"><span :class="sourceCheckClass(verification)" data-testid="kt-procset-rule-verification">{{ verificationShort }}</span></span></div>
				<div><span class="kt-label">{{ __("Details") }}</span><span class="kt-meta-value"><span :class="detailsComplete ? 'kt-status is-live' : 'kt-status is-pending'" data-testid="kt-procset-rule-details">{{ detailsComplete ? __("Details complete") : __("Details missing") }}</span></span></div>
			</div>
			<div v-if="issue" class="kt-notice is-warning" style="margin-bottom:16px" data-testid="kt-procset-rule-incomplete-notice">
				<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M12 3l9 16H3z" /><path d="M12 10v4M12 17h.01" /></svg>
				<div class="kt-notice-body">{{ issueText }}</div>
			</div>

			<!-- C03BC #states — a version that can no longer be corrected in place
			     says so, with the one way to change it. -->
			<div v-if="!rule.can_edit" class="kt-notice is-info" style="flex-direction:column;align-items:flex-start;margin-bottom:16px" data-testid="kt-procset-rule-readonly">
				<div style="display:flex;gap:12px;align-items:flex-start">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><rect x="5" y="11" width="14" height="10" rx="2" /><path d="M8 11V7a4 4 0 0 1 8 0v4" /></svg>
					<div class="kt-notice-body"><strong>{{ __("This version is read-only.") }}</strong> {{ __("Create a new version to change it.") }}</div>
				</div>
				<a href="#" style="margin-left:30px;font-size:13px" data-testid="kt-procset-rule-readonly-new" @click.prevent="emit('new-version')">{{ __("Create new version") }}</a>
			</div>

			<!-- With values tables the first two groups run full width: a
			     conditions table does not fit half the card. -->
			<div class="kt-procset-rule-groups" :class="{ 'has-values': hasValues }">
				<div class="kt-section" data-testid="kt-procset-rule-details-group">
					<h6 class="kt-card-title">{{ __("Rule details") }}</h6>
					<div class="kt-panel">
						<div v-if="kind === 'method'" class="kt-meta-row">
							<div><span class="kt-label">{{ __("Method") }}</span><span class="kt-meta-value">{{ dash(rule.procurement_method) }}</span></div>
							<div><span class="kt-label">{{ __("Category") }}</span><span class="kt-meta-value">{{ categories }}</span></div>
							<div><span class="kt-label">{{ __("Currency") }}</span><span class="kt-meta-value">{{ dash(rule.applicability_currency || "KES") }}</span></div>
							<!-- §4.6 — a correction is a new version, so the account of
							     why it was made belongs with the version it produced. -->
							<div><span class="kt-label">{{ __("Reason for this version") }}</span><span class="kt-meta-value" data-testid="kt-procset-rule-change-reason">{{ rule.change_reason || __("Not recorded") }}</span></div>
						</div>
						<div v-else-if="payloadFacts.length" class="kt-meta-row">
							<div v-for="fact in payloadFacts" :key="fact.key">
								<span class="kt-label">{{ fact.label }}</span>
								<span class="kt-meta-value" :data-testid="'kt-procset-rule-fact-' + fact.key">{{ fact.value }}</span>
							</div>
						</div>
						<span v-else class="kt-meta-value" data-testid="kt-procset-rule-values-empty">{{ __("Not yet established") }}</span>
						<!-- What the rule says, beyond the board's pending specimen: a
						     method rule's conditions and a reference rule's typed rows
						     (never raw JSON). See DEPARTURES. -->
						<table v-if="kind === 'method' && conditions.length" class="table" style="margin-top:12px" data-testid="kt-procset-rule-values">
							<thead><tr><th>{{ __("Condition") }}</th><th>{{ __("Kind") }}</th><th>{{ __("Category") }}</th><th>{{ __("Limit") }}</th><th>{{ __("Evidence") }}</th><th>{{ __("Authorisation") }}</th></tr></thead>
							<tbody>
								<tr v-for="row in conditions" :key="row.condition_id">
									<td>{{ row.description }}</td>
									<td>{{ row.kind }}</td>
									<td>{{ row.procurement_category || __("All") }}</td>
									<td>{{ row.maximum_amount ? __("KES {0}", [Number(row.maximum_amount).toLocaleString("en-KE")]) : __("No fixed maximum") }}<span v-if="row.cumulative_basis && row.cumulative_basis !== 'None'" class="text-muted"> · {{ row.cumulative_basis }}</span></td>
									<td>{{ dash(row.required_evidence) }}</td>
									<!-- A Known fact is checked by the system from the
									     Planner's own estimate, never by a named approver;
									     only a Declaration without an approver is a gap. -->
									<td>{{ row.authorisation_actor ? row.authorisation_actor + ' · ' + row.authorisation_stage : (row.kind === 'Known fact' ? __("Not required — evaluated automatically") : "—") }}</td>
								</tr>
							</tbody>
						</table>
						<template v-for="table in (kind === 'method' ? [] : payloadTables)" :key="table.key">
							<h6 class="kt-card-title" style="margin-top:12px">{{ table.label }}</h6>
							<table class="table" data-testid="kt-procset-rule-values" :data-key="table.key">
								<thead><tr><th v-for="column in table.columns" :key="column.key">{{ column.label }}</th></tr></thead>
								<tbody>
									<tr v-for="(row, index) in table.rows" :key="index">
										<td v-for="column in table.columns" :key="column.key">{{ cellText(row[column.key]) }}</td>
									</tr>
								</tbody>
							</table>
						</template>
					</div>
				</div>

				<div class="kt-section">
					<h6 class="kt-card-title">{{ __("When this rule applies") }}</h6>
					<div class="kt-panel">
						<!-- Method eligibility gates on category and estimated value,
						     the same for every entity: a real answer, not a gap. -->
						<div v-if="kind === 'method'" class="kt-meta-row">
							<div><span class="kt-label">{{ __("Which date determines the rule to use?") }}</span><span class="kt-meta-value">{{ applicabilityBasis || __("Not yet established") }}</span></div>
							<div><span class="kt-label">{{ __("Entity applicability") }}</span><span class="kt-meta-value">{{ __("Every entity - governed by category and estimated value, not entity type") }}</span></div>
							<div><span class="kt-label">{{ __("County applicability") }}</span><span class="kt-meta-value">{{ __("Not applicable to method eligibility") }}</span></div>
						</div>
						<!-- A blank list on a reference rule means "no restriction"
						     (as `resolve_reference` reads it), not a missing fact. -->
						<div v-else class="kt-meta-row">
							<div><span class="kt-label">{{ __("Which date determines the rule to use?") }}</span><span class="kt-meta-value">{{ applicabilityBasis || __("Not yet established") }}</span></div>
							<div><span class="kt-label">{{ __("Entity applicability") }}</span><span class="kt-meta-value">{{ (rule.applicability_entity_types || []).join(", ") || __("All entity types") }}</span></div>
							<div><span class="kt-label">{{ __("County applicability") }}</span><span class="kt-meta-value">{{ dash(rule.applicability_county) }}</span></div>
							<div><span class="kt-label">{{ __("Category applicability") }}</span><span class="kt-meta-value">{{ (rule.applicability_categories || []).join(", ") || __("All categories") }}</span></div>
						</div>
					</div>
				</div>

				<div class="kt-section" style="grid-column:1/-1">
					<h6 class="kt-card-title">{{ __("Sources and interpretation") }}</h6>
					<div class="kt-panel">
						<div class="kt-meta-row">
							<div><span class="kt-label">{{ __("Source instrument") }}</span><span class="kt-meta-value">{{ rule.source_instrument || __("Not yet established") }}</span></div>
							<!-- §4.6 — the edition is verification evidence, appended by a
							     source check rather than carried on the immutable version. -->
							<div><span class="kt-label">{{ __("Edition") }}</span><span class="kt-meta-value" data-testid="kt-procset-rule-edition">{{ __("Recorded with the source check") }}</span></div>
							<div><span class="kt-label">{{ __("Provisions") }}</span><span class="kt-meta-value">{{ rule.provision || __("Not yet established") }}</span></div>
							<div><span class="kt-label">{{ __("Source document") }}</span><span class="kt-meta-value"><a v-if="rule.source_document" :href="rule.source_document" target="_blank" rel="noopener">{{ __("View document") }}</a><template v-else>{{ __("Not attached") }}</template></span></div>
							<!-- The method model has no interpretation field; its
							     conditions are its interpretation. -->
							<div><span class="kt-label">{{ __("Interpretation") }}</span><span class="kt-meta-value">{{ kind === 'method' ? __("See the conditions under Rule details") : (rule.interpretation || __("Not yet established")) }}</span></div>
						</div>
					</div>
				</div>

				<div class="kt-section" style="grid-column:1/-1">
					<h6 class="kt-card-title">{{ __("Usage and history") }}</h6>
					<div class="kt-panel">
						<span class="kt-meta-value" data-testid="kt-procset-rule-usage-note">{{ __("Which decisions used this version is not recorded yet.") }}</span>
					</div>
				</div>
			</div>

			<!-- §10.6 saved-detail actions, then the decided extras. -->
			<div style="display:flex;gap:8px;margin-top:16px;flex-wrap:wrap">
				<button v-if="rule.can_edit" type="button" class="btn btn-secondary" data-testid="kt-procset-rule-edit" @click="emit('edit-rule')">{{ __("Edit rule") }}</button>
				<button type="button" class="btn btn-secondary" data-testid="kt-procset-rule-new-version" @click="emit('new-version')">{{ __("Create new version") }}</button>
				<button v-if="kind !== 'method'" type="button" class="btn btn-secondary" data-testid="kt-procset-rule-check-sources" @click="emit('check-sources')">{{ __("Check sources") }}</button>
				<!-- Owner, 23 Sep 2026 (D20): a method rule has no source check
				     behind it; its validity is the administrator's own statement,
				     allowed while the version is in force and in use. -->
				<button
					v-if="canSetValidity"
					type="button"
					class="btn btn-secondary"
					:disabled="validityBusy"
					data-testid="kt-procset-rule-validity"
					@click="setValidity(!valid)"
				>{{ valid ? __("Remove valid mark") : __("Mark as valid") }}</button>
				<button v-if="kind !== 'method'" type="button" class="btn btn-ghost" data-testid="kt-procset-rule-usage" @click="emit('check-sources')">{{ __("View usage and history") }}</button>
				<button v-if="kind !== 'method'" type="button" class="btn btn-ghost" data-testid="kt-procset-rule-rename" @click="renaming = true">{{ __("Edit rule name") }}</button>
			</div>
			<div v-if="validityError" class="kt-notice is-critical" role="alert" style="margin-top:12px" data-testid="kt-procset-rule-validity-error">
				<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12" /></svg>
				<div class="kt-notice-body">{{ validityError }}</div>
			</div>
			<!-- §10.6 — identifier and kind are separate read-only facts. -->
			<div class="kt-meta-row" style="margin-top:16px">
				<div><span class="kt-label">{{ __("Rule identifier") }}</span><span class="kt-meta-value" data-testid="kt-procset-rule-identifier">{{ dash(rule.reference_key || rule.profile || name) }}</span></div>
			</div>

			<RuleRenameDialog
				v-if="renaming"
				:reference-set="rule.reference_set"
				:name="rule.display_name || rule.reference_kind || ''"
				@saved="renaming = false; load(); emit('renamed')"
				@cancel="renaming = false"
			/>
		</div>
	</div>
</template>
