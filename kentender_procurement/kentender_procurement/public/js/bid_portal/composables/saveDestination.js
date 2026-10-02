// Where Save and continue goes (owner report, 2 Oct 2026: the wizard "redirected
// to another section"). The button does what its label said when it was clicked:
// the destination is taken from the footer at that moment, before any save or
// re-read can change the page, and the navigation happens once, after the save.
// A footer that says it `stays` (this is the only task left, and it is not
// finished) re-reads the task and brings what is missing into view instead.
import { nextTick } from "vue";

export function destinationOf(footer) {
	return { href: footer.next_href, stays: !!footer.stays };
}

export async function arrive(destination, { go, load }) {
	if (!destination.stays) return go(destination.href);
	await load();
	await nextTick();
	const missing = document.querySelector('[data-testid$="-attention"], .kt-field-error');
	if (missing && missing.scrollIntoView) missing.scrollIntoView({ block: "center" });
}
