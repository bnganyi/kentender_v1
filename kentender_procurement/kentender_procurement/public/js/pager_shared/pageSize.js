// The reader's chosen rows-per-page, remembered per screen in this browser. A
// convenience only: the fixed offer is checked on the way in and out, and a
// browser that refuses storage simply gets the default of ten.
export const PAGE_SIZES = [10, 25, 50, 100];
export const DEFAULT_PAGE_SIZE = 10;

const keyOf = (screen) => `kt-page-size:${screen}`;

export function savedPageSize(screen) {
	try {
		const value = Number(window.localStorage.getItem(keyOf(screen)));
		return PAGE_SIZES.includes(value) ? value : DEFAULT_PAGE_SIZE;
	} catch {
		return DEFAULT_PAGE_SIZE;
	}
}

export function savePageSize(screen, size) {
	try {
		window.localStorage.setItem(keyOf(screen), String(size));
	} catch {
		/* storage can be blocked; the choice then lasts until the page is left */
	}
}
