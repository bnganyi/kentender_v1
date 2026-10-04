<!-- The board's own icon set (REQ-CHG-001 v1.11 board v2), path-for-path. -->
<template>
	<svg :class="cls" :width="size" :height="size" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" v-html="PATHS[name] || ''"></svg>
</template>

<script setup>
defineProps({ name: { type: String, required: true }, size: { type: [Number, String], default: 15 }, cls: { type: String, default: "" } });

const PATHS = {
	inbox: '<path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.45 5.11L2 12v6a2 2 0 002 2h16a2 2 0 002-2v-6l-3.45-6.89A2 2 0 0016.76 4H7.24a2 2 0 00-1.79 1.11z"/>',
	clipboard: '<rect x="8" y="2" width="8" height="4" rx="1"/><path d="M16 4h2a2 2 0 012 2v14a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2h2"/>',
	file: '<path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M14 2v6h6"/>',
	calendar: '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4"/><path d="M8 2v4"/><path d="M3 10h18"/>',
	coins: '<circle cx="8" cy="8" r="6"/><path d="M18.09 10.37A6 6 0 1110.34 18M7 6h1v4M16.71 13.88l.7.71-2.82 2.82"/>',
	monitor: '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M2 20h20"/>',
	sliders: '<path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6"/>',
	"check-square": '<path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/>',
	wrench: '<path d="M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z"/>',
	paperclip: '<path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48"/>',
	target: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
	dollar: '<path d="M12 2v20M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/>',
	"calendar-plain": '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
	"check-circle": '<path d="M9 12l2 2 4-4"/><circle cx="12" cy="12" r="9"/>',
	wallet: '<rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="12" cy="12" r="2.5"/><path d="M6 12h.01M18 12h.01"/>',
	info: '<circle cx="12" cy="12" r="9"/><path d="M12 8h.01M11 12h1v5h1"/>',
	x: '<path d="M18 6L6 18M6 6l12 12"/>',
	warning: '<path d="M12 3l9 16H3z"/><path d="M12 10v4M12 17h.01"/>',
	check: '<path d="M20 6L9 17l-5-5"/>',
	chevron: '<path d="M6 9l6 6 6-6"/>',
};
</script>
