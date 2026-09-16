<script setup>
// PLN-CHG-001 v1.18 §10.11 C03/C04 + §11.6 — the fifth System setup tab:
// funding sources, procurement rules (method eligibility and reservation
// rules), schedule profiles and the reminder threshold. Ported from
// docs/mvp-1-r1/04_planning/design/C01-C04-Setup.dc.html (frames C03,
// C03-source-editor, C03-detail, C04, C04-eligibility-reminder), class for
// class. Every rule is applied server-side; the sub-path (`source/<name>`,
// `rule/<name>`, `profile/<name>`, `new-source`) lives in the page hash so
// refresh and back/forward restore the same view.
import { computed, onMounted, ref, watch } from "vue";
import FundingSourceEditor from "../components/FundingSourceEditor.vue";
import RuleVersionDetail from "../components/RuleVersionDetail.vue";
import RuleEditor from "../components/RuleEditor.vue";
import SourceCheckScreen from "../components/SourceCheckScreen.vue";
import CalendarEditor from "../components/CalendarEditor.vue";
import ScheduleProfileDetail from "../components/ScheduleProfileDetail.vue";
import ReminderSettingCard from "../components/ReminderSettingCard.vue";
import { procurementSettingsApi } from "../data/procurementSettingsApi.js";
import { fmtDate, sourceCheckClass, sourceCheckLabel } from "../data/format.js";

const props = defineProps({
	subpath: { type: String, default: "" },
});
const emit = defineEmits(["navigate"]);

const loading = ref(true);
const loadError = ref("");
const data = ref(null);

async function load({ quiet = false } = {}) {
	if (!quiet) loading.value = true;
	loadError.value = "";
	try {
		const result = await procurementSettingsApi.get();
		if (result && result.outcome === "FORBIDDEN") {
			loadError.value = "FORBIDDEN";
			data.value = null;
			return;
		}
		data.value = result;
	} catch (error) {
		loadError.value = error.message;
		data.value = null;
	} finally {
		loading.value = false;
	}
}
onMounted(load);

const view = computed(() => {
	const [kind, ...rest] = (props.subpath || "").split("/");
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
// The set + current version behind `rule/<name>`, for the new-version editor.
// §11.6 — a correction copies the current version's own values, so the full
// record is fetched rather than reusing the list row's summary.
const editingRule = computed(() => rules.value.find((row) => row.name === view.value.name) || null);
const ruleVersion = ref(null);
watch(
	() => (view.value.kind === "new-rule-version" ? view.value.name : ""),
	async (name) => {
		ruleVersion.value = null;
		if (!name) return;
		try {
			ruleVersion.value = await procurementSettingsApi.getRegulatoryReferenceVersion(name);
		} catch (error) {
			ruleVersion.value = null;
		}
	},
	{ immediate: true }
);
const visibleRules = computed(() => {
	const text = ruleSearch.value.trim().toLowerCase();
	return rules.value.filter((row) => {
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

function scrollTo(id) {
	const el = document.getElementById(id);
	if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
}

function verificationLabel(value) {
	return __(sourceCheckLabel(value));
}

function verificationClass(value) {
	return sourceCheckClass(value);
}

watch(
	() => props.subpath,
	() => {
		// Returning from a detail or editor re-reads the authoritative list
		// (a new Version or a renamed source must be reflected, §11.6).
		if (view.value.kind === "list" && data.value) load({ quiet: true });
	}
);

async function afterChange() {
	await load({ quiet: true });
}
</script>

<template>
	<section class="kt-setup-section kt-procset" data-testid="kt-procset">
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

		<!-- C03-source-editor / new source -->
		<FundingSourceEditor
			v-else-if="view.kind === 'source' || view.kind === 'new-source'"
			:source="view.kind === 'source' ? fundingSources.find((row) => row.name === view.name) || null : null"
			:creating="view.kind === 'new-source'"
			:existing="fundingSources"
			@saved="afterChange().then(() => go(''))"
			@cancel="go('')"
		/>

		<!-- C03-B "add" / "version" — one editor for a new rule and a new version -->
		<RuleEditor
			v-else-if="view.kind === 'new-rule' || view.kind === 'new-rule-version'"
			:reference-set="view.kind === 'new-rule-version' ? (editingRule || {}).reference_set || '' : ''"
			:current-version="view.kind === 'new-rule-version' ? ruleVersion : null"
			:kinds="ruleKinds"
			:entity-types="entityTypes"
			:categories="procurementCategories"
			:methods="procurementMethods"
			@saved="afterChange().then(() => go(''))"
			@cancel="go('')"
		/>

		<!-- C04 "calendar" — a working-day calendar version -->
		<CalendarEditor
			v-else-if="view.kind === 'calendar' || view.kind === 'new-calendar'"
			:name="view.kind === 'calendar' ? view.name : ''"
			:creating="view.kind === 'new-calendar'"
			@back="go('')"
			@saved="afterChange().then(() => go(''))"
		/>

		<!-- C03-D — Check sources against one exact version, with both histories -->
		<SourceCheckScreen
			v-else-if="view.kind === 'check-sources'"
			:name="view.name"
			@back="go('rule/' + view.name)"
			@recorded="afterChange().then(() => go('rule/' + view.name))"
		/>

		<!-- C03-detail — a rule Version (method eligibility or reservation rules) -->
		<RuleVersionDetail
			v-else-if="view.kind === 'rule'"
			:name="view.name"
			:kind="(rules.find((row) => row.name === view.name) || {}).source || 'reference'"
			:verification-statuses="data.verification_statuses"
			@back="go('')"
			@registered="afterChange().then(() => go(''))"
			@new-version="go('new-rule-version/' + view.name)"
			@check-sources="go('check-sources/' + view.name)"
		/>

		<!-- C04 — a schedule profile Version -->
		<ScheduleProfileDetail
			v-else-if="view.kind === 'profile'"
			:name="view.name"
			:verification-statuses="data.verification_statuses"
			@back="go('')"
			@registered="afterChange().then(() => go(''))"
		/>

		<template v-else>
			<!-- C03 section links: document anchors, not steps -->
			<nav class="kt-setup-subnav" data-testid="kt-procset-subnav">
				<a href="#" class="is-active" @click.prevent="scrollTo('kt-procset-sources')">{{ __("Funding sources") }}</a>
				<a href="#" @click.prevent="scrollTo('kt-procset-rules')">{{ __("Procurement rules") }}</a>
				<a href="#" @click.prevent="scrollTo('kt-procset-profiles')">{{ __("Schedule profiles") }}</a>
				<a href="#" @click.prevent="scrollTo('kt-procset-calendars')">{{ __("Working-day calendars") }}</a>
				<a href="#" @click.prevent="scrollTo('kt-procset-reminders')">{{ __("Reminders") }}</a>
			</nav>

			<!-- CFG-CHG-002 v0.11 §10.5 (C03-A) — funding sources, ported
			     class-for-class: the availability column states what the
			     setting governs ("Available for new selection"), never a bare
			     "Enabled" flag. -->
			<div id="kt-procset-sources" class="kt-card kt-blueprint kt-table-card" data-testid="kt-procset-sources">
				<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
				<div class="kt-section-head">
					<div>
						<h3 class="kt-card-title">{{ __("Funding sources") }}</h3>
						<p class="kt-muted">{{ __("Maintain the sources used in procurement budgets.") }}</p>
					</div>
					<button type="button" class="kt-btn kt-btn-primary" data-testid="kt-procset-source-add" @click="go('new-source')">
						{{ __("Add funding source") }}
					</button>
				</div>
				<table v-if="fundingSources.length" class="kt-table">
					<thead>
						<tr><th>{{ __("Name") }}</th><th>{{ __("Available for new selection") }}</th><th>{{ __("Action") }}</th></tr>
					</thead>
					<tbody>
						<tr v-for="row in fundingSources" :key="row.name" :data-testid="'kt-procset-source-' + row.name">
							<td class="kt-row-name">{{ row.label }}</td>
							<td><span :class="row.enabled ? 'kt-status is-live' : 'kt-status is-critical'">{{ row.enabled ? __("Yes") : __("No") }}</span></td>
							<td class="kt-row-actions"><a href="#" :data-testid="'kt-procset-source-edit-' + row.name" @click.prevent="go('source/' + row.name)">{{ __("Edit") }}</a></td>
						</tr>
					</tbody>
				</table>
				<div v-else class="kt-empty" data-testid="kt-procset-sources-empty">
					<h2>{{ __("No funding sources yet") }}</h2>
					<p>{{ __("Add the sources used by this site's procurement budgets.") }}</p>
					<button type="button" class="kt-btn kt-btn-primary" @click="go('new-source')">{{ __("Add funding source") }}</button>
				</div>
			</div>

			<!-- C03 procurement rules -->
			<div id="kt-procset-rules" class="kt-card kt-blueprint kt-table-card" data-testid="kt-procset-rules">
				<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
				<div class="kt-section-head">
					<div>
						<h3 class="kt-card-title">{{ __("Procurement rules") }}</h3>
						<p class="kt-muted">{{ __("Maintain procurement rules and their supporting sources.") }}</p>
					</div>
					<button type="button" class="kt-btn kt-btn-primary" data-testid="kt-procset-rule-add" @click="go('new-rule')">
						{{ __("Add rule") }}
					</button>
				</div>
				<div v-if="rules.length" class="kt-procset-filters" style="display:flex;gap:12px;flex-wrap:wrap;margin:12px 0">
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
				<table v-if="rules.length" class="kt-table">
					<thead>
						<tr><th>{{ __("Rule") }}</th><th>{{ __("Applies from") }}</th><th>{{ __("Applies until") }}</th><th>{{ __("Version") }}</th><th>{{ __("Source check") }}</th><th>{{ __("Action") }}</th></tr>
					</thead>
					<tbody>
						<tr v-for="row in visibleRules" :key="row.key" :data-testid="'kt-procset-rule-' + row.name" :data-status="row.status">
							<!-- Only an explicitly non-active status is superseded; the set
							     projection carries no status at all for its current version. -->
							<td class="kt-row-name">{{ row.rule }}<span v-if="row.has_version && row.status && row.status !== 'Active'" class="kt-tag kt-tag-neutral kt-procset-superseded">{{ __("Superseded") }}</span></td>
							<!-- §7.3 — a rule whose set exists with no version yet is a real
							     recoverable state, not an empty row pretending to be a version. -->
							<template v-if="row.has_version">
								<td>{{ fmtDate(row.effective_from) }}</td>
								<td>{{ fmtDate(row.effective_until) }}</td>
								<td>{{ row.version_number }}</td>
								<td><span :class="verificationClass(row.verification_status)">{{ verificationLabel(row.verification_status) }}</span></td>
								<td class="kt-row-actions"><a href="#" :data-testid="'kt-procset-rule-view-' + row.name" @click.prevent="go('rule/' + row.name)">{{ __("View") }}</a></td>
							</template>
							<template v-else>
								<td colspan="4"><span class="kt-status is-pending" :data-testid="'kt-procset-rule-noversion-' + row.name">{{ __("No version saved") }}</span></td>
								<td class="kt-row-actions"><span class="kt-muted">{{ __("Add first version") }}</span></td>
							</template>
						</tr>
					</tbody>
				</table>
				<div v-else class="kt-empty" data-testid="kt-procset-rules-empty">
					<h2>{{ __("No procurement rules yet") }}</h2>
					<p>{{ __("Add rules for the procurement procedures supported by this release.") }}</p>
					<button type="button" class="kt-btn kt-btn-primary" @click="go('new-rule')">{{ __("Add rule") }}</button>
				</div>
			</div>

			<!-- C04 schedule profiles (list; detail is its own frame) -->
			<div id="kt-procset-profiles" class="kt-card kt-blueprint kt-table-card" data-testid="kt-procset-profiles">
				<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
				<h3 class="kt-card-title">{{ __("Schedule profiles") }}</h3>
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
			<div id="kt-procset-calendars" class="kt-card kt-blueprint kt-table-card" data-testid="kt-procset-calendars">
				<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
				<div class="kt-section-head">
					<div>
						<h3 class="kt-card-title">{{ __("Working-day calendars") }}</h3>
						<p class="kt-muted">{{ __("Set the weekends and holidays that working-day intervals count against.") }}</p>
					</div>
					<button type="button" class="kt-btn kt-btn-primary" data-testid="kt-procset-calendar-add" @click="go('new-calendar')">
						{{ __("Add calendar") }}
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
					<button type="button" class="kt-btn kt-btn-primary" @click="go('new-calendar')">{{ __("Add calendar") }}</button>
				</div>
			</div>

			<!-- C04-eligibility-reminder — the reminder threshold -->
			<div id="kt-procset-reminders">
				<ReminderSettingCard :days="data.reminder_threshold_days" @saved="afterChange" />
			</div>
		</template>
	</section>
</template>
