# KenTender monorepo helpers — bench root: /home/midasuser/frappe-bench
# Default site matches sites/common_site_config.json → default_site

SITE ?= kentender.midas.com
BENCH_ROOT := /home/midasuser/frappe-bench
KENTENDER_APPS := kentender_core,kentender_strategy,kentender_budget,kentender_procurement,kentender_suppliers,kentender_governance,kentender_compliance,kentender_stores,kentender_assets,kentender_integrations,kentender_transparency
INSTALL_ORDER := kentender_core kentender_strategy kentender_budget kentender_procurement kentender_suppliers kentender_governance kentender_compliance kentender_stores kentender_assets kentender_integrations kentender_transparency

.PHONY: help install install-one migrate build build-kentender clear restart doctor list symlinks validate-links smoke ui-smoke ui-workspace-pattern-gate tm2-v1-contamination-audit p11-04-tm2-surface-gate p11-05-tm2-surface-legacy-literal-gate p12-01-scenario-harness x-01-planning-std-poc-gate x-02-no-plain-bench-build-gate x-03-doc9-acceptance-sequence-gate std-verbatim-gate std-step1-gate nssf-calibration-gate it-wizard-static-gate it-wizard-dashboard-gate seed-stable-platform seed-stable-platform-reset seed-stable-platform-validate

help:
	@echo "Targets:"
	@echo "  make install SITE=$(SITE)     — install-app all KenTender apps in order"
	@echo "  make install-one APP=...      — install-app single app"
	@echo "  make migrate SITE=$(SITE)"
	@echo "  make build — desk assets via ./scripts/bench-with-node.sh (Node ≥24; see frappe-bench AGENTS.md)"
	@echo "  make build-kentender — all KenTender apps via bench-with-node.sh"
	@echo "  make clear SITE=$(SITE)"
	@echo "  make restart"
	@echo "  make doctor"
	@echo "  make list SITE=$(SITE)"
	@echo "  make symlinks"
	@echo "  make validate-links"
	@echo "  make smoke SITE=$(SITE) — guard_frappe_scaffolds + Wave 0 smoke tests"
	@echo "  make tm2-v1-contamination-audit SITE=$(SITE) — P11-03 static scan + catalogue (kentender_procurement)"
	@echo "  make p11-04-tm2-surface-gate SITE=$(SITE) — P11-04 TM2 paths must not get_doc/new_doc Procurement Tender"
	@echo "  make p11-05-tm2-surface-legacy-literal-gate SITE=$(SITE) — P11-05 TM2 paths + v2 desk JS must not quote Procurement Tender"
	@echo "  make p12-01-scenario-harness SITE=$(SITE) — P12-01 doc 7 §2 scenario catalog + S01–S13 stub test modules"
	@echo "  make x-01-planning-std-poc-gate SITE=$(SITE) — X-01 planning + STD POC regression slice (tender-management §X)"
	@echo "  make x-02-no-plain-bench-build-gate — X-02 tender-management prompts must not document bare bench asset build (doc 9 §3.1)"
	@echo "  make x-03-doc9-acceptance-sequence-gate — X-03 doc 9 §23.4 KenTender acceptance runbook markers (doc + audit)"
	@echo "  make ui-smoke — Phase La: npm run test:ui:smoke (needs Node, running site, apps/kentender_v1/.env.ui)"
	@echo "  make ui-workspace-pattern-gate — workspace contract tests (selection, scroll, anti-flicker)"
	@echo "  make std-verbatim-gate SITE=$(SITE) — BE-14 verbatim extraction + smoke contracts"
	@echo "  make std-step1-gate SITE=$(SITE) — BE-15 Step 1 activation/consumption/render smoke"
	@echo "  make nssf-calibration-gate SITE=$(SITE) — CAL-NSSF golden proof gate"
	@echo "  make it-wizard-static-gate SITE=$(SITE) — IT Wizard Phase 1 static layout guards (45 tests)"
	@echo "  make it-wizard-dashboard-gate SITE=$(SITE) — ITW-01 dashboard backend + desk wiring gate"
	@echo "  make seed-stable-platform SITE=$(SITE) — load MOH stable platform seed (Works + IT STD)"
	@echo "  make seed-stable-platform-reset SITE=$(SITE) — clear + reload stable platform seed"
	@echo "  make seed-stable-platform-validate SITE=$(SITE) — validate stable platform seed only"
	@for app in $(INSTALL_ORDER); do \
		echo "Installing $$app on $(SITE)"; \
		cd $(BENCH_ROOT) && bench --site $(SITE) install-app $$app || exit 1; \
	done

install-one:
	@test -n "$(APP)" || (echo "Usage: make install-one APP=kentender_core SITE=..." && exit 1)
	cd $(BENCH_ROOT) && bench --site $(SITE) install-app $(APP)

migrate:
	cd $(BENCH_ROOT) && bench --site $(SITE) migrate

build:
	cd $(BENCH_ROOT) && ./scripts/bench-with-node.sh build

build-kentender:
	cd $(BENCH_ROOT) && ./scripts/bench-with-node.sh build --apps $(KENTENDER_APPS)

clear:
	cd $(BENCH_ROOT) && bench --site $(SITE) clear-cache && bench --site $(SITE) clear-website-cache

restart:
	cd $(BENCH_ROOT) && bench restart

doctor:
	cd $(BENCH_ROOT) && bench doctor

list:
	cd $(BENCH_ROOT) && bench --site $(SITE) list-apps

symlinks:
	cd $(BENCH_ROOT)/apps && \
	ln -sfn kentender_v1/kentender_core kentender_core && \
	ln -sfn kentender_v1/kentender_strategy kentender_strategy && \
	ln -sfn kentender_v1/kentender_budget kentender_budget && \
	ln -sfn kentender_v1/kentender_procurement kentender_procurement && \
	ln -sfn kentender_v1/kentender_governance kentender_governance && \
	ln -sfn kentender_v1/kentender_compliance kentender_compliance && \
	ln -sfn kentender_v1/kentender_stores kentender_stores && \
	ln -sfn kentender_v1/kentender_assets kentender_assets && \
	ln -sfn kentender_v1/kentender_integrations kentender_integrations && \
	ln -sfn kentender_v1/kentender_suppliers kentender_suppliers && \
	ln -sfn kentender_v1/kentender_transparency kentender_transparency

validate-links:
	@test -L $(BENCH_ROOT)/apps/kentender_core
	@test -L $(BENCH_ROOT)/apps/kentender_strategy
	@test -L $(BENCH_ROOT)/apps/kentender_budget
	@test -L $(BENCH_ROOT)/apps/kentender_procurement
	@test -L $(BENCH_ROOT)/apps/kentender_governance
	@test -L $(BENCH_ROOT)/apps/kentender_compliance
	@test -L $(BENCH_ROOT)/apps/kentender_stores
	@test -L $(BENCH_ROOT)/apps/kentender_assets
	@test -L $(BENCH_ROOT)/apps/kentender_integrations
	@test -L $(BENCH_ROOT)/apps/kentender_suppliers
	@test -L $(BENCH_ROOT)/apps/kentender_transparency
	@echo "All KenTender symlinks look present."

smoke:
	cd $(BENCH_ROOT) && python3 apps/kentender_v1/scripts/guard_frappe_scaffolds.py
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_core --module kentender_core.tests.test_wave0_smoke

ui-smoke:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npm run test:ui:smoke

ui-workspace-pattern-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test \
		tests/ui/smoke/strategy-landing/strategy-pattern-lock.spec.ts \
		tests/ui/smoke/budget-landing/budget-pattern-lock.spec.ts \
		tests/ui/smoke/dia-landing/dia-pattern-lock.spec.ts

ui-std-config-gate:
	@echo "STD Module POC archived (2026-07). Use: make verify-std-archived && npm run test:ui:smoke:std-module-retired"
	@exit 1

verify-std-archived:
	chmod +x $(BENCH_ROOT)/apps/kentender_v1/scripts/verify-std-archived.sh
	$(BENCH_ROOT)/apps/kentender_v1/scripts/verify-std-archived.sh

ui-std-module-retired-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npm run test:ui:smoke:std-module-retired

tm2-v1-contamination-audit:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_management.tests.test_p11_03_tm2_v1_contamination_audit

p11-04-tm2-surface-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_management.tests.test_p11_04_tm2_surface_no_procurement_tender

p11-05-tm2-surface-legacy-literal-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_management.tests.test_p11_05_tm2_surface_no_procurement_tender_literal

p12-01-scenario-harness:
	SITE=$(SITE) $(BENCH_ROOT)/scripts/p12_01_tm2_works_scenario_harness.sh

x-01-planning-std-poc-gate:
	SITE=$(SITE) $(BENCH_ROOT)/scripts/x_01_planning_std_poc_regression_gate.sh

x-02-no-plain-bench-build-gate:
	$(BENCH_ROOT)/scripts/x_02_tender_management_docs_no_plain_bench_build_gate.sh

x-03-doc9-acceptance-sequence-gate:
	$(BENCH_ROOT)/scripts/x_03_doc9_section_23_4_acceptance_sequence_gate.sh

std-verbatim-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && PYTHONPATH=. python3 scripts/std_extraction/verbatim/run.py
	cd $(BENCH_ROOT)/apps/kentender_v1 && PYTHONPATH=. python3 scripts/std_extraction/build_package.py v1_1
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.std_engine.tests.test_verbatim_extract_clauses
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.std_engine.tests.test_record_mapper_verbatim_fields
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.std_engine.tests.test_be_14_verbatim_smoke_contracts

std-step1-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.std_engine.tests.test_be_12_smoke_contracts
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.std_engine.tests.test_be_14_verbatim_smoke_contracts
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.std_engine.tests.test_be_15_step1_activation_consumption

nssf-calibration-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.std_engine.tests.test_be_15_step1_activation_consumption \
		--test kentender_procurement.std_engine.tests.test_be_15_step1_activation_consumption.TestBe15Step1ActivationConsumption.test_cal_nssf_001_fixture_import_without_master_mutation
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.std_engine.tests.test_be_15_step1_activation_consumption \
		--test kentender_procurement.std_engine.tests.test_be_15_step1_activation_consumption.TestBe15Step1ActivationConsumption.test_cal_nssf_002_golden_bind
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.std_engine.tests.test_be_15_step1_activation_consumption \
		--test kentender_procurement.std_engine.tests.test_be_15_step1_activation_consumption.TestBe15Step1ActivationConsumption.test_cal_nssf_003_tds_values_validate_against_fixture
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.std_engine.tests.test_be_15_step1_activation_consumption \
		--test kentender_procurement.std_engine.tests.test_be_15_step1_activation_consumption.TestBe15Step1ActivationConsumption.test_cal_nssf_012_render_uses_official_locked_text
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.std_engine.tests.test_be_15_step1_activation_consumption \
		--test kentender_procurement.std_engine.tests.test_be_15_step1_activation_consumption.TestBe15Step1ActivationConsumption.test_cal_nssf_013_fixture_activation_blocked

it-wizard-static-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.it_tender_wizard.tests.test_it_wizard_ui_dashboard_layout_guard
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.it_tender_wizard.tests.test_it_wizard_ui_std_config_overview_layout_guard
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.it_tender_wizard.tests.test_it_wizard_ui_tender_profile_layout_guard
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.it_tender_wizard.tests.test_it_wizard_ui_tds_layout_guard
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.it_tender_wizard.tests.test_it_wizard_ui_it_requirements_layout_guard
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.it_tender_wizard.tests.test_it_wizard_ui_implementation_schedule_layout_guard
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.it_tender_wizard.tests.test_it_wizard_ui_system_inventory_layout_guard
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.it_tender_wizard.tests.test_it_wizard_ui_price_schedule_layout_guard
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.it_tender_wizard.tests.test_it_wizard_ui_evaluation_setup_layout_guard
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.it_tender_wizard.tests.test_it_wizard_ui_forms_and_evidence_layout_guard
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.it_tender_wizard.tests.test_it_wizard_ui_scc_layout_guard
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.it_tender_wizard.tests.test_it_wizard_ui_validation_report_layout_guard
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.it_tender_wizard.tests.test_it_wizard_ui_review_and_approval_layout_guard
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.it_tender_wizard.tests.test_it_wizard_ui_render_preview_layout_guard
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.it_tender_wizard.tests.test_it_wizard_ui_publication_readiness_layout_guard

it-wizard-dashboard-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.it_tender_wizard.tests.test_wizard_instance_service
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.it_tender_wizard.tests.test_wizard_overview_service
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.it_tender_wizard.tests.test_instance_api
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.it_tender_wizard.tests.test_dashboard_kpi_service
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.it_tender_wizard.tests.test_wizard_tender_profile_service
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.it_tender_wizard.tests.test_wizard_tds_service
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.it_tender_wizard.tests.test_it_wizard_tds_desk_wiring
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.it_tender_wizard.tests.test_it_wizard_tender_profile_desk_wiring
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.it_tender_wizard.tests.test_it_wizard_dashboard_desk_wiring
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.it_tender_wizard.tests.test_it_wizard_overview_desk_wiring
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.it_tender_wizard.tests.test_it_wizard_navigation_contract
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test tests/ui/smoke/it-std-wizard/dashboard-desk-wiring.spec.ts
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test tests/ui/smoke/it-std-wizard/overview-desk-wiring.spec.ts
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test tests/ui/smoke/it-std-wizard/tender-profile-desk-wiring.spec.ts
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test tests/ui/smoke/it-std-wizard/tds-desk-wiring.spec.ts

seed-stable-platform:
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_core.seeds.seed_stable_platform.run

seed-stable-platform-reset:
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_core.seeds.seed_stable_platform.run --kwargs '{"reset": true}'

seed-stable-platform-validate:
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_core.seeds.seed_stable_platform.validate
