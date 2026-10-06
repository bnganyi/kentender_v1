#!/usr/bin/env python3
"""Migrate every consumer of the old Industry class names to the design pack's (HOME-CHG-001 v0.6 Phase 1B, plan D9: no aliases).

The table is `RENAMES` in scripts/industry_design_css.py. Whole class tokens only: `kt-btn` is renamed, `kt-btn-x` and
`kt-button` are not. Source files of the apps and the browser/unit tests; not docs, not the generated stylesheet, not the
old-stylesheet snapshot.

    python3 scripts/industry_rename_classes.py            # dry run: counts per file and per class
    python3 scripts/industry_rename_classes.py --apply    # rewrite the files
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import industry_design_css as ids  # noqa: E402

ROOT = ids.ROOT
EXTENSIONS = {".vue", ".js", ".ts", ".py", ".css", ".html", ".mjs", ".cjs"}
SKIP_DIRS = {"node_modules", ".git", "docs", "test-results", "__pycache__", "dist", "playwright-report", "artifacts"}
SKIP_FILES = {
	ids.TARGET.resolve(), ids.OLD.resolve(), (ROOT / "scripts/industry_rename_classes.py").resolve(), (ROOT / "scripts/industry_design_css.py").resolve(),
	(ROOT / "scripts/home_design_css.py").resolve(),
}
PATTERN = re.compile(r"(?<![\w-])(" + "|".join(sorted(map(re.escape, ids.RENAMES), key=len, reverse=True)) + r")(?![\w-])")


def files():
	for top in sorted(ROOT.iterdir()):
		if top.name in SKIP_DIRS or top.name.startswith("."):
			continue
		if not (top.name.startswith("kentender_") or top.name in ("tests", "scripts")):
			continue
		for path in top.rglob("*"):
			if path.suffix in EXTENSIONS and path.is_file() and not (SKIP_DIRS & set(path.parts)) and path.resolve() not in SKIP_FILES:
				yield path


def main() -> None:
	apply = "--apply" in sys.argv
	per_class: Counter = Counter()
	per_file: Counter = Counter()
	for path in files():
		try:
			text = path.read_text(encoding="utf-8")
		except UnicodeDecodeError:
			continue
		hits = PATTERN.findall(text)
		if not hits:
			continue
		per_class.update(hits)
		per_file[str(path.relative_to(ROOT))] = len(hits)
		if apply:
			path.write_text(PATTERN.sub(lambda m: ids.RENAMES[m.group(1)], text), encoding="utf-8")
	print(f"{'rewrote' if apply else 'would rewrite'} {len(per_file)} files, {sum(per_class.values())} occurrences")
	for name, count in per_class.most_common():
		print(f"  {name} -> {ids.RENAMES[name]}: {count}")


if __name__ == "__main__":
	main()
