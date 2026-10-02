<script setup>
// BDS-CHG-001 v0.8 §10.9 BDS-DES-08 — Company, declarations and tender
// security, ported from "Bid Board v3 - C" (1440 tables; 390 labelled cards).
// The task read decides the organisation as copied to the bid, the Tender
// contact, one row per form of the task (its fields open in the response
// drawer), the tender security and the Authorised Signatory. Save and
// continue saves this page's own changes — the security answers and the
// bid's contact — then opens the next task; a refusal is named in place.
import { computed, inject, onMounted, onUnmounted, reactive, ref, watch } from "vue";
import PortalGuidance from "../../../../../../kentender_core/kentender_core/public/js/kt_portal/PortalGuidance.vue";
import CommonState from "../components/CommonState.vue";
import NotifySignatory from "../components/NotifySignatory.vue";
import TaskStepper from "../components/TaskStepper.vue";
import FieldControl from "../components/FieldControl.vue";
import ResponseDrawer from "../components/ResponseDrawer.vue";
import { fixRoute } from "../composables/fixRoute.js";
import { useNarrow } from "../composables/useNarrow.js";
import { arrive, destinationOf } from "../composables/saveDestination.js";

const READ = "kentender_procurement.bid_submission.api.get_bid_task";
const SAVE = "kentender_procurement.bid_submission.api.save_bid_task";
const CONTACT = "kentender_procurement.bid_submission.api.update_tender_contact";
const NOTICE = "kentender_procurement.bid_submission.api.update_tender_notice_contact";
const SNAPSHOT = "kentender_procurement.bid_submission.api.refresh_bid_organisation_snapshot";
const props = defineProps({
	initial: { type: Object, default: null },
	reference: { type: String, required: true },
});
const emit = defineEmits(["not-found"]);
const portal = inject("portal");
const { route, go, epoch } = portal.useRoute({ ref, onMounted, onUnmounted });
const narrow = useNarrow();
// empty until the first take, so the blank form is never read as the person's own entries
const data = ref(null);
// the server says whether this Draft can change now (closed, or its bound
// release withdrawn): read-only fields and no Save and continue otherwise
const canEdit = computed(() => !data.value || !data.value.bid || data.value.bid.editable !== false);
const failure = ref("");
const errors = ref({});
const drawer = ref(null); // the declaration row open in the drawer
const keepBid = ref(false); // Keep bid details: closes the comparison, changes nothing
const security = reactive({});
const contact = reactive({ email: "", phone: "", notice: "", person: "" });
const guard = portal.createSequenceGuard();
const runner = portal.createCommandRunner({ ref }, { onError: (e) => (failure.value = e.message) });
const pending = computed(() => runner.pending.value);
const bid = computed(() => (data.value ? { reference: data.value.bid.reference, record_version: data.value.bid.record_version } : null));
const org = computed(() => (data.value && data.value.organisation) || {});

// Take a read. Entries the person has typed but not saved stay as typed: a
// file command or another save re-reads the page mid-edit.
function adopt(result) {
	const unsaved = data.value ? securityChanges() : {};
	const typed = data.value ? { email: contact.email !== data.value.contact.email ? contact.email : null, phone: contact.phone !== data.value.contact.phone ? contact.phone : null, person: contact.person !== (data.value.contact.person || "") ? contact.person : null } : {};
	data.value = result;
	const fields = (result.tender_security && result.tender_security.fields) || [];
	for (const key of Object.keys(security)) delete security[key];
	for (const f of fields) security[f.handle] = f.handle in unsaved ? unsaved[f.handle] : f.value;
	contact.email = typed.email ?? result.contact.email;
	contact.phone = typed.phone ?? result.contact.phone;
	contact.person = typed.person ?? (result.contact.person || "");
	contact.notice = result.contact.notice ? result.contact.notice.current : "";
}
if (props.initial) adopt(props.initial);

function read() {
	return portal.call(READ, { tender_reference: props.reference, bid_reference: "", task: "company", organisation: route.value.query.organisation || "" });
}
async function load() {
	const token = guard.next();
	try {
		const result = await read();
		if (!guard.isCurrent(token)) return;
		if (result && result.outcome === "NOT_FOUND") {
			emit("not-found");
			return;
		}
		adopt(result);
		failure.value = "";
	} catch (e) {
		if (guard.isCurrent(token)) failure.value = e.message;
	}
}
function visible(field) {
	const rule = field.shown_when;
	if (!rule) return field.visible !== false;
	return rule.handles.some((handle) => rule.values.includes(security[handle]));
}
function securityChanges() {
	const fields = (data.value.tender_security && data.value.tender_security.fields) || [];
	return Object.fromEntries(fields.filter((f) => f.editable && f.kind !== "evidence" && JSON.stringify(security[f.handle]) !== JSON.stringify(f.value)).map((f) => [f.handle, security[f.handle]]));
}
function key(name) {
	return `bds-company-${name}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`;
}
function saveAndContinue() {
	failure.value = "";
	errors.value = {};
	// the caller's own security entries, taken before any re-read replaces the page
	const answers = securityChanges();
	const destination = destinationOf(data.value.footer); // where the label said, before the re-reads below change the footer
	return runner.run(async () => {
		const notice = data.value.contact.notice;
		if (notice && contact.notice && contact.notice !== notice.current) {
			const result = await portal.call(NOTICE, { bidder_arrangement_id: notice.arrangement, notice_contact_id: contact.notice, expected_record_version: notice.record_version, idempotency_key: key("notice") }, { type: "POST" });
			if (!(result && result.ok)) {
				errors.value = (result && result.errors) || {};
				failure.value = result && !result.errors ? result.message || "" : "";
				return;
			}
			adopt(await read()); // typed contact and security entries stay as typed
		}
		const personChanged = !!contact.person && contact.person !== (data.value.contact.person || "");
		if (personChanged || contact.email !== data.value.contact.email || contact.phone !== data.value.contact.phone) {
			const change = { bid_reference: data.value.bid.reference, email: contact.email, phone: contact.phone, expected_record_version: data.value.contact.record_version, idempotency_key: key("contact") };
			if (personChanged) change.assignment_id = contact.person; // §10.9: another person of the organisation
			const result = await portal.call(CONTACT, change, { type: "POST" });
			if (!(result && result.ok)) {
				errors.value = (result && result.errors) || {};
				failure.value = result && !result.errors ? result.message || "" : "";
				return;
			}
			data.value = { ...data.value, contact: { ...data.value.contact, email: contact.email, phone: contact.phone, person: contact.person } }; // saved
			adopt(await read());
			Object.assign(security, answers); // keep what was entered, now against the new version
		}
		if (Object.keys(answers).length) {
			const result = await portal.call(SAVE, { bid_reference: data.value.bid.reference, task: "company", values: JSON.stringify(answers), expected_record_version: data.value.bid.record_version, idempotency_key: key("security") }, { type: "POST" });
			if (!(result && result.ok)) {
				errors.value = (result && result.errors) || {};
				failure.value = result && !result.errors ? result.message || "" : "";
				return;
			}
		}
		await arrive(destination, { go, load });
	}, "Save and continue");
}
function useUpdated() {
	failure.value = "";
	return runner.run(async () => {
		const result = await portal.call(SNAPSHOT, { bid_reference: data.value.bid.reference, confirm: 1, expected_record_version: data.value.organisation.update.record_version, idempotency_key: key("snapshot") }, { type: "POST" });
		if (result && (result.ok || result.refreshed)) adopt(await read());
		else if (result) failure.value = result.message || "";
	}, "Use updated details");
}
async function afterDrawer() {
	drawer.value = null;
	await load();
}
// A file command inside the drawer: re-read, and show the drawer's form as read again.
async function drawerChanged() {
	await load();
	if (drawer.value) drawer.value = data.value.declarations.find((row) => row.key === drawer.value.key) || null;
}
function onFix(fix) {
	const href = fixRoute(fix, props.reference);
	if (href && href !== route.value.path) go(href);
}
watch(epoch, () => load());
onMounted(() => {
	portal.setTitle(__("Company, declarations and tender security"));
	if (!data.value) load();
});
</script>

<template>
	<div v-if="data" class="kt-page" data-testid="bds-company-task">
		<TaskStepper v-if="data.step" :step="data.step" />
		<div class="kt-page-head">
			<div class="bds-head-main">
				<a :href="data.page.back_href" class="bds-back" data-testid="bds-company-back"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 12H5" /><path d="m12 19-7-7 7-7" /></svg>{{ __("Back to bid") }}</a>
				<div class="bds-title-row">
					<h1 class="kt-page-title">{{ __(data.page.title) }}</h1>
					<span class="kt-status" :class="'is-' + data.badge.tone" data-testid="bds-company-badge">{{ data.badge.label }}</span>
				</div>
				<p class="kt-page-desc">{{ __(data.page.description) }}</p>
			</div>
		</div>

		<PortalGuidance :journey="data.journey" :answer="data.next_step" :label="__('Bid journey')" @fix="onFix" />

		<NotifySignatory v-if="data.handover && data.bid" :handover="data.handover" :bid="data.bid" :organisation="route.query.organisation || ''" @sent="load" />

		<div class="kt-region">
			<h2>{{ __("Bidding organisation") }}</h2>
			<div class="bds-region-body">
				<div class="bds-facts" data-testid="bds-company-facts">
					<div v-for="fact in org.facts" :key="fact.label" class="bds-fact"><span class="kt-label">{{ fact.label }}</span><span class="bds-fact-value">{{ fact.value }}</span></div>
				</div>
				<table v-if="org.members && !narrow" class="kt-table" data-testid="bds-company-members">
					<thead><tr><th>{{ __("Organisation") }}</th><th>{{ __("Role") }}</th><th>{{ __("Account") }}</th></tr></thead>
					<tbody><tr v-for="m in org.members" :key="m.name"><td class="bds-strong">{{ m.name }}</td><td>{{ m.role }}</td><td><span class="kt-status is-live">{{ m.status }}</span></td></tr></tbody>
				</table>
				<div v-else-if="org.members" data-testid="bds-company-members-cards">
					<div v-for="m in org.members" :key="m.name" class="bds-card"><div class="bds-card-title">{{ m.name }}</div><div class="bds-card-fact"><span class="kt-label">{{ __("Role") }}</span><span>{{ m.role }}</span></div></div>
				</div>
				<div class="bds-snapshot-line">
					<span class="kt-label">{{ org.snapshot_text }}</span>
					<span v-if="org.current_text" class="bds-muted">{{ org.current_text }}</span>
					<a :href="org.update_account_href">{{ __("Update Account") }}</a>
				</div>
				<div v-if="org.update && !keepBid" class="kt-group bds-account-update" data-testid="bds-account-update">
					<span class="bds-strong">{{ __("Updated Account details are available") }}</span>
					<table v-if="!narrow" class="kt-table">
						<thead><tr><th>{{ org.update.fact }}</th><th>{{ __("Value") }}</th></tr></thead>
						<tbody><tr v-for="row in org.update.rows" :key="row.label"><td>{{ row.label }}</td><td>{{ row.value }}</td></tr></tbody>
					</table>
					<div v-else>
						<div v-for="row in org.update.rows" :key="row.label" class="bds-card"><div class="bds-card-title">{{ row.label }}</div><div class="bds-card-fact"><span class="kt-label">{{ __("Value") }}</span><span>{{ row.value }}</span></div></div>
					</div>
					<div class="bds-row-actions">
						<button type="button" class="kt-btn kt-btn-secondary" :disabled="pending" data-testid="bds-use-updated" @click="useUpdated">{{ __("Use updated details") }}</button>
						<button type="button" class="kt-btn kt-btn-ghost" :disabled="pending" data-testid="bds-keep-bid" @click="keepBid = true">{{ __("Keep bid details") }}</button>
					</div>
					<p class="bds-muted">{{ org.update.note }}</p>
				</div>
			</div>
		</div>

		<div class="kt-region">
			<h2>{{ __("Tender contact") }}</h2>
			<div class="bds-region-body">
				<div class="bds-grid-2">
					<div class="kt-field">
						<label for="bds-contact-person">{{ __("Assigned person") }}</label>
						<select v-if="data.contact.people && data.contact.people.length > 1 && canEdit" id="bds-contact-person" v-model="contact.person" class="kt-input" :aria-invalid="!!errors.assignment_id" data-testid="bds-contact-person">
							<option v-for="p in data.contact.people" :key="p.assignment_id" :value="p.assignment_id">{{ p.name }}</option>
						</select>
						<select v-else id="bds-contact-person" class="kt-input" disabled><option>{{ data.contact.assigned }}</option></select>
						<p v-if="errors.assignment_id" class="kt-field-error">{{ errors.assignment_id }}</p>
					</div>
					<div class="kt-field">
						<label for="bds-contact-notice">{{ __("Tender notice email") }}</label>
						<div class="bds-inline-status">
							<select v-if="data.contact.notice && data.contact.notice.options.length" id="bds-contact-notice" v-model="contact.notice" class="kt-input" :aria-invalid="!!errors.notice_contact_id" data-testid="bds-contact-notice">
								<option v-for="o in data.contact.notice.options" :key="o.contact_id" :value="o.contact_id">{{ o.value }}</option>
							</select>
							<select v-else id="bds-contact-notice" class="kt-input" disabled><option>{{ data.contact.notice_email }}</option></select>
							<span v-if="data.contact.notice_verified" class="kt-status is-live">{{ __("Verified") }}</span>
						</div>
						<p v-if="errors.notice_contact_id" class="kt-field-error">{{ errors.notice_contact_id }}</p>
						<p v-else class="bds-help">{{ data.contact.notice_help }}</p>
					</div>
					<div class="kt-field">
						<label for="bds-contact-email">{{ __("Email") }}</label>
						<input id="bds-contact-email" v-model="contact.email" class="kt-input" type="email" :aria-invalid="!!errors.email" data-testid="bds-contact-email" />
						<p v-if="errors.email" class="kt-field-error">{{ errors.email }}</p>
					</div>
					<div class="kt-field">
						<label for="bds-contact-phone">{{ __("Phone") }}</label>
						<input id="bds-contact-phone" v-model="contact.phone" class="kt-input" type="tel" :aria-invalid="!!errors.phone" data-testid="bds-contact-phone" />
						<p v-if="errors.phone" class="kt-field-error">{{ errors.phone }}</p>
					</div>
				</div>
				<p class="bds-muted">{{ data.contact.note }}</p>
			</div>
		</div>

		<div class="kt-region">
			<h2>{{ __("Declarations") }}</h2>
			<div class="bds-region-body">
				<table v-if="!narrow" class="kt-table" data-testid="bds-declarations-table">
					<thead><tr><th>{{ __("Declaration") }}</th><th>{{ __("Status") }}</th><th>{{ __("Action") }}</th></tr></thead>
					<tbody>
						<tr v-for="row in data.declarations" :key="row.key" :data-testid="'bds-declaration-' + row.key">
							<td class="bds-strong">{{ row.label }}</td>
							<td><span class="kt-status" :class="'is-' + row.tone">{{ row.status }}</span><div v-if="row.confirmed_text" class="kt-label bds-confirmed">{{ row.confirmed_text }}</div></td>
							<td><button type="button" class="bds-link-button" @click="drawer = row">{{ __("View declaration") }}</button></td>
						</tr>
					</tbody>
				</table>
				<div v-else data-testid="bds-declarations-cards">
					<div v-for="row in data.declarations" :key="row.key" class="bds-card" :data-testid="'bds-declaration-' + row.key">
						<div class="bds-card-title">{{ row.label }}</div>
						<div class="bds-card-fact"><span class="kt-label">{{ __("Status") }}</span><span><span class="kt-status" :class="'is-' + row.tone">{{ row.status }}</span></span></div>
						<div class="bds-card-actions"><button type="button" class="bds-link-button" @click="drawer = row">{{ __("View declaration") }}</button></div>
					</div>
				</div>
			</div>
		</div>

		<div v-if="data.tender_security" class="kt-region">
			<h2>{{ __("Tender security") }}</h2>
			<div class="bds-region-body">
				<p v-if="!data.tender_security.entered" class="bds-muted" data-testid="bds-security-empty">{{ __("Tender security has not been entered for this bid.") }}</p>
				<div class="bds-grid-2">
					<template v-for="field in data.tender_security.fields" :key="field.handle">
						<FieldControl v-if="field.kind !== 'evidence' && visible(field)" v-model="security[field.handle]" :field="field" :error="errors[field.handle] || ''" :bid="bid" id-prefix="bds-security" @changed="load" />
					</template>
				</div>
				<div class="bds-facts">
					<div v-for="fact in data.tender_security.published_facts" :key="fact.label" class="bds-fact"><span class="kt-label">{{ fact.label }}</span><span class="bds-fact-value">{{ fact.value }}</span></div>
				</div>
				<template v-for="field in data.tender_security.fields" :key="'proof-' + field.handle">
					<FieldControl v-if="field.kind === 'evidence' && visible(field)" :model-value="field.value" :field="field" :error="errors[field.handle] || ''" :bid="bid" id-prefix="bds-security" @changed="load" />
				</template>
				<div v-if="data.tender_security.physical" class="kt-notice" :class="data.tender_security.physical.tone === 'live' ? 'is-live' : 'is-warning'" role="status" data-testid="bds-security-physical">
					<svg class="kt-notice-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 8h.01M11 12h1v5h1" /></svg>
					<div class="kt-notice-body">
						<strong>{{ data.tender_security.physical.title }}</strong>
						<div v-if="data.tender_security.physical.text" class="bds-notice-text">{{ data.tender_security.physical.text }}</div>
						<div v-if="data.tender_security.physical.facts.length" class="bds-notice-facts">
							<div v-for="fact in data.tender_security.physical.facts" :key="fact.label" class="bds-drawer-fact"><span class="kt-label">{{ fact.label }}</span><span>{{ fact.value }}</span></div>
						</div>
					</div>
				</div>
			</div>
		</div>

		<div v-if="data.signatory" class="kt-region">
			<h2>{{ __("Authorised Signatory") }}</h2>
			<div class="bds-region-body">
				<div class="bds-facts" data-testid="bds-company-signatory">
					<div class="bds-fact"><span class="kt-label">{{ __("Authorised Signatory") }}</span><span class="bds-fact-value">{{ data.signatory.name }}</span></div>
					<div v-if="data.signatory.organisation" class="bds-fact"><span class="kt-label">{{ __("Organisation") }}</span><span class="bds-fact-value">{{ data.signatory.organisation }}</span></div>
					<div v-if="data.signatory.job_title" class="bds-fact"><span class="kt-label">{{ __("Job title") }}</span><span class="bds-fact-value">{{ data.signatory.job_title }}</span></div>
					<div v-if="data.signatory.authority_href" class="bds-fact"><span class="kt-label">{{ __("Authority evidence") }}</span><span class="bds-fact-value"><a :href="data.signatory.authority_href" target="_blank" rel="noopener">{{ __("View") }}</a></span></div>
					<div v-if="data.signatory.certificate" class="bds-fact"><span class="kt-label">{{ __("Digital certificate") }}</span><span class="bds-fact-value"><span class="kt-status" :class="'is-' + data.signatory.certificate.tone">{{ data.signatory.certificate.status }}</span></span></div>
				</div>
				<p v-if="data.signatory.certificate_note" class="bds-muted" data-testid="bds-signatory-certificate-note">{{ data.signatory.certificate_note }}</p>
				<p v-if="data.signatory.change_note" class="bds-muted" data-testid="bds-signatory-change-note">{{ data.signatory.change_note }}<template v-if="data.signatory.change_href"> <a :href="data.signatory.change_href">{{ __("Open Account") }}</a></template></p>
			</div>
		</div>

		<div v-if="failure" class="kt-notice is-critical bds-load-failure" role="alert" data-testid="bds-load-failure"><div class="kt-notice-body">{{ failure }}</div></div>

		<div v-if="narrow" class="bds-footer-stack">
			<button v-if="canEdit" type="button" class="kt-btn kt-btn-primary bds-btn-block" :disabled="pending" data-testid="bds-company-save" @click="saveAndContinue">{{ pending ? __("Saving…") : __(data.footer.save_label) }}</button>
			<a :href="data.page.back_href" class="kt-btn kt-btn-secondary bds-btn-block">{{ __("Back to bid") }}</a>
		</div>
		<div v-else class="bds-footer">
			<a :href="data.page.back_href" class="kt-btn kt-btn-secondary">{{ __("Back to bid") }}</a>
			<div class="bds-footer-end"><button v-if="canEdit" type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="bds-company-save" @click="saveAndContinue">{{ pending ? __("Saving…") : __(data.footer.save_label) }}</button></div>
		</div>

		<ResponseDrawer v-if="drawer" :group="drawer" task="company" :bid="bid" @close="drawer = null" @saved="afterDrawer" @changed="drawerChanged" />
	</div>
	<CommonState v-else-if="failure" state="load-failure" @action="load" />
	<div v-else class="kt-page" aria-hidden="true"><div class="bds-skeleton" data-testid="bds-company-loading"></div></div>
</template>
