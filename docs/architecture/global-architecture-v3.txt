# KenTender Global Architecture v3

## 1. System Backbone

Strategy  
→ Budget  
→ Demand Intake and Approval  
→ Procurement Planning  
→ Supplier Management  
→ Tendering / Solicitation  
→ Bid Submission & Opening  
→ Evaluation & Award  
→ Contract Management  
→ Contract Execution  
→ Inspection & Acceptance  
→ Stores / Assets  
→ Reporting / Audit

---

## 2. Application Map

### Core
- kentender_core
  - shared masters (entity, department, users, etc.)
  - shared utilities
  - base permissions

---

### Planning Layer
- kentender_strategy
  - strategic plans
  - programs
  - outputs
  - performance targets

- kentender_budget
  - budgets
  - budget lines
  - budget controls

---

### Procurement Transaction Layer
- kentender_procurement
  - Demand Intake and Approval
  - Procurement Planning
  - Tendering / Solicitation
  - Bid Opening
  - Evaluation & Award
  - Contract Management
  - Inspection & Acceptance

---

### Supplier Domain (NEW)
- kentender_suppliers
  - supplier registration
  - supplier onboarding
  - supplier classification
  - supplier performance
  - supplier sanctions / blacklisting

---

### Oversight / Control
- kentender_governance
  - approvals framework
  - delegation of authority

- kentender_compliance
  - regulatory checks
  - audit rules

---

### Execution / Operations
- kentender_stores
  - inventory
  - goods receipt

- kentender_assets
  - asset registration
  - lifecycle

---

### External / Integration
- kentender_integrations
  - IFMIS / finance
  - payment systems
  - external registries

---

### Transparency (NEW)
- kentender_transparency
  - public notices
  - tender publication
  - award publication
  - audit transparency portal

---

## 3. Dependency Direction

Strict downstream flow:

core  
→ strategy  
→ budget  
→ procurement  
→ stores  
→ assets  

Side apps:
- suppliers → referenced by procurement
- governance/compliance → enforce rules
- transparency → read-only publishing
- integrations → external interfaces

---

## 4. Non-Negotiable Rules

1. No upstream dependency allowed
2. No cross-app direct DB writes
3. All logic goes through services
4. Each module must define governance BEFORE build
5. Each module must produce a trusted downstream artifact

---

## 5. Architectural Principle

> Each app owns a domain.  
> Each module owns a lifecycle.  
> Each lifecycle must be governed.