<!-- .kt-disclosure — Level 3 evidence behind a labelled disclosure (§14.1
     Record details / Source details). Native <details>/<summary>, as the
     peer modules build it: keyboard and focus behaviour come with it. -->
<template>
	<details class="kt-disclosure" :open="open" :data-testid="testid" @toggle="open = $event.target.open">
		<summary class="kt-disclosure-head">
			<div class="kt-disclosure-title-row"><span class="kt-disclosure-title">{{ title }}</span></div>
			<Icon name="chevron" :size="16" :cls="`kt-disclosure-chevron${open ? ' is-open' : ''}`" />
		</summary>
		<div v-if="open" class="kt-disclosure-body"><slot /></div>
	</details>
</template>

<script setup>
import { ref, watch } from "vue";
import Icon from "./Icon.vue";

const props = defineProps({ title: { type: String, required: true }, startOpen: { type: Boolean, default: false }, testid: { type: String, default: "" } });
const open = ref(props.startOpen);
watch(() => props.startOpen, (value) => { if (value) open.value = true; });
</script>
