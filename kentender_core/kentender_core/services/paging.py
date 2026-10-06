"""Server-side paging for table lists (the table-pagination standard).

A list that can grow returns one page and the total that matched, so the browser
can draw the shared pager without holding every row. The offer is fixed: a page
size outside it is not honoured, so a hand-built request cannot ask for a whole
register in one call.
"""

from __future__ import annotations

from typing import Any, Sequence

DEFAULT_PAGE_SIZE = 10
PAGE_SIZES = (10, 25, 50, 100)


def _whole(value: Any, default: int) -> int:
	try:
		return int(value)
	except (TypeError, ValueError):
		return default


def page_of(rows: Sequence[Any], page: Any = 1, page_size: Any = DEFAULT_PAGE_SIZE) -> tuple[list[Any], dict[str, int]]:
	"""One page of `rows` and its `{page, page_size, total, pages}`.

	`rows` is already filtered, so `total` is what matched. A page below one is the
	first page and a page past the end is the last, so a filter that shrinks the list
	never leaves the reader on a page that no longer exists."""
	size = _whole(page_size, DEFAULT_PAGE_SIZE)
	if size not in PAGE_SIZES:
		size = DEFAULT_PAGE_SIZE
	total = len(rows)
	pages = max(1, -(-total // size))
	current = min(max(_whole(page, 1), 1), pages)
	start = (current - 1) * size
	return list(rows[start : start + size]), {"page": current, "page_size": size, "total": total, "pages": pages}
