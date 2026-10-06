// The numbered buttons of the shared table pager: at most seven slots, the first
// and last page always present, the current page and its neighbours always
// present, and "gap" where pages are skipped.
//
//   9 pages, page 1 -> 1 2 3 4 5 … 9
//   9 pages, page 5 -> 1 … 4 5 6 … 9
//   9 pages, page 9 -> 1 … 5 6 7 8 9
export function pageWindow(current, pages) {
	if (pages <= 7) return Array.from({ length: pages }, (_, i) => i + 1);
	if (current <= 4) return [1, 2, 3, 4, 5, "gap-end", pages];
	if (current >= pages - 3) return [1, "gap-start", pages - 4, pages - 3, pages - 2, pages - 1, pages];
	return [1, "gap-start", current - 1, current, current + 1, "gap-end", pages];
}
