# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""KT-FONTS-001 — Self-hosted brand font foundation (app-wide).

Guards that Manrope / Inter / JetBrains Mono / Material Symbols are self-hosted
(no Google CDN) via ``public/css/kt_fonts.css`` and that the IT-Wizard iframe
screens reference the self-hosted CSS instead of ``fonts.googleapis.com``.
"""

from __future__ import annotations

import glob
import os
import re

import frappe
from frappe.tests import UnitTestCase

_REQUIRED_FAMILIES = ("Inter", "Manrope", "JetBrains Mono", "Material Symbols Outlined")
_URL_RE = re.compile(r"url\(\s*['\"]?(?P<url>[^'\")]+)['\"]?\s*\)")


def _app_path(*parts: str) -> str:
	return os.path.join(frappe.get_app_path("kentender_procurement"), *parts)


def _kt_fonts_path() -> str:
	return _app_path("public", "css", "kt_fonts.css")


def _read(path: str) -> str:
	return open(path, encoding="utf-8").read()


class TestKtFontsSelfHosted(UnitTestCase):
	def test_kt_fonts_css_exists(self) -> None:
		self.assertTrue(os.path.exists(_kt_fonts_path()), "kt_fonts.css must exist")

	def test_font_faces_declared_for_all_families(self) -> None:
		css = _read(_kt_fonts_path())
		for family in _REQUIRED_FAMILIES:
			self.assertIn(f"'{family}'", css, f"@font-face for {family} missing")
		# Material Symbols base class ships with the foundation.
		self.assertIn(".material-symbols-outlined", css)

	def test_no_cdn_or_external_urls(self) -> None:
		css = _read(_kt_fonts_path())
		# Strip comments before scanning for URLs / imports.
		body = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
		self.assertNotIn("@import", body)
		self.assertNotIn("http://", body)
		self.assertNotIn("https://", body)
		self.assertNotIn("googleapis", body)
		self.assertNotIn("gstatic", body)

	def test_all_font_faces_use_relative_asset_urls_that_exist(self) -> None:
		css = _read(_kt_fonts_path())
		urls = _URL_RE.findall(css)
		self.assertGreaterEqual(len(urls), 5, "expected several woff2 sources")
		app_root = frappe.get_app_path("kentender_procurement")
		for url in urls:
			self.assertTrue(
				url.startswith("/assets/kentender_procurement/fonts/"),
				f"font src must be a relative self-hosted asset: {url}",
			)
			self.assertTrue(url.endswith(".woff2"), f"expected woff2: {url}")
			rel = url[len("/assets/kentender_procurement/") :]
			on_disk = os.path.join(app_root, "public", rel)
			self.assertTrue(os.path.exists(on_disk), f"woff2 not on disk: {on_disk}")

	def test_hooks_include_kt_fonts_css(self) -> None:
		from kentender_procurement.hooks import app_include_css

		joined = "\n".join(app_include_css)
		self.assertIn("css/kt_fonts.css", joined)

	def test_iframe_screens_reference_self_hosted_fonts_not_cdn(self) -> None:
		impl_dir = _app_path("public", "it_tender_wizard_impl")
		html_files = sorted(glob.glob(os.path.join(impl_dir, "*.html")))
		self.assertGreater(len(html_files), 10, "expected the IT-Wizard iframe screens")
		screens_checked = 0
		for path in html_files:
			html = _read(path)
			# No file may reach the Google Fonts CDN, ever.
			self.assertNotIn(
				"fonts.googleapis.com", html, f"{os.path.basename(path)} still hits Google Fonts CDN"
			)
			self.assertNotIn(
				"fonts.gstatic.com", html, f"{os.path.basename(path)} still hits gstatic CDN"
			)
			# Actual screen mockups (Tailwind + Material Symbols) must link the
			# self-hosted CSS. The `index.html` preview list has no fonts — skip it.
			is_screen = "cdn.tailwindcss.com" in html or "material-symbols" in html
			if is_screen:
				screens_checked += 1
				self.assertIn(
					"/assets/kentender_procurement/css/kt_fonts.css",
					html,
					f"{os.path.basename(path)} must link the self-hosted font CSS",
				)
		self.assertGreaterEqual(screens_checked, 10, "expected the 14 iframe screen mockups")
