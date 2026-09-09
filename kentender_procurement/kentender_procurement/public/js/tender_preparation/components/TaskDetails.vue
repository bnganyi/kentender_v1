<!-- TPR-DES-03 · Task 1 — Tender details (§8.1, §13.5). "Read-only context"
     as kt-label + value pairs (never inputs), the Strategic Objective / plan
     horizon row with its "Internal only — never rendered to bidders" tag;
     "Officer controls" with exactly the §8.1 controls: text, date/datetime,
     integer, currency, the Yes/No switch and its conditional meeting fields.
     Template-fixed values render as disabled inputs, as the artboard does. -->
<template>
	<div>
		<div class="tpr-section">
			<div class="kt-card-title">Read-only context</div>
			<div class="tpr-grid-3">
				<div class="tpr-ro-field"><span class="kt-label">Plan Item and Requisition</span><span class="tpr-ro-val">{{ inherited.plan_item_id }} · {{ inherited.requisition_reference }}</span></div>
				<div class="tpr-ro-field"><span class="kt-label">Requirement title</span><span class="tpr-ro-val">{{ inherited.requirement_title }}</span></div>
				<div class="tpr-ro-field"><span class="kt-label">Procurement method</span><span class="tpr-ro-val">{{ inherited.planned_method }}</span></div>
				<div class="tpr-ro-field"><span class="kt-label">Authorised value (internal only)</span><span class="tpr-ro-val">{{ inherited.authorised_value }}</span></div>
				<div class="tpr-ro-field"><span class="kt-label">Latest delivery date</span><span class="tpr-ro-val">{{ inherited.latest_delivery_date }}</span></div>
				<div class="tpr-ro-field"><span class="kt-label">Requirement summary</span><span class="tpr-ro-val">{{ summary }}</span></div>
				<div class="tpr-ro-field"><span class="kt-label">Template</span><span class="tpr-ro-val">{{ binding.template_label }}</span></div>
				<div class="tpr-ro-field"><span class="kt-label">Tender reference</span><span class="tpr-ro-val">{{ generated.tender_reference }}</span></div>
				<div class="tpr-ro-field"><span class="kt-label">Opening date/time</span><span class="tpr-ro-val">{{ generated.opening_datetime || "Generated equal to the submission deadline" }}</span></div>
				<div class="tpr-ro-field"><span class="kt-label">Reservation category</span><span class="tpr-ro-val">{{ inherited.reservation_category }}</span></div>
				<div class="tpr-ro-field tpr-span-2" data-testid="tpr-internal-context">
					<span class="kt-label">Strategic Objective / plan horizon <span class="tpr-tag is-outline" style="margin-left: 6px">Internal only — never rendered to bidders</span></span>
					<span class="tpr-ro-val">{{ internalLine }}</span>
				</div>
			</div>
		</div>
		<div class="tpr-section">
			<div class="kt-card-title">Officer controls</div>
			<div class="tpr-grid-3">
				<div class="tpr-field"><label for="tpr-tender-title">Tender title</label><input id="tpr-tender-title" class="kt-input" maxlength="160" :value="form.tender_title" :disabled="!editable" @input="set('tender_title', $event.target.value)" /><p v-if="errors.tender_title" class="tpr-field-error">{{ errors.tender_title }}</p></div>
				<div class="tpr-field"><label for="tpr-issue-date">Issue date</label><div class="tpr-date-field"><input id="tpr-issue-date" type="date" class="kt-input" :value="form.issue_date" :disabled="!editable" @input="set('issue_date', $event.target.value)" /><CalendarIcon /></div><p v-if="errors.issue_date" class="tpr-field-error">{{ errors.issue_date }}</p></div>
				<div class="tpr-field"><label for="tpr-clarification">Clarification deadline</label><div class="tpr-date-field"><input id="tpr-clarification" type="datetime-local" class="kt-input" :value="form.clarification_deadline" :disabled="!editable" @input="set('clarification_deadline', $event.target.value)" /><CalendarIcon /></div><p v-if="errors.clarification_deadline" class="tpr-field-error">{{ errors.clarification_deadline }}</p></div>
				<div class="tpr-field"><label for="tpr-submission">Submission deadline</label><div class="tpr-date-field"><input id="tpr-submission" type="datetime-local" class="kt-input" :value="form.submission_deadline" :disabled="!editable" @input="set('submission_deadline', $event.target.value)" /><CalendarIcon /></div><p v-if="errors.submission_deadline" class="tpr-field-error">{{ errors.submission_deadline }}</p></div>
				<div class="tpr-field"><label for="tpr-validity">Tender validity (days)</label><input id="tpr-validity" type="number" min="1" max="365" class="kt-input" :value="form.tender_validity_days" :disabled="!editable" @input="set('tender_validity_days', $event.target.value)" /><p v-if="errors.tender_validity_days" class="tpr-field-error">{{ errors.tender_validity_days }}</p></div>
				<div class="tpr-field"><label>Tender security treatment</label><input class="kt-input" :value="generated.tender_security_treatment" disabled /></div>
				<div class="tpr-field"><label>Tender security currency</label><input class="kt-input" :value="generated.tender_security_currency" disabled /></div>
				<div class="tpr-field"><label for="tpr-security">Tender security amount</label><input id="tpr-security" type="number" min="0" step="0.01" class="kt-input" :value="form.tender_security_amount" :disabled="!editable" @input="set('tender_security_amount', $event.target.value)" /><p v-if="errors.tender_security_amount" class="tpr-field-error">{{ errors.tender_security_amount }}</p></div>
				<div class="tpr-field"><label>Pre-tender meeting</label><SegControl name="tpr-meeting" label="Pre-tender meeting" :model-value="form.pre_tender_meeting" :disabled="!editable" @update:model-value="set('pre_tender_meeting', $event)" /><p v-if="errors.pre_tender_meeting" class="tpr-field-error">{{ errors.pre_tender_meeting }}</p></div>
				<template v-if="form.pre_tender_meeting">
					<div class="tpr-field"><label for="tpr-meeting-dt">Meeting date/time</label><div class="tpr-date-field"><input id="tpr-meeting-dt" type="datetime-local" class="kt-input" :value="form.meeting_datetime" :disabled="!editable" @input="set('meeting_datetime', $event.target.value)" /><CalendarIcon /></div><p v-if="errors.meeting_datetime" class="tpr-field-error">{{ errors.meeting_datetime }}</p></div>
					<div class="tpr-field"><label>Meeting mode</label><SegControl name="tpr-meeting-mode" label="Meeting mode" :options="['Physical', 'Online']" :model-value="form.meeting_mode" :disabled="!editable" @update:model-value="set('meeting_mode', $event)" /><p v-if="errors.meeting_mode" class="tpr-field-error">{{ errors.meeting_mode }}</p></div>
					<div v-if="form.meeting_mode === 'Physical'" class="tpr-field"><label for="tpr-venue">Meeting venue</label><select id="tpr-venue" class="kt-input" :value="form.meeting_venue || ''" :disabled="!editable" @change="set('meeting_venue', $event.target.value)"><option value="">Select an Active location</option><option v-for="o in options.delivery_locations || []" :key="o.value" :value="o.value">{{ o.label }}</option></select><p v-if="errors.meeting_venue" class="tpr-field-error">{{ errors.meeting_venue }}</p></div>
					<div v-if="form.meeting_mode === 'Online'" class="tpr-field tpr-span-2"><label for="tpr-joining">Online joining information</label><input id="tpr-joining" class="kt-input" maxlength="240" :value="form.online_joining_information" :disabled="!editable" @input="set('online_joining_information', $event.target.value)" /><p v-if="errors.online_joining_information" class="tpr-field-error">{{ errors.online_joining_information }}</p></div>
				</template>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, h, reactive, watch } from "vue";
import SegControl from "./SegControl.vue";
import { fromInputDateTime, toInputDate, toInputDateTime } from "../data/format.js";

const CalendarIcon = () =>
	h("svg", { width: 15, height: 15, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": "1.5", "aria-hidden": "true" }, [
		h("rect", { x: 3, y: 4, width: 18, height: 18, rx: 2 }), h("path", { d: "M16 2v4" }), h("path", { d: "M8 2v4" }), h("path", { d: "M3 10h18" }),
	]);

const props = defineProps({ editor: { type: Object, default: () => ({}) }, errors: { type: Object, default: () => ({}) }, editable: { type: Boolean, default: true } });
const inherited = computed(() => props.editor.inherited || {});
const binding = computed(() => props.editor.binding || {});
const generated = computed(() => props.editor.generated || {});
const options = computed(() => props.editor.options || {});
const FIELDS = ["tender_title", "issue_date", "clarification_deadline", "submission_deadline", "tender_validity_days", "tender_security_amount", "pre_tender_meeting", "meeting_datetime", "meeting_mode", "meeting_venue", "online_joining_information"];
const form = reactive({});
const dirty = new Set();

function hydrate() {
	const v = props.editor.officer_values || {};
	for (const f of FIELDS) {
		if (dirty.has(f)) continue;
		let value = v[f];
		if (f === "issue_date") value = toInputDate(value);
		if (["clarification_deadline", "submission_deadline", "meeting_datetime"].includes(f)) value = toInputDateTime(value);
		if (f === "pre_tender_meeting") value = value === null || value === undefined ? false : !!value;
		form[f] = value === undefined ? null : value;
	}
}
// Re-hydrate only when the record identity or version changes — never from an
// in-place refresh that carries nothing new (AGENTS.md §6.4).
watch(() => [(props.editor.tender || {}).tender, (props.editor.tender || {}).record_version], () => { dirty.clear(); hydrate(); }, { immediate: true });

function set(field, value) {
	dirty.add(field);
	form[field] = value;
}

const summary = computed(() => {
	const c = inherited.value.counts || {};
	return `${c.items || 0} item${c.items === 1 ? "" : "s"} · ${c.technical_requirements || 0} technical rows · ${c.related_services || 0} services · ${c.acceptance_requirements || 0} acceptance rows · ${c.supporting_materials || 0} materials`;
});
const internalLine = computed(() => {
	const i = inherited.value.internal_context || {};
	const horizon = i.plan_horizon ? (i.multi_year_justification ? `${i.plan_horizon} — ${i.multi_year_justification}` : i.plan_horizon) : "";
	return [i.strategic_objective_path, horizon].filter(Boolean).join(" · ") || "—";
});

function getPayload() {
	const out = {};
	for (const f of dirty) {
		let value = form[f];
		if (["clarification_deadline", "submission_deadline", "meeting_datetime"].includes(f)) value = fromInputDateTime(value);
		if (["tender_validity_days"].includes(f) && value !== "" && value !== null) value = Number(value);
		if (["tender_security_amount"].includes(f) && value !== "" && value !== null) value = Number(value);
		out[f] = value === "" ? null : value;
	}
	return out;
}
defineExpose({ getPayload });
</script>
