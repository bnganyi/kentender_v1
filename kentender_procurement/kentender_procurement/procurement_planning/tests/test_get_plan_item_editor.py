from unittest import TestCase
from unittest.mock import patch

from kentender_procurement.procurement_planning.services.procurement_method_catalogue import (
	OPEN_TENDER,
	procurement_method_is_allowed,
	resolve_procurement_methods,
)


class TestProcurementMethodCatalogue(TestCase):
	@patch("kentender_procurement.procurement_planning.services.procurement_method_catalogue._doctype_select_methods", return_value=[])
	@patch("kentender_procurement.procurement_planning.services.procurement_method_catalogue._catalogue_methods", return_value=["Restricted tender"])
	def test_configured_method_is_available_with_open_tender_safety_fallback(self, _catalogue, _schema) -> None:
		contract = resolve_procurement_methods()
		self.assertIn("Restricted tender", contract["methods"])
		self.assertIn(OPEN_TENDER, contract["methods"])
		self.assertTrue(procurement_method_is_allowed("Restricted tender", contract))

	@patch("kentender_procurement.procurement_planning.services.procurement_method_catalogue._doctype_select_methods", return_value=[])
	@patch("kentender_procurement.procurement_planning.services.procurement_method_catalogue._catalogue_methods", return_value=[])
	def test_empty_configuration_degrades_to_open_tender_with_reason_code(self, _catalogue, _schema) -> None:
		contract = resolve_procurement_methods()
		self.assertEqual(contract["methods"], [OPEN_TENDER])
		self.assertTrue(contract["degraded"])
		self.assertEqual(contract["recommendation_reason_code"], "PROCUREMENT_METHOD_FALLBACK_OPEN_TENDER")

	def test_unsupported_method_is_rejected(self) -> None:
		self.assertFalse(procurement_method_is_allowed("Direct procurement", {"methods": [OPEN_TENDER]}))
