<!-- PLN-CHG-001 v1.23 §10.16 — the Planning-side missing-setting panel
     (C01–C04), ported from C01-C04.dc.html.

     Setup itself belongs to System setup. This panel exists so that the person
     looking at the blocked action learns three things without leaving it: the
     setting that is missing, the action it is blocking, and who is responsible
     for it. C03 and C04 add the purchase the rule is missing for, because a
     maintainer cannot act on "a rule is missing" alone.

     The control is real or it is absent. A maintainer gets a route to the
     exact section; everyone else gets the sentence naming who to ask. Planning
     shows no disabled setup control. -->
<template>
	<div class="kt-notice is-attention pln-missing-setting" data-testid="pln-missing-setting">
		<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
			<path d="M12 3l9 16H3z"></path><path d="M12 10v4M12 17h.01"></path>
		</svg>
		<div class="kt-notice-body">
			<div class="kt-meta-row">
				<div>
					<span class="kt-label">Setting</span>
					<span class="kt-meta-value" data-testid="pln-missing-setting-name">{{ panel.setting }}</span>
				</div>
				<div v-if="panel.affected_purchase">
					<span class="kt-label">Affected purchase</span>
					<span class="kt-meta-value" data-testid="pln-missing-setting-purchase">{{ panel.affected_purchase }}</span>
				</div>
				<div>
					<span class="kt-label">Affected action</span>
					<span class="kt-meta-value" data-testid="pln-missing-setting-action">{{ panel.affected_action }}</span>
				</div>
				<div>
					<span class="kt-label">Responsible role</span>
					<span class="kt-meta-value" data-testid="pln-missing-setting-role">{{ panel.responsible_role }}</span>
				</div>
			</div>
			<!-- What is still permitted, where the closed setting does not stop
			     everything (C02-DPP-CLOSED). -->
			<p v-if="panel.note" class="kt-muted" data-testid="pln-missing-setting-note">{{ panel.note }}</p>
			<!-- A real link for a maintainer; the plain sentence for everyone
			     else. Never a disabled control. -->
			<a
				v-if="panel.can_open_setup"
				class="kt-btn kt-btn-secondary"
				data-testid="pln-open-setup"
				:href="panel.href"
			>{{ panel.action }}</a>
			<p v-else class="kt-muted" data-testid="pln-ask-administrator">{{ panel.ask_text }}</p>
		</div>
	</div>
</template>

<script setup>
defineProps({
	panel: { type: Object, required: true },
});
</script>
