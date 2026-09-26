<!-- TPR-CHG-001 v0.11 §10.15 bound-release states (Superseded, Withdrawn,
     integrity failed) on the Tender record. The server composes the words and
     sends the STD Templates route only to a user who may inspect templates
     (STD-TPL-IMP-001 follow-up FU-10); no board draws this notice, so it uses
     the shared `kt-notice`. -->
<template>
	<div class="tnd-page" style="padding-bottom: 0">
		<div class="kt-notice" :class="notice.tone" role="status" data-testid="tnd-template-notice">
			<div class="kt-notice-body" style="flex: 1">
				<strong>{{ notice.heading }}</strong>
				<div>{{ notice.text }}</div>
			</div>
			<button v-if="route.length" type="button" class="kt-btn kt-btn-secondary" data-testid="tnd-template-notice-link" @click="$emit('navigate', route)">View STD Template</button>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({ notice: { type: Object, required: true } });
defineEmits(["navigate"]);

const route = computed(() => props.notice.std_template_route || []);
</script>
