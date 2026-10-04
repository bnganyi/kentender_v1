<script setup>
// BDS-CHG-001 v0.8 §10.5 BDS-DES-04 (and -ATTENTION, -VERIFY, -SUSPENDED),
// ported from "Bid Board v3 - A" (1440 tables; 390 labelled cards). The
// `GetSupplierAccount` read decides the status, the actions this person may
// take, the next step and the journey; nothing here derives them. A person
// with several organisations names one per request (`?organisation=`).
// A suspended Account keeps its facts and receipts and offers no way to
// reactivate itself.
import { computed, inject, onMounted, onUnmounted, ref, watch } from "vue";
import PortalGuidance from "../../../../../../kentender_core/kentender_core/public/js/kt_portal/PortalGuidance.vue";
import { useNarrow } from "../../../../../../kentender_core/kentender_core/public/js/kt_portal/useNarrow.js";
import AddEvidenceDialog from "../components/AddEvidenceDialog.vue";
import AddPersonDialog from "../components/AddPersonDialog.vue";
import EditBusinessProfileDialog from "../components/EditBusinessProfileDialog.vue";
import EditOrganisationDialog from "../components/EditOrganisationDialog.vue";
import ViewPersonDialog from "../components/ViewPersonDialog.vue";

const READ = "kentender_suppliers.supplier_accounts.api.get_supplier_account";
const RESEND = "kentender_suppliers.supplier_accounts.api.send_account_verification";
const DOWNLOAD = "/api/method/kentender_suppliers.supplier_accounts.api.download_account_evidence";
// the profile facts each structure shows (the owners tables are shown separately)
const PROFILE_FACTS = {
	"Sole proprietor": [["sole_proprietor_name", "Name in full"], ["sole_proprietor_age", "Age"], ["sole_proprietor_nationality", "Nationality"], ["sole_proprietor_country_of_origin", "Country of origin"], ["sole_proprietor_citizenship", "Citizenship"]],
	Partnership: [],
	"Registered company": [["company_type", "Company type"], ["nominal_capital", "Nominal capital (KES)"], ["issued_capital", "Issued capital (KES)"]],
};
const PROFILE_COMMON = [["trade_licence_number", "Trade licence number"], ["trade_licence_expiry", "Trade licence expiry"], ["maximum_business_value", "Maximum value of business (KES)"], ["state_owned", "State-owned"], ["year_of_registration", "Year of registration"]];
const FACTS = [
	["legal_name", "Legal name"], ["country", "Country"], ["registration_number", "Registration number"], ["tax_identifier", "KRA PIN"],
	["registered_address", "Registered address"], ["official_email", "Official email"], ["official_phone", "Official phone"],
];
const props = defineProps({ initial: { type: Object, default: null } });
const emit = defineEmits(["no-account"]);
const portal = inject("portal");
const { route, epoch } = portal.useRoute({ ref, onMounted, onUnmounted });
const narrow = useNarrow();
const data = ref(props.initial);
const failure = ref("");
const notFound = ref(false);
const message = ref("");
const dialog = ref(null); // { kind, focus?, person? }
const guard = portal.createSequenceGuard();
const runner = portal.createCommandRunner({ ref }, { onError: (e) => (failure.value = e.message) });
const pending = computed(() => runner.pending.value);

const org = computed(() => (data.value && data.value.organisation) || {});
const allowed = computed(() => new Set((data.value && data.value.allowed_actions) || []));
const status = computed(() => (data.value && data.value.status) || null);
const profile = computed(() => (data.value && data.value.business_profile) || null);
const profileValues = computed(() => (profile.value && profile.value.values) || {});
const profileFacts = computed(() => [{ key: "business_structure", label: "Business structure" }, ...(PROFILE_FACTS[profileValues.value.business_structure] || []).map(([key, label]) => ({ key, label })), ...PROFILE_COMMON.map(([key, label]) => ({ key, label }))]);
const owners = computed(() => (profileValues.value.business_structure === "Partnership" ? "partners" : profileValues.value.business_structure === "Registered company" ? "directors" : ""));
const choosing = computed(() => data.value && data.value.state === "choose_organisation");

function statusClass(value) {
	// row severity for the read's own status words (a leaf marker, not a derivation)
	return ["Available", "Verified"].includes(value) ? "is-live" : ["Expired", "Removed", "Rejected"].includes(value) ? "is-critical" : "is-attention";
}
function evidenceHref(row) {
	return `${DOWNLOAD}?organisation=${encodeURIComponent(org.value.organisation)}&evidence=${encodeURIComponent(row.evidence)}&inline=1`;
}
async function load() {
	const token = guard.next();
	try {
		const result = await portal.call(READ, { organisation: route.value.query.organisation || "" });
		if (!guard.isCurrent(token)) return;
		if (result && result.outcome === "NOT_FOUND") {
			notFound.value = true;
			return;
		}
		if (result && result.state === "no_account") {
			emit("no-account");
			return;
		}
		data.value = result;
		notFound.value = false;
		failure.value = "";
	} catch (e) {
		if (guard.isCurrent(token)) failure.value = e.message;
	}
}
function resend() {
	message.value = "";
	return runner.run(async () => {
		const result = await portal.call(RESEND, { organisation: org.value.organisation, idempotency_key: `acc-resend-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}` }, { type: "POST" });
		message.value = result && result.message ? result.message : result && result.sent_to ? __("We sent a new verification link to {0}.", [result.sent_to]) : "";
	}, "Resend verification link");
}
function onFix(fix) {
	if (fix.fix_id === "send_account_verification") return resend();
	if (String(fix.fix_id).startsWith("edit_organisation")) dialog.value = { kind: "edit", focus: fix.target || "" };
	if (String(fix.fix_id).startsWith("edit_business_profile")) dialog.value = { kind: "profile", focus: fix.target || "" };
}
async function saved(result) {
	dialog.value = null;
	message.value = result && result.verification_sent_to ? __("We sent a verification link to {0}.", [result.verification_sent_to]) : "";
	await load();
}
watch(epoch, () => load());
onMounted(() => {
	portal.setTitle(__("Account"));
	if (!data.value || data.value.outcome !== "OK") load();
});
</script>

<template>
	<div v-if="notFound" class="kt-page" data-testid="acc-not-found">
		<div class="kt-page-head"><div><h1 class="kt-page-title">{{ __("Account not found") }}</h1><p class="kt-page-desc">{{ __("This supplier account is unavailable or you do not have permission to view it.") }}</p></div></div>
	</div>

	<div v-else-if="choosing" class="kt-page" data-testid="acc-choose">
		<div class="kt-page-head"><div><h1 class="kt-page-title">{{ __("Account") }}</h1><p class="kt-page-desc">{{ __("Choose the organisation to manage.") }}</p></div></div>
		<div class="kt-region">
			<h2>{{ __("Your organisations") }}</h2>
			<ul class="acc-choose-list">
				<li v-for="o in data.organisations" :key="o.organisation"><a :href="`/account?organisation=${encodeURIComponent(o.organisation)}`" @click.prevent="portal.go(`/account?organisation=${encodeURIComponent(o.organisation)}`)">{{ o.legal_name }}</a></li>
			</ul>
		</div>
	</div>

	<div v-else-if="data && data.organisation" class="kt-page" data-testid="acc-account">
		<div class="kt-page-head" :class="{ 'acc-head-stack': narrow }">
			<div class="acc-head-main">
				<div class="acc-title-row">
					<h1 class="kt-page-title">{{ __("Account") }}</h1>
					<span v-if="status" class="kt-status" :class="`is-${status.tone}`" data-testid="acc-status">{{ __(status.label) }}</span>
				</div>
				<div class="acc-legal-name">{{ org.legal_name }}</div>
				<p class="kt-page-desc">{{ __("Manage the organisation information and people used for bids.") }}</p>
			</div>
			<div v-if="allowed.has('edit_organisation')" class="kt-page-actions" :class="{ 'acc-actions-stack': narrow }">
				<button v-if="allowed.has('send_account_verification')" type="button" class="kt-btn kt-btn-secondary" :class="{ 'acc-btn-block': narrow }" :disabled="pending" data-testid="acc-resend" @click="resend">{{ __("Resend verification link") }}</button>
				<button type="button" class="kt-btn kt-btn-primary" :class="{ 'acc-btn-block': narrow }" data-testid="acc-edit" @click="dialog = { kind: 'edit' }">{{ __("Edit organisation") }}</button>
			</div>
		</div>

		<PortalGuidance :journey="data.journey" :answer="data.next_step" :label="__('Supplier account journey')" :pending="pending" @fix="onFix" />
		<div v-if="data.links && data.links.length" class="acc-links" data-testid="acc-links">
			<a v-for="link in data.links" :key="link.key" :href="link.href">{{ __(link.label) }}</a>
		</div>

		<div v-if="failure" class="kt-notice is-critical acc-load-failure" role="alert">
			<div class="kt-notice-body">{{ failure }}</div>
			<button type="button" class="kt-btn kt-btn-secondary" @click="load">{{ __("Try again") }}</button>
		</div>
		<p v-if="message" class="acc-muted" role="status" data-testid="acc-message">{{ message }}</p>

		<div class="kt-region">
			<h2>{{ __("Organisation") }}</h2>
			<div class="acc-region-body">
				<div class="acc-facts">
					<div v-for="[key, label] in FACTS" :key="key" class="acc-fact"><span class="kt-label">{{ __(label) }}</span><span class="acc-fact-value">{{ org[key] || "—" }}</span></div>
				</div>
			</div>
		</div>

		<div v-if="profile" class="kt-region" data-testid="acc-profile">
			<h2>{{ __("Business profile") }}</h2>
			<div class="acc-region-body">
				<div class="acc-facts">
					<div v-for="f in profileFacts" :key="f.key" class="acc-fact"><span class="kt-label">{{ __(f.label) }}</span><span class="acc-fact-value" :data-testid="`acc-profile-fact-${f.key}`">{{ profileValues[f.key] || "—" }}</span></div>
				</div>
				<template v-if="owners && profileValues[owners].length">
					<table v-if="!narrow" class="kt-table acc-owners" :data-testid="`acc-profile-${owners}-table`">
						<caption class="kt-label">{{ owners === "partners" ? __("Partners") : __("Directors") }}</caption>
						<thead><tr><th>{{ __("Name") }}</th><th>{{ __("Nationality") }}</th><th>{{ __("Citizenship") }}</th><th>{{ __("Shares owned (%)") }}</th></tr></thead>
						<tbody><tr v-for="(r, i) in profileValues[owners]" :key="i"><td class="acc-strong">{{ r.name }}</td><td>{{ r.nationality }}</td><td>{{ r.citizenship }}</td><td>{{ r.shares }}</td></tr></tbody>
					</table>
					<div v-else :data-testid="`acc-profile-${owners}-cards`">
						<div class="kt-label">{{ owners === "partners" ? __("Partners") : __("Directors") }}</div>
						<div v-for="(r, i) in profileValues[owners]" :key="i" class="acc-card">
							<div class="acc-card-title">{{ r.name }}</div>
							<div class="acc-card-fact"><span class="kt-label">{{ __("Nationality") }}</span><span>{{ r.nationality }}</span></div>
							<div class="acc-card-fact"><span class="kt-label">{{ __("Citizenship") }}</span><span>{{ r.citizenship }}</span></div>
							<div class="acc-card-fact"><span class="kt-label">{{ __("Shares owned (%)") }}</span><span>{{ r.shares }}</span></div>
						</div>
					</div>
				</template>
				<p v-if="profile.missing.length" class="acc-muted" data-testid="acc-profile-missing">{{ __("Still needed: {0}.", [profile.missing.map((m) => m.text.toLowerCase()).join("; ")]) }}</p>
				<p class="acc-muted">{{ __("A bid copies these facts when you start it. Changing them here does not change a bid already prepared until you choose to refresh it.") }}</p>
				<div v-if="allowed.has('edit_business_profile')">
					<button type="button" class="kt-btn kt-btn-secondary" :class="{ 'acc-btn-touch': narrow }" data-testid="acc-edit-profile" @click="dialog = { kind: 'profile' }">{{ __("Edit business profile") }}</button>
				</div>
			</div>
		</div>

		<div class="kt-region">
			<h2>{{ __("People") }}</h2>
			<div class="acc-region-body">
				<table v-if="!narrow" class="kt-table" data-testid="acc-people">
					<thead><tr><th>{{ __("Person") }}</th><th>{{ __("Responsibility") }}</th><th>{{ __("Effective period") }}</th><th>{{ __("Action") }}</th></tr></thead>
					<tbody>
						<tr v-for="p in data.people" :key="p.assignment">
							<td class="acc-strong">{{ p.person }}<div v-if="p.job_title" class="kt-label acc-strong">{{ p.job_title }}</div></td>
							<td>{{ p.responsibility }}</td>
							<td>{{ p.effective_period }}</td>
							<td><a href="#" @click.prevent="dialog = { kind: 'person', person: p }">{{ __("View") }}</a></td>
						</tr>
					</tbody>
				</table>
				<div v-else data-testid="acc-people-cards">
					<div v-for="p in data.people" :key="p.assignment" class="acc-card">
						<div class="acc-card-title">{{ p.person }}<div v-if="p.job_title" class="kt-label acc-strong">{{ p.job_title }}</div></div>
						<div class="acc-card-fact"><span class="kt-label">{{ __("Responsibility") }}</span><span>{{ p.responsibility }}</span></div>
						<div class="acc-card-fact"><span class="kt-label">{{ __("Effective period") }}</span><span>{{ p.effective_period }}</span></div>
						<div class="acc-card-actions"><a href="#" @click.prevent="dialog = { kind: 'person', person: p }">{{ __("View") }}</a></div>
					</div>
				</div>
				<div v-if="allowed.has('add_person')">
					<button type="button" class="kt-btn kt-btn-secondary" :class="{ 'acc-btn-touch': narrow }" data-testid="acc-add-person" @click="dialog = { kind: 'add-person' }">
						<span class="acc-btn-icon"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 5v14M5 12h14" /></svg>{{ __("Add person") }}</span>
					</button>
				</div>
			</div>
		</div>

		<div class="kt-region">
			<h2>{{ __("Reusable evidence") }}</h2>
			<div class="acc-region-body">
				<template v-if="data.evidence.length">
					<table v-if="!narrow" class="kt-table" data-testid="acc-evidence">
						<thead><tr><th>{{ __("Evidence") }}</th><th>{{ __("Reference") }}</th><th>{{ __("Valid until") }}</th><th>{{ __("Status") }}</th><th>{{ __("Action") }}</th></tr></thead>
						<tbody>
							<tr v-for="e in data.evidence" :key="e.evidence">
								<td class="acc-strong">{{ e.label }}</td>
								<td>{{ e.reference || "—" }}</td>
								<td>{{ e.valid_until }}</td>
								<td><span class="kt-status" :class="statusClass(e.status)">{{ e.status }}</span></td>
								<td><a :href="evidenceHref(e)" target="_blank" rel="noopener">{{ __("View") }}</a></td>
							</tr>
						</tbody>
					</table>
					<div v-else data-testid="acc-evidence-cards">
						<div v-for="e in data.evidence" :key="e.evidence" class="acc-card">
							<div class="acc-card-title">{{ e.label }}</div>
							<div class="acc-card-fact"><span class="kt-label">{{ __("Reference") }}</span><span>{{ e.reference || "—" }}</span></div>
							<div class="acc-card-fact"><span class="kt-label">{{ __("Valid until") }}</span><span>{{ e.valid_until }}</span></div>
							<div class="acc-card-fact"><span class="kt-label">{{ __("Status") }}</span><span><span class="kt-status" :class="statusClass(e.status)">{{ e.status }}</span></span></div>
							<div class="acc-card-actions"><a :href="evidenceHref(e)" target="_blank" rel="noopener">{{ __("View") }}</a></div>
						</div>
					</div>
				</template>
				<p class="acc-muted">{{ __("A bid uses an exact copy of linked evidence. Updating this list does not change a submitted bid.") }}</p>
				<div v-if="allowed.has('add_evidence')">
					<button type="button" class="kt-btn kt-btn-secondary" :class="{ 'acc-btn-touch': narrow }" data-testid="acc-add-evidence" @click="dialog = { kind: 'add-evidence' }">
						<span class="acc-btn-icon"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><path d="m7 10 5-5 5 5" /><path d="M12 5v12" /></svg>{{ __("Add evidence") }}</span>
					</button>
				</div>
			</div>
		</div>

		<div class="kt-region">
			<h2>{{ __("Tender notice contacts") }}</h2>
			<div class="acc-region-body">
				<template v-if="data.notice_contacts.length">
					<table v-if="!narrow" class="kt-table" data-testid="acc-contacts">
						<thead><tr><th>{{ __("Email") }}</th><th>{{ __("Verification") }}</th></tr></thead>
						<tbody>
							<tr v-for="c in data.notice_contacts" :key="c.email">
								<td class="acc-strong">{{ c.email }}</td>
								<td><span class="kt-status" :class="statusClass(c.status)">{{ c.status }}</span></td>
							</tr>
						</tbody>
					</table>
					<div v-else data-testid="acc-contacts-cards">
						<div v-for="c in data.notice_contacts" :key="c.email" class="acc-card">
							<div class="acc-card-title">{{ c.email }}</div>
							<div class="acc-card-fact"><span class="kt-label">{{ __("Verification") }}</span><span><span class="kt-status" :class="statusClass(c.status)">{{ c.status }}</span></span></div>
						</div>
					</div>
				</template>
				<p class="acc-muted">{{ data.notice_contacts.length ? __("Each bid chooses one verified email for mandatory notices. Changing an Account email does not rewrite notices already sent.") : __("No verified email yet. Verify the official email to use it for Tender notices.") }}</p>
			</div>
		</div>

		<EditOrganisationDialog v-if="dialog && dialog.kind === 'edit'" :organisation="org" :focus="dialog.focus || ''" @close="dialog = null" @saved="saved" />
		<EditBusinessProfileDialog v-if="dialog && dialog.kind === 'profile'" :profile="profile" :focus="dialog.focus || ''" @close="dialog = null" @saved="saved" />
		<AddPersonDialog v-if="dialog && dialog.kind === 'add-person'" :organisation="org" @close="dialog = null" @saved="saved" />
		<AddEvidenceDialog v-if="dialog && dialog.kind === 'add-evidence'" :organisation="org" @close="dialog = null" @saved="saved" />
		<ViewPersonDialog v-if="dialog && dialog.kind === 'person'" :person="dialog.person" @close="dialog = null" />
	</div>

	<div v-else-if="failure" class="kt-page">
		<div class="kt-notice is-critical acc-load-failure" role="alert">
			<div class="kt-notice-body">{{ failure }}</div>
			<button type="button" class="kt-btn kt-btn-secondary" @click="load">{{ __("Try again") }}</button>
		</div>
	</div>
	<div v-else class="kt-page" aria-hidden="true"><div class="acc-skeleton" data-testid="acc-loading"></div></div>
</template>
