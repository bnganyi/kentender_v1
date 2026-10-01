# AWD-CHG-001 v0.4 — error contract

Copied by script from AWD v0.4 §8 (tracker AWD4-002). 13 codes. `award/services/errors.py` holds exactly these messages; `test_awd_errors.py` checks them against this file. Messages never show table names, payloads, hashes or stack traces; detail is returned separately.

| Code | User-facing message | Resolution |
|---|---|---|
| `AWD_SOURCE_INCOMPLETE` | The evaluation report is incomplete. The Head of Procurement has been notified. | Automatic source issue; EVL owner fixes source. |
| `AWD_RECORD_CHANGED` | This record has changed. Review the latest version before continuing. | Reload comparison, preserve unsaved narrative. |
| `AWD_AUTHORITY_REQUIRED` | You are not authorised to take this action. | Current holder shown where disclosure is allowed. |
| `AWD_SIGNATURE_UNAVAILABLE` | Signing is unavailable. Your draft has been saved. | Technical recovery; no false signature. |
| `AWD_NO_SUPPORTED_AWARD` | An award cannot be made from the current report. Review the recorded reasons. | Return or reasoned no-award outcome. |
| `AWD_VALIDITY_EXPIRED` | Tender validity has expired. No award can proceed. | HOP records facts and proposed action; AO decides any change to the award or procurement outcome. |
| `AWD_NOTICE_FAILED` | A required notice is not yet confirmed. | Exact recipient/channel visible only to permitted users; retry owner named. |
| `AWD_ON_HOLD` | This award is on hold. Review the reason and responsible officer. | Resolve source-specific restriction. |
| `AWD_RESPONSE_LATE` | Your response was received after the deadline. It cannot be used to proceed with this award. | Store response, HOP task. |
| `AWD_NOTICE_CHANGED` | The award notice has changed. Review the current notice before replying. | No response recorded against unseen new terms. |
| `AWD_RULE_UNVERIFIED` | The applicable rules have not been confirmed. The award cannot proceed yet. | Named legal-rule owner resolves release/rule evidence. |
| `AWD_CONTRACTING_UNAVAILABLE` | Contracting is unavailable. KenTender will check that the award can still proceed before sending it. | Durable retry and incident. |
| `AWD_STATUS_UNAVAILABLE` | The current tender status could not be confirmed. The system will check again when service is restored. | Fail closed; named incident owner. |
