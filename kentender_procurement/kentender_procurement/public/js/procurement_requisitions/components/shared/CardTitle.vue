<!-- The board's section heading: h6.kt-card-title with its leading icon. -->
<template>
	<h6 class="kt-card-title req-card-title"><Icon v-if="icon" :name="icon" />{{ title }}<slot /></h6>
</template>

<script setup>
import Icon from "./Icon.vue";

defineProps({ title: { type: String, required: true }, icon: { type: String, default: "" } });
</script>
