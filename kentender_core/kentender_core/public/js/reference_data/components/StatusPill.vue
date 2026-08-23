<script setup>
import { computed } from "vue";
import { statusKind } from "../data/statusKind.js";

const props = defineProps({ status: { type: String, required: true } });
const kind = computed(() => statusKind(props.status));
</script>

<template>
	<span class="kt-status" :class="kind">{{ status }}</span>
</template>
