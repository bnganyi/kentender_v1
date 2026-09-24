<script setup>
// PLN-CHG-001 v1.18 §10.11 C03/C04 + §11.6 — the fifth System setup tab:
// funding sources, procurement rules (method eligibility and reservation
// rules), schedule profiles and the reminder threshold. Ported from
// docs/mvp-1-r1/04_planning/design/C01-C04-Setup.dc.html (frames C03,
// C03-source-editor, C03-detail, C04, C04-eligibility-reminder), class for
// class. Every rule is applied server-side. The view comes from the page's
// §9 link (`#procurement-settings/{section}/{id}…`, parsed by the root);
// this tab still switches on its older internal view names, derived from
// that link by data/routes.js until the Phase 5 re-port.
import { computed, nextTick, onMounted, ref, watch } from "vue";
import { routeToLegacy } from "../data/routes.js";
import { onSetupRevalidate } from "../composables/useRouteState.js";
import ConfirmDialog from "../components/ConfirmDialog.vue";
import FundingSourceDialog from "../components/FundingSourceDialog.vue";
import RuleVersionDetail from "../components/RuleVersionDetail.vue";
import RuleEditor from "../components/RuleEditor.vue";
import MethodVersionEditor from "../components/MethodVersionEditor.vue";
import ScheduleVersionEditor from "../components/ScheduleVersionEditor.vue";
import SourceCheckScreen from "../components/SourceCheckScreen.vue";
import CalendarEditor from "../components/CalendarEditor.vue";
import ScheduleProfileDetail from "../components/ScheduleProfileDetail.vue";
import ReminderSettingCard from "../components/ReminderSettingCard.vue";
import { procurementSettingsApi } from "../data/procurementSettingsApi.js";
import { fmtDate, sourceCheckClass, sourceCheckLabel } from "../data/format.js";

const props = defineProps({
	// The parsed §9 route ({tab, section, id, versionId, action}).
	route: { type: Object, default: () => ({}) },
});
const emit = defineEmits(["navigate"]);

const loading = ref(true);
const loadError = ref("");
const data = ref(null);

// Reads overlap (a quiet re-read on returning to the list, another after a
// command); only the newest answer is applied, so an older one arriving late
// can never put back a row a later command removed.
const sequence = kentender_core.desk_page.createSequenceGuard();

async function load({ quiet = false } = {}) {
	const ticket = sequence.next();
	if (!quiet) loading.value = true;
	loadError.value = "";
	try {
		const result = await procurementSettingsApi.get();
		if (!sequence.isCurrent(ticket)) return;
		if (result && result.outcome === "FORBIDDEN") {
			loadError.value = "FORBIDDEN";
			data.value = null;
			return;
		}
		data.value = result;
	} catch (error) {
		if (!sequence.isCurrent(ticket)) return;
		loadError.value = error.message;
		data.value = null;
	} finally {
		if (sequence.isCurrent(ticket)) loading.value = false;
	}
}
onMounted(load);
onSetupRevalidate(load);

// A rule id is a method rule when the server's own list says so. Until that
// list has arrived the two cannot be told apart, so a rule's editor view is
// not derived at all — guessing "reference" would fetch a reference version
// for a method rule and the server would refuse it.
const subpath = computed(() => {
	const r = props.route || {};
	if (!data.value && r.section === "procurement-rules" && ["new-version", "edit"].includes(r.action)) return "";
	return routeToLegacy(r, {
		isMethodRule: (id) => (data.value?.method_profiles || []).some((row) => row.name === id || row.profile === id),
	});
});
const view = computed(() => {
	const [kind, ...rest] = (subpath.value || "").split("/");
	return { kind: kind || "list", name: rest.join("/") };
});

const fundingSources = computed(() => data.value?.funding_sources || []);
// CFG-CHG-002 v0.11 §10.6 (C03-B) — one row per rule. Method eligibility is
// owned by `Procedure Method Profile` (plan D10) and the other six kinds by
// the `Regulatory Reference Set` / version envelope, so this list merges the
// two server projections into the artboard's single "Rule" table. A set with
// no version yet is a real, recoverable state (§7.3) and gets its own row.
const rules = computed(() => {
	const methods = (data.value?.method_profiles || []).map((row) => ({
		key: `rule/${row.profile}`,
		name: row.profile,
		source: "method",
		kind: "Method eligibility",
		rule: `${__("Method eligibility")} — ${row.procurement_method}`,
		effective_from: row.effective_from,
		effective_until: row.effective_until,
		version_number: row.version_number,
		status: row.status,
		verification_status: row.verification_status,
		details_missing: row.details_missing || [],
		has_version: true,
	}));
	const references = (data.value?.reference_sets || []).map((row) => ({
		key: `rule/${row.version?.name || row.reference_set}`,
		name: row.version?.name || row.reference_set,
		reference_set: row.reference_set,
		source: "reference",
		kind: row.reference_kind,
		rule: row.display_name || row.reference_kind,
		effective_from: row.version?.effective_from || "",
		effective_until: row.version?.effective_until || "",
		version_number: row.version?.version_number || "",
		status: row.version?.status || "",
		verification_status: row.version?.verification_status || "",
		details_missing: row.version?.details_missing || [],
		has_version: !!row.has_version,
	}));
	return [...methods, ...references];
});

// C03-B's three list controls. All three are local view filters over the
// server's own list — never authority, and never a second query.
const ruleSearch = ref("");
const ruleKind = ref("All");
const ruleCheck = ref("All");
const ruleKinds = computed(() => data.value?.reference_kinds || []);
const verificationOptions = computed(() => data.value?.verification_statuses || []);
const entityTypes = computed(() => data.value?.entity_types || []);
const procurementCategories = computed(() => data.value?.procurement_categories || []);
const procurementMethods = computed(() => data.value?.procurement_methods || []);
// §10.6 — the Method eligibility editor's closed vocabularies. They are the
// server's, read from this same projection, so the editor cannot offer a
// value the database will reject.
const conditionKinds = computed(() => data.value?.condition_kinds || []);
const cumulativeBases = computed(() => data.value?.cumulative_bases || []);
const methodApplicabilityBases = computed(() => data.value?.method_applicability_bases || []);
// The set + current version behind `rule/<name>`, for the new-version editor.
// §11.6 — a correction copies the current version's own values, so the full
// record is fetched rather than reusing the list row's summary.
const editingRule = computed(() => rules.value.find((row) => row.name === view.value.name) || null);
const ruleVersion = ref(null);
async function fetchRuleVersion(name) {
	try {
		return await procurementSettingsApi.getRegulatoryReferenceVersion(name);
	} catch (error) {
		return null;
	}
}
watch(
	() => (["new-rule-version", "edit-rule-version"].includes(view.value.kind) ? view.value.name : ""),
	async (name) => {
		ruleVersion.value = null;
		if (!name) return;
		ruleVersion.value = await fetchRuleVersion(name);
	},
	{ immediate: true }
);
// A stale save: re-read the version it came from; the editor keeps the entries.
async function reloadRuleVersion() {
	if (view.value.name) ruleVersion.value = await fetchRuleVersion(view.value.name);
}
// The table lists saved versions; a rule with none yet is its own card (§7.3).
const versionedRules = computed(() => rules.value.filter((row) => row.has_version));
const unversionedRules = computed(() => rules.value.filter((row) => !row.has_version));
const visibleRules = computed(() => {
	const text = ruleSearch.value.trim().toLowerCase();
	return versionedRules.value.filter((row) => {
		if (text && !`${row.rule} ${row.name}`.toLowerCase().includes(text)) return false;
		if (ruleKind.value !== "All" && row.kind !== ruleKind.value) return false;
		if (ruleCheck.value !== "All" && row.verification_status !== ruleCheck.value) return false;
		return true;
	});
});
const scheduleProfiles = computed(() => data.value?.schedule_profiles || []);
const calendars = computed(() => data.value?.calendars || []);

function go(sub) {
	emit("navigate", sub);
}

function verificationLabel(value) {
	return __(sourceCheckLabel(value));
}

function verificationClass(value) {
	return sourceCheckClass(value);
}

// CFG-CHG-002 v0.14 §9/§10.1 (D19) — each section is its own view behind the
// section links, as the boards draw them (one board per section, the active
// link bold). `#procurement-settings` opens the first, Funding sources.
// Calendars open inside Procurement schedules, not as a section of their own.
const SECTION_LINKS = [
	["funding-sources", "Funding sources"],
	["procurement-rules", "Procurement rules"],
	["schedule-profiles", "Procurement schedules"],
	["reminders", "Reminders"],
];
const activeSection = computed(() => {
	const section = props.route?.section || "";
	if (section === "calendars") return "schedule-profiles";
	return SECTION_LINKS.some(([key]) => key === section) ? section : "funding-sources";
});
// The funding-source dialog is drawn over the list (C03A #add/#edit), so the
// list stays rendered underneath it.
const sourceDialog = computed(() => {
	if (view.value.kind === "new-source") return { creating: true, source: null };
	if (view.value.kind === "source") {
		const source = fundingSources.value.find((row) => row.name === view.value.name);
		return source ? { creating: false, source } : null;
	}
	return null;
});
const listView = computed(() => ["list", "source", "new-source"].includes(view.value.kind));
// Focus returns to the control that opened the dialog (Add, or the row's
// Edit) when it closes. Held here, not in the dialog: by the time the dialog
// exists the route change has already moved focus off the trigger.
let sourceTrigger = null;
function openSource(sub, event) {
	sourceTrigger = event?.currentTarget || null;
	go(sub);
}
watch(sourceDialog, async (now, before) => {
	if (!before || now) return;
	const trigger = sourceTrigger;
	sourceTrigger = null;
	await nextTick();
	if (trigger && trigger.isConnected) trigger.focus();
});

watch(
	() => subpath.value,
	() => {
		// Returning from a detail or editor re-reads the authoritative list
		// (a new Version or a renamed source must be reflected, §11.6).
		if (listView.value && !sourceDialog.value && data.value) load({ quiet: true });
	}
);

async function afterChange() {
	await load({ quiet: true });
}

// A source nothing has ever used carries no history to protect, so it can be
// removed outright instead of sitting in the list forever as clutter (e.g. a
// mistaken or test entry). A referenced source is never offered the action —
// "Disable" (the existing availability toggle in its own editor) is its only
// removal — and the server refuses a referenced deletion regardless.
const deletingSource = ref(null); // the row, while its confirm dialog is open
const deleteError = ref("");
const deleteBusy = ref(false);
function askRemoveSource(row) {
	deletingSource.value = row;
	deleteError.value = "";
}
async function confirmRemoveSource() {
	deleteBusy.value = true;
	deleteError.value = "";
	try {
		await procurementSettingsApi.deleteFundingSource(deletingSource.value.name);
		deletingSource.value = null;
		await afterChange();
	} catch (error) {
		deleteError.value = error.message;
	} finally {
		deleteBusy.value = false;
	}
}
</script>

<template>
	<section class="kt-setup-section kt-procset is-flow" data-testid="kt-procset">
		<!-- §10.1 section links: each opens its own view. Tender formats is
		     deferred this cycle (D11), so it has no link. The real href keeps
		     open-in-new-tab working; `.stop` keeps Frappe's body-level link
		     handler from re-routing the click and overwriting the Back step. -->
		<nav v-if="!loading && !loadError" class="kt-setup-subnav" :aria-label="__('Procurement settings sections')" data-testid="kt-procset-subnav">
			<a
				v-for="[key, text] in SECTION_LINKS"
				:key="key"
				:href="'#procurement-settings/' + key"
				:class="{ 'is-active': activeSection === key }"
				:aria-current="activeSection === key ? 'page' : undefined"
				:data-testid="'kt-procset-link-' + key"
				@click.stop.prevent="go(key)"
			>{{ __(text) }}</a>
		</nav>

		<div v-if="loading" class="kt-card kt-blueprint" data-testid="kt-procset-loading">
			<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
			<span class="kt-eyebrow">{{ __("Loading procurement settings…") }}</span>
			<div class="kt-skel" style="width:84%" />
			<div class="kt-skel" style="width:62%" />
		</div>

		<div v-else-if="loadError === 'FORBIDDEN'" class="kt-card kt-blueprint kt-empty" data-testid="kt-procset-forbidden">
			<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
			<h2>{{ __("You do not have access to System setup") }}</h2>
			<p>{{ __("This area needs Administrator or System Manager access.") }}</p>
		</div>

		<div v-else-if="loadError" class="kt-card kt-blueprint kt-empty" data-testid="kt-procset-error">
			<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
			<h2>{{ __("Procurement settings could not be loaded") }}</h2>
			<p>{{ __("Try again. If the problem continues, contact support.") }}</p>
			<button type="button" class="kt-btn kt-btn-secondary" data-testid="kt-procset-retry" @click="load">{{ __("Try again") }}</button>
		</div>

		<!-- C03-B "add" / "version" — one editor for a new rule and a new version -->
		<RuleEditor
			v-else-if="view.kind === 'new-rule' || view.kind === 'new-rule-version' || view.kind === 'edit-rule-version'"
			:reference-set="view.kind === 'new-rule' ? '' : (editingRule || {}).reference_set || ''"
			:current-version="view.kind === 'new-rule' ? null : ruleVersion"
			:mode="view.kind === 'edit-rule-version' ? 'correct' : 'version'"
			:kinds="ruleKinds"
			:entity-types="entityTypes"
			:categories="procurementCategories"
			:methods="procurementMethods"
			:method-rules="data.method_profiles || []"
			:condition-kinds="conditionKinds"
			:cumulative-bases="cumulativeBases"
			:applicability-bases="methodApplicabilityBases"
			:verification-statuses="verificationOptions"
			@saved="afterChange().then(() => go(view.kind === 'edit-rule-version' ? 'rule/' + view.name : 'procurement-rules'))"
			@cancel="go(view.kind === 'new-rule' ? 'procurement-rules' : 'rule/' + view.name)"
			@refresh="reloadRuleVersion"
			@review="go(view.name ? 'rule/' + view.name : 'procurement-rules')"
			@open-method-version="(profile) => go('new-method-version/' + profile)"
			@method-saved="(profile) => afterChange().then(() => go('rule/' + profile))"
		/>

		<!-- C03-BC — a method eligibility rule's new version: the full editor,
		     not the reference-rule form (a different model entirely). -->
		<MethodVersionEditor
			v-else-if="view.kind === 'new-method-version' || view.kind === 'edit-method-rule'"
			:name="view.name"
			:mode="view.kind === 'edit-method-rule' ? 'correct' : 'version'"
			:categories="procurementCategories"
			:condition-kinds="conditionKinds"
			:cumulative-bases="cumulativeBases"
			:applicability-bases="methodApplicabilityBases"
			:verification-statuses="verificationOptions"
			@saved="(profile) => afterChange().then(() => go('rule/' + profile))"
			@cancel="go('rule/' + view.name)"
			@refresh="afterChange"
			@review="go('rule/' + view.name)"
		/>

		<!-- C04 — a schedule's new version, or a correction to one nothing
		     depends on yet. Same editor, the mode the server chose. -->
		<ScheduleVersionEditor
			v-else-if="view.kind === 'new-schedule-version' || view.kind === 'edit-schedule'"
			:name="view.name"
			:mode="view.kind === 'edit-schedule' ? 'correct' : 'version'"
			:calendars="calendars"
			:applicability-bases="methodApplicabilityBases"
			:verification-statuses="verificationOptions"
			@saved="(profile) => afterChange().then(() => go('profile/' + profile))"
			@cancel="go('profile/' + view.name)"
		/>

		<!-- C04 "calendar" — a working-day calendar version -->
		<CalendarEditor
			v-else-if="view.kind === 'calendar' || view.kind === 'new-calendar'"
			:name="view.kind === 'calendar' ? view.name : ''"
			:creating="view.kind === 'new-calendar'"
			@back="go('schedule-profiles')"
			@saved="afterChange().then(() => go('schedule-profiles'))"
		/>

		<!-- C03-D — Check sources against one exact version, with both histories -->
		<SourceCheckScreen
			v-else-if="view.kind === 'check-sources'"
			:name="view.name"
			@back="go('rule/' + view.name)"
			@recorded="afterChange().then(() => go('rule/' + view.name))"
			@view-version="(reference) => go('rule/' + reference)"
		/>

		<!-- C03-detail — a rule Version (method eligibility or reservation rules) -->
		<RuleVersionDetail
			v-else-if="view.kind === 'rule'"
			:name="view.name"
			:kind="(rules.find((row) => row.name === view.name) || {}).source || 'reference'"
			:verification-statuses="data.verification_statuses"
			@back="go('procurement-rules')"
			@registered="afterChange().then(() => go('procurement-rules'))"
			@renamed="afterChange"
			@new-version="go(((rules.find((row) => row.name === view.name) || {}).source === 'method' ? 'new-method-version/' : 'new-rule-version/') + view.name)"
			@edit-rule="go(((rules.find((row) => row.name === view.name) || {}).source === 'method' ? 'edit-method-rule/' : 'edit-rule-version/') + view.name)"
			@check-sources="go('check-sources/' + view.name)"
		/>

		<!-- C04 — a schedule profile Version -->
		<ScheduleProfileDetail
			v-else-if="view.kind === 'profile'"
			:name="view.name"
			:verification-statuses="data.verification_statuses"
			@back="go('schedule-profiles')"
			@registered="afterChange().then(() => go('schedule-profiles'))"
			@new-version="go('new-schedule-version/' + view.name)"
			@edit-schedule="go('edit-schedule/' + view.name)"
		/>

		<template v-else-if="listView">

			<!-- CFG-CHG-002 v0.14 §10.5 — C03A #list and #empty, ported element
			     by element. The availability column states what the setting
			     governs ("Available for new selection"), never a bare flag. -->
			<div v-if="activeSection === 'funding-sources'" id="kt-procset-sources" data-testid="kt-procset-sources">
				<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:16px;flex-wrap:wrap">
					<div>
						<h3 style="margin-bottom:4px">{{ __("Funding sources") }}</h3>
						<p class="card-body" style="margin-bottom:0">{{ __("Maintain the sources used in procurement budgets.") }}</p>
					</div>
					<button type="button" class="kt-btn kt-btn-primary" data-testid="kt-procset-source-add" @click="openSource('new-source', $event)">
						<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M12 5v14M5 12h14" /></svg>{{ __("Add funding source") }}
					</button>
				</div>
				<table v-if="fundingSources.length" class="kt-table">
					<thead>
						<tr><th>{{ __("Name") }}</th><th>{{ __("Available for new selection") }}</th><th>{{ __("Action") }}</th></tr>
					</thead>
					<tbody>
						<tr v-for="row in fundingSources" :key="row.name" :data-testid="'kt-procset-source-' + row.name">
							<td>{{ row.label }}</td>
							<td><span :class="row.enabled ? 'kt-status is-live' : 'kt-status is-critical'">{{ row.enabled ? __("Yes") : __("No") }}</span></td>
							<td>
								<a href="#" :data-testid="'kt-procset-source-edit-' + row.name" @click.prevent="openSource('source/' + row.name, $event)">{{ __("Edit") }}</a>
								<!-- A source nothing has ever used can be removed outright
								     (owner decision, 18 Sep 2026); see DEPARTURES. -->
								<a
									v-if="!row.referenced"
									href="#"
									class="kt-procset-remove"
									:data-testid="'kt-procset-source-remove-' + row.name"
									@click.prevent="askRemoveSource(row)"
								>{{ __("Remove") }}</a>
							</td>
						</tr>
					</tbody>
				</table>
				<div v-else class="kt-procset-empty" data-testid="kt-procset-sources-empty">
					<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="var(--kt-color-neutral-400)" stroke-width="1.5" aria-hidden="true"><path d="M22 12h-6l-2 3h-4l-2-3H2" /><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z" /></svg>
					<p style="font-weight:600;margin-bottom:4px">{{ __("No funding sources yet") }}</p>
					<p class="card-body">{{ __("Add the sources used by this site's procurement budgets.") }}</p>
					<button type="button" class="kt-btn kt-btn-primary" @click="openSource('new-source', $event)"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M12 5v14M5 12h14" /></svg>{{ __("Add funding source") }}</button>
				</div>
			</div>

			<!-- CFG-CHG-002 v0.14 §10.6 — C03BC #list, ported element by element:
			     header row, the three filters, the seven-column table ("Source
			     check" and "Details" separate), then the board's cards for a rule
			     with no version yet (or an unpublished price index) and the empty
			     catalogue. -->
			<div v-if="activeSection === 'procurement-rules'" id="kt-procset-rules" data-testid="kt-procset-rules">
				<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:16px;flex-wrap:wrap">
					<div>
						<h3 style="margin-bottom:4px">{{ __("Procurement rules") }}</h3>
						<p class="card-body" style="margin-bottom:0">{{ __("Maintain procurement rules and their supporting sources.") }}</p>
					</div>
					<button type="button" class="kt-btn kt-btn-primary" data-testid="kt-procset-rule-add" @click="go('new-rule')">
						<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M12 5v14M5 12h14" /></svg>{{ __("Add rule") }}
					</button>
				</div>
				<template v-if="versionedRules.length">
					<div style="display:flex;gap:12px;flex-wrap:wrap;margin:12px 0">
						<div class="kt-field" style="flex:1;min-width:200px">
							<label for="kt-procset-rule-search">{{ __("Search") }}</label>
							<input id="kt-procset-rule-search" v-model="ruleSearch" class="kt-input" data-testid="kt-procset-rule-search">
						</div>
						<div class="kt-field" style="min-width:160px">
							<label for="kt-procset-rule-kind">{{ __("Rule kind") }}</label>
							<select id="kt-procset-rule-kind" v-model="ruleKind" class="kt-input" data-testid="kt-procset-rule-kind">
								<option value="All">{{ __("All") }}</option>
								<option v-for="kind in ruleKinds" :key="kind" :value="kind">{{ kind }}</option>
							</select>
						</div>
						<div class="kt-field" style="min-width:160px">
							<label for="kt-procset-rule-check">{{ __("Source check") }}</label>
							<select id="kt-procset-rule-check" v-model="ruleCheck" class="kt-input" data-testid="kt-procset-rule-check">
								<option value="All">{{ __("All") }}</option>
								<option v-for="status in verificationOptions" :key="status" :value="status">{{ verificationLabel(status) }}</option>
							</select>
						</div>
					</div>
					<table class="kt-table">
						<thead>
							<tr><th>{{ __("Rule") }}</th><th>{{ __("Applies from") }}</th><th>{{ __("Applies until") }}</th><th>{{ __("Version") }}</th><th>{{ __("Source check") }}</th><th>{{ __("Details") }}</th><th>{{ __("Action") }}</th></tr>
						</thead>
						<tbody>
							<tr v-for="row in visibleRules" :key="row.key" :data-testid="'kt-procset-rule-' + row.name" :data-status="row.status">
								<!-- Only an explicitly non-active status is superseded; the set
								     projection carries no status for its current version. -->
								<td>{{ row.rule }}<span v-if="row.status && row.status !== 'Active'" class="kt-tag kt-tag-neutral kt-procset-superseded">{{ __("Superseded") }}</span></td>
								<td>{{ fmtDate(row.effective_from) }}</td>
								<td>{{ fmtDate(row.effective_until) }}</td>
								<td>{{ row.version_number }}</td>
								<td><span :class="verificationClass(row.verification_status)">{{ verificationLabel(row.verification_status) }}</span></td>
								<td>
									<span
										:class="row.details_missing.length ? 'kt-status is-pending' : 'kt-status is-live'"
										:title="row.details_missing.join(', ')"
										:data-testid="'kt-procset-rule-details-' + row.name"
									>{{ row.details_missing.length ? __("Details missing") : __("Details complete") }}</span>
								</td>
								<td><a href="#" :data-testid="'kt-procset-rule-view-' + row.name" @click.prevent="go('rule/' + row.name)">{{ __("View") }}</a></td>
							</tr>
							<tr v-if="!visibleRules.length"><td colspan="7" class="text-muted" data-testid="kt-procset-rules-none-match">{{ __("No rules match these filters.") }}</td></tr>
						</tbody>
					</table>
				</template>
				<div v-if="!rules.length || unversionedRules.length" class="kt-procset-rule-cards">
					<div v-if="!rules.length" class="kt-card kt-procset-empty-card" data-testid="kt-procset-rules-empty">
						<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="var(--kt-color-neutral-400)" stroke-width="1.5" aria-hidden="true"><path d="M22 12h-6l-2 3h-4l-2-3H2" /><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z" /></svg>
						<p style="font-weight:600;margin-bottom:4px">{{ __("No procurement rules yet") }}</p>
						<p class="card-body">{{ __("Add rules for the procurement procedures supported by this release.") }}</p>
						<button type="button" class="kt-btn kt-btn-primary kt-btn-block" @click="go('new-rule')"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M12 5v14M5 12h14" /></svg>{{ __("Add rule") }}</button>
					</div>
					<template v-for="row in unversionedRules" :key="row.key">
						<!-- §8.1 — an optional price index with nothing published is
						     informational, not a missing version. -->
						<div v-if="row.kind === 'Market price index'" class="kt-card" :data-testid="'kt-procset-rule-unpublished-' + row.name">
							<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
								<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 8v4M12 16h.01" /></svg>
								<span class="kt-tag kt-tag-neutral">{{ __("Not published") }}</span>
							</div>
							<p class="card-body">{{ __("No price index has been published for this period.") }}</p>
						</div>
						<!-- §7.3 — a rule saved with no version is recoverable in place. -->
						<div v-else class="kt-card" :data-testid="'kt-procset-rule-noversion-' + row.name">
							<div class="kt-status is-pending" style="margin-bottom:6px">{{ __("No version saved") }}</div>
							<div class="kt-meta-row"><div><span class="kt-label">{{ __("Rule") }}</span><span class="kt-meta-value">{{ row.rule }}</span></div></div>
							<button type="button" class="kt-btn kt-btn-secondary" style="margin-top:8px" :data-testid="'kt-procset-rule-first-version-' + row.name" @click="go('new-rule-version/' + row.name)">{{ __("Add first version") }}</button>
						</div>
					</template>
				</div>
			</div>

			<!-- C04 schedule profiles (list; detail is its own frame) -->
			<div v-if="activeSection === 'schedule-profiles'" id="kt-procset-profiles" class="kt-card kt-blueprint kt-table-card" data-testid="kt-procset-profiles">
				<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
				<h3 class="kt-card-title">{{ __("Procurement schedules") }}</h3>
				<p class="kt-muted">{{ __("Set the time intervals used to prepare procurement schedules.") }}</p>
				<table class="kt-table">
					<thead>
						<tr><th>{{ __("Profile") }}</th><th>{{ __("Method") }}</th><th>{{ __("Category") }}</th><th>{{ __("Version") }}</th><th>{{ __("Effective") }}</th><th>{{ __("Source verification") }}</th><th class="kt-visually-hidden-th"><span class="kt-visually-hidden">{{ __("Actions") }}</span></th></tr>
					</thead>
					<tbody>
						<tr v-for="row in scheduleProfiles" :key="row.profile" :data-testid="'kt-procset-profile-' + row.profile" :data-status="row.status">
							<td class="kt-row-name">{{ row.profile_name }}<span v-if="row.status !== 'Active'" class="kt-tag kt-tag-neutral kt-procset-superseded">{{ __("Superseded") }}</span></td>
							<td>{{ row.procurement_method }}</td>
							<td>{{ row.procurement_category }}</td>
							<td>{{ row.version_number }}</td>
							<td>{{ fmtDate(row.effective_from) }} – {{ fmtDate(row.effective_until) }}</td>
							<td><span :class="verificationClass(row.verification_status)">{{ verificationLabel(row.verification_status) }}</span></td>
							<td class="kt-row-actions"><a href="#" :data-testid="'kt-procset-profile-view-' + row.profile" @click.prevent="go('profile/' + row.profile)">{{ __("View") }}</a></td>
						</tr>
						<tr v-if="!scheduleProfiles.length"><td colspan="7" class="kt-muted">{{ __("No schedule profiles have been registered.") }}</td></tr>
					</tbody>
				</table>
			</div>

			<!-- CFG-CHG-002 v0.11 §10.9 (C04 "calendar") — working-day calendars
			     are their own versioned record, drawn as their own states rather
			     than folded into the schedule card (plan D4). A schedule's
			     working-day interval cannot resolve without one. -->
			<div v-if="activeSection === 'schedule-profiles'" id="kt-procset-calendars" class="kt-card kt-blueprint kt-table-card" data-testid="kt-procset-calendars">
				<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
				<div class="kt-section-head">
					<div>
						<h3 class="kt-card-title">{{ __("Working-day calendars") }}</h3>
						<p class="kt-muted">{{ __("Set the weekends and holidays that working-day intervals count against.") }}</p>
					</div>
					<button type="button" class="kt-btn kt-btn-primary" data-testid="kt-procset-calendar-add" @click="go('new-calendar')">
						<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 5v14M5 12h14" /></svg>{{ __("Add calendar") }}
					</button>
				</div>
				<table v-if="calendars.length" class="kt-table">
					<thead>
						<tr><th>{{ __("Calendar name") }}</th><th>{{ __("Version") }}</th><th>{{ __("Applies from") }}</th><th>{{ __("Applies until") }}</th><th>{{ __("Source check") }}</th><th>{{ __("Action") }}</th></tr>
					</thead>
					<tbody>
						<tr v-for="row in calendars" :key="row.calendar" :data-testid="'kt-procset-calendar-' + row.calendar">
							<td class="kt-row-name">{{ row.calendar_name }}<span v-if="row.status !== 'Active'" class="kt-tag kt-tag-neutral kt-procset-superseded">{{ __("Superseded") }}</span></td>
							<td>{{ row.version_number }}</td>
							<td>{{ fmtDate(row.effective_from) }}</td>
							<td>{{ fmtDate(row.effective_until) }}</td>
							<td><span :class="verificationClass(row.verification_status)">{{ verificationLabel(row.verification_status) }}</span></td>
							<td class="kt-row-actions"><a href="#" :data-testid="'kt-procset-calendar-view-' + row.calendar" @click.prevent="go('calendar/' + row.calendar)">{{ __("View calendar") }}</a></td>
						</tr>
					</tbody>
				</table>
				<div v-else class="kt-empty" data-testid="kt-procset-calendars-empty">
					<h2>{{ __("No working-day calendars yet") }}</h2>
					<p>{{ __("Add a calendar before a schedule can count working days.") }}</p>
					<button type="button" class="kt-btn kt-btn-primary" @click="go('new-calendar')"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 5v14M5 12h14" /></svg>{{ __("Add calendar") }}</button>
				</div>
			</div>

			<!-- C04-eligibility-reminder — the reminder threshold -->
			<div v-if="activeSection === 'reminders'" id="kt-procset-reminders">
				<ReminderSettingCard :days="data.reminder_threshold_days" @saved="afterChange" />
			</div>
		</template>

		<FundingSourceDialog
			v-if="sourceDialog && !loading && !loadError"
			:key="sourceDialog.source ? sourceDialog.source.name : 'new'"
			:source="sourceDialog.source"
			:creating="sourceDialog.creating"
			:existing="fundingSources"
			@saved="afterChange().then(() => go('funding-sources'))"
			@cancel="go('funding-sources')"
		/>

		<ConfirmDialog
			v-if="deletingSource"
			:title="__('Remove this funding source?')"
			:body="__('{0} has never been used and will be removed permanently. This cannot be undone.', [deletingSource.label])"
			:confirm-label="__('Remove')"
			destructive
			:error="deleteError"
			:busy="deleteBusy"
			testid="kt-procset-source-remove-confirm"
			@confirm="confirmRemoveSource"
			@cancel="deletingSource = null"
		/>
	</section>
</template>
