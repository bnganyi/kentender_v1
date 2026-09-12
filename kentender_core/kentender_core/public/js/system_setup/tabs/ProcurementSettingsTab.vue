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
import ScheduleProfileDetail from "../components/ScheduleProfileDetail.vue";
import ReminderSettingCard from "../components/ReminderSettingCard.vue";
import { procurementSettingsApi } from "../data/procurementSettingsApi.js";
import { fmtDate } from "../data/format.js";

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
const rules = computed(() => {
	// C03 — one row per rule Version: method eligibility profiles and the
	// regulator reference ("Reservation rules") Versions, newest first.
	const methods = (data.value?.method_profiles || []).map((row) => ({
		key: `rule/${row.profile}`,
		name: row.profile,
		kind: "method",
		reference_set: `${__("Method eligibility")} — ${row.procurement_method}`,
		effective_from: row.effective_from,
		effective_until: row.effective_until,
		version_number: row.version_number,
		status: row.status,
		verification_status: row.verification_status,
	}));
	const references = (data.value?.regulatory_references || []).map((row) => ({
		key: `rule/${row.reference}`,
		name: row.reference,
		kind: "reference",
		reference_set: __("Reservation rules"),
		effective_from: row.effective_from,
		effective_until: "",
		version_number: row.reference.split("-").pop().replace(/^0+/, "") || "1",
		status: row.status,
		verification_status: row.verification_status,
	}));
	return [...methods, ...references];
});
const scheduleProfiles = computed(() => data.value?.schedule_profiles || []);

function go(sub) {
	emit("navigate", sub);
}

function scrollTo(id) {
	const el = document.getElementById(id);
	if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
}

function verificationLabel(value) {
	return value === "Verified" ? __("Verified") : value === "Fixture-verified — not production law" ? __("Fixture-verified — not production law") : __("Production verification pending");
}

function verificationClass(value) {
	return value === "Verified" ? "kt-status is-live" : "kt-status is-attention";
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
			@saved="afterChange().then(() => go(''))"
			@cancel="go('')"
		/>

		<!-- C03-detail — a rule Version (method eligibility or reservation rules) -->
		<RuleVersionDetail
			v-else-if="view.kind === 'rule'"
			:name="view.name"
			:kind="(rules.find((row) => row.name === view.name) || {}).kind || (view.name.startsWith('REG-') ? 'reference' : 'method')"
			:verification-statuses="data.verification_statuses"
			@back="go('')"
			@registered="afterChange().then(() => go(''))"
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
				<a href="#" @click.prevent="scrollTo('kt-procset-reminders')">{{ __("Reminders") }}</a>
			</nav>

			<!-- C03 funding sources -->
			<div id="kt-procset-sources" class="kt-card kt-blueprint kt-table-card" data-testid="kt-procset-sources">
				<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
				<table class="kt-table">
					<thead>
						<tr><th>{{ __("Name") }}</th><th>{{ __("Enabled") }}</th><th class="kt-visually-hidden-th"><span class="kt-visually-hidden">{{ __("Actions") }}</span></th></tr>
					</thead>
					<tbody>
						<tr v-for="row in fundingSources" :key="row.name" :data-testid="'kt-procset-source-' + row.name">
							<td class="kt-row-name">{{ row.label }}</td>
							<td><span :class="row.enabled ? 'kt-status is-live' : 'kt-tag kt-tag-neutral'">{{ row.enabled ? __("Yes") : __("No") }}</span></td>
							<td class="kt-row-actions"><button type="button" class="kt-btn kt-btn-secondary kt-btn-sm" :data-testid="'kt-procset-source-edit-' + row.name" @click="go('source/' + row.name)">{{ __("Edit") }}</button></td>
						</tr>
					</tbody>
				</table>
				<div class="kt-procset-card-actions"><button type="button" class="kt-btn kt-btn-secondary" data-testid="kt-procset-source-add" @click="go('new-source')">{{ __("Add funding source") }}</button></div>
			</div>

			<!-- C03 procurement rules -->
			<div id="kt-procset-rules" class="kt-card kt-blueprint kt-table-card" data-testid="kt-procset-rules">
				<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
				<h3 class="kt-card-title">{{ __("Procurement rules") }}</h3>
				<table class="kt-table">
					<thead>
						<tr><th>{{ __("Reference set") }}</th><th>{{ __("Applies from") }}</th><th>{{ __("Applies until") }}</th><th>{{ __("Version") }}</th><th>{{ __("Source verification") }}</th><th class="kt-visually-hidden-th"><span class="kt-visually-hidden">{{ __("Actions") }}</span></th></tr>
					</thead>
					<tbody>
						<tr v-for="row in rules" :key="row.key" :data-testid="'kt-procset-rule-' + row.name" :data-status="row.status">
							<td class="kt-row-name">{{ row.reference_set }}<span v-if="row.status !== 'Active'" class="kt-tag kt-tag-neutral kt-procset-superseded">{{ __("Superseded") }}</span></td>
							<td>{{ fmtDate(row.effective_from) }}</td>
							<td>{{ fmtDate(row.effective_until) }}</td>
							<td>{{ row.version_number }}</td>
							<td><span :class="verificationClass(row.verification_status)">{{ verificationLabel(row.verification_status) }}</span></td>
							<td class="kt-row-actions"><a href="#" :data-testid="'kt-procset-rule-view-' + row.name" @click.prevent="go('rule/' + row.name)">{{ __("View") }}</a></td>
						</tr>
					</tbody>
				</table>
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

			<!-- C04-eligibility-reminder — the reminder threshold -->
			<div id="kt-procset-reminders">
				<ReminderSettingCard :days="data.reminder_threshold_days" @saved="afterChange" />
			</div>
		</template>
	</section>
</template>
