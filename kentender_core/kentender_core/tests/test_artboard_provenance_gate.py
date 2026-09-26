# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Hard gate — a Vue component that claims a `.dc.html` artboard as its build
source must actually be checkable against a real one.

This exists because of a concrete, already-diagnosed incident: a "reconcile
with v1.24 artboards" commit in Procurement Planning (`2246d66b`,
2026-09-22 15:31:48) was made 53 minutes *before* the real v1.24 artboard
pack was added to the repo (`f2b74524`, 16:25:21). One screen built in that
window was ported from a stale, since-deleted v1.23 file while its own
header claimed the v1.24 source — found only by hand, via git archaeology,
after the mismatch had already shipped and been reported live. A second
pass found 5 more components with the identical timing defect, plus 18
further components whose header still names a `.dc.html` file the same
commit deleted outright (a dangling reference, not even a timing question).

Two independent checks, both mechanical and cheap:

- **Check A — existence.** The `.dc.html` file a component's header names
  must actually exist somewhere under `docs/mvp-1-r1/`.
- **Check B — provenance ordering.** For a file that does exist, the
  component's own last commit must not predate that artboard file's true
  first-add date (`git log --follow`, so a rename/move in the artboard's own
  history is not mistaken for a fresh file). A component whose last edit is
  older than the artboard it claims cannot possibly have been built by
  looking at that artboard — it was necessarily built against whatever
  existed at the time, then had its header comment relabelled to name the
  file that replaced it.

Scope is repo-wide (`KENTENDER_APPS`, matching the precedent
`test_industry_design_gate.py`) rather than limited to the module that
happened to trip this once — the mechanism should watch for the same defect
class anywhere it could recur, not just where it has already been found.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import frappe
from frappe.tests.utils import FrappeTestCase

KENTENDER_APPS: tuple[str, ...] = (
	"kentender_core",
	"kentender_strategy",
	"kentender_budget",
	"kentender_procurement",
	"kentender_stores",
	"kentender_assets",
	"kentender_suppliers",
	"kentender_governance",
	"kentender_compliance",
	"kentender_integrations",
	"kentender_transparency",
)

# Matches both "ported from X.dc.html" and "ported class-for-class from
# X.dc.html", including where the filename wraps onto the next header line
# (the repo's own header-comment style wraps at ~80 columns) — `\s+` matches
# the intervening newline+indentation just as readily as a single space.
PORTED_FROM_RE = re.compile(r"ported\s+(?:class-for-class\s+)?from\s+([A-Za-z0-9_.\- ]+\.dc\.html)", re.IGNORECASE)

# Only the leading header comment is in scope — reading the whole file risks
# a false match inside example copy/help text quoting an unrelated filename.
HEADER_SCAN_CHARS = 1500


def _repo_root() -> Path:
	# .../apps/kentender_v1/kentender_core/kentender_core -> .../apps/kentender_v1
	return Path(frappe.get_app_path("kentender_core")).parent.parent


def _docs_root() -> Path:
	return _repo_root() / "docs" / "mvp-1-r1"


def _app_public_js(app: str) -> Path | None:
	try:
		base = Path(frappe.get_app_path(app)) / "public" / "js"
	except Exception:
		return None
	return base if base.is_dir() else None


def _git(*args: str) -> str:
	result = subprocess.run(
		["git", *args], cwd=_repo_root(), capture_output=True, text=True, check=False,
	)
	return result.stdout.strip()


def _artboard_first_added(artboard_path: Path) -> str | None:
	"""True first-add date across renames, oldest entry first."""
	rel = artboard_path.relative_to(_repo_root())
	out = _git("log", "--follow", "--diff-filter=A", "--format=%ad", "--date=iso-strict", "--", str(rel))
	lines = [line for line in out.splitlines() if line.strip()]
	return lines[-1] if lines else None


def _component_last_commit(component_path: Path) -> str | None:
	rel = component_path.relative_to(_repo_root())
	out = _git("log", "-1", "--format=%ad", "--date=iso-strict", "--", str(rel))
	return out or None


def _live_boards(name: str) -> list[Path]:
	"""Boards by file name, excluding superseded copies: a board under a
	`retired/` or `archive/` folder is history, not a design source (TPR-CHG-001
	v0.12 moved the v0.8 Tender boards to `11_tenders/retired/design/` under the
	same file names as their replacements)."""
	return [p for p in _docs_root().rglob(name) if not ({"retired", "archive"} & {part.lower() for part in p.parts})]


class _Reference:
	def __init__(self, component: Path, claimed_name: str):
		self.component = component
		self.claimed_name = claimed_name
		matches = _live_boards(claimed_name)
		self.resolved = matches[0] if len(matches) == 1 else None
		self.ambiguous = len(matches) > 1


def _find_references() -> list[_Reference]:
	refs: list[_Reference] = []
	for app in KENTENDER_APPS:
		base = _app_public_js(app)
		if not base:
			continue
		for vue_path in base.rglob("*.vue"):
			header = vue_path.read_text(encoding="utf-8", errors="ignore")[:HEADER_SCAN_CHARS]
			match = PORTED_FROM_RE.search(header)
			if match:
				refs.append(_Reference(vue_path, match.group(1).strip()))
	return refs


#: A `.dc.html` path written into a UI test, e.g. the `ARTBOARD_FILE` constant
#: every design-fidelity spec opens. Quoted, so the pattern is the quote body.
SPEC_BOARD_RE = re.compile(r"[\"'`]([^\"'`\n]*\.dc\.html)[\"'`]")


def _spec_board_references() -> list[tuple[Path, str]]:
	"""Every artboard path a UI test names.

	Check A watches component headers. It does not watch the specs, and a spec
	is where the whole gate is wired up — so when the Requisitions board was
	renamed from `REQ-CHG-001 Artboards.dc.html` to `Requisitions - Design
	Board.dc.html`, its fidelity spec kept pointing at the old name, every one
	of its eleven tests died on `ERR_FILE_NOT_FOUND`, and nothing said so
	(found live 24 Sep 2026: the suite had simply stopped comparing anything).
	"""
	root = _repo_root() / "tests" / "ui"
	out: list[tuple[Path, str]] = []
	if not root.exists():
		return out
	for spec in root.rglob("*.ts"):
		for line in spec.read_text(encoding="utf-8", errors="ignore").splitlines():
			stripped = line.strip()
			# A path written in prose is documentation, not a reference the
			# suite will open.
			if stripped.startswith(("*", "//", "/*")):
				continue
			for match in SPEC_BOARD_RE.finditer(line):
				claimed = match.group(1).strip()
				# A bare suffix is half of a concatenation, and an interpolated
				# path is only knowable at run time.
				if claimed == ".dc.html" or "${" in claimed:
					continue
				out.append((spec, claimed))
	return out


class TestArtboardProvenanceGate(FrappeTestCase):
	def test_every_artboard_a_ui_test_opens_actually_exists(self):
		"""Check C. A design-fidelity spec that names a `.dc.html` file must
		name one that is in the repo. A missing board does not fail loudly —
		it fails as `ERR_FILE_NOT_FOUND` inside one test, and in a serial
		describe it takes every test after it down with it, silently."""
		missing = []
		for spec, claimed in _spec_board_references():
			candidate = _repo_root() / claimed
			if candidate.exists():
				continue
			if _live_boards(Path(claimed).name):
				continue
			missing.append(f"{spec.relative_to(_repo_root())} names {claimed!r}, which is not in the repo")
		self.assertEqual(missing, [], "\n".join(["A UI test opens an artboard that does not exist:", *missing]))


	def test_ported_from_references_an_artboard_that_exists(self):
		"""Check A. A header claiming a `.dc.html` source names a file that is
		actually still in the repo — not one a later commit deleted out from
		under it while leaving the claim behind."""
		refs = _find_references()
		self.assertGreaterEqual(len(refs), 10, "expected at least the already-known Planning components")

		violations = [
			f"{r.component.relative_to(_repo_root())}: claims {r.claimed_name!r}, "
			+ ("multiple files share that name under docs/mvp-1-r1/" if r.ambiguous else "no such file exists under docs/mvp-1-r1/")
			for r in refs
			if r.resolved is None
		]
		self.assertEqual(
			violations,
			[],
			f"{len(violations)} component(s) cite a deleted or unresolvable artboard file "
			"(update the header to the file that replaced it, once the component has actually "
			"been re-diffed against it): \n" + "\n".join(violations),
		)

	def test_ported_from_component_postdates_its_claimed_artboard(self):
		"""Check B. For a claim that does resolve to a real file, the
		component's own last edit must not predate that file's first
		appearance — otherwise the component was necessarily built against
		something else, and the header is misattributing its source."""
		refs = [r for r in _find_references() if r.resolved is not None]
		# Only the subset whose Check A already resolves is in scope here —
		# the 6 already-known v1.24 "Artboards-*" references plus the 1
		# Strategy reference, at minimum.
		self.assertGreaterEqual(len(refs), 5, "expected at least the already-known resolvable references")

		violations: list[str] = []
		for r in refs:
			artboard_date = _artboard_first_added(r.resolved)
			component_date = _component_last_commit(r.component)
			if not artboard_date or not component_date:
				# An uncommitted/untracked artboard or component has no git
				# history to compare yet — not this gate's concern.
				continue
			if component_date < artboard_date:
				violations.append(
					f"{r.component.relative_to(_repo_root())}: last committed {component_date}, "
					f"but {r.resolved.relative_to(_repo_root())} was only added {artboard_date} — "
					"this component cannot have been built by looking at that file"
				)
		self.assertEqual(
			violations,
			[],
			f"{len(violations)} component(s) were last committed before their claimed artboard "
			"existed (re-diff against the real current artboard, fix the drift, then this clears "
			"once the fix itself is committed): \n" + "\n".join(violations),
		)
