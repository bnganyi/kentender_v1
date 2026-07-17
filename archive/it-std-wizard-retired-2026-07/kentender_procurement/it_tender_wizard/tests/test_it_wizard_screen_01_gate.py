# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ITW-01 gate suite — run all Screen 01 backend tests in one Frappe process."""

from __future__ import annotations

from kentender_procurement.it_tender_wizard.tests.test_dashboard_kpi_service import TestDashboardKpiService
from kentender_procurement.it_tender_wizard.tests.test_it_wizard_dashboard_desk_wiring import (
	TestItWizardDashboardDeskWiring,
	TestItWizardDashboardDeskWiringSite,
	TestItWizardDashboardNativeGuard,
)
from kentender_procurement.it_tender_wizard.tests.test_it_wizard_navigation_contract import (
	TestItWizardNavigationContract,
	TestItWizardNavigationContractSite,
)
from kentender_procurement.it_tender_wizard.tests.test_kt_fonts_selfhosted import TestKtFontsSelfHosted
from kentender_procurement.it_tender_wizard.tests.test_std_test_fixtures import TestStdTestFixtures
from kentender_procurement.it_tender_wizard.tests.test_wizard_instance_service import TestWizardInstanceService

__all__ = [
	"TestDashboardKpiService",
	"TestItWizardDashboardDeskWiring",
	"TestItWizardDashboardDeskWiringSite",
	"TestItWizardDashboardNativeGuard",
	"TestItWizardNavigationContract",
	"TestItWizardNavigationContractSite",
	"TestKtFontsSelfHosted",
	"TestStdTestFixtures",
	"TestWizardInstanceService",
]
