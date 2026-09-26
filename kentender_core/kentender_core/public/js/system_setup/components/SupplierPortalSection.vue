<script setup>
// CFG-CHG-002 v0.16 §10.10A (C05 — Supplier portal settings), built ahead of
// CFG v0.16 approval under BDS-CHG-001 v0.8 owner decision OD-A. The spec has
// no artboard for this section, so it follows the §10.10A text in the same
// flat Procurement-settings composition as the Reminders card (recorded as a
// departure in the Bid Submission follow-ups, FU-V08-14).
//
// Every rule is server-side (kentender_core.services.public_portal): authority,
// validation, version check, audit. The field checks below only state the
// same messages before the round trip; server field errors bind to the same
// fields, and a failed save keeps every entered value.
import { computed, ref, watch } from "vue";
import { publicPortalApi } from "../data/publicPortalApi.js";

const props = defineProps({
	settings: { type: Object, default: null },
});
const emit = defineEmits(["saved"]);

const SUPPORT_FIELDS = [
	{ key: "supplier_support_email", label: "Support email", type: "email" },
	{ key: "supplier_support_phone", label: "Support phone (optional)", type: "tel" },
	{ key: "supplier_support_hours", label: "Support hours (optional)", type: "text" },
];
const LINK_FIELDS = [
	{ key: "privacy_notice_url", label: "Privacy and data use" },
	{ key: "portal_terms_url", label: "Terms of portal use" },
	{ key: "accessibility_statement_url", label: "Accessibility" },
];
const ALL = [...SUPPORT_FIELDS, ...LINK_FIELDS].map((field) => field.key);

function blank() {
	return Object.fromEntries(ALL.map((key) => [key, ""]));
}
const form = ref(blank());
const version = ref(0);
function load(settings) {
	form.value = { ...blank(), ...((settings && settings.values) || {}) };
	version.value = (settings && settings.record_version) || 0;
}
load(props.settings);
watch(() => props.settings, (settings) => load(settings));

const serverErrors = ref({});
const notice = ref("");
const failure = ref("");

function isHttps(value) {
	const text = String(value || "").trim();
	if (!text || /\s/.test(text)) return false;
	try {
		const url = new URL(text);
		return url.protocol === "https:" && Boolean(url.hostname) && !url.username && !url.password;
	} catch (e) {
		return false;
	}
}
function isEmail(value) {
	return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(value || "").trim());
}
const clientErrors = computed(() => {
	const errors = {};
	if (!isEmail(form.value.supplier_support_email)) errors.supplier_support_email = __("Enter the email suppliers should use for support.");
	for (const field of LINK_FIELDS) {
		if (!isHttps(form.value[field.key])) errors[field.key] = __("Enter a complete HTTPS address for {0}.", [__(field.label)]);
	}
	if (String(form.value.supplier_support_hours || "").trim().length > 160) errors.supplier_support_hours = __("Enter at most 160 characters.");
	return errors;
});
function problemFor(key) {
	return serverErrors.value[key] || clientErrors.value[key] || "";
}
const incomplete = computed(() => Object.keys(clientErrors.value).length > 0);

const { pending: busy, run } = kentender_core.desk_page.createCommandRunner(
	{ ref },
	{
		onStart: () => {
			notice.value = "";
			failure.value = "";
			serverErrors.value = {};
		},
		onError: (e) => (failure.value = e.message),
	}
);
const canSave = computed(() => !busy.value && !incomplete.value);

function save() {
	return run(async () => {
		const result = await publicPortalApi.update({ ...form.value }, version.value);
		if (result && result.ok === false) {
			serverErrors.value = result.errors || {};
			return;
		}
		version.value = result.record_version;
		notice.value = __("Supplier portal settings saved.");
		emit("saved");
	});
}

function openLink(url) {
	// Opens the entered destination in a new context; it saves nothing.
	window.open(url, "_blank", "noopener,noreferrer");
}
</script>

<template>
	<div class="kt-supplier-portal" data-testid="kt-procset-supplier-portal">
		<h3>{{ __("Supplier portal") }}</h3>
		<p class="text-muted">{{ __("Set the support contact and public information links shown to suppliers.") }}</p>

		<div class="kt-notice is-info" data-testid="kt-portal-info">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 8h.01M11 12h1v4h1" /></svg>
			<div class="kt-notice-body">{{ __("These details appear on public Tender and bid pages. They do not change a Tender, candidate notice or submission status.") }}</div>
		</div>

		<div v-if="incomplete" class="kt-notice is-warning" role="status" data-testid="kt-portal-incomplete">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M12 9v4M12 17h.01M10.3 3.9L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" /></svg>
			<div class="kt-notice-body">{{ __("Complete the supplier support and public-information links before suppliers start or submit bids.") }}</div>
		</div>

		<section class="kt-portal-group" :aria-label="__('Supplier support')">
			<h4>{{ __("Supplier support") }}</h4>
			<div v-for="field in SUPPORT_FIELDS" :key="field.key" class="kt-field">
				<label :for="'kt-portal-' + field.key">{{ __(field.label) }}</label>
				<input
					:id="'kt-portal-' + field.key"
					v-model="form[field.key]"
					class="kt-input"
					:type="field.type"
					:aria-invalid="problemFor(field.key) ? 'true' : 'false'"
					:aria-describedby="problemFor(field.key) ? 'kt-portal-' + field.key + '-error' : undefined"
					:data-testid="'kt-portal-' + field.key"
				>
				<p v-if="problemFor(field.key)" :id="'kt-portal-' + field.key + '-error'" class="kt-field-error" :data-testid="'kt-portal-' + field.key + '-error'">{{ problemFor(field.key) }}</p>
			</div>
			<p class="kt-field-hint">{{ __("Support hours do not extend a procurement deadline.") }}</p>
		</section>

		<section class="kt-portal-group" :aria-label="__('Public information')">
			<h4>{{ __("Public information") }}</h4>
			<div v-for="field in LINK_FIELDS" :key="field.key" class="kt-field kt-portal-link">
				<label :for="'kt-portal-' + field.key">{{ __(field.label) }}</label>
				<div class="kt-portal-link-row">
					<input
						:id="'kt-portal-' + field.key"
						v-model="form[field.key]"
						class="kt-input"
						type="url"
						inputmode="url"
						:aria-invalid="problemFor(field.key) ? 'true' : 'false'"
						:aria-describedby="problemFor(field.key) ? 'kt-portal-' + field.key + '-error' : undefined"
						:data-testid="'kt-portal-' + field.key"
					>
					<button
						v-if="isHttps(form[field.key])"
						type="button"
						class="kt-btn kt-btn-secondary"
						:data-testid="'kt-portal-open-' + field.key"
						@click="openLink(form[field.key])"
					>{{ __("Open link") }}</button>
				</div>
				<p v-if="problemFor(field.key)" :id="'kt-portal-' + field.key + '-error'" class="kt-field-error" :data-testid="'kt-portal-' + field.key + '-error'">{{ problemFor(field.key) }}</p>
			</div>
		</section>

		<div v-if="failure" class="kt-notice is-critical" role="alert" data-testid="kt-portal-error">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12" /></svg>
			<div class="kt-notice-body">{{ failure }}</div>
		</div>
		<div v-else-if="notice" class="kt-notice is-live" role="status" data-testid="kt-portal-saved">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M5 12l5 5L20 7" /></svg>
			<div class="kt-notice-body">{{ notice }}<br><span class="text-muted">{{ __("Used by Tenders and Bid Submission") }}</span></div>
		</div>

		<div class="kt-portal-actions">
			<button type="button" class="kt-btn kt-btn-primary" :disabled="!canSave" data-testid="kt-portal-save" @click="save">{{ __("Save changes") }}</button>
		</div>
	</div>
</template>
