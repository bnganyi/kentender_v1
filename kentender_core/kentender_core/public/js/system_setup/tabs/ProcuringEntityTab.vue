<script setup>
// CFG-CHG-002 v0.6 §10.1/§10.2 + §11.2 — the Procuring entity tab.
//
// First run (CFG-DES-02): a setup notice, the identity card with an editable
// code, and one primary action, "Configure site" — no Cancel, no wizard, no
// draft. Configured (CFG-DES-01): the code is read-only, "Save changes" is
// disabled until a field changes and re-disables after a successful save.
import { computed, reactive, ref, watch } from "vue";
import { siteConfigApi } from "../data/siteConfigApi.js";

const props = defineProps({
	site: { type: Object, required: true },
});
const emit = defineEmits(["configured", "updated"]);

const busy = ref(false);
const error = ref("");
const notice = ref("");

const configured = computed(() => !!props.site?.configured);
const pe = computed(() => props.site?.procuring_entity || null);
const peTypes = computed(() => props.site?.pe_types || []);

const form = reactive({
	pe_name: pe.value?.pe_name || "",
	pe_code: pe.value?.pe_code || "",
	pe_type: pe.value?.pe_type || "",
	ppra_registration: pe.value?.ppra_registration || "",
	timezone: pe.value?.timezone || "Africa/Nairobi",
});

watch(pe, (value) => {
	form.pe_name = value?.pe_name || "";
	form.pe_code = value?.pe_code || "";
	form.pe_type = value?.pe_type || "";
	form.ppra_registration = value?.ppra_registration || "";
	form.timezone = value?.timezone || "Africa/Nairobi";
});

const dirty = computed(() => {
	if (!configured.value) return true;
	return (
		form.pe_name !== (pe.value?.pe_name || "") ||
		form.pe_type !== (pe.value?.pe_type || "") ||
		form.ppra_registration !== (pe.value?.ppra_registration || "") ||
		form.timezone !== (pe.value?.timezone || "")
	);
});

const canSubmit = computed(() => {
	if (busy.value) return false;
	if (!configured.value) {
		return !!(form.pe_name.trim() && form.pe_code.trim() && form.pe_type);
	}
	return dirty.value;
});

async function submit() {
	busy.value = true;
	error.value = "";
	notice.value = "";
	try {
		if (!configured.value) {
			await siteConfigApi.configure({
				pe_name: form.pe_name,
				pe_code: form.pe_code,
				pe_type: form.pe_type,
				ppra_registration: form.ppra_registration,
				timezone: form.timezone,
			});
			emit("configured");
			notice.value = __("Site configured. The remaining tabs are now available.");
		} else {
			await siteConfigApi.update(
				{
					pe_name: form.pe_name,
					pe_type: form.pe_type,
					ppra_registration: form.ppra_registration,
					timezone: form.timezone,
				},
				pe.value?.expected_version
			);
			emit("updated");
			notice.value = __("Changes saved.");
		}
	} catch (e) {
		error.value = e.message;
	} finally {
		busy.value = false;
	}
}

function fmt(value) {
	return value || "—";
}
</script>

<template>
	<section class="kt-setup-section" data-testid="kt-setup-pe">
		<!-- CFG-DES-02 setup notice — first run only -->
		<div v-if="!configured" class="kt-setup-notice" data-testid="kt-setup-pe-notice">
			<h2>{{ __("Configure this site") }}</h2>
			<p>{{ __("KenTender represents one procuring entity. Enter its details to create the site and its root organisation unit.") }}</p>
		</div>

		<div class="kt-card kt-blueprint" data-testid="kt-setup-pe-card">
			<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
			<div class="kt-card-title">{{ __("Procuring entity") }}</div>
			<p v-if="configured" class="kt-muted kt-card-lede">
				{{ __("This site represents one procuring entity. The code is fixed once the site is configured.") }}
			</p>

			<div class="kt-setup-grid">
				<div class="kt-field">
					<label for="kt-pe-code">{{ __("Entity code") }}</label>
					<div v-if="configured" class="kt-ro" data-testid="kt-setup-pe-code-ro">{{ form.pe_code }}</div>
					<input
						v-else
						id="kt-pe-code"
						v-model="form.pe_code"
						class="kt-input"
						data-testid="kt-setup-pe-code"
					>
				</div>
				<div class="kt-field">
					<label for="kt-pe-name">{{ __("Entity name") }}</label>
					<input id="kt-pe-name" v-model="form.pe_name" class="kt-input" data-testid="kt-setup-pe-name">
				</div>
				<div class="kt-field">
					<label for="kt-pe-type">{{ __("Entity type") }}</label>
					<select id="kt-pe-type" v-model="form.pe_type" class="kt-input" data-testid="kt-setup-pe-type">
						<option value="">{{ __("Select the entity type") }}</option>
						<option v-for="kind in peTypes" :key="kind" :value="kind">{{ kind }}</option>
					</select>
				</div>
				<div class="kt-field">
					<label for="kt-pe-ppra">{{ __("PPRA registration") }}</label>
					<input
						id="kt-pe-ppra"
						v-model="form.ppra_registration"
						class="kt-input"
						:placeholder="__('Optional')"
						data-testid="kt-setup-pe-ppra"
					>
				</div>
				<div class="kt-field">
					<label for="kt-pe-tz">{{ __("Timezone") }}</label>
					<!-- CFG-DES-01 draws Timezone as a dropdown -->
					<select id="kt-pe-tz" v-model="form.timezone" class="kt-input" data-testid="kt-setup-pe-tz">
						<option v-for="zone in site.timezones || ['Africa/Nairobi']" :key="zone" :value="zone">
							{{ zone }}
						</option>
					</select>
				</div>
			</div>
		</div>

		<!-- CFG-DES-01 configuration record card — configured only -->
		<div v-if="configured" class="kt-card kt-blueprint" data-testid="kt-setup-pe-record">
			<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
			<div class="kt-card-title">{{ __("Configuration record") }}</div>
			<div class="kt-record-rows">
				<div class="kt-record-row">
					<span class="kt-label">{{ __("Configured by") }}</span>
					<span>{{ fmt(pe?.configured_by) }}</span>
				</div>
				<div class="kt-record-row">
					<span class="kt-label">{{ __("Configured at") }}</span>
					<span>{{ fmt(pe?.configured_at_label || pe?.configured_at) }}</span>
				</div>
				<div class="kt-record-row">
					<span class="kt-label">{{ __("Root organisation unit") }}</span>
					<span>{{ site.root_unit ? site.root_unit.name + " · " + site.root_unit.code : __("Missing — see Organisation structure") }}</span>
				</div>
			</div>
		</div>

		<p v-if="error" class="kt-inline-error" role="alert" data-testid="kt-setup-pe-error">{{ error }}</p>
		<p v-else-if="notice" class="kt-setup-success" data-testid="kt-setup-pe-success">{{ notice }}</p>

		<div class="kt-setup-footer">
			<button
				type="button"
				class="kt-btn kt-btn-primary"
				:disabled="!canSubmit"
				data-testid="kt-setup-pe-submit"
				@click="submit"
			>{{ configured ? __("Save changes") : __("Configure site") }}</button>
		</div>
	</section>
</template>
