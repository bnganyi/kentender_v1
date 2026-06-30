# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""Realistic DIA demand seed — replaces test/placeholder data with 28 MoH procurement scenarios.

Clears ALL demand records on the site (including test debris), then re-creates
28 realistic demands across all four MOH departments, all three requisition types
(Goods, Works, Services), and all lifecycle stages.

Usage (via bench console or Python):
    from kentender_procurement.demand_intake.seeds.seed_dia_realistic import run
    run()

Prerequisites (run once per site):
    from kentender_core.seeds.seed_core_minimal import run; run()
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import today

from kentender_core.seeds import constants as C
from kentender_core.seeds._common import find_department
from kentender_procurement.demand_intake.seeds.dia_seed_common import ensure_core_prerequisites

# ── Seed users ────────────────────────────────────────────────────────────────

U_REQ  = "requisitioner@moh.test"
U_HOD  = "hod.approver@moh.test"
U_FIN  = "finance.reviewer@moh.test"
U_PLAN = "planner@moh.test"

# Business IDs reserved for this realistic seed
REALISTIC_DEMAND_IDS: tuple[str, ...] = tuple(
    f"DIA-MOH-2026-{i:04d}" for i in range(1, 29)
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _dept(label: str) -> str:
    d = find_department(label, C.ENTITY_MOH)
    if not d:
        frappe.throw(
            f"Department '{label}' not found for MOH. Run seed_core_minimal first.",
            title="seed_dia_realistic",
        )
    return d


def _items(*rows: tuple) -> list[dict]:
    """rows: (description, category, uom, qty, unit_cost)"""
    return [
        {
            "item_description": r[0],
            "category": r[1],
            "uom": r[2],
            "quantity": r[3],
            "estimated_unit_cost": r[4],
        }
        for r in rows
    ]


# ── Demand catalogue ──────────────────────────────────────────────────────────
# Columns: id, title, dept, req_type, demand_type, priority, status,
#          required_by_date, beneficiary_summary, specification_summary,
#          items: [(desc, category, uom, qty, unit_cost)]

_DEMANDS: list[dict[str, Any]] = [

    # ── CLINICAL SERVICES — Goods ─────────────────────────────────────────────

    {
        "id": "DIA-MOH-2026-0001",
        "title": "Ultrasound Diagnostic Machines — Level 4 Hospitals (10 Units)",
        "dept": C.DEPT_CLIN,
        "req_type": "Goods", "demand_type": "Planned", "priority": "High",
        "status": "Draft",
        "required_by_date": "2026-12-31",
        "beneficiary_summary": (
            "Ten county-level hospitals currently share two portable ultrasound units. "
            "This creates a critical bottleneck for obstetric and abdominal imaging, delaying "
            "diagnoses for an estimated 4,200 outpatients per month."
        ),
        "specification_summary": (
            "Portable cart-based ultrasound units, minimum 3.5 MHz convex probe, colour Doppler, "
            "USB export, 15-inch display. Includes 2-year on-site warranty and user training."
        ),
        "items": _items(
            ("Portable Ultrasound Machine, 3.5 MHz Convex Probe + Doppler", "Medical Equipment", "Units", 10, 950_000),
        ),
    },

    {
        "id": "DIA-MOH-2026-0002",
        "title": "Essential Medicines Replenishment — Q3 2026 (National Stock)",
        "dept": C.DEPT_CLIN,
        "req_type": "Goods", "demand_type": "Planned", "priority": "Critical",
        "status": "Pending HoD Approval",
        "required_by_date": "2026-09-30",
        "beneficiary_summary": (
            "National essential medicines buffer stock is projected to fall below 3-month "
            "safety stock for 14 tracer medicines by end of Q2. Replenishment covers 47 counties."
        ),
        "specification_summary": (
            "WHO/KEBS-compliant generic pharmaceuticals per attached item schedule. Cold-chain "
            "compliant delivery to Kenya Medical Supplies Authority (KEMSA) central warehouse. "
            "Shelf life minimum 24 months at delivery."
        ),
        "items": _items(
            ("Amoxicillin 500 mg Capsules (1,000 count packs)",     "Pharmaceuticals", "Packs",  8_000, 850),
            ("Metformin 500 mg Tablets (1,000 count packs)",        "Pharmaceuticals", "Packs",  5_000, 620),
            ("Paracetamol 500 mg Tablets (1,000 count packs)",      "Pharmaceuticals", "Packs", 10_000, 420),
            ("Oral Rehydration Salts — Sachet (100-sachet cartons)", "Pharmaceuticals", "Cartons", 3_000, 480),
            ("Zinc Sulfate 20 mg Dispersible Tablets (100-tab packs)","Pharmaceuticals","Packs",  2_000, 960),
        ),
    },

    {
        "id": "DIA-MOH-2026-0003",
        "title": "Biomedical Equipment Maintenance Services — Annual Contract 2026/27",
        "dept": C.DEPT_CLIN,
        "req_type": "Services", "demand_type": "Planned", "priority": "Normal",
        "status": "Pending Finance Approval",
        "required_by_date": "2027-06-30",
        "beneficiary_summary": (
            "Annual preventive maintenance and corrective repair for 340 biomedical equipment items "
            "across 12 hospitals. Current ad-hoc repairs cause average 18-day equipment downtime, "
            "affecting diagnostic throughput."
        ),
        "specification_summary": (
            "Full-service contract: quarterly preventive maintenance visits, 48-hour emergency "
            "response SLA, spare parts included up to KES 50,000 per item per visit. Certified "
            "biomedical engineers required. Monthly performance reports."
        ),
        "items": _items(
            ("Biomedical Equipment Preventive Maintenance — Annual (340 items)", "Maintenance Services", "Contract", 1, 5_100_000),
        ),
    },

    {
        "id": "DIA-MOH-2026-0004",
        "title": "Surgical Instrument Sets — Level 4 Hospitals (24 Sets)",
        "dept": C.DEPT_CLIN,
        "req_type": "Goods", "demand_type": "Planned", "priority": "Normal",
        "status": "Approved",
        "required_by_date": "2026-10-31",
        "beneficiary_summary": (
            "Eighteen level-4 hospitals and six sub-county hospitals are operating with incomplete "
            "surgical instrument sets, limiting theatre utilisation to 60% of rated capacity."
        ),
        "specification_summary": (
            "Complete general surgery instrument set per WHO/MOH standards: scalpels, forceps, "
            "retractors, needle holders, scissors — stainless steel grade 316L, autoclave-compatible, "
            "with instrument count list and carrying case."
        ),
        "items": _items(
            ("General Surgery Instrument Set, Grade 316L SS, WHO Standard", "Medical Equipment", "Sets", 24, 150_000),
        ),
    },

    {
        "id": "DIA-MOH-2026-0005",
        "title": "Medical Waste Disposal Services — FY 2026/27 Contract",
        "dept": C.DEPT_CLIN,
        "req_type": "Services", "demand_type": "Planned", "priority": "Normal",
        "status": "Planning Ready",
        "required_by_date": "2027-06-30",
        "beneficiary_summary": (
            "Compliant medical waste disposal for 8 MOH facilities. Current contract expires "
            "30 June 2026. Uninterrupted service required to maintain NEMA licensing compliance."
        ),
        "specification_summary": (
            "Collection, transportation, and incineration of Category A/B medical waste. "
            "Licensed by NEMA and county environmental authority. Weekly scheduled collection, "
            "monthly manifests, incident reporting within 24 hours."
        ),
        "items": _items(
            ("Medical Waste Disposal — Annual Service (8 Facilities)", "Environmental Services", "Contract", 1, 3_600_000),
        ),
    },

    {
        "id": "DIA-MOH-2026-0006",
        "title": "Neonatal Incubators — MCH Units Upgrade (8 Units)",
        "dept": C.DEPT_CLIN,
        "req_type": "Goods", "demand_type": "Planned", "priority": "High",
        "status": "Rejected",
        "required_by_date": "2026-11-30",
        "beneficiary_summary": (
            "Eight mother-and-child health units require incubator replacements. Current units "
            "are 12–15 years old with frequent breakdowns, increasing neonatal mortality risk."
        ),
        "specification_summary": (
            "Servo-controlled incubators, humidity range 20–95%, temperature 25–39°C, "
            "integrated alarm system, oxygen port, access ports. ISO 13485-certified manufacturer."
        ),
        "items": _items(
            ("Neonatal Servo-Controlled Incubator, ISO 13485 Certified", "Medical Equipment", "Units", 8, 1_200_000),
        ),
    },

    {
        "id": "DIA-MOH-2026-0007",
        "title": "Blood Bank Refrigeration Units — County Hospitals (3 Units)",
        "dept": C.DEPT_CLIN,
        "req_type": "Goods", "demand_type": "Planned", "priority": "Normal",
        "status": "Cancelled",
        "required_by_date": "2026-12-31",
        "beneficiary_summary": (
            "Three county referral hospitals require blood bank refrigeration units to replace "
            "non-compliant household refrigerators currently used to store blood products."
        ),
        "specification_summary": (
            "Purpose-built blood bank refrigerator, 4±2°C, 200–300L capacity, "
            "audible and visual alarm, digital temperature logging, forced-air circulation."
        ),
        "items": _items(
            ("Blood Bank Refrigerator, 250L, 4±2°C, Digital Logging", "Medical Equipment", "Units", 3, 2_466_667),
        ),
    },

    {
        "id": "DIA-MOH-2026-0008",
        "title": "Emergency Malaria Treatment Medicines — Outbreak Response (Kwale)",
        "dept": C.DEPT_CLIN,
        "req_type": "Goods", "demand_type": "Emergency", "priority": "Critical",
        "status": "Approved",
        "required_by_date": "2026-08-15",
        "beneficiary_summary": (
            "Emergency procurement triggered by WHO malaria alert for Kwale and Kilifi counties. "
            "Current county health stores have fewer than 10 days of Artemether-Lumefantrine "
            "remaining. This demand covers treatment for an estimated 50,000 cases."
        ),
        "specification_summary": (
            "Artemether 20 mg + Lumefantrine 120 mg tablets — co-formulated blister packs (24 tablets). "
            "WHO pre-qualified or KEBS-certified. Emergency airfreight delivery acceptable."
        ),
        "items": _items(
            ("Artemether 20mg/Lumefantrine 120mg Tablets — 24-tab blister", "Pharmaceuticals", "Packs", 50_000, 300),
        ),
    },

    {
        "id": "DIA-MOH-2026-0009",
        "title": "Laboratory Reagents and Consumables — FY 2026 Annual Supply",
        "dept": C.DEPT_CLIN,
        "req_type": "Goods", "demand_type": "Planned", "priority": "Normal",
        "status": "Pending Finance Approval",
        "required_by_date": "2026-12-31",
        "beneficiary_summary": (
            "Annual supply of laboratory reagents and consumables for 22 referral laboratories. "
            "Stock-outs of haematology and biochemistry reagents currently affect diagnostic "
            "services for an estimated 15,000 patients monthly."
        ),
        "specification_summary": (
            "Full-blood count reagents, liver function test kits, renal function kits, blood "
            "glucose strips, HIV test kits (rapid), specimen collection tubes. "
            "ISO 15189-compatible, with cold-chain delivery certification."
        ),
        "items": _items(
            ("Full Blood Count Reagent Kit (500 tests)",        "Laboratory Supplies", "Kits",    200, 8_500),
            ("Liver/Renal Function Reagent Pack (100 tests)",   "Laboratory Supplies", "Packs",   400, 4_200),
            ("HIV Rapid Test Kit — WHO Pre-qualified (25 tests)","Laboratory Supplies", "Boxes", 1_500, 1_800),
            ("EDTA Specimen Collection Tubes — 100-pack",       "Laboratory Supplies", "Packs",   800,   950),
        ),
    },

    {
        "id": "DIA-MOH-2026-0010",
        "title": "Portable Oxygen Concentrators — Rural Dispensaries (30 Units)",
        "dept": C.DEPT_CLIN,
        "req_type": "Goods", "demand_type": "Planned", "priority": "High",
        "status": "Approved",
        "required_by_date": "2026-11-30",
        "beneficiary_summary": (
            "Thirty rural dispensaries and health centres lack reliable oxygen supply for "
            "neonatal and acute respiratory care. Oxygen concentrators remove dependency on "
            "cylinder delivery logistics in hard-to-reach areas."
        ),
        "specification_summary": (
            "Portable oxygen concentrators, output 1–5 L/min, oxygen purity ≥93%, "
            "weight <8 kg, integrated low-oxygen alarm, 2-year warranty, user training included."
        ),
        "items": _items(
            ("Portable Oxygen Concentrator, 5 L/min, ≥93% Purity", "Medical Equipment", "Units", 30, 291_667),
        ),
    },

    # ── HUMAN RESOURCES — Services ────────────────────────────────────────────

    {
        "id": "DIA-MOH-2026-0011",
        "title": "Clinical Skills Refresher Training — Nurses Cadre (200 Staff)",
        "dept": C.DEPT_HR,
        "req_type": "Services", "demand_type": "Planned", "priority": "Normal",
        "status": "Planning Ready",
        "required_by_date": "2026-12-31",
        "beneficiary_summary": (
            "Two hundred registered nurses across 25 facilities require refresher training on "
            "updated clinical protocols (sepsis management, BEOC obstetric care, infection "
            "prevention). Training gap identified in 2025 annual performance review."
        ),
        "specification_summary": (
            "Five-day residential training programme per cohort of 40. Facilitators must be "
            "registered clinical trainers. Training materials, venue, accommodation, and "
            "transport allowances included. Post-training assessment and certification required."
        ),
        "items": _items(
            ("5-Day Clinical Skills Training Programme — Cohort of 40 (5 cohorts)", "Training Services", "Cohorts", 5, 560_000),
        ),
    },

    {
        "id": "DIA-MOH-2026-0012",
        "title": "Leadership and Management Development Programme — Senior Health Officers",
        "dept": C.DEPT_HR,
        "req_type": "Services", "demand_type": "Planned", "priority": "Normal",
        "status": "Pending HoD Approval",
        "required_by_date": "2027-03-31",
        "beneficiary_summary": (
            "Forty senior health officers (grade P/Q and above) across ministry headquarters "
            "and county health departments lack structured leadership development. Programme "
            "targets strategic planning, resource management, and team leadership competencies."
        ),
        "specification_summary": (
            "Six-module blended-learning programme over 12 weeks: two face-to-face residential "
            "modules (3 days each) plus four online modules. Facilitators must hold accreditation "
            "from KASNEB or equivalent. Certificates upon 80% completion."
        ),
        "items": _items(
            ("Leadership Development Programme — 12-week Blended (40 participants)", "Training Services", "Programme", 1, 1_600_000),
        ),
    },

    {
        "id": "DIA-MOH-2026-0013",
        "title": "Staff Uniforms and Personal Protective Equipment — FY 2026 Annual Supply",
        "dept": C.DEPT_HR,
        "req_type": "Goods", "demand_type": "Planned", "priority": "Normal",
        "status": "Approved",
        "required_by_date": "2026-09-30",
        "beneficiary_summary": (
            "Annual uniform and PPE supply for 1,500 MOH staff at headquarters and 15 "
            "attached facilities. Previous contract expired March 2026. Uniforms are mandatory "
            "for patient-facing roles under MOH HR policy §6.4."
        ),
        "specification_summary": (
            "Cotton/polyester uniforms per gender-specific MOH design specifications, "
            "two sets per staff. PPE: reusable face shields, disposable gloves (box of 100), "
            "disposable aprons. KEBS-certified manufacturer required."
        ),
        "items": _items(
            ("Clinical Uniform Set — MOH Standard (2 pieces per set)", "Uniforms", "Sets", 1_500, 1_200),
            ("Disposable Examination Gloves — 100-pair box",           "PPE",      "Boxes",   300,  850),
            ("Reusable Face Shield, Anti-fog Polycarbonate",           "PPE",      "Units",   600,  450),
        ),
    },

    {
        "id": "DIA-MOH-2026-0014",
        "title": "HR Information System Upgrade — Consultancy and Implementation",
        "dept": C.DEPT_HR,
        "req_type": "Services", "demand_type": "Planned", "priority": "Normal",
        "status": "Draft",
        "required_by_date": "2027-06-30",
        "beneficiary_summary": (
            "Current HRIS (deployed 2018) does not support payroll integration, leave "
            "management automation, or performance tracking for the 4,200 MOH staff on "
            "establishment. Manual processes cause monthly payroll errors affecting ~180 staff."
        ),
        "specification_summary": (
            "System requirements analysis, vendor selection support, implementation oversight, "
            "change management, and go-live support for a cloud-based HRIS. Includes 6-month "
            "hypercare post-go-live. Consultants must have prior ERP/HRIS experience in GoK context."
        ),
        "items": _items(
            ("HRIS Upgrade Consultancy — Requirements, Implementation & Hypercare", "ICT Consultancy", "Contract", 1, 4_200_000),
        ),
    },

    {
        "id": "DIA-MOH-2026-0015",
        "title": "Community Health Worker Capacity Building — Digital Health Tools (1,200 CHWs)",
        "dept": C.DEPT_HR,
        "req_type": "Services", "demand_type": "Planned", "priority": "High",
        "status": "Pending HoD Approval",
        "required_by_date": "2026-12-31",
        "beneficiary_summary": (
            "1,200 community health workers across 18 sub-counties transitioning to digital "
            "health data collection (KenyaEMR/CommCare). Training required before Q4 device "
            "rollout to ensure data quality and CHW confidence with the platform."
        ),
        "specification_summary": (
            "Three-day training programme per cohort of 30, delivered in sub-county venues. "
            "Practical device handling, data entry, synchronisation, and troubleshooting. "
            "Facilitated by ICT-trained community health supervisors. Job aids and user guides included."
        ),
        "items": _items(
            ("CHW Digital Health Training — 3-day cohort (40 cohorts × 30 participants)", "Training Services", "Cohorts", 40, 85_000),
        ),
    },

    {
        "id": "DIA-MOH-2026-0016",
        "title": "Biomedical Equipment Operator Training — Clinical and Technical Staff",
        "dept": C.DEPT_HR,
        "req_type": "Services", "demand_type": "Planned", "priority": "Normal",
        "status": "Planning Ready",
        "required_by_date": "2026-11-30",
        "beneficiary_summary": (
            "Sixty clinical and technical staff require formal operator certification for "
            "newly deployed imaging and theatre equipment. Improper use is the leading cause "
            "of premature equipment failure (MOH biomedical unit report, Feb 2026)."
        ),
        "specification_summary": (
            "Hands-on certification training: 3 days per equipment type (X-ray, ultrasound, "
            "anaesthesia machine, electrosurgical unit). Manufacturer-authorised trainers. "
            "Competency assessment on final day; certificates required for equipment sign-off."
        ),
        "items": _items(
            ("Equipment Operator Certification Training (60 staff, 4 equipment types)", "Training Services", "Programme", 1, 1_200_000),
        ),
    },

    # ── FINANCE — Services ─────────────────────────────────────────────────────

    {
        "id": "DIA-MOH-2026-0017",
        "title": "External Audit Services — FY 2025/26 Annual Accounts",
        "dept": C.DEPT_FIN,
        "req_type": "Services", "demand_type": "Planned", "priority": "Normal",
        "status": "Approved",
        "required_by_date": "2026-11-30",
        "beneficiary_summary": (
            "Statutory annual audit of MOH financial statements for FY 2025/26. "
            "Submission to the National Treasury and Public Accounts Committee by 30 November 2026 "
            "is a statutory requirement under the Public Finance Management Act."
        ),
        "specification_summary": (
            "External audit of consolidated MOH accounts including all programme funds and "
            "donor-funded projects. Audit firm must be registered with ICPAK and prequalified "
            "by OAG. Includes management letter and follow-up on prior year recommendations."
        ),
        "items": _items(
            ("External Audit Services — MOH FY 2025/26 Consolidated Accounts", "Audit Services", "Contract", 1, 2_400_000),
        ),
    },

    {
        "id": "DIA-MOH-2026-0018",
        "title": "Financial Management System Upgrade — IFMIS Integration Licences",
        "dept": C.DEPT_FIN,
        "req_type": "Goods", "demand_type": "Planned", "priority": "High",
        "status": "Pending Finance Approval",
        "required_by_date": "2027-03-31",
        "beneficiary_summary": (
            "MOH requires upgraded IFMIS-compatible financial management licences to align "
            "with National Treasury circular 2025/06. Current system lacks real-time commitment "
            "control, causing budget over-commitments averaging KES 8.2M per quarter."
        ),
        "specification_summary": (
            "Three-year software licence bundle: budget module, commitment accounting, "
            "procurement interface, reporting dashboard. Includes annual maintenance, "
            "two system updates, and on-site technical support (one visit per quarter)."
        ),
        "items": _items(
            ("IFMIS-Compatible FMS Software Licence — 3-Year Bundle", "Software Licences", "Licences", 1, 3_800_000),
        ),
    },

    {
        "id": "DIA-MOH-2026-0019",
        "title": "Accounting Workstations and Peripherals — Finance Directorate (25 Units)",
        "dept": C.DEPT_FIN,
        "req_type": "Goods", "demand_type": "Planned", "priority": "Normal",
        "status": "Draft",
        "required_by_date": "2026-12-31",
        "beneficiary_summary": (
            "Twenty-five workstations in the Finance Directorate are over 7 years old and "
            "cannot run current IFMIS and payroll software. Hardware failures cause average "
            "4 hours of lost processing time per week per affected user."
        ),
        "specification_summary": (
            "Desktop workstations: Intel Core i7 or equivalent, 16 GB RAM, 512 GB SSD, "
            "Windows 11 Pro, 24-inch monitor, keyboard, mouse. Three-year onsite warranty. "
            "Delivery, installation, and data migration included."
        ),
        "items": _items(
            ("Desktop Workstation, Core i7, 16GB RAM, 512GB SSD, Win11 Pro", "ICT Equipment", "Units", 25, 115_000),
            ("24-inch LED Monitor, IPS Panel",                                "ICT Equipment", "Units", 25,  28_000),
            ("UPS 1000VA — Workstation Protection",                           "ICT Equipment", "Units", 25,  12_000),
        ),
    },

    {
        "id": "DIA-MOH-2026-0020",
        "title": "Internal Audit Consultancy — Q3 and Q4 2026 Performance Audit",
        "dept": C.DEPT_FIN,
        "req_type": "Services", "demand_type": "Planned", "priority": "Normal",
        "status": "Rejected",
        "required_by_date": "2026-12-31",
        "beneficiary_summary": (
            "Performance audit of three MOH programmes to assess value-for-money, "
            "governance compliance, and implementation effectiveness. Required by Audit Committee "
            "resolution dated 15 March 2026."
        ),
        "specification_summary": (
            "Structured performance audit covering: programme design vs delivery assessment, "
            "expenditure vs output analysis, beneficiary interviews, site visits. "
            "Final report to Audit Committee within 8 weeks. ICPAK-registered firm required."
        ),
        "items": _items(
            ("Performance Audit Consultancy — 3 MOH Programmes (Q3–Q4 2026)", "Audit Services", "Contract", 1, 1_800_000),
        ),
    },

    {
        "id": "DIA-MOH-2026-0021",
        "title": "Staff Medical Insurance — Group Cover FY 2026/27 (4,200 Staff + Dependants)",
        "dept": C.DEPT_FIN,
        "req_type": "Services", "demand_type": "Planned", "priority": "Critical",
        "status": "Approved",
        "required_by_date": "2026-09-30",
        "beneficiary_summary": (
            "Annual group medical insurance premium renewal for 4,200 MOH staff and an "
            "estimated 8,400 registered dependants. Current policy expires 30 September 2026. "
            "Lapse would leave staff without medical cover, increasing HR attrition risk."
        ),
        "specification_summary": (
            "In-patient limit KES 1.5M per person per annum, out-patient KES 75,000, "
            "maternity KES 150,000, dental and optical KES 30,000 each. Nationally recognised "
            "insurer with IRA licence. Panel includes all major public referral hospitals."
        ),
        "items": _items(
            ("Group Medical Insurance Premium — 4,200 Staff + 8,400 Dependants", "Insurance Services", "Premium", 1, 22_500_000),
        ),
    },

    {
        "id": "DIA-MOH-2026-0022",
        "title": "Emergency Finance System Continuity — Disaster Recovery Infrastructure",
        "dept": C.DEPT_FIN,
        "req_type": "Goods", "demand_type": "Emergency", "priority": "High",
        "status": "Draft",
        "required_by_date": "2026-10-31",
        "beneficiary_summary": (
            "Following a primary server room flooding incident in June 2026, finance systems "
            "have no functional off-site backup. Business continuity risk classified as High "
            "by ICT unit. Emergency procurement authorised under Financial Regulation 16(2)."
        ),
        "specification_summary": (
            "Network-attached storage (NAS) device, 48 TB usable, RAID-6, off-site replication "
            "capability, rack-mountable. Includes 3-year hardware warranty and 1-year backup "
            "software licence."
        ),
        "items": _items(
            ("Enterprise NAS Storage, 48TB Usable, RAID-6, Rack-Mount", "ICT Equipment", "Units", 1, 2_600_000),
        ),
    },

    # ── PROCUREMENT — Works ────────────────────────────────────────────────────

    {
        "id": "DIA-MOH-2026-0023",
        "title": "Renovation of Central Medical Stores — Structural and Cold-Chain Upgrade",
        "dept": C.DEPT_PROC,
        "req_type": "Works", "demand_type": "Planned", "priority": "High",
        "status": "Approved",
        "required_by_date": "2027-06-30",
        "beneficiary_summary": (
            "Central Medical Stores facility (Nairobi, built 1987) requires structural "
            "rehabilitation and cold-chain room upgrades to support national medicines "
            "distribution. Current facility fails NEMA cold-chain compliance requirements."
        ),
        "specification_summary": (
            "Scope: structural repairs (roof, walls, loading dock), installation of three "
            "walk-in cold rooms (2–8°C, 10m³ each), electrical upgrade (3-phase, 400A), "
            "security fencing and CCTV. Contractor must be NCA-registered Grade 3+. "
            "Supervision by registered structural engineer. 12-month defects liability."
        ),
        "items": _items(
            ("Structural Rehabilitation Works — Central Medical Stores",        "Construction Works", "Lot", 1, 18_500_000),
            ("Walk-in Cold Room Installation (3 × 10m³, 2–8°C)",               "Cold-Chain Works",   "Lot", 1,  7_200_000),
            ("Electrical Upgrade — 3-Phase 400A Supply + CCTV",                 "Electrical Works",   "Lot", 1,  2_800_000),
        ),
    },

    {
        "id": "DIA-MOH-2026-0024",
        "title": "Office Furniture — Procurement Directorate New Fit-out",
        "dept": C.DEPT_PROC,
        "req_type": "Goods", "demand_type": "Planned", "priority": "Normal",
        "status": "Draft",
        "required_by_date": "2026-11-30",
        "beneficiary_summary": (
            "Procurement Directorate relocated to new floor (4th floor, Afya House) in May 2026. "
            "Forty workstations currently lack ergonomic furniture and filing storage, "
            "reducing operational efficiency and creating occupational health risk."
        ),
        "specification_summary": (
            "Adjustable-height desks (ergonomic, electric or manual), ergonomic chairs, "
            "3-drawer pedestal filing cabinets, 4-shelf bookcases, reception counter. "
            "Furniture must meet KEBS standard KS 04-1560."
        ),
        "items": _items(
            ("Ergonomic Adjustable-Height Workstation Desk",   "Office Furniture", "Units", 40, 28_000),
            ("Ergonomic Swivel Office Chair, Lumbar Support",  "Office Furniture", "Units", 40, 12_500),
            ("3-Drawer Pedestal Filing Cabinet, Lockable",     "Office Furniture", "Units", 40,  8_500),
            ("4-Shelf Bookcase, Steel, 1.8m",                  "Office Furniture", "Units", 20,  9_500),
        ),
    },

    {
        "id": "DIA-MOH-2026-0025",
        "title": "MOH HQ Network Infrastructure Upgrade — LAN and Wi-Fi Expansion",
        "dept": C.DEPT_PROC,
        "req_type": "Goods", "demand_type": "Planned", "priority": "High",
        "status": "Planning Ready",
        "required_by_date": "2026-12-31",
        "beneficiary_summary": (
            "Afya House LAN infrastructure (installed 2013) cannot support current bandwidth "
            "demands for 680 network users. Average connection speed is 2 Mbps against a "
            "50 Mbps contracted WAN link, due to switch and access point capacity limits."
        ),
        "specification_summary": (
            "48-port managed Layer 3 switches (×8), 802.11ax Wi-Fi 6 access points (×40), "
            "structured Cat6A cabling for 200 new drops, patch panels, and rack equipment. "
            "Installation, testing, and 2-year warranty included. Cisco or Aruba preferred."
        ),
        "items": _items(
            ("48-Port Managed L3 Switch, 10G Uplink (Cisco/Aruba)",  "ICT Equipment", "Units",  8,  285_000),
            ("Wi-Fi 6 Access Point, 802.11ax, PoE+ (Cisco/Aruba)",  "ICT Equipment", "Units", 40,   75_000),
            ("Cat6A Structured Cabling — 200 drops (supply + install)","ICT Works",  "Lot",    1, 2_500_000),
            ("19-inch 42U Server Rack with Patch Panels",            "ICT Equipment", "Units",  2,   95_000),
        ),
    },

    {
        "id": "DIA-MOH-2026-0026",
        "title": "Solar Backup Power System — Afya House MOH HQ Installation",
        "dept": C.DEPT_PROC,
        "req_type": "Works", "demand_type": "Planned", "priority": "Normal",
        "status": "Pending HoD Approval",
        "required_by_date": "2027-03-31",
        "beneficiary_summary": (
            "Frequent power outages (averaging 6 hours per week) disrupt critical ICT and "
            "medical systems at MOH headquarters. Diesel generator fuel costs are KES 1.8M "
            "per annum. Solar + battery hybrid system will reduce costs by ~70% and improve "
            "uptime to 99.5%."
        ),
        "specification_summary": (
            "Design, supply, and installation of 120 kW rooftop solar PV array with 200 kWh "
            "lithium-iron-phosphate battery storage and smart ATS controller. Grid-tied with "
            "export capability. EPRA-licensed installer. NCA Grade 2+ for civil works. "
            "15-year panel warranty, 10-year battery warranty."
        ),
        "items": _items(
            ("Solar PV System — 120 kW Rooftop Array (Design, Supply, Install)", "Electrical Works", "Lot", 1, 11_200_000),
        ),
    },

    {
        "id": "DIA-MOH-2026-0027",
        "title": "Procurement Compliance and Value-for-Money Audit — FY 2025/26",
        "dept": C.DEPT_PROC,
        "req_type": "Services", "demand_type": "Planned", "priority": "Normal",
        "status": "Approved",
        "required_by_date": "2026-10-31",
        "beneficiary_summary": (
            "Annual independent compliance audit of MOH procurement activities for FY 2025/26. "
            "Required under Public Procurement and Asset Disposal Act, Section 68, and World Bank "
            "project fiduciary assurance terms."
        ),
        "specification_summary": (
            "Post-award audit of 30 sampled contracts: compliance with PPADA, single-source "
            "justification review, contract management assessment, payments audit. "
            "Auditor must be ICPAK-registered. Report due within 6 weeks of engagement."
        ),
        "items": _items(
            ("Procurement Compliance Audit — 30 Contracts, FY 2025/26", "Audit Services", "Contract", 1, 1_500_000),
        ),
    },

    {
        "id": "DIA-MOH-2026-0028",
        "title": "Emergency Cholera Response — Water Treatment Chemicals (Turkana and Marsabit)",
        "dept": C.DEPT_PROC,
        "req_type": "Goods", "demand_type": "Emergency", "priority": "Critical",
        "status": "Pending Finance Approval",
        "required_by_date": "2026-08-31",
        "beneficiary_summary": (
            "Active cholera outbreak in Turkana and Marsabit counties (WHO Alert, 18 June 2026). "
            "County health departments have requested emergency water treatment chemicals for "
            "point-of-use disinfection in 120 affected villages. Estimated population at risk: 85,000."
        ),
        "specification_summary": (
            "Aquatabs (1-tablet/10L sachets), sodium hypochlorite solution (5% for bucket "
            "chlorination), and water testing kits. WHO/UNICEF-approved specification. "
            "Delivery to Lodwar and Marsabit county health stores within 5 working days."
        ),
        "items": _items(
            ("Aquatabs Water Purification Tablets — 10L dose (carton of 1,000)", "Public Health Supplies", "Cartons", 800,  2_500),
            ("Sodium Hypochlorite 5% Solution — 25L drum",                       "Public Health Supplies", "Drums",   120, 12_000),
            ("Field Water Testing Kit — Chlorine/pH",                            "Public Health Supplies", "Kits",     60, 18_000),
        ),
    },
]


# ── Clear helper ──────────────────────────────────────────────────────────────

def _clear_all_demands() -> int:
    """Delete every Demand record on this site."""
    frappe.only_for(("System Manager", "Administrator"))
    count = frappe.db.count("Demand")
    if count:
        frappe.db.delete("Demand Item")
        frappe.db.delete("Demand")
    return count


# ── Builder ───────────────────────────────────────────────────────────────────

_STATUS_FIELDS: dict[str, dict] = {
    "Draft":                    {},
    "Pending HoD Approval":     {"submitted_at": frappe.utils.now_datetime},
    "Pending Finance Approval": {
        "submitted_at":     frappe.utils.now_datetime,
        "hod_approved_at":  frappe.utils.now_datetime,
        "hod_approved_by":  U_HOD,
    },
    "Approved": {
        "submitted_at":       frappe.utils.now_datetime,
        "hod_approved_at":    frappe.utils.now_datetime,
        "hod_approved_by":    U_HOD,
        "finance_approved_at": frappe.utils.now_datetime,
        "finance_approved_by": U_FIN,
        "reservation_status":  "Reserved",
    },
    "Planning Ready": {
        "submitted_at":        frappe.utils.now_datetime,
        "hod_approved_at":     frappe.utils.now_datetime,
        "hod_approved_by":     U_HOD,
        "finance_approved_at": frappe.utils.now_datetime,
        "finance_approved_by": U_FIN,
        "reservation_status":  "Reserved",
        "planning_status":     "Planning Ready",
    },
    "Rejected": {
        "submitted_at":   frappe.utils.now_datetime,
        "rejected_at":    frappe.utils.now_datetime,
        "rejected_by":    U_HOD,
        "rejection_reason": "Does not meet current budget priorities. Resubmit in next planning cycle.",
    },
    "Cancelled": {
        "submitted_at":        frappe.utils.now_datetime,
        "hod_approved_at":     frappe.utils.now_datetime,
        "hod_approved_by":     U_HOD,
        "finance_approved_at": frappe.utils.now_datetime,
        "finance_approved_by": U_FIN,
        "cancelled_at":        frappe.utils.now_datetime,
        "cancelled_by":        U_REQ,
        "cancellation_reason": "Procurement funded from alternative source (donor contribution confirmed).",
    },
}


def _seed_demands() -> dict[str, str]:
    out: dict[str, str] = {}

    for spec in _DEMANDS:
        dept   = _dept(spec["dept"])
        status = spec["status"]

        doc = frappe.get_doc({
            "doctype":            "Demand",
            "demand_id":          spec["id"],
            "title":              spec["title"],
            "procuring_entity":   C.ENTITY_MOH,
            "requesting_department": dept,
            "requested_by":       U_REQ,
            "request_date":       today(),
            "required_by_date":   spec["required_by_date"],
            "priority_level":     spec.get("priority", "Normal"),
            "demand_type":        spec.get("demand_type", "Planned"),
            "requisition_type":   spec["req_type"],
            "beneficiary_summary":   spec.get("beneficiary_summary", ""),
            "specification_summary": spec.get("specification_summary", ""),
            "delivery_location":  "Nairobi HQ",
            "requested_delivery_period_days": 45,
            "items":              spec["items"],
            "status":             "Draft",
        })
        doc.flags.ignore_mandatory = True
        doc.insert(ignore_permissions=True)

        # Ensure the business ID is set correctly
        if frappe.db.get_value("Demand", doc.name, "demand_id") != spec["id"]:
            frappe.db.set_value("Demand", doc.name, "demand_id", spec["id"], update_modified=False)

        # Apply lifecycle state fields directly
        extra_fields: dict = {}
        for k, v in _STATUS_FIELDS.get(status, {}).items():
            extra_fields[k] = v() if callable(v) else v

        if status == "Approved":
            extra_fields["reservation_reference"] = f"SEED-RES-{doc.name}"
        if status == "Planning Ready":
            extra_fields["reservation_reference"] = f"SEED-RES-{doc.name}"

        extra_fields["status"] = status
        frappe.db.set_value("Demand", doc.name, extra_fields, update_modified=False)

        out[spec["id"]] = doc.name

    return out


# ── Entry point ───────────────────────────────────────────────────────────────

def run():
    frappe.only_for(("System Manager", "Administrator"))
    frappe.set_user("Administrator")

    ensure_core_prerequisites()

    cleared = _clear_all_demands()
    mapping = _seed_demands()
    frappe.db.commit()

    return {
        "cleared": cleared,
        "seeded":  len(mapping),
        "demands": mapping,
        "pack":    "seed_dia_realistic",
    }
