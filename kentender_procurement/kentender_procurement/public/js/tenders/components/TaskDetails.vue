<!-- TPR-DES-03 Draft: Tender details — the three form groups (Tender dates,
     Tender security, Pre-tender meeting) ported class-for-class. Inputs are
     hydrated once per record identity + record_version (AGENTS.md §6.4) and
     bound to the officer's own edits; every rule is the server's catalogue
     (§5.2) — the client only shows the server's field errors inline. -->
<template>
	<div>
		<div class="tnd-section tnd-section--form">
			<h3 class="kt-card-title tnd-section-title"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4"/><path d="M8 2v4"/><path d="M3 10h18"/></svg>Tender dates</h3>
			<div class="kt-field tnd-form-row"><label for="tnd-tender_title">Tender title</label><input id="tnd-tender_title" class="kt-input" v-model="form.tender_title" maxlength="160" data-testid="tnd-field-tender_title" /><p v-if="errors.tender_title" class="tnd-field-error" :data-testid="`tnd-error-tender_title`">{{ errors.tender_title }}</p></div>
			<div class="tnd-grid-2 tnd-form-row">
				<div class="kt-field" style="margin: 0"><label for="tnd-issue_date">Issue date</label><input id="tnd-issue_date" type="date" class="kt-input" v-model="form.issue_date" data-testid="tnd-field-issue_date" /><p v-if="errors.issue_date" class="tnd-field-error">{{ errors.issue_date }}</p></div>
				<div class="kt-field" style="margin: 0"><label for="tnd-clarification_deadline">Clarification deadline</label><input id="tnd-clarification_deadline" type="datetime-local" class="kt-input" v-model="form.clarification_deadline" data-testid="tnd-field-clarification_deadline" /><p v-if="errors.clarification_deadline" class="tnd-field-error">{{ errors.clarification_deadline }}</p></div>
			</div>
			<div class="tnd-grid-2">
				<div class="kt-field" style="margin: 0"><label for="tnd-submission_deadline">Submission deadline</label><input id="tnd-submission_deadline" type="datetime-local" class="kt-input" v-model="form.submission_deadline" data-testid="tnd-field-submission_deadline" /><p v-if="errors.submission_deadline" class="tnd-field-error">{{ errors.submission_deadline }}</p></div>
				<div class="kt-field" style="margin: 0"><label for="tnd-tender_validity_days">Tender validity (days)</label><input id="tnd-tender_validity_days" type="number" min="1" max="365" step="1" class="kt-input" v-model="form.tender_validity_days" data-testid="tnd-field-tender_validity_days" />
					<div class="kt-label tnd-hint-label">How long suppliers' offers must remain valid.</div>
					<p v-if="errors.tender_validity_days" class="tnd-field-error">{{ errors.tender_validity_days }}</p>
				</div>
			</div>
		</div>

		<div class="tnd-section tnd-section--form">
			<h3 class="kt-card-title tnd-section-title"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/></svg>Tender security</h3>
			<div class="tnd-grid-3">
				<div class="tnd-fact"><div class="kt-label">Treatment</div><div class="tnd-fact-value tnd-fact-value--muted">Fixed by template</div></div>
				<div class="tnd-fact"><div class="kt-label">Currency</div><div class="tnd-fact-value tnd-fact-value--muted">KES</div></div>
				<div class="kt-field" style="margin: 0"><label for="tnd-tender_security_amount">Amount</label><input id="tnd-tender_security_amount" class="kt-input" inputmode="decimal" v-model="form.tender_security_amount" data-testid="tnd-field-tender_security_amount" @blur="normaliseMoney" /><p v-if="errors.tender_security_amount" class="tnd-field-error" data-testid="tnd-error-tender_security_amount">{{ errors.tender_security_amount }}</p></div>
			</div>
		</div>

		<div class="tnd-section tnd-section--form tnd-section--last">
			<h3 class="kt-card-title tnd-section-title"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>Pre-tender meeting</h3>
			<div class="tnd-seg" role="radiogroup" aria-label="Pre-tender meeting" style="margin-bottom: 16px">
				<label class="tnd-seg-opt"><input type="radio" name="tnd-meeting" :checked="!form.pre_tender_meeting" data-testid="tnd-meeting-no" @change="form.pre_tender_meeting = false" />No</label>
				<label class="tnd-seg-opt"><input type="radio" name="tnd-meeting" :checked="form.pre_tender_meeting" data-testid="tnd-meeting-yes" @change="form.pre_tender_meeting = true" />Yes</label>
			</div>
			<p v-if="errors.pre_tender_meeting" class="tnd-field-error">{{ errors.pre_tender_meeting }}</p>
			<template v-if="form.pre_tender_meeting">
				<div class="tnd-grid-2" style="margin-bottom: 16px">
					<div class="kt-field" style="margin: 0"><label for="tnd-meeting_datetime">Meeting date/time</label><input id="tnd-meeting_datetime" type="datetime-local" class="kt-input" v-model="form.meeting_datetime" data-testid="tnd-field-meeting_datetime" /><p v-if="errors.meeting_datetime" class="tnd-field-error">{{ errors.meeting_datetime }}</p></div>
					<div class="kt-field" style="margin: 0"><label>Meeting mode</label>
						<div class="tnd-seg" role="radiogroup" aria-label="Meeting mode">
							<label class="tnd-seg-opt"><input type="radio" name="tnd-mode" :checked="form.meeting_mode === 'Physical'" data-testid="tnd-mode-physical" @change="form.meeting_mode = 'Physical'" />Physical</label>
							<label class="tnd-seg-opt"><input type="radio" name="tnd-mode" :checked="form.meeting_mode === 'Online'" data-testid="tnd-mode-online" @change="form.meeting_mode = 'Online'" />Online</label>
						</div>
						<p v-if="errors.meeting_mode" class="tnd-field-error">{{ errors.meeting_mode }}</p>
					</div>
				</div>
				<div v-if="form.meeting_mode === 'Physical'" class="kt-field" style="margin: 0"><label for="tnd-meeting_venue">Meeting venue</label>
					<select id="tnd-meeting_venue" class="kt-input" v-model="form.meeting_venue" data-testid="tnd-field-meeting_venue"><option value="">Choose a location</option><option v-for="l in options.delivery_locations || []" :key="l" :value="l">{{ l }}</option></select>
					<p v-if="errors.meeting_venue" class="tnd-field-error">{{ errors.meeting_venue }}</p>
				</div>
				<div v-if="form.meeting_mode === 'Online'" class="kt-field" style="margin: 0"><label for="tnd-online_joining_information">Online joining information</label><input id="tnd-online_joining_information" class="kt-input" maxlength="240" v-model="form.online_joining_information" data-testid="tnd-field-online_joining_information" /><p v-if="errors.online_joining_information" class="tnd-field-error">{{ errors.online_joining_information }}</p></div>
			</template>
		</div>
	</div>
</template>

<script setup>
import { reactive, watch } from "vue";
import { fromInputDateTime, toInputDate, toInputDateTime } from "../data/format.js";

const props = defineProps({
	values: { type: Object, default: () => ({}) },
	options: { type: Object, default: () => ({}) },
	identity: { type: String, default: "" }, // `${tender}:${record_version}` — the only hydration trigger
	errors: { type: Object, default: () => ({}) },
});

const form = reactive({ tender_title: "", issue_date: "", clarification_deadline: "", submission_deadline: "", tender_validity_days: "", tender_security_amount: "", pre_tender_meeting: false, meeting_datetime: "", meeting_mode: "", meeting_venue: "", online_joining_information: "" });
let hydrated = "";
let dirty = false;

function hydrate() {
	const v = props.values || {};
	form.tender_title = v.tender_title || "";
	form.issue_date = toInputDate(v.issue_date);
	form.clarification_deadline = toInputDateTime(v.clarification_deadline);
	form.submission_deadline = toInputDateTime(v.submission_deadline);
	form.tender_validity_days = v.tender_validity_days ?? "";
	form.tender_security_amount = v.tender_security_amount != null ? Number(v.tender_security_amount).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : "";
	form.pre_tender_meeting = !!v.pre_tender_meeting;
	form.meeting_datetime = toInputDateTime(v.meeting_datetime);
	form.meeting_mode = v.meeting_mode || "";
	form.meeting_venue = v.meeting_venue || "";
	form.online_joining_information = v.online_joining_information || "";
	dirty = false;
}
watch(
	() => props.identity,
	(id) => {
		if (id !== hydrated) {
			hydrated = id;
			hydrate();
		}
	},
	{ immediate: true }
);
watch(form, () => {
	dirty = true;
});

function normaliseMoney() {
	const n = Number(String(form.tender_security_amount).replace(/,/g, ""));
	if (!Number.isNaN(n) && form.tender_security_amount !== "") form.tender_security_amount = n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function getPayload() {
	const payload = {
		tender_title: form.tender_title,
		issue_date: form.issue_date,
		clarification_deadline: fromInputDateTime(form.clarification_deadline),
		submission_deadline: fromInputDateTime(form.submission_deadline),
		tender_validity_days: form.tender_validity_days === "" ? null : Number(form.tender_validity_days),
		tender_security_amount: form.tender_security_amount === "" ? null : String(form.tender_security_amount).replace(/,/g, ""),
		pre_tender_meeting: !!form.pre_tender_meeting,
	};
	if (form.pre_tender_meeting) {
		payload.meeting_datetime = fromInputDateTime(form.meeting_datetime);
		payload.meeting_mode = form.meeting_mode;
		if (form.meeting_mode === "Physical") payload.meeting_venue = form.meeting_venue;
		if (form.meeting_mode === "Online") payload.online_joining_information = form.online_joining_information;
	}
	// Blank strings mean "not set yet"; the server's own required-field rule
	// speaks for itself and never receives an empty text to reject as text.
	for (const key of Object.keys(payload)) if (payload[key] === "" || payload[key] === null) delete payload[key];
	return payload;
}
function isDirty() {
	return dirty;
}
defineExpose({ getPayload, isDirty });
</script>
