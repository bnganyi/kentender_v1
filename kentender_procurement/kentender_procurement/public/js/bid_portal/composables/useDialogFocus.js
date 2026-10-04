// BDS-CHG-001 v0.8 §10.1 / WCAG 2.4.3 (BDS01-AC-088, BDS07-AC-014): a bid
// dialog takes focus on its first control, keeps Tab and Shift+Tab inside
// itself, and gives focus back to the control that opened it when it closes.
import { nextTick, onBeforeUnmount, onMounted } from "vue";

const FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]):not([type="hidden"]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

export function useDialogFocus(first, container) {
	const opener = typeof document !== "undefined" ? document.activeElement : null;
	function onKeydown(event) {
		if (event.key !== "Tab" || !container.value) return;
		const items = [...container.value.querySelectorAll(FOCUSABLE)].filter((el) => !el.closest("[hidden]"));
		if (!items.length) return;
		const [head, tail] = [items[0], items[items.length - 1]];
		if (event.shiftKey && document.activeElement === head) {
			event.preventDefault();
			tail.focus();
		} else if (!event.shiftKey && document.activeElement === tail) {
			event.preventDefault();
			head.focus();
		}
	}
	onMounted(() => {
		if (container.value) container.value.addEventListener("keydown", onKeydown);
		nextTick(() => first.value && first.value.focus());
	});
	onBeforeUnmount(() => {
		if (container.value) container.value.removeEventListener("keydown", onKeydown);
		if (opener && opener.isConnected && typeof opener.focus === "function") nextTick(() => opener.focus());
	});
}
