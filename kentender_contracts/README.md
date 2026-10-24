### Kentender Contracts

KenTender Contract Management (CM-CHG-001): the agreement, delivery and acceptance, invoices and payment follow-up, and close-out of one contract, with ERPNext holding the stock, asset and accounting records.

**Boundary.** This app depends only on `frappe`, `erpnext` and `kentender_core`, and must install and run without the tendering apps. Award, Budget and supplier accounts reach it through published hooks and guarded adapters (`kentender_contracts/adapters/`); it never imports their code or reads their tables. `tests/test_cm_import_boundary.py` and `make cm-independence-gate` guard this.

**Records** change only through Contract Management commands (`command_write("Contract Management")`), never through a Desk save.

See `docs/mvp-1-r1/21_contract_management/` for the requirements, the implementation plan and the tracker.

### Installation

```bash
cd $PATH_TO_YOUR_BENCH
bench --site <site> install-app kentender_contracts
```

### Tests

Run on the test site only (tests write real rows and nothing rolls them back):

```bash
scripts/test-site.sh run make cm-services-gate
make cm-independence-gate SITE=kentender-test.local   # the site that holds only ERPNext, core, supplier accounts and this app
```
