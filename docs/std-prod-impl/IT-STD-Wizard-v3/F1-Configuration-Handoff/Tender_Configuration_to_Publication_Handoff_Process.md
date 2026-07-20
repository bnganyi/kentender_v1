# Tender Configuration to Publication Workflow Handoff

**Project:** KenTender e-Procurement System  
**Workflow area:** Tender Configurations → Tender Documents → Publications  
**Purpose:** Define the controlled handoff from a confirmed tender document preview into the publication workflow.  
**Status:** Process specification for implementation

---

## 1. Workflow Position

The handoff starts from the **Tender Document Preview** screen in **Tender Configurations**.

The **Confirm Preview** action confirms the generated tender document package. It does **not** publish the tender.

```text
Tender Document Preview
→ Confirm Preview
→ Create confirmed Tender Document Package
→ Enable Send to Publication Workflow
→ Publications module receives package
→ Publications user completes publication setup
→ Publish Tender
```

---

## 2. Confirm Preview

### User action

The user reviews the generated tender document preview and selects:

```text
I have reviewed the generated tender document.
```

Then the user clicks:

```text
Confirm Preview
```

### Confirmation modal

```text
Confirm Tender Document Preview?

This confirms that the generated tender document reflects the approved tender configuration.

This action does not publish the tender, notify bidders, open bid submission, approve an award, or create a contract.

After confirmation, the document package will be locked and may be sent to the publication workflow.

[Cancel] [Confirm Preview]
```

---

## 3. System Action After Confirmation

When the preview is confirmed, the system creates an immutable **Confirmed Tender Document Package**.

The package must include:

| Item | Source |
|---|---|
| Generated tender PDF | Preview renderer |
| Tender configuration ref | Tender Configuration |
| Procurement package ref | Approved Procurement Package |
| STD version | Bound STD Engine version |
| Configuration version | Approved configuration snapshot |
| Bidder submission schema | Generated electronic response schema |
| Evaluation schema | CFG-07 Evaluation Setup |
| Price schedule schema | CFG-06 Price Schedule |
| Forms/evidence schema | CFG-08 Forms & Evidence |
| Contract carry-forward values | CFG-09 Contract Values |
| Readiness report | WG-01 Readiness Check |
| Review approval record | WG-02 Review & Approval |
| Preview confirmation record | WG-03 Tender Document Preview |
| Document hash | Generated at confirmation |

---

## 4. UI State After Confirmation

After confirmation, the preview state changes from:

```text
Generated
```

to:

```text
Preview Confirmed
```

The system must then:

| Action | Required behavior |
|---|---|
| Confirm Preview | Replace with confirmed state |
| Regenerate Preview | Disabled |
| Download Preview PDF | Becomes Download Confirmed PDF |
| Return for Correction | Still available with reason |
| Send to Publication Workflow | Enabled |

Recommended footer/actions:

```text
Back to Configuration Home
Download Confirmed PDF
Return for Correction
Send to Publication Workflow
```

---

## 5. Send to Publication Workflow

### User action

The user clicks:

```text
Send to Publication Workflow
```

### Confirmation modal

```text
Send to Publication Workflow?

This will make the confirmed tender document package available to the Publications team.

This action does not publish the tender, notify bidders, open bid submission, approve an award, or create a contract.

[Cancel] [Send to Publication Workflow]
```

---

## 6. System Action After Handoff

After handoff:

| Object | New state |
|---|---|
| Tender Configuration | Sent to Publication Workflow |
| Tender Document Package | Awaiting Publication Setup |
| Publication Record | Created |
| Generated PDF | Locked |
| Bidder submission schema | Locked for publication setup |
| Configuration values | Read-only for this package |

The publication record must be linked to the confirmed tender document package.

---

## 7. Publications Module Responsibility

The **Publications** module receives a read-only package and manages only publication-specific setup.

Allowed publication setup fields:

| Field | Purpose |
|---|---|
| Publication date/time | When tender becomes visible |
| Clarification deadline | Last time for bidder clarifications |
| Submission deadline | Final bid submission deadline |
| Opening date/time | Bid opening time |
| Supplier visibility | Supplier/public access rules |
| Tender notice | Publication-facing notice |
| Bidder workspace activation | Enables electronic bid response |
| Publish Tender | Final publication action |

---

## 8. Boundary Rules

The Publications module must **not**:

- edit tender configuration values;
- regenerate the tender document;
- change the bound STD version;
- change evaluation criteria;
- change price schedule structure;
- change required bidder forms/evidence;
- change contract carry-forward values.

If changes are required, the publication record must return the package for correction.

---

## 9. Return for Correction

If an issue is found after confirmation but before publication, the user must select:

```text
Return for Correction
```

Required modal:

```text
Return for Correction?

This will invalidate the confirmed preview package and return the tender configuration for correction.

A new readiness check, review approval, and preview confirmation will be required before the tender can be sent again to publication.

Reason for return
[textarea]

[Cancel] [Return for Correction]
```

Resulting state:

| Object | State |
|---|---|
| Tender Configuration | Returned for Correction |
| Tender Document Package | Invalidated |
| Publication Record | Cancelled or Returned |
| Preview Confirmation | Invalidated |

---

## 10. Implementation Contract for Cursor

```text
Implement the WG-03 handoff from Tender Configurations to Publications.

Confirm Preview must create an immutable Confirmed Tender Document Package. It must not publish the tender.

After confirmation, disable preview regeneration and enable Send to Publication Workflow.

Send to Publication Workflow creates a Publication record linked to the confirmed document package and sets the configuration status to Sent to Publication Workflow.

The Publication record must receive:
- tender PDF artifact
- STD version
- configuration version
- bidder submission schema
- evaluation schema
- price schedule schema
- forms/evidence schema
- contract carry-forward values
- readiness report reference
- review approval reference
- preview confirmation record
- document hash

Do not allow Publications to edit tender configuration values or regenerate the tender document.
```

---

## 11. Summary

```text
Confirm Preview locks the tender document package.
Send to Publication Workflow hands it over.
Publish Tender happens later in Publications.
```
