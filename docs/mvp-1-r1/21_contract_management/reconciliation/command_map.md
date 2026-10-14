# CM-CHG-001 v0.8: control → command map

| Control | Value |
|---|---|
| Version | 0.8-command-map.1 |
| Date | 14 October 2026 |
| Source | board dump (`tools/extract_boards.mjs`), CM v0.8 §7 and §§11–11.1, built by `tools/build_contracts.py` (tracker CM8-004); CM-AC-44 |

Every visible control of the 157 boards maps to exactly one command or read of §7, or is local (cancel, close) or navigation. The script reads the controls from the design (primary and secondary actions, page and empty-state actions, dialog actions, next-step fixes, button and link blocks, row links) and fails if one is unmapped. **83 commands and reads** are named in §7. **Status:** *Named* = the §11 / §11.1 row names this control; *Inferred* = the spec names the command or read but not this control on this board (a View-style link opens an exact linked version read-only, §11 View row); *Gap* = the spec names no command for this control (see Gaps). The mapping column and its source line are the authored content of this file (new content for review).

## Controls

| Design | Control | Boards | Kind | Command or read | §11 source line | Status |
|---|---|---|---|---|---|---|
| D-DENIED | Back to contracts | D-DENIED | Read | `GetContractWorkspace` | CM v0.8 line 1231 | Named |
| D-ERR | Back to contracts | D-ERR | Read | `GetContractWorkspace` | CM v0.8 line 1231 | Named |
| D-ERR | Retry | D-ERR | Read | (operation-status projection) | CM v0.8 line 1244 | Named |
| D01 | Clear search | D01-F | Read | (list query) | CM v0.8 line 1230 | Named |
| D01 | Open contract | D01, D01-AUD, D01-T | Read | `GetContractWorkspace` | CM v0.8 line 1231 | Named |
| D01 | Register existing contract | D01, D01-E, D01-F | Navigation | (route /app/contracts/register) | CM v0.8 line 1222 | Named |
| D01-S | Open contract | D01-S | Read | `GetContractWorkspace` | CM v0.8 line 1231 | Named |
| D02 | Download agreement 1 | D02-V | Read | `GetContractHistory` | CM v0.8 line 1667 | Named |
| D02 | Send for signature | D02 | Command | `RequestContractSignatures` | CM v0.8 line 1233 | Named |
| D02 | View agreement 1 | D02, D02-H | Read | `GetContractHistory` | CM v0.8 line 1232 | Named |
| D02 | View award | D02, D02-H | Read | `GetContractHistory` | CM v0.8 line 1232 | Named |
| D02 | View issue | D02-H | Read | `GetContractWorkspace` | CM v0.8 line 1242 | Named |
| D02 | View update status | D02-S | Read | (operation-status projection) | CM v0.8 line 1244 | Named |
| D03 | Report a problem | D03, D03-A | Command | `RecordContractIssue` | CM v0.8 line 1223 | Named |
| D03 | Sign contract | D03, D03-A | Command | `SignContractVersion` | CM v0.8 line 1233 | Named |
| D03 | View agreement | D03-W | Read | `GetContractHistory` | CM v0.8 line 1232 | Named |
| D03 | View agreement 1 | D03, D03-A, D03-W | Read | `GetContractHistory` | CM v0.8 line 1232 | Named |
| D04 | Cancel | D04, D04 · Units | Local | (closes the local dialog or edit; commits nothing) | CM v0.8 line 1245 | Named |
| D04 | Enter unit references | D04, D04 · Units | Local | (local arrival draft; RecordContractArrival commits) | CM v0.8 line 1217 | Named |
| D04 | Record delivery | D04, D04 · Units | Command | `RecordContractArrival` | CM v0.8 line 1234 | Named |
| D04 | Use references | D04 · Units | Local | (local arrival draft; RecordContractArrival commits) | CM v0.8 line 1217 | Named |
| D05 | Cancel | D05 · Record | Local | (closes the local dialog or edit; commits nothing) | CM v0.8 line 1245 | Named |
| D05 | Close | D05 · All | Local | (closes the local dialog) | CM v0.8 line 1245 | Inferred |
| D05 | Record observations | D05, D05 · All … (4 boards) | Navigation | (opens the observation editor; RecordInspectionObservations saves) | CM v0.8 line 1235 | Named |
| D05 | Save observations | D05 · Record | Command | `RecordInspectionObservations` | CM v0.8 line 1235 | Named |
| D05 | View all observations | D05, D05 · All … (4 boards) | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D06 | Prepare report for signing | D06 | Command | `PrepareAcceptanceReport` | CM v0.8 line 1236 | Named |
| D06 | View observations | D06 | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D07 | Cancel | D07 · Correction | Local | (closes the local dialog or edit; commits nothing) | CM v0.8 line 1245 | Named |
| D07 | Request correction | D07, D07 · Correction | Command | `RequestAcceptanceCorrection` | CM v0.8 line 1237 | Named |
| D07 | Send request | D07 · Correction | Command | `RequestAcceptanceCorrection` | CM v0.8 line 1237 | Named |
| D07 | Sign report | D07, D07 · Correction | Command | `SignAcceptanceReport` | CM v0.8 line 1236 | Named |
| D07 | View report | D07-P | Read | `GetContractHistory` | CM v0.8 line 1232 | Named |
| D07 | View update status | D07-P | Read | (operation-status projection) | CM v0.8 line 1244 | Named |
| D08 | Cancel | D08 · Correction | Local | (closes the local dialog or edit; commits nothing) | CM v0.8 line 1245 | Named |
| D08 | Request correction | D08, D08 · Correction | Command | `RequestInvoiceCorrection` | CM v0.8 line 1237 | Named |
| D08 | Send request | D08 · Correction | Command | `RequestInvoiceCorrection` | CM v0.8 line 1237 | Named |
| D08 | Sign certification | D08-C | Command | `SignContractCertification` | CM v0.8 line 1238 | Named |
| D08 | View acceptance report | D08, D08 · Correction, D08-C | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D08-L | View accounting invoice | D08-L | Read | (native record projection) | CM v0.8 line 1239 | Named |
| D08-L | View correction | D08-L | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D09 | Cancel | D09-F | Local | (closes the local dialog or edit; commits nothing) | CM v0.8 line 1245 | Named |
| D09 | Review latest version | D09-F · Stale | Read | `GetContractWorkspace` | CM v0.8 line 588 | Inferred |
| D09 | Save draft | D09-F | Command | `SaveNativeFinanceDraft` | CM v0.8 line 1240 | Named |
| D09 | Submit payment for approval | D09-F | Command | `SubmitNativeFinanceForApproval` | CM v0.8 line 1240 | Named |
| D09 | View certification | D09, D09-AUD … (5 boards) | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D09 | View payment record | D09, D09-AUD, D09-T | Read | (native record projection) | CM v0.8 line 1239 | Named |
| D10 | Open | D10 | Read | `GetContractWorkspace` | CM v0.8 line 1231 | Named |
| D10 | Open replacement issue | D10 | Read | `GetContractWorkspace` | CM v0.8 line 1242 | Named |
| D10 | View agreement | D10 | Read | `GetContractHistory` | CM v0.8 line 1232 | Named |
| D11 | Cancel | D11 · Return | Local | (closes the local dialog or edit; commits nothing) | CM v0.8 line 1245 | Named |
| D11 | Return | D11 · Return | Command | `ReturnContractCloseout` | CM v0.8 line 1243 | Named |
| D11 | Return for correction | D11, D11 · Return | Command | `ReturnContractCloseout` | CM v0.8 line 1243 | Named |
| D11 | Sign close-out | D11, D11 · Return | Command | `SignContractCloseout` | CM v0.8 line 1243 | Named |
| D11 | View claim | D11-B | Read | `GetContractWorkspace` | CM v0.8 line 1242 | Named |
| D11 | View close-out record | D11-C | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D11 | View history | D11-C | Read | `GetContractHistory` | CM v0.8 line 1232 | Named |
| D11 | View remaining obligations | D11-B | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D11 | View settlement | D11-T | Read | (native record projection) | CM v0.8 line 1239 | Named |
| D11 | View termination record | D11-T | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D12 | Cancel | D12, D12-G | Local | (closes the local dialog or edit; commits nothing) | CM v0.8 line 1245 | Named |
| D12 | Save and review | D12, D12-G | Command | `RegisterExistingContract`, `ReviseContractIntake` | CM v0.8 line 1222 | Named |
| D13 | Report a new issue | D13-C | Command | `RecordContractIssue` | CM v0.8 line 1223 | Named |
| D13 | Send message | D13 | Command | `SendContractCorrespondence` | CM v0.8 line 1223 | Named |
| D13 | Send reply | D13-S | Command | `ReplyContractCorrespondence` | CM v0.8 line 1223 | Named |
| D13 | View acceptance report | D13, D13-S | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D13 | View replacement acceptance | D13-C | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D14 | Approve extension | D14, D14 · Approve, D14 · Decline | Command | `DecideContractChange` | CM v0.8 line 1224 | Named |
| D14 | Cancel | D14 · Approve, D14 · Decline | Local | (closes the local dialog or edit; commits nothing) | CM v0.8 line 1245 | Named |
| D14 | Confirm decision | D14 · Approve, D14 · Decline | Command | `DecideContractChange` | CM v0.8 line 1224 | Named |
| D14 | Current committee recommendation 1 | D14, D14 · Approve, D14 · Decline | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D14 | Decline | D14, D14 · Approve, D14 · Decline | Command | `DecideContractChange` | CM v0.8 line 1224 | Named |
| D14 | Legal review 1 | D14, D14 · Approve, D14 · Decline | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D14 | Return for correction | D14, D14 · Approve, D14 · Decline | Command | `ReturnContractChange` | CM v0.8 line 1224 | Named |
| D14 | Supplier request 1 | D14, D14 · Approve, D14 · Decline | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D14 | Technical review 1 | D14, D14 · Approve, D14 · Decline | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D14 | View amendment | D14-P | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D14 | View decision | D14-P | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D15 | Cancel | D15-L · Evidence | Local | (closes the local dialog or edit; commits nothing) | CM v0.8 line 1245 | Named |
| D15 | Record source evidence | D15-L, D15-L · Evidence | Command | `RecordLegalSourceEvidence` | CM v0.8 line 1226 | Named |
| D15 | Save evidence | D15-L · Evidence | Command | `RecordLegalSourceEvidence` | CM v0.8 line 1226 | Named |
| D15 | Submit report | D15 | Command | `SubmitContractReport` | CM v0.8 line 1226 | Named |
| D15 | View contract | D15 | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D15 | View signing record | D15-L, D15-L · Evidence | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D15 | View source event | D15-L, D15-L · Evidence | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D16 | Record return | D16 | Command | `RecordSecurityAction` | CM v0.8 line 1227 | Named |
| D16 | Send notice | D16-W | Command | `SendContractCorrespondence` | CM v0.8 line 1223 | Named |
| D16 | View claim history | D16-P | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D16 | View guarantee | D16 | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D16 | View notice | D16-P | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D16 | View warranty | D16-W | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D17 | Approve payment | D17, D17 · Return | Command | `ApproveNativeFinanceRecord` | CM v0.8 line 1241 | Named |
| D17 | Cancel | D17 · Return | Local | (closes the local dialog or edit; commits nothing) | CM v0.8 line 1245 | Named |
| D17 | Confirm payment | D17-S | Command | `RecordFinanceSettlement` | CM v0.8 line 1228 | Named |
| D17 | Return payment | D17 · Return | Command | `ReturnNativeFinanceForCorrection` | CM v0.8 line 1241 | Named |
| D17 | Return payment for correction | D17, D17 · Return | Command | `ReturnNativeFinanceForCorrection` | CM v0.8 line 1241 | Named |
| D17 | View certification | D17, D17 · Return | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D17 | View missing certification | D17-H | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D17 | View payment record | D17 · Posted, D17-S | Read | (native record projection) | CM v0.8 line 1239 | Named |
| D17 | View update status | D17 · Pending | Read | (operation-status projection) | CM v0.8 line 1244 | Named |
| D18 | Cancel | D18, D18-C | Local | (closes the local dialog or edit; commits nothing) | CM v0.8 line 1245 | Named |
| D18 | Submit correction | D18-C | Command | `CorrectContractInvoice` | CM v0.8 line 1229 | Named |
| D18 | Submit invoice | D18 | Command | `SubmitContractInvoice` | CM v0.8 line 1229 | Named |
| D18 | View acceptance | D18-R | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D18 | View invoice | D18-R | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D19 | Request correction | D19 | Command | `RequestAcceptanceCorrection` | CM v0.8 line 1237 | Named |
| D19 | Sign technical certificate | D19 | Command | `SignTechnicalCertificate` | CM v0.8 line 1227 | Named |
| D20 | Approve termination | D20, D20 · Decline | Command | `DecideContractTermination` | CM v0.8 line 1225 | Named |
| D20 | Cancel | D20 · Decline | Local | (closes the local dialog or edit; commits nothing) | CM v0.8 line 1245 | Named |
| D20 | Confirm decision | D20 · Decline | Command | `DecideContractTermination` | CM v0.8 line 1225 | Named |
| D20 | Contract clause 8 | D20, D20 · Decline … (4 boards) | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D20 | Cure-period record | D20, D20 · Decline … (4 boards) | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D20 | Decline | D20, D20 · Decline | Command | `DecideContractTermination` | CM v0.8 line 1225 | Named |
| D20 | Default notice and delivery proof | D20, D20 · Decline … (4 boards) | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D20 | Legal advice 1 | D20, D20 · Decline … (4 boards) | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D20 | Return for correction | D20, D20 · Decline | Command | `ReturnContractTermination` | CM v0.8 line 1225 | Named |
| D20 | Settlement calculation 1 | D20, D20 · Decline … (4 boards) | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D20 | View delivery status | D20-P | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D20 | View notice | D20-P | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D20 | View settlement | D20-T | Read | (native record projection) | CM v0.8 line 1239 | Named |
| D20 | View termination record | D20-T | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D21 | Confirm opening position | D21 | Command | `ConfirmOpeningPosition` | CM v0.8 line 1222 | Named |
| D21 | Report difference | D21 | Command | `RecordContractIssue` | CM v0.8 line 1223 | Named |
| D21 | Start management | D21-H | Command | `StartContractManagement` | CM v0.8 line 1222 | Named |
| D21 | View source contract | D21-H | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D22 | Sign and issue certificate | D22 | Command | `IssueCompletionCertificate` | CM v0.8 line 1227 | Named |
| D22 | View certificate | D22-P | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D22 | View completion evidence | D22 | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D22 | View delivery status | D22-P | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D23 | Appoint | D23 · Appoint | Command | `AppointContractInspectors` | CM v0.8 line 1211 | Named |
| D23 | Appoint inspectors | D23, D23 · Appoint, D23 · Return | Command | `AppointContractInspectors` | CM v0.8 line 1211 | Named |
| D23 | Cancel | D23 · Appoint, D23 · Return, D23-R | Local | (closes the local dialog or edit; commits nothing) | CM v0.8 line 1245 | Named |
| D23 | Recommend inspectors | D23-R | Command | `RecommendContractInspectors` | CM v0.8 line 1211 | Named |
| D23 | Return | D23 · Return | Command | `ReturnContractAppointment` | CM v0.8 line 1211 | Named |
| D23 | Return for correction | D23, D23 · Appoint, D23 · Return | Command | `ReturnContractAppointment` | CM v0.8 line 1211 | Named |
| D23 | View appointment | D23-P | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D23 | View recommendation | D23, D23 · Appoint, D23 · Return | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D24 | Revise appointment recommendation | D24-X | Command | `RecommendContractInspectors` | CM v0.8 line 1211 | Named |
| D24 | Save declaration | D24, D24-C | Command | `DeclareContractInterest` | CM v0.8 line 1211 | Named |
| D24 | View appointment | D24, D24-C, D24-S | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D24 | View declaration | D24-X | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D25 | Cancel | D25 · Reject, D25 · Verify, D25-R | Local | (closes the local dialog or edit; commits nothing) | CM v0.8 line 1245 | Named |
| D25 | Reject | D25 · Reject | Command | `RejectContractSecurity` | CM v0.8 line 1212 | Named |
| D25 | Reject security | D25, D25 · Reject, D25 · Verify | Command | `RejectContractSecurity` | CM v0.8 line 1212 | Named |
| D25 | Save security | D25-R | Command | `RecordContractSecurity` | CM v0.8 line 1212 | Named |
| D25 | Verify | D25 · Verify | Command | `VerifyContractSecurity` | CM v0.8 line 1212 | Named |
| D25 | Verify security | D25, D25 · Reject, D25 · Verify | Command | `VerifyContractSecurity` | CM v0.8 line 1212 | Named |
| D25 | View contract | D25-J | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D25 | View guarantee | D25, D25 · Reject, D25 · Verify | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D25 | View rejection | D25-J | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D26 | Confirm signature evidence | D26-E | Command | `ConfirmOutsideSignatureEvidence` | CM v0.8 line 1213 | Named |
| D26 | Record source evidence | D26-H | Command | `RecordLegalSourceEvidence` | CM v0.8 line 1226 | Named |
| D26 | Report a problem | D26-E | Command | `RecordContractIssue` | CM v0.8 line 1223 | Named |
| D26 | Save signature evidence | D26 | Command | `RecordOutsideContractSignature` | CM v0.8 line 1213 | Named |
| D26 | Signed agreement 1 — entity | D26-E | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D26 | Signed agreement 1 — supplier | D26-E | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D26 | View agreement 1 | D26 | Read | `GetContractHistory` | CM v0.8 line 1232 | Named |
| D26 | View differences | D26-H | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D27 | Cancel | D27 | Local | (closes the local dialog or edit; commits nothing) | CM v0.8 line 1245 | Named |
| D27 | Report a problem | D27-A | Command | `RecordContractIssue` | CM v0.8 line 1223 | Named |
| D27 | Request extension | D27 | Command | `RequestContractChange` | CM v0.8 line 1214 | Named |
| D27 | Return for correction | D27-R | Command | `ReturnContractChange` | CM v0.8 line 1224 | Named |
| D27 | Sign amendment | D27-A | Command | `SignContractVersion` | CM v0.8 line 1214 | Named |
| D27 | Submit change for decision | D27-R | Command | `SubmitContractChangeForDecision` | CM v0.8 line 1214 | Named |
| D27 | View amendment 1 | D27-A | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D27 | View appointment | D27 · Blocked | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D28 | Cancel | D28-F · Editor | Local | (closes the local dialog or edit; commits nothing) | CM v0.8 line 1245 | Named |
| D28 | Original settlement | D28-V | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D28 | Prepare payment | D28-F | Navigation | (opens the KenTender payment editor) | CM v0.8 line 1219 | Named |
| D28 | Reversal | D28-V | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D28 | Save draft | D28-F · Editor | Command | `SaveNativeFinanceDraft` | CM v0.8 line 1240 | Named |
| D28 | Submit payment for approval | D28-F · Editor | Command | `SubmitNativeFinanceForApproval` | CM v0.8 line 1240 | Named |
| D28 | View certification | D28, D28-C … (4 boards) | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D28 | View settlement | D28, D28-C, D28-V | Read | (native record projection) | CM v0.8 line 1239 | Named |
| D29 | Sign advance certification | D29 | Command | `SignAdvanceCertification` | CM v0.8 line 1216 | Named |
| D29 | Sign certification | D29-R | Command | `SignContractCertification` | CM v0.8 line 1238 | Named |
| D29 | View advance clause | D29, D29-R | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D29 | View guarantee | D29, D29-H | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D29 | View issue | D29-H | Read | `GetContractWorkspace` | CM v0.8 line 1242 | Named |
| D31 | Save observations | D31 | Command | `RecordInspectionObservations` | CM v0.8 line 1235 | Named |
| D31 | Sign report | D31-A | Command | `SignAcceptanceReport` | CM v0.8 line 1236 | Named |
| D31 | View service requirement | D31 | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D32 | Cancel | D32 · Return | Local | (closes the local dialog or edit; commits nothing) | CM v0.8 line 1245 | Named |
| D32 | Claim 1 | D32-H | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D32 | Defect notice 1 | D32-H | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D32 | Diagnostic 1 | D32-H | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D32 | Initial report 1 | D32, D32 · Return | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D32 | Replacement report 1 | D32, D32 · Return | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D32 | Return | D32 · Return | Command | `ReturnContractCloseout` | CM v0.8 line 1243 | Gap |
| D32 | Return for correction | D32, D32 · Return | Command | `ReturnContractCloseout` | CM v0.8 line 1243 | Gap |
| D32 | Sign final acceptance | D32, D32 · Return | Command | `SignFinalContractAcceptance` | CM v0.8 line 1218 | Named |
| D32 | View claim | D32-H | Read | `GetContractWorkspace` | CM v0.8 line 1242 | Named |
| D32 | Warranty history 1 | D32, D32 · Return | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D33 | Approve accounting invoice | D33-A, D33-A · Return | Command | `ApproveNativeFinanceRecord` | CM v0.8 line 1241 | Named |
| D33 | Cancel | D33, D33-A · Return | Local | (closes the local dialog or edit; commits nothing) | CM v0.8 line 1245 | Named |
| D33 | Return invoice | D33-A · Return | Command | `ReturnNativeFinanceForCorrection` | CM v0.8 line 1241 | Named |
| D33 | Return invoice for correction | D33-A, D33-A · Return | Command | `ReturnNativeFinanceForCorrection` | CM v0.8 line 1241 | Named |
| D33 | Save draft | D33 | Command | `SaveNativeFinanceDraft` | CM v0.8 line 1240 | Named |
| D33 | Submit invoice for approval | D33 | Command | `SubmitNativeFinanceForApproval` | CM v0.8 line 1240 | Named |
| D33 | View accounting invoice | D33-A · Posted | Read | (native record projection) | CM v0.8 line 1239 | Named |
| D33 | View certification | D33, D33-A … (5 boards) | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D34 | Approve change | D34-A, D34-A · Decide | Command | `DecideContractChange` | CM v0.8 line 1224 | Named |
| D34 | Cancel | D34, D34-A · Decide | Local | (closes the local dialog or edit; commits nothing) | CM v0.8 line 1245 | Named |
| D34 | Confirm decision | D34-A · Decide | Command | `DecideContractChange` | CM v0.8 line 1224 | Named |
| D34 | Decline | D34-A, D34-A · Decide | Command | `DecideContractChange` | CM v0.8 line 1224 | Named |
| D34 | Report a problem | D34-P | Command | `RecordContractIssue` | CM v0.8 line 1223 | Named |
| D34 | Request change | D34 | Command | `RequestContractChange` | CM v0.8 line 1251 | Named |
| D34 | Return for correction | D34-A, D34-A · Decide … (4 boards) | Command | `ReturnContractChange` | CM v0.8 line 1224 | Named |
| D34 | Sign amendment | D34-P | Command | `SignContractVersion` | CM v0.8 line 1214 | Named |
| D34 | Submit change for decision | D34-R | Command | `SubmitContractChangeForDecision` | CM v0.8 line 1214 | Named |
| D34 | View amendment | D34-H | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D34 | View issue | D34-X | Read | `GetContractWorkspace` | CM v0.8 line 1242 | Named |
| D34 | View request | D34-L | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D34 | View rule | D34-L, D34-X | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D34 | View update status | D34-H | Read | (operation-status projection) | CM v0.8 line 1244 | Named |
| D35 | Cancel | D35 · Return | Local | (closes the local dialog or edit; commits nothing) | CM v0.8 line 1245 | Named |
| D35 | Record return | D35, D35 · Return | Command | `RecordAcceptanceCorrection` | CM v0.8 line 1252 | Named |
| D35 | Request correction | D35-V | Command | `RequestAcceptanceCorrection` | CM v0.8 line 1237 | Named |
| D35 | Verify remedy | D35-V | Command | `VerifyContractRemedy` | CM v0.8 line 1253 | Named |
| D35 | View affected records | D35-H | Read | `GetContractWorkspace` | CM v0.8 line 1260 | Named |
| D35 | View claim | D35-H | Read | `GetContractWorkspace` | CM v0.8 line 1242 | Named |
| D35 | View history | D35-C | Read | `GetContractHistory` | CM v0.8 line 1232 | Named |
| D35 | View remedy | D35-C | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D36 | Approve adjustment | D36-A, D36-A · Decide | Command | `DecideContractAdjustment` | CM v0.8 line 1254 | Named |
| D36 | Cancel | D36-A · Decide | Local | (closes the local dialog or edit; commits nothing) | CM v0.8 line 1245 | Named |
| D36 | Confirm decision | D36-A · Decide | Command | `DecideContractAdjustment` | CM v0.8 line 1254 | Named |
| D36 | Decline | D36-A, D36-A · Decide | Command | `DecideContractAdjustment` | CM v0.8 line 1254 | Named |
| D36 | Return for correction | D36, D36-A … (4 boards) | Command | `DecideContractAdjustment` | CM v0.8 line 1254 | Named |
| D36 | Sign certification | D36-S | Command | `SignContractCertification` | CM v0.8 line 1238 | Named |
| D36 | Submit adjustment for decision | D36, D36-E | Command | `PrepareContractAdjustment` | CM v0.8 line 1254 | Named |
| D36 | View calculation | D36-H, D36-S | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D36 | View clause | D36, D36-E | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D36 | View issue | D36-H | Read | `GetContractWorkspace` | CM v0.8 line 1242 | Named |
| D37 | Approve claim | D37-A | Command | `DecideSecurityClaim` | CM v0.8 line 1255 | Named |
| D37 | Cancel | D37, D37-P · Outcome | Local | (closes the local dialog or edit; commits nothing) | CM v0.8 line 1245 | Named |
| D37 | Decline | D37-A | Command | `DecideSecurityClaim` | CM v0.8 line 1255 | Named |
| D37 | Record claim outcome | D37-P, D37-P · Outcome | Command | `RecordSecurityClaimOutcome` | CM v0.8 line 1255 | Named |
| D37 | Reject replacement | D37-X | Command | `RejectContractSecurity` | CM v0.8 line 1212 | Named |
| D37 | Request claim | D37 | Command | `RequestSecurityClaim` | CM v0.8 line 1255 | Named |
| D37 | Return for correction | D37-A | Command | `DecideSecurityClaim` | CM v0.8 line 1255 | Named |
| D37 | Save outcome | D37-P · Outcome | Command | `RecordSecurityClaimOutcome` | CM v0.8 line 1255 | Named |
| D37 | Verify replacement | D37-X | Command | `VerifyContractSecurity` | CM v0.8 line 1212 | Named |
| D37 | View instrument | D37 | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D38 | Cancel | D38 · Reopen, D38-P | Local | (closes the local dialog or edit; commits nothing) | CM v0.8 line 1245 | Named |
| D38 | Closure 1 | D38, D38 · Reopen | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D38 | Confirm reopening | D38 · Reopen | Command | `ReopenContractCloseout` | CM v0.8 line 1257 | Named |
| D38 | Delivery incident 1 | D38, D38 · Reopen | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D38 | HOP review 1 | D38, D38 · Reopen | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D38 | Keep closed with surviving work | D38, D38 · Reopen | Command | `ConfirmContractClosure` | CM v0.8 line 1257 | Named |
| D38 | Reopen contract | D38, D38 · Reopen | Command | `ReopenContractCloseout` | CM v0.8 line 1257 | Named |
| D38 | Return for correction | D38, D38 · Reopen | Command | `ReturnContractCloseout` | CM v0.8 line 1257 | Named |
| D38 | Save draft | D38-P | Command | `PrepareContractClosureCorrection` | CM v0.8 line 1258 | Named |
| D38 | Submit correction | D38-P | Command | `PrepareContractClosureCorrection` | CM v0.8 line 1258 | Named |
| D38 | View closure | D38, D38 · Reopen | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D38 | View history | D38-R | Read | `GetContractHistory` | CM v0.8 line 1232 | Named |
| D38 | View settlement | D38-T | Read | (native record projection) | CM v0.8 line 1239 | Named |
| D38 | View termination | D38-T | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D39 | Cancel | D39 · Complete | Local | (closes the local dialog or edit; commits nothing) | CM v0.8 line 1245 | Named |
| D39 | Complete settlement | D39, D39 · Complete | Command | `CompleteTerminationSettlement` | CM v0.8 line 1259 | Named |
| D39 | Confirm completion | D39 · Complete | Command | `CompleteTerminationSettlement` | CM v0.8 line 1259 | Named |
| D39 | Return for correction | D39, D39 · Complete, D39-P | Command | `ReturnContractTermination` | CM v0.8 line 1243 | Gap |
| D39 | Submit settlement for completion | D39-P | Command | `PrepareTerminationSettlement` | CM v0.8 line 1258 | Named |
| D39 | View funding update | D39-C | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D39 | View reconciliation | D39-P | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D39 | View recovery | D39-H | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D39 | View remaining obligations | D39-H | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D39 | View settlement | D39-C | Read | (native record projection) | CM v0.8 line 1239 | Named |
| D39 | View termination | D39, D39 · Complete | Read | `GetContractHistory` | CM v0.8 line 1232 | Inferred |
| D40 | Back to contracts | D40-D | Read | `GetContractWorkspace` | CM v0.8 line 1231 | Named |
| D40 | Open | D40, D40-AO … (6 boards) | Read | `GetContractWorkspace` | CM v0.8 line 1231 | Named |
| D40 | Open replacement issue | D40 | Read | `GetContractWorkspace` | CM v0.8 line 1242 | Named |
| D40 | View agreement | D40, D40-AO … (6 boards) | Read | `GetContractHistory` | CM v0.8 line 1232 | Named |
| D40 | View issue | D40-S | Read | `GetContractWorkspace` | CM v0.8 line 1242 | Named |

**Totals:** 273 (design, control) pairs: 187 Named, 83 Inferred, 3 Gap.

## Commands and reads with no board control

| Command or read | Why there is no control on a board |
|---|---|
| `ReceiveAwardPackage` | Event / adapter: arrives from Award's receiver hook; no board control (CM-IF-01). |
| `ReceiveAwardUpdate` | Event / adapter: immutable Award update; no board control. |
| `ReceiveAwardPublicationEvent` | Event / adapter: `AwardDecisionRecorded v1`; no board control. |
| `RecordContractAwardPublication` | Command with no board in the design: HOP records actual publication evidence for a publication obligation (§5.2, §5.15). **Design gap — logged.** |
| `RecordCustodyReturn` | Command with no board in the design: returns of unaccepted units to the supplier (§5.4). **Design gap — logged.** D35 draws only the accepted-unit return. |
| `RecordWarrantyClaim` | Command with no board of its own: the D16-W / D16-P warranty claim controls (**Send notice**, **Record return**) record claims; **Design gap — confirm which control.** |
| `CorrectFinanceSettlement` | Command with no board in the design: correcting an evidenced settlement (§5.18 'Payment reversed or settlement correction'). **Design gap — logged.** D28-V shows only the reversal read. |
| `SaveContractParticulars` | Command with no board of its own: the D02 particulars fields save through it (§7 pairs it with RequestContractSignatures). Control label not drawn separately. |
| `PostAcceptedReceipt` | Service-only: worker posting from an effective acceptance decision (§7 'Service-only'); no board control. |
| `ReceiveFinanceResult` | Service / event: trusted native document event; no board control. |
| `RespondToContractIssue` | Command with no board of its own: supplier and holder replies to an issue (D13 **Send reply** uses ReplyContractCorrespondence). **Design gap — confirm which control.** |
| `ResolveContractIssue` | Service-only: called by VerifyContractRemedy when all evidence is complete, and by an authorised disposition (§5.20); no board control of its own. |
| `ActivateContractChange` | Service-only: runs after required amendment signatures and effectiveness (§11.1 D34 row); no board control. |
| `PrepareContractCloseout` | Service-only: generates the close-out review (§5.9); the board D11 shows its output. |
| `GenerateContractReport` | Service / scheduler: period report generation (§5.15); no board control. D15 submits the generated report. |
| `RecordContractReportSubmission` | Command with no board of its own: records an actual external submission reference (§5.15). D15 draws **Submit report**; **Design gap — confirm control for external evidence.** |
| `RequestContractFundingUpdate` | Service-only: durable funding intent (§7); no board control. |
| `ReceiveContractFundingResult` | Service-only: owner's idempotent funding result; no board control. |
| `PrepareContractAdvance` | Service-only: produces the entitlement D29 **Sign advance certification** signs (§11 advance row). |
| `RecordTerminationNotice` | Command with no board in the design: actual notice dispatch and effectiveness evidence (§5.7). **Design gap — logged.** D20-T shows the recorded result. |
| `RecordContractChangeReview` | Command with no board in the design: reviewer recommendation record (§7 final paragraph). D27-R shows the result. **Design gap — logged.** |
| `SignContractChangeReview` | Command with no board in the design: reviewer personal signature on a review (§7 final paragraph). **Design gap — logged.** |

## Commands with their controls

| Command or read | Board controls that invoke it |
|---|---|
| `RegisterExistingContract` | 1: D12 Save and review |
| `ReviseContractIntake` | 1: D12 Save and review |
| `ConfirmOpeningPosition` | 1: D21 Confirm opening position |
| `StartContractManagement` | 1: D21 Start management |
| `RecordAcceptanceCorrection` | 1: D35 Record return |
| `SignTechnicalCertificate` | 1: D19 Sign technical certificate |
| `IssueCompletionCertificate` | 1: D22 Sign and issue certificate |
| `RecordSecurityAction` | 1: D16 Record return |
| `RecordFinanceSettlement` | 1: D17 Confirm payment |
| `CompleteTerminationSettlement` | 2: D39 Complete settlement; D39 Confirm completion |
| `RequestContractSignatures` | 1: D02 Send for signature |
| `SignContractVersion` | 3: D03 Sign contract; D27 Sign amendment; D34 Sign amendment |
| `RecordContractArrival` | 1: D04 Record delivery |
| `RecordInspectionObservations` | 2: D05 Save observations; D31 Save observations |
| `PrepareAcceptanceReport` | 1: D06 Prepare report for signing |
| `SignAcceptanceReport` | 2: D07 Sign report; D31 Sign report |
| `SubmitContractInvoice` | 1: D18 Submit invoice |
| `CorrectContractInvoice` | 1: D18 Submit correction |
| `SignContractCertification` | 3: D08 Sign certification; D29 Sign certification; D36 Sign certification |
| `SaveNativeFinanceDraft` | 3: D09 Save draft; D28 Save draft; D33 Save draft |
| `SubmitNativeFinanceForApproval` | 3: D09 Submit payment for approval; D28 Submit payment for approval; D33 Submit invoice for approval |
| `ApproveNativeFinanceRecord` | 2: D17 Approve payment; D33 Approve accounting invoice |
| `ReturnNativeFinanceForCorrection` | 4: D17 Return payment; D17 Return payment for correction; D33 Return invoice; D33 Return invoice for correction |
| `RecordContractIssue` | 6: D03 Report a problem; D13 Report a new issue; D21 Report difference; D26 Report a problem; D27 Report a problem; D34 Report a problem |
| `RequestContractChange` | 2: D27 Request extension; D34 Request change |
| `DecideContractChange` | 6: D14 Approve extension; D14 Confirm decision; D14 Decline; D34 Approve change; D34 Confirm decision; D34 Decline |
| `SignContractCloseout` | 1: D11 Sign close-out |
| `GetContractWorkspace` | 19: D-DENIED Back to contracts; D-ERR Back to contracts; D01 Open contract; D01-S Open contract; D02 View issue; D09 Review latest version; D10 Open; D10 Open replacement issue; D11 View claim; D29 View issue; D32 View claim; D34 View issue; D35 View affected records; D35 View claim; D36 View issue; D40 Back to contracts; D40 Open; D40 Open replacement issue; D40 View issue |
| `GetContractHistory` | 93: D02 Download agreement 1; D02 View agreement 1; D02 View award; D03 View agreement; D03 View agreement 1; D05 View all observations; D06 View observations; D07 View report; D08 View acceptance report; D08-L View correction; D09 View certification; D10 View agreement; D11 View close-out record; D11 View history; D11 View remaining obligations; D11 View termination record; D13 View acceptance report; D13 View replacement acceptance; D14 Current committee recommendation 1; D14 Legal review 1; D14 Supplier request 1; D14 Technical review 1; D14 View amendment; D14 View decision; D15 View contract; D15 View signing record; D15 View source event; D16 View claim history; D16 View guarantee; D16 View notice; D16 View warranty; D17 View certification; D17 View missing certification; D18 View acceptance; D18 View invoice; D20 Contract clause 8; D20 Cure-period record; D20 Default notice and delivery proof; D20 Legal advice 1; D20 Settlement calculation 1; D20 View delivery status; D20 View notice; D20 View termination record; D21 View source contract; D22 View certificate; D22 View completion evidence; D22 View delivery status; D23 View appointment; D23 View recommendation; D24 View appointment; D24 View declaration; D25 View contract; D25 View guarantee; D25 View rejection; D26 Signed agreement 1 — entity; D26 Signed agreement 1 — supplier; D26 View agreement 1; D26 View differences; D27 View amendment 1; D27 View appointment; D28 Original settlement; D28 Reversal; D28 View certification; D29 View advance clause; D29 View guarantee; D31 View service requirement; D32 Claim 1; D32 Defect notice 1; D32 Diagnostic 1; D32 Initial report 1; D32 Replacement report 1; D32 Warranty history 1; D33 View certification; D34 View amendment; D34 View request; D34 View rule; D35 View history; D35 View remedy; D36 View calculation; D36 View clause; D37 View instrument; D38 Closure 1; D38 Delivery incident 1; D38 HOP review 1; D38 View closure; D38 View history; D38 View termination; D39 View funding update; D39 View reconciliation; D39 View recovery; D39 View remaining obligations; D39 View termination; D40 View agreement |
| `RecommendContractInspectors` | 2: D23 Recommend inspectors; D24 Revise appointment recommendation |
| `AppointContractInspectors` | 2: D23 Appoint; D23 Appoint inspectors |
| `ReturnContractAppointment` | 2: D23 Return; D23 Return for correction |
| `DeclareContractInterest` | 1: D24 Save declaration |
| `RecordContractSecurity` | 1: D25 Save security |
| `VerifyContractSecurity` | 3: D25 Verify; D25 Verify security; D37 Verify replacement |
| `RejectContractSecurity` | 3: D25 Reject; D25 Reject security; D37 Reject replacement |
| `RecordOutsideContractSignature` | 1: D26 Save signature evidence |
| `ConfirmOutsideSignatureEvidence` | 1: D26 Confirm signature evidence |
| `SubmitContractReport` | 1: D15 Submit report |
| `RecordLegalSourceEvidence` | 3: D15 Record source evidence; D15 Save evidence; D26 Record source evidence |
| `PrepareContractClosureCorrection` | 2: D38 Save draft; D38 Submit correction |
| `ReopenContractCloseout` | 2: D38 Confirm reopening; D38 Reopen contract |
| `ConfirmContractClosure` | 1: D38 Keep closed with surviving work |
| `SignAdvanceCertification` | 1: D29 Sign advance certification |
| `PrepareContractAdjustment` | 1: D36 Submit adjustment for decision |
| `DecideContractAdjustment` | 4: D36 Approve adjustment; D36 Confirm decision; D36 Decline; D36 Return for correction |
| `RequestSecurityClaim` | 1: D37 Request claim |
| `DecideSecurityClaim` | 3: D37 Approve claim; D37 Decline; D37 Return for correction |
| `RecordSecurityClaimOutcome` | 2: D37 Record claim outcome; D37 Save outcome |
| `VerifyContractRemedy` | 1: D35 Verify remedy |
| `PrepareTerminationSettlement` | 1: D39 Submit settlement for completion |
| `SubmitContractChangeForDecision` | 2: D27 Submit change for decision; D34 Submit change for decision |
| `ReturnContractChange` | 3: D14 Return for correction; D27 Return for correction; D34 Return for correction |
| `ReturnContractTermination` | 2: D20 Return for correction; D39 Return for correction |
| `DecideContractTermination` | 3: D20 Approve termination; D20 Confirm decision; D20 Decline |
| `SignFinalContractAcceptance` | 1: D32 Sign final acceptance |
| `SendContractCorrespondence` | 2: D13 Send message; D16 Send notice |
| `ReplyContractCorrespondence` | 1: D13 Send reply |
| `RequestAcceptanceCorrection` | 4: D07 Request correction; D07 Send request; D19 Request correction; D35 Request correction |
| `RequestInvoiceCorrection` | 2: D08 Request correction; D08 Send request |
| `ReturnContractCloseout` | 5: D11 Return; D11 Return for correction; D32 Return; D32 Return for correction; D38 Return for correction |

## Gaps found (logged as follow-ups)

1. **No command for a Return from D32 (final acceptance) or D39 (termination settlement).** Both boards draw **Return for correction** (D32 also a **Return** dialog). §7 names ReturnContractChange, ReturnContractTermination and ReturnContractCloseout only. The map proposes ReturnContractCloseout for D32 and ReturnContractTermination for D39; the owner confirms or names a command.
2. **Commands with no board.** `RecordContractAwardPublication`, `RecordCustodyReturn`, `RecordWarrantyClaim`, `CorrectFinanceSettlement`, `RespondToContractIssue`, `RecordContractReportSubmission`, `RecordTerminationNotice`, `RecordContractChangeReview`, `SignContractChangeReview` have no control drawn on any board (see the table above). Each is a required §7 command; their surface is a decision for the owner and the designer, not something the build invents.
3. **Boards carry no per-field control labels** (field edits save through the originating command). The map covers actions, not fields.
