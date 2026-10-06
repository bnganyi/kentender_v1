<!-- Hosts kentender_core's shared table pager (kt_industry_pager.bundle.js) on
     this bundle's own Vue instance — AGENTS.md §6.6: a component cannot cross a
     bundle boundary, so the core publishes a mount helper and every module
     reaches it through this one wrapper. The caller keeps `page` and `pageSize`
     (v-model:page / v-model:page-size); this only draws them and reports picks. -->
<template>
	<div ref="host" />
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from "vue";

const props = defineProps({
	total: { type: Number, default: 0 },
	page: { type: Number, default: 1 },
	pageSize: { type: Number, default: 10 },
	noun: { type: String, default: "row" },
	nounPlural: { type: String, default: "" },
});
const emit = defineEmits(["update:page", "update:pageSize"]);

const host = ref(null);
let handle = null;

onMounted(() => {
	const mount = window.kentender_core?.industry?.mountPager;
	if (!mount || !host.value) return;
	handle = mount(host.value, {
		total: props.total,
		page: props.page,
		pageSize: props.pageSize,
		noun: props.noun,
		nounPlural: props.nounPlural,
		onPage: (n) => emit("update:page", n),
		onSize: (n) => emit("update:pageSize", n),
	});
});

watch(
	() => [props.total, props.page, props.pageSize, props.noun, props.nounPlural],
	([total, page, pageSize, noun, nounPlural]) => handle?.update({ total, page, pageSize, noun, nounPlural })
);

onBeforeUnmount(() => {
	handle?.unmount();
	handle = null;
});
</script>
