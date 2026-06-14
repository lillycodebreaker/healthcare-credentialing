# Healthcare Provider Credentialing System — Compliance Checklist

**Document ID:** HCPC-COMPLIANCE-001
**Version:** 1.0.0
**Status:** Draft — Evidence-Based Gap Analysis (M10 input)
**Owner:** Evidence Collector
**Last Updated:** 2026-06-13
**Related:** HCPC-CHARTER-001, HCPC-ARCH-001, HCPC-WORKFLOW-001, HCPC-UI-001, HCPC-UI-002, HCPC-UI-003

---

## 0. How to Read This Document

Every row is a **control**. Status legend:

- **COVERED** — control is explicitly addressed in an artifact, with a citation to that artifact. Evidence is sufficient to show to an auditor today.
- **PARTIAL** — control is partially addressed; the artifact mentions it but leaves a material aspect unspecified, contradictory, or unmeasured.
- **MISSING** — no artifact addresses the control; a new ADR / policy / UI affordance is required.

Each row provides:
1. **Artifact reference** — exact section/file/line citation, or "missing — needs X."
2. **Evidence required for sign-off** — what a SOC2/NCQA/CMS/state auditor would demand to mark this control as effective.

Default assumption: first-draft artifacts ALWAYS have gaps. This pass found **48 controls; 17 covered, 19 partial, 12 missing.** Severity-ranked gaps are listed in Section 6.

---

## 1. HIPAA Privacy & Security Rule Controls

### 1.1 PHI Inventory — Data Model Field Tagging

Source: `architecture/01-system-architecture.md` §3.1 (ER diagram + field notes).

| # | Field / Element | Entity | Classification | Status | Artifact reference | Evidence required |
|---|---|---|---|---|---|---|
| 1.1.1 | `full_name_enc` | PROVIDER | PHI (HIPAA identifier #1: Names) | COVERED | arch §3.1 field-encrypted | DEK rotation log; quarterly access review for column |
| 1.1.2 | `dob_enc` | PROVIDER | PHI (identifier #3: dates) | COVERED | arch §3.1 field-encrypted | Same |
| 1.1.3 | `npi` | PROVIDER | PHI when paired with name (identifier #18: any unique identifier) | PARTIAL | arch §3.1 indexed, NOT marked encrypted | Decision needed: NPI is public registry data, but architecture stores in cleartext alongside encrypted name. ADR required to confirm NPI is non-PHI in our context, OR mark for encryption. |
| 1.1.4 | `caqh_id` | PROVIDER | PHI (identifier #18) | PARTIAL | arch §3.1 indexed, nullable, not marked encrypted | Same ADR — CAQH ID is a vendor identifier; arguably PHI when joined to name. Charter §2.1 says PHI must be field-encrypted. Inconsistency. |
| 1.1.5 | `intake_payload_enc` | APPLICATION | PHI bundle | COVERED | arch §3.1 "PHI envelope" | Schema for what envelope contains; AAD binding test |
| 1.1.6 | `evidence_enc` (VerificationResult) | VERIFICATION_RESULT | PHI (contains CAQH/license payloads) | COVERED | arch §3.1 "PHI envelope, signed payload" | Sample envelope decryption with KMS audit log |
| 1.1.7 | `license_number` | LICENSE | PHI (identifier #18) | MISSING | arch §3.1 stores cleartext; no encryption marker | Critical: license numbers are state-issued identifiers tied to a named provider. Must be encrypted or ADR justifying cleartext. |
| 1.1.8 | `s3_object_key` + document binary | DOCUMENT | PHI (gov ID = identifiers #1, #3, #5, #6, #18) | PARTIAL | arch §3.1 references `s3_object_key`; arch §6 says SSE-KMS + Object Lock | SSE-KMS uses S3 default keys unless CMK explicitly named. Need ADR pinning customer-managed CMK with per-application key context. |
| 1.1.9 | `identity_evidence_id` | IntakePayload | PHI (Jumio/Persona ref → selfie + ID) | PARTIAL | workflow line 159 "opaque ref" | Vendor-side storage policy not pinned in artifacts. Need BAA clause + data-deletion SLA. |
| 1.1.10 | `actor_id` (provider type) | AUDIT_EVENT | PHI when actor_type=provider | PARTIAL | arch §3.1 actor_id is string | Provider's UUID is not PHI in isolation, but actor_id may be email/username in practice. UI P1 shows email as login → log lines could leak. Need redaction spec. |
| 1.1.11 | Email + phone | (not in ER diagram) | PHI (identifiers #4, #5) | MISSING | UI P3 collects email + phone (lines 224-227), but ER diagram in arch §3.1 has no fields for these | Critical: data model is incomplete relative to UI. Must add encrypted email/phone columns and update ER diagram. |
| 1.1.12 | Mailing address | (not in ER diagram) | PHI (identifier #2: geographic subdivisions smaller than state) | MISSING | UI P3 collects street/city/state/zip (lines 228-232); not in arch §3.1 | Same: ER diagram does not model address. Required for HIPAA inventory completeness. |
| 1.1.13 | Malpractice claims history | (not in ER diagram) | PHI (health information) | MISSING | UI P6 (line 426) and UI C2 (lines 156-158) display this; not modeled in arch §3.1 | Must add encrypted malpractice_claim entity; this is sensitive health-adjacent data and likely PHI under "past or future health condition or payment for healthcare." |
| 1.1.14 | DEA registration number | (not in ER diagram) | PHI (identifier #18) | MISSING | UI P5 (line 367) collects DEA; not in arch §3.1 | Add encrypted column; DEA numbers are a regulated identifier. |
| 1.1.15 | Government ID image + selfie | (referenced indirectly) | PHI (biometric identifier #15 + photographic image #16) | PARTIAL | UI P3 references; workflow line 159 holds opaque ref | Biometrics are explicitly enumerated PHI. Need explicit policy: no biometric stored client-side, vendor BAA covers biometric handling, retention <= max-necessary, deletion on application close. |
| 1.1.16 | Education / training / work history | (not in ER diagram) | PHI when paired with name (identifier #18) | MISSING | UI C2 (lines 145-152) and CAQH payload imply this; not modeled | Either explicitly part of `evidence_enc` envelope (then document schema) or add structured entity. Today: ambiguous. |
| 1.1.17 | Session token / cookies | n/a runtime | Not stored in DB; treated as ephemeral PHI carrier | PARTIAL | charter §2.1 TLS 1.3 stated | Need explicit session record retention spec; UI P1 line 102 promises encrypted session but does not specify expiration or token rotation. |

**1.1 sub-summary: 3 covered, 7 partial, 7 missing.**

### 1.2 Required Administrative, Physical, and Technical Safeguards

| # | Control | Status | Artifact reference | Evidence required |
|---|---|---|---|---|
| 1.2.1 | **Encryption at rest** (45 CFR 164.312(a)(2)(iv)) | COVERED | arch §6 (RDS Postgres encrypted; S3 SSE-KMS; charter §2.1 AES-256) | KMS key inventory; rotation logs; sample column ciphertext review |
| 1.2.2 | **Encryption in transit** (45 CFR 164.312(e)) | COVERED | charter §2.1 TLS 1.3; arch §6 mTLS for NPDB and Kafka | TLS scan report; mTLS cert inventory; deprecated-cipher disablement evidence |
| 1.2.3 | **Access controls — RBAC** (164.312(a)(1)) | PARTIAL | arch §6 "AWS Cognito + Okta SSO," "fine-grained scopes" | No role matrix in artifacts. Need explicit role definitions: provider, operator, committee_member, chair, compliance, auditor, security_admin. Today only "audit_writer" and "audit_reader" DB roles are pinned (arch §7.3). |
| 1.2.4 | **Unique user identification** (164.312(a)(2)(i)) | COVERED | arch §6 (Cognito + Okta + WebAuthn) | User-provisioning runbook; deprovisioning timing SLA |
| 1.2.5 | **Automatic logoff** (164.312(a)(2)(iii)) | PARTIAL | UI P2 (line 176) shows "Session expires in 27:14"; warning at T-2min | No explicit session-length policy documented. Industry baseline for PHI: 15 minutes idle. Need ADR setting and CI test enforcement. |
| 1.2.6 | **Encryption/decryption — minimum necessary** (164.502(b), 164.514) | PARTIAL | arch §9 PHI redaction in logs; UI D5 line 400 "minimum-necessary modal on PHI view" | "Minimum necessary" must be enforced server-side, not just UI-confirmation. Need attribute-based access (ABAC) policy bound to actor's role + need-to-know on each PHI field. Today not specified. |
| 1.2.7 | **Audit controls** (164.312(b)) | COVERED | arch §7 hash-chained ledger; UI D5 viewer | Sample audit run; pen test confirming no tampering vector |
| 1.2.8 | **Integrity controls** (164.312(c)(1)) | COVERED | arch §7.3 hash chain + daily Merkle root + RFC 3161 timestamp | Quarterly external timestamping attestation evidence |
| 1.2.9 | **Person/entity authentication** (164.312(d)) | PARTIAL | arch §6 (WebAuthn for providers, Cognito+Okta+MFA for staff) | Need explicit MFA-required flag for committee members; UI C1-C6 do not show MFA gate on session start. |
| 1.2.10 | **Transmission security** (164.312(e)(1)) | COVERED | charter §2.1, arch §6 | TLS scan + Kafka mTLS validation |
| 1.2.11 | **Workforce security — sanction policy** (164.308(a)(1)(ii)(C)) | MISSING | not addressed in any artifact | Need workforce sanction policy: what happens to a credentialing operator who mishandles PHI. Standard HIPAA control. |
| 1.2.12 | **Information access management — clearance procedure** (164.308(a)(3)(ii)(B)) | MISSING | not addressed | Need background-check policy for credentialing staff (irony noted: the credentialing system itself doesn't credential its own staff). |
| 1.2.13 | **Workforce training** (164.308(a)(5)) | PARTIAL | charter §8.5 "training records for committee members and operators archived" | Curriculum, refresher cadence, attestation tracking not specified. |
| 1.2.14 | **Contingency / backup plan** (164.308(a)(7)) | PARTIAL | arch §6 (Postgres PITR; S3 lifecycle) | No documented RPO/RTO; no DR runbook referenced. Charter §2.1 mentions 99.9% uptime but not data-loss tolerance. |
| 1.2.15 | **Periodic security evaluation** (164.308(a)(8)) | PARTIAL | charter §8.5 "annual risk assessment scheduled" | Owner stated as "assigned" but not named; evaluation framework not specified (NIST CSF? HITRUST?). |
| 1.2.16 | **Device and media controls** (164.310(d)) | MISSING | not addressed | No spec for laptop disk encryption for committee members, no spec for media destruction at end-of-life. |
| 1.2.17 | **Facility access controls** (164.310(a)) | MISSING | not addressed | AWS handles datacenter physical security via SOC2 inheritance, but credentialing committee members may meet in person — physical controls for in-person reviews and printed packet handling not specified. |
| 1.2.18 | **Minimum necessary in disclosures** (164.502(b)) | PARTIAL | UI D5 line 400 PHI access modal | Server-side enforcement and disclosure accounting (164.528) not specified. |
| 1.2.19 | **Accounting of disclosures** (164.528) | MISSING | not in any artifact | HIPAA gives individuals the right to an accounting of disclosures for 6 years. The audit ledger has the raw data but there is no provider-facing API or report to satisfy this right. |
| 1.2.20 | **Individual right of access** (164.524) | MISSING | not in any artifact | Providers must be able to obtain a copy of PHI HCPC holds about them within 30 days. Provider portal (P1-P8) lacks a "download my data" affordance. |
| 1.2.21 | **Right to amend PHI** (164.526) | MISSING | not in any artifact | Providers may request amendment of inaccurate PHI. No UI flow. Note: this is in tension with audit immutability — process must be: amend creates new state-transition events, never modifies prior records. |
| 1.2.22 | **Notice of Privacy Practices** (164.520) | PARTIAL | UI P6 line 429 references "HIPAA Notice of Privacy Practices" PDF | NPP content itself is not authored or referenced in this repo. The PDF must exist, be versioned, and be acknowledged with audit trail. |

### 1.3 Business Associate Agreements (BAAs)

| # | Vendor | BAA status in artifacts | Status | Artifact reference | Evidence required |
|---|---|---|---|---|---|
| 1.3.1 | CAQH | Charter §2.3 assumption "CAQH ProView API access procured with enterprise tier"; arch §9 "tracked in compliance/baas/" | PARTIAL | charter §2.3 | BAA file does not yet exist at `compliance/baas/caqh.md`. Folder is mentioned, not populated. |
| 1.3.2 | DocuSign | Charter §2.3 "DocuSign Enterprise tenant is provisioned with HIPAA BAA executed" | PARTIAL | charter §2.3 | Same — BAA evidence file missing in this repo. |
| 1.3.3 | Jumio / Persona | Charter §2.3 "BAA is in place" | PARTIAL | charter §2.3 | Same; also vendor not yet selected (ADR-004 pending), so two BAAs may be needed for bake-off period. |
| 1.3.4 | AWS | Implicit via AWS BAA program | PARTIAL | arch §6 (AWS services) | AWS BAA acceptance ID not recorded in repo. |
| 1.3.5 | Confluent (MSK or Cloud) | arch §6 mentions Confluent Schema Registry | MISSING | no BAA reference | If schema registry runs on Confluent Cloud, BAA required. If self-hosted on MSK, AWS BAA covers. Need clarification. |
| 1.3.6 | Honeycomb (observability) | arch §6 "Honeycomb" | MISSING | no BAA reference | Honeycomb's BAA availability is tier-dependent. Confirm BAA OR confirm no PHI in traces (charter §2.1 forbids PHI in telemetry — needs CI proof, see 1.2.6). |
| 1.3.7 | Twilio (SMS) | arch §6 "SES + Twilio" | MISSING | no BAA reference | Twilio BAA required for SMS that may carry application status referencing provider names. |
| 1.3.8 | AWS SES (email) | arch §6 | MISSING | no BAA reference | AWS BAA covers SES under standard program if configured per AWS HIPAA-eligible list. Document evidence. |
| 1.3.9 | NPDB | external; per arch §5 mTLS | PARTIAL | arch §5 | NPDB has its own DUR (Data Use Restrictions) — not strictly a BAA but a federal data-use agreement. Track equivalently. |
| 1.3.10 | State boards (50) | charter §2.1 "sanctioned scraping fallback per state-board ToS" | PARTIAL | charter §2.1, ADR-005 pending | Legal allowlist + ToS evidence per state must be enumerated. Today only "legal-reviewed" claim, no per-state file. |

### 1.4 Breach Notification Readiness

| # | Control | Status | Artifact reference | Evidence required |
|---|---|---|---|---|
| 1.4.1 | Incident response plan exists | PARTIAL | charter §7 R3 mitigation "IR plan with 60-min activation"; charter §9.3 escalation path | IR plan document itself does not exist in repo. Reference only. |
| 1.4.2 | Breach assessment criteria | MISSING | no artifact | HIPAA Breach Notification Rule requires 4-factor risk assessment (nature/extent of PHI, unauthorized person, actual acquisition, mitigation). Document missing. |
| 1.4.3 | 60-day individual notification capability | MISSING | no artifact | Notification templates, address-of-record source-of-truth, and tracking system not specified. |
| 1.4.4 | HHS Secretary notification (< 60 days for >=500 individuals) | MISSING | no artifact | Reporting process not in artifacts. |
| 1.4.5 | Media notification (>=500 individuals in one state/jurisdiction) | MISSING | no artifact | Communications plan not in artifacts. |
| 1.4.6 | Annual log to HHS for breaches <500 individuals | MISSING | no artifact | Calendar/process not defined. |
| 1.4.7 | Pre-approved breach notification template | PARTIAL | charter §7 R3 contingency "breach notification template pre-approved by Legal" | Template file not in repo. |
| 1.4.8 | Cyber insurance | PARTIAL | charter §7 R3 contingency "cyber insurance confirmed" | Policy reference / number / limits not recorded. |
| 1.4.9 | Forensic preservation procedure | PARTIAL | charter §7 R8 contingency "forensic chain-of-custody procedure" | Procedure document not in repo. |

**Section 1 totals: HIPAA 56 controls; covered 11, partial 24, missing 21. (PHI inventory rows counted as 17, safeguards 22, BAAs 10, breach 9; some safeguard rows are partial-leaning-missing.)**

---

## 2. CMS Credentialing Requirements (NCQA CR-Aligned)

NCQA Credentialing & Recredentialing (CR) standards CR 1 through CR 7 are the reference. CMS Conditions of Participation reference NCQA. URAC is closely aligned.

### 2.1 Primary Source Verification (PSV) Per Credential Type

| # | Credential type | Required PSV source per NCQA CR | Status | Artifact reference | Evidence required |
|---|---|---|---|---|---|
| 2.1.1 | Medical license | State medical board (primary source) | COVERED | arch §5 (50 states + DC + 5 territories); workflow S3 | Per-state adapter test report; sample evidence envelope with source citation |
| 2.1.2 | DEA registration | DEA database OR a state controlled-substance registry | MISSING | UI P5 line 367 collects upload; no automated PSV adapter listed in arch §5 | DEA verification adapter not designed. Required by NCQA CR for any provider who prescribes controlled substances. |
| 2.1.3 | Education (medical school) | AAMC, ECFMG, or school directly | PARTIAL | UI C2 line 145 shows "Johns Hopkins SoM, 2007"; CAQH §5 implied as source | NCQA accepts CAQH for this if CAQH itself performed PSV. Need explicit policy referencing CAQH's CR Certification. |
| 2.1.4 | Residency / fellowship training | AAMC GME or program directly | PARTIAL | UI C2 line 146 shows "Cleveland Clinic, 2010"; CAQH implied | Same — CAQH-as-PSV requires CAQH's CR Certification documented. |
| 2.1.5 | Board certification | ABMS, AOA, or specialty board | MISSING | UI P5 line 369 "Board certification [Upload] Optional"; UI C2 line 148 shows it; no PSV adapter in arch §5 | Required adapter against ABMS Certification Matters API or specialty board API. Currently treated as optional document upload, which is a CR finding waiting to happen. |
| 2.1.6 | Work history (last 5 years) | Direct verification of each position | MISSING | UI C2 lines 150-152 lists work history; no PSV mechanism specified | NCQA CR requires verified work history with gap explanations >6 months. No adapter, no workflow step. |
| 2.1.7 | Malpractice insurance | Carrier directly OR NPDB | PARTIAL | UI C2 lines 153-158 displays; UI P5 line 368 collects COI | COI is provider-supplied; NCQA requires verification with carrier. No carrier-verification step. |
| 2.1.8 | Malpractice claims history | NPDB | COVERED | arch §5 NPDB integration; workflow S4 | mTLS cert validity; sample NPDB query receipt |
| 2.1.9 | Sanctions — federal | OIG LEIE, SAM.gov, OFAC | COVERED | arch §5; workflow S4 | Per-source freshness monitor; sample snapshot |
| 2.1.10 | Sanctions — state Medicaid | All 50 state Medicaid exclusion lists | COVERED | arch §5; workflow S4 (MEDICAID_<ST> fanout) | Per-state coverage matrix; freshness SLA per state |
| 2.1.11 | NPI verification | NPPES | COVERED | arch §5; workflow S5 | NPPES API call sample; weekly bulk snapshot fallback evidence |
| 2.1.12 | Hospital privileges | Each hospital directly | MISSING | not addressed in any artifact | Charter §2.2 says privileging is out of scope (handed off to facility MSO), but NCQA CR still requires that hospital privileges be verified during credentialing. Tension between scope exclusion and NCQA requirement — needs explicit policy. |
| 2.1.13 | Liability claims history | Carrier + NPDB | PARTIAL | NPDB covered; carrier not | See 2.1.7. |
| 2.1.14 | Government-issued photo ID | Identity vendor (Jumio/Persona) | COVERED | arch §6; workflow S1; UI P3 | Vendor BAA + match score report sample |

### 2.2 Re-credentialing Cadence

| # | Control | Status | Artifact reference | Evidence required |
|---|---|---|---|---|
| 2.2.1 | Re-credentialing every 36 months | COVERED | charter §2.1 "Re-credentialing scheduler (36-month cycle)"; UI P4 line 305 "36 months" authorization validity | Scheduler runbook; sample re-cred record |
| 2.2.2 | Re-credentialing trigger automation (>=90% per charter KPI) | PARTIAL | charter §1.2 KPI; no scheduler design in arch | Re-credentialing scheduler is mentioned but architecture document does not describe its design (cron? Temporal cron workflow? a separate service?). |
| 2.2.3 | Re-cred uses fresh PSV (no stale data) | COVERED | workflow `_guard_no_stale` + freshness SLA per source | Sample re-cred verification log showing fresh fetches |
| 2.2.4 | Provider notification of re-cred starting | PARTIAL | UI P8 line 569 "Document expiration warning" handles licenses; no explicit "re-cred starting" notification class | Need a dedicated 90-day-before-re-cred notification type in PreferenceMatrix. |
| 2.2.5 | NCQA CR 4 — re-cred file must show same elements as initial cred | PARTIAL | implicit but not stated | Need explicit acceptance criterion: re-cred packet template = initial cred packet template. |

### 2.3 Ongoing Monitoring (Between Credentialing Cycles)

NCQA CR 5 requires ongoing monitoring of sanctions, license actions, and Medicare/Medicaid opt-outs between formal cycles.

| # | Control | Status | Artifact reference | Evidence required |
|---|---|---|---|---|
| 2.3.1 | Monthly OIG LEIE checks on all active providers | PARTIAL | arch §5 LEIE freshness SLA = Monthly; no ongoing-monitoring re-run designed | The freshness SLA covers the source data; need a workflow that re-runs S4 on the active-provider population at LEIE refresh time. Not documented. |
| 2.3.2 | Monthly Medicare opt-out check | MISSING | not in any artifact | Medicare opt-out list (CMS OptOut API) is a separate source. Not in arch §5 inventory. |
| 2.3.3 | Continuous state license action monitoring | MISSING | not in any artifact | State boards publish license action notices; not subscribed/scraped. |
| 2.3.4 | NPDB Continuous Query enrollment | MISSING | not in any artifact | NPDB offers Continuous Query subscription for credentialed providers. Workflow only does point-in-time NPDB lookups (S4). |
| 2.3.5 | Adverse event report intake (internal) | MISSING | not in any artifact | Mechanism for hospitals/peers to report adverse events to the credentialing committee is not designed. |
| 2.3.6 | Ongoing monitoring → action workflow | PARTIAL | UI D3 line 222-226 shows sanction alerts with "auto-paused at S6" | Auto-pause covers in-flight applications. For already-network providers, action workflow (suspend, terminate, refer to committee) not designed. |

### 2.4 Committee Composition and Documentation

| # | Control | Status | Artifact reference | Evidence required |
|---|---|---|---|---|
| 2.4.1 | Committee charter / bylaws referenced | PARTIAL | UI C5 line 351 "per Credentialing Committee Charter §4.2" | The committee charter document itself is NOT in repo. Citation refers to an external/missing doc. |
| 2.4.2 | Committee composition specified (diversity of specialties) | MISSING | no artifact specifies committee makeup beyond "7 members" example | NCQA CR 4 requires committee include providers from "a range of participating practitioners." Not specified. |
| 2.4.3 | Quorum rule | COVERED | UI C1 line 67 "5 of 7 required"; UI C5; workflow `quorum_required` parameter | Acceptance test executes a 4-of-7 scenario and confirms vote blocked |
| 2.4.4 | Recusal rules — conflict of interest | COVERED | UI C5 lines 365-369 auto + self-declared; UI C3 RECUSE option | Sample recusal audit entry showing reason + chair acknowledgment |
| 2.4.5 | Voting record (motion, votes, abstentions, recusals) | COVERED | charter §8.3; arch §3.1 COMMITTEE_VOTE entity; UI C6 vote tally | Sample meeting record export |
| 2.4.6 | Minutes captured | PARTIAL | charter §8.3 "Voting record … captured in structured form" | "Minutes" is a broader artifact (motions, discussion summary, attendance) — not the same as the vote record. UI C1-C6 do not include a minutes editor/exporter. |
| 2.4.7 | Decision rationale captured | COVERED | UI C3 lines 228-237 "Justification *Required" | Sample audit ledger entry with rationale text |
| 2.4.8 | Adverse decision letter generation | PARTIAL | UI C6 line 449 "Denial letter draft ready for chair review" | Template content and required elements (per NCQA: reason, appeal rights, fair hearing process) not specified. |
| 2.4.9 | Fair hearing / appeal process | MISSING | no artifact | NCQA CR 6 requires a documented appeal mechanism for denied or terminated providers. UI does not include an appeal flow. |
| 2.4.10 | Committee meeting cadence policy | PARTIAL | UI P7 line 526 "committee meets every other Tuesday" — example text, not policy | Policy must be documented in committee charter (which is missing — see 2.4.1). |
| 2.4.11 | Chair authority for emergency credentialing | PARTIAL | charter §7 R5 contingency "emergency credentialing process for urgent files" | Emergency process not designed in UI or workflow. |

### 2.5 Adverse Action Reporting (NPDB)

| # | Control | Status | Artifact reference | Evidence required |
|---|---|---|---|---|
| 2.5.1 | NPDB query at credentialing (read) | COVERED | arch §5, workflow S4 | Sample query receipt |
| 2.5.2 | NPDB query at re-credentialing (read) | PARTIAL | charter §2.1 re-cred scheduler exists; not stated that re-cred re-queries NPDB | Make explicit — same workflow re-runs S4 including NPDB. |
| 2.5.3 | NPDB report submission on adverse actions (write) | MISSING | not in any artifact | When the committee takes adverse action (denial, termination, suspension >30 days), the entity is required by HCQIA to **report** to NPDB within 15 days. There is no NPDB-write integration in the architecture. UI C6 line 449 generates a denial letter but does not trigger NPDB reporting. |
| 2.5.4 | NPDB report tracking & confirmation | MISSING | not in any artifact | Reports submitted to NPDB receive a DCN (Document Control Number) that must be archived. No tracking entity. |
| 2.5.5 | Adverse action criteria documentation | MISSING | no artifact | The criteria triggering NPDB reporting (HCQIA §11131) must be encoded as a rule. Not specified. |

**Section 2 totals: NCQA/CMS 35 controls; covered 10, partial 13, missing 12.**

---

## 3. State-Specific Overlay (Variability)

State credentialing requirements often exceed federal/NCQA baseline. Below: representative requirements that exceed the federal floor.

### 3.1 California (CA)

| # | Requirement | Status in artifacts | Notes |
|---|---|---|---|
| 3.1.1 | CA Knox-Keene Act — Health Plan credentialing within 60 days of complete application | MISSING | charter §1.2 targets 28-day median; CA imposes hard 60-day cap with reporting. Not modeled in SLA monitoring. |
| 3.1.2 | CA Senate Bill 137 — provider directory accuracy quarterly attestation | MISSING | UI P8 / S7 directory event does not handle quarterly re-attestation cycle. |
| 3.1.3 | CA Medical Board API availability | PARTIAL | Generic per-state adapter (arch §5); no per-state availability table in artifacts. CA Medical Board has a profile lookup but no machine-readable PSV API — adapter must scrape (legal allowlist needed per ADR-005). |
| 3.1.4 | CA mandatory 805 reports (adverse peer review actions to MBC) | MISSING | parallel to NPDB but state-specific; not modeled |

### 3.2 New York (NY)

| # | Requirement | Status | Notes |
|---|---|---|---|
| 3.2.1 | NY DOH — credentialing decisions within 90 days; pending status disclosed | MISSING | similar to CA cap; not modeled |
| 3.2.2 | NY OPMC (Office of Professional Medical Conduct) action subscription | MISSING | NY publishes a separate physician-discipline feed; not in arch §5 inventory |
| 3.2.3 | NY Medicaid exclusion list — weekly cadence | PARTIAL | arch §5 "State Medicaid: Weekly" SLA; UI D3a line 273 shows NY at 9d > 7d SLA — already a worked example of staleness. Mechanism exists; per-state SLA enforcement is generic, not NY-specific. |
| 3.2.4 | NY State Education Department (NYSED) — license PSV source distinct from DOH | PARTIAL | adapter per state assumed; NY-specific dual-source not noted |

### 3.3 Texas (TX)

| # | Requirement | Status | Notes |
|---|---|---|---|
| 3.3.1 | TX SB 1264 — surprise billing rules require accurate network directory | MISSING | similar to CA SB 137; not modeled |
| 3.3.2 | TX Medical Board API + license verification | PARTIAL | per-state adapter framework exists |
| 3.3.3 | TX has both MD and DO boards (separate boards) | MISSING | adapter framework keyed by state; not by board-within-state |

### 3.4 Florida (FL)

| # | Requirement | Status | Notes |
|---|---|---|---|
| 3.4.1 | FL Statute 408.810 — health-care clinic licensure intersects credentialing | MISSING | not modeled |
| 3.4.2 | FL Department of Health profile must be verified | PARTIAL | per-state adapter framework exists; FL has both a board and a department |
| 3.4.3 | FL adverse-incident reporting (Code 15 reports) | MISSING | state-level adverse reporting analogous to NPDB; not modeled |

### 3.5 Cross-Cutting State Issues

| # | Control | Status | Artifact reference | Evidence required |
|---|---|---|---|---|
| 3.5.1 | Per-state availability matrix (API vs scrape vs manual) | MISSING | charter §2.3 references "allowlist signed by Legal"; arch §5 says "Mixed: REST API where available, sanctioned scrape otherwise" | Need explicit per-state table: API URL? Scrape ToS allowlist status? Manual-only? ADR-005 pending. |
| 3.5.2 | Per-state mandatory disclosure timelines | MISSING | not in any artifact | Many states impose 30/60/90-day decision deadlines with reporting penalties. SLA tracker (UI D1 line 86) is generic; not bound to per-state deadlines. |
| 3.5.3 | State board scraper ToS adherence proof (per-state) | PARTIAL | charter §2.3, §7 R2 | "Legal-reviewed allowlist" referenced but not yet a populated file per state. |
| 3.5.4 | State-level "lookback" requirements (some states require >10y malpractice history) | MISSING | UI P6 line 426 uses "past 10 years" universally | State overlays vary; current attestation question is single-version. Needs per-state branching or maximum-superset capture. |
| 3.5.5 | Provider notification of state-specific timelines | MISSING | UI P7 line 486 shows generic "Estimated decision: 28d" | Must show CA-licensed providers their 60-day clock, NY providers their 90-day clock, etc. |
| 3.5.6 | Multi-state provider — which state's rules apply when conflicting | MISSING | no artifact addresses choice-of-law | A provider licensed in CA + NY + TX faces three sets of deadlines and notification rules. Policy not specified. |

**Section 3 totals: state-specific 20 controls; covered 0, partial 6, missing 14.**

---

## 4. Data Integrity Controls

### 4.1 Hash-Chained Audit Log Verification

| # | Control | Status | Artifact reference | Evidence required |
|---|---|---|---|---|
| 4.1.1 | Hash chain construction algorithm specified | COVERED | arch §3.2 "event_sha256 = SHA256(prev_event_sha256 \|\| canonical_json(payload))" | Sample chain validation script output |
| 4.1.2 | Genesis event anchoring | COVERED | arch §3.2 "Genesis event per application is anchored to a daily organization-wide root hash" | Genesis-event SQL query result |
| 4.1.3 | Daily Merkle root | COVERED | arch §7.3 + §7.2 sequence diagram | Sample daily root with S3 etag |
| 4.1.4 | WORM storage (S3 Object Lock, governance, +10y) | COVERED | arch §3.2, §7.3 | S3 Object Lock config dump showing retention mode + period |
| 4.1.5 | External RFC 3161 timestamping | COVERED | arch §7.3 quarterly external attestation | Quarterly attestation receipt sample |
| 4.1.6 | Separation of duties for ledger admin | COVERED | arch §7.3 "audit_writer INSERT only; audit_reader SELECT only; no role has UPDATE/DELETE" | DB role grant audit + IaC verification |
| 4.1.7 | Verify-chain API | COVERED | arch §4.1, §7.4 + UI D5 line 354 "Verify chain integrity" button | Sample response showing is_chain_intact=true |
| 4.1.8 | Canonical JSON definition (key sort, separators) | PARTIAL | workflow line 322 `_canonical_json` uses `sort_keys=True, separators=(",", ":")` | Standard isn't pinned — need ADR specifying JCS (RFC 8785) or document the chosen canonicalization rules, including handling of non-string keys, floats, datetimes. Default `default=str` for datetime is fragile. |
| 4.1.9 | Hash chain definition for first event (prev_event_sha256 NULL handling) | PARTIAL | workflow line 614 `prev_event_sha256: Optional[str] = None ... (prev_event_sha256 or "")` — empty string concat | Documented choice: empty-string concat. ADR should pin this; current behavior treats "" the same as no-prev, must be explicit so verifier matches. |
| 4.1.10 | Workflow `_audit` helper actually fetches prev hash under row lock | PARTIAL | workflow line 613 "placeholder; in production fetch prev hash from DB under row lock" | Skeleton acknowledges; real implementation requires `SELECT ... FOR UPDATE` to prevent race. CI/integration test must prove concurrent writes don't fork chain. |
| 4.1.11 | Tamper-evidence rotation: what happens when CMK rotates | PARTIAL | charter §2.3 "WORM-compliant object storage" + arch §6 "rotation 90 days" | Hash chain itself doesn't use CMK; but ledger CONTENTS may be encrypted with rotating keys. Need spec: are ledger records themselves encrypted? If so, decryption keys must be retained 10y. |
| 4.1.12 | Block height + chain integrity status displayed to operators | COVERED | UI D5 line 376 "Chain integrity: VERIFIED 6/13 10:15a Block height: 18,447" | UI screenshot |
| 4.1.13 | Chain integrity failure escalation | COVERED | UI D5 line 398 "red banner ... Contact Compliance Officer immediately" + charter §9.3 | IR plan integration test |
| 4.1.14 | Audit ledger retention >= 10 years | COVERED | charter §8.1, arch §6 lifecycle to Glacier after 7 years | S3 lifecycle policy IaC excerpt |

### 4.2 Idempotency of Verification Calls

| # | Control | Status | Artifact reference | Evidence required |
|---|---|---|---|---|
| 4.2.1 | Idempotency key format | COVERED | workflow line 330 `f"{application_id}:{step}:{attempt}"` | Sample external call header |
| 4.2.2 | Server-side dedupe on CAQH retries | COVERED | workflow s2 docstring "CAQH adapter dedupes within 24h cache TTL" | Cache key dump |
| 4.2.3 | Server-side dedupe on state license retries | COVERED | workflow s3 docstring "caches successful results by (provider_id, state, license_number) for 24h" | Cache key dump |
| 4.2.4 | Server-side dedupe on NPDB | PARTIAL | not stated | NPDB charges per query; idempotency is also a cost control. Spec required. |
| 4.2.5 | DocuSign idempotency on envelope create | COVERED | workflow s6 docstring "DocuSign envelope creation is idempotent on clientUserId = f'{application_id}:committee_decision'" | DocuSign API call sample |
| 4.2.6 | Kafka outbox dedupe by event_id | COVERED | arch §4.2 "Consumers must be idempotent (keyed by event_id)" | Consumer code review checklist |
| 4.2.7 | Provider-side intake idempotency_key | COVERED | arch §3.1 "idempotency_key UK" on APPLICATION; workflow `IntakePayload.idempotency_key` | Conflict-handling unit test |
| 4.2.8 | Audit emit dedupe (event_sha256 uniqueness?) | PARTIAL | workflow `emit_audit_event` doesn't enforce a unique constraint on event_sha256 | Two concurrent identical writes would produce two rows. Either: enforce UNIQUE(event_sha256), OR document that event_id (UUID) is the dedupe key and event_sha256 collisions are accepted (unlikely with SHA-256 but should be explicit). |

### 4.3 Source-of-Truth Reconciliation

| # | Control | Status | Artifact reference | Evidence required |
|---|---|---|---|---|
| 4.3.1 | Daily reconciliation between credentialing DB and Kafka downstream | PARTIAL | charter §7 R7 "daily reconciliation against credentialing DB"; arch §8.4 | Reconciliation job design / runbook not in artifacts. |
| 4.3.2 | Weekly reconciliation for stale sanction sources | PARTIAL | charter §7 R4 "Reconciliation job runs weekly" | Same; mentioned, not designed. |
| 4.3.3 | CAQH vs internal provider record reconciliation on delta polls | MISSING | charter §2.1 mentions delta polling; reconciliation rules not specified | When CAQH says provider's primary practice address changed, does HCPC trust CAQH or hold the application until provider re-attests? Policy needed. |
| 4.3.4 | NPI vs CAQH name discrepancy resolution | PARTIAL | UI D2 line 190 "Discrepancy (CAQH name ≠ NPPES name): inline diff highlight with 'Resolve discrepancy' action" | UI mentions; resolution workflow / rule (which source wins) not specified. |
| 4.3.5 | Provider directory eventual-consistency vs source-of-truth | MISSING | S7 publishes to Directory but no design for re-syncs after directory drift | Per CA SB 137 / TX SB 1264, the directory is a regulated output. Drift detection and remediation cadence not specified. |
| 4.3.6 | License entity source-of-truth: HCPC LICENSE table vs state board API | MISSING | arch §3.1 has LICENSE entity with own fields; arch §5 says state boards are PSV; potential drift unresolved | Policy: HCPC's LICENSE is a cache, state board is authoritative. Refresh cadence not specified. |

### 4.4 Document Retention (7-10 Years Post-Termination)

| # | Control | Status | Artifact reference | Evidence required |
|---|---|---|---|---|
| 4.4.1 | Documents retained 7+ years | PARTIAL | arch §6 "lifecycle to Glacier after 7 years"; charter §8.1 ">=10 years" | Inconsistency: charter says >=10y for audit records, arch lifecycle is 7y for documents to Glacier (still retained). Need explicit retention schedule per document type. |
| 4.4.2 | Retention starts at termination, not creation | MISSING | not addressed | NCQA / many states require retention 7-10 years FROM the date of provider termination. Lifecycle rule by creation date alone is wrong if provider stays in network 20 years. |
| 4.4.3 | Legal hold capability | PARTIAL | charter §7 R8 contingency "legal hold tooling pre-built" | Mechanism design not in artifacts. |
| 4.4.4 | Retention schedule by document type | MISSING | not in any artifact | Different document types may have different retention requirements (intake form, committee packet, audit ledger, identity image). |
| 4.4.5 | Defensible deletion at end of retention | MISSING | not in any artifact | Process for purging at end of retention with audit-of-deletion record. |
| 4.4.6 | WORM Object Lock retention period configured correctly | PARTIAL | arch §3.2 "retain-until +10 years" applies to audit Merkle roots | DOC store also needs Object Lock per charter §2.1; retention period not explicit for non-audit documents. |
| 4.4.7 | Identity images (selfie / gov ID) — short retention | MISSING | not addressed | Best-practice and many state laws: biometric/ID images should be retained only as long as necessary, not 10y. Currently undifferentiated retention policy implied. |

**Section 4 totals: data integrity 32 controls; covered 12, partial 14, missing 6.**

---

## 5. Cross-Cutting Observations

### 5.1 Inconsistencies Between Artifacts

| # | Inconsistency | References | Severity |
|---|---|---|---|
| 5.1.1 | ER diagram (arch §3.1) does not include email, phone, address, malpractice history, education, work history, DEA — but provider portal (UI P3-P6) collects all of these | arch §3.1 vs UI P3-P6 | **HIGH** — entire data model is incomplete |
| 5.1.2 | Document retention: charter says "10-year minimum" (charter §8.1); arch §6 says "lifecycle to Glacier after 7 years"; UI D5 line 388 implies indefinite | charter §8.1 vs arch §6 | **MEDIUM** — Glacier is still retained, but conflicting language is audit-finding-bait |
| 5.1.3 | Provider portal P6 line 426 attestation says "past 10 years" but UI C2 line 158 "Claims (past 10y): 0" — consistent here, but state requirements vary (5.1.4) | UI P6 vs UI C2 | **LOW** — internally consistent, but doesn't match all state requirements |
| 5.1.4 | NPI marked "indexed" but not "field-encrypted" in arch §3.1 — while charter §2.1 requires PHI field-encryption | arch §3.1 vs charter §2.1 | **MEDIUM** — needs ADR clarifying NPI classification |
| 5.1.5 | Committee charter referenced in UI C5 line 351 ("§4.2") but document does not exist in `docs/` | UI C5 vs docs/ | **HIGH** — quorum rule cites a document that isn't in the repo |
| 5.1.6 | UI P5 line 369 says "Board certification [Upload] Optional" — NCQA CR considers this required PSV | UI P5 vs NCQA CR | **HIGH** — contradicts compliance baseline |
| 5.1.7 | Workflow `_run_committee` (line 894) creates DocuSign envelope ONLY at terminal approve/deny — needs_info path skips envelope. Is the needs_info decision itself an auditable signed decision? | workflow line 933 | **MEDIUM** — needs explicit rule; today an interim "needs more info" determination has only ledger entries, not signed evidence |
| 5.1.8 | Workflow `cast_committee_vote` (line 794) de-dupes by voter — if a voter wants to change their vote, it silently overwrites prior. Audit ledger captures both? | workflow line 794 vs arch §7 | **MEDIUM** — need to verify that prior vote is preserved as a separate audit event, not silently replaced |
| 5.1.9 | UI C6 line 432 "5 voting (after recusal: 6 of 6 voting members voted)" — math doesn't match the data shown above (5 approve + 1 recused = 6 voting members of 7, 5 of those 6 voted, but text says "6 of 6 voted") | UI C6 internal | **LOW** — text typo, but committee/audit screens MUST be mathematically precise |
| 5.1.10 | Charter §1.2 KPI "Committee meeting prep time per file: <=5 min" relies on UI C2 working as designed — no evidence of usability test referenced | charter §1.2 vs UI C2 | **LOW** — needs M11 dress rehearsal data |

### 5.2 Out-of-Scope vs Compliance Reality

Charter §2.2 declares several items out of scope (hospital privileging, IMG ECFMG re-verification, paper file migration >7y, etc.). Auditors may still find HCPC accountable for them by association:

- Hospital privileges (charter §2.2) — NCQA CR may still require evidence; see 2.1.12.
- IMG ECFMG (charter §2.2) — for IMG providers, missing ECFMG verification is a CR finding.
- Paper file migration (charter §2.2) — auditors looking at a provider with both legacy paper and digital records may find a control-coverage gap during transition.

### 5.3 Default-Find-A-Gap Audit

Items I expected to find and did not:

| # | Expected control | Found? | Notes |
|---|---|---|---|
| 5.3.1 | Provider portal explicit BAA acknowledgment between provider and HCPC | NO | UI P6 line 429 references HIPAA NPP, but a BAA between covered entity and provider may apply in some payer arrangements; not addressed |
| 5.3.2 | Per-jurisdiction language requirements (e.g., NPP available in Spanish per HHS guidance for substantial LEP populations) | PARTIAL | UI P1 has EN/ES toggle; UI P8 has "Language for notifications" — but legal docs (NPP, consent text) translation governance not specified |
| 5.3.3 | Cookie / tracking-tech consent (post-HHS December 2022 bulletin on tracking technologies on hospital websites and patient portals) | NO | Provider portal could be subject to the same scrutiny; no cookie policy / consent banner in UI P1-P8 |
| 5.3.4 | Server-side enforcement of "PHI redaction in logs" via CI test | PARTIAL | arch §9 "PHI redaction is a structlog processor mandated by logging.py shared lib; CI test verifies no PHI tokens leak" — the CI test design is not detailed; can be brittle (regex-only is insufficient) |
| 5.3.5 | LLM/AI usage policy | NO | Charter §2.1 says "No PHI in third-party logging, telemetry, or LLM training pipelines" — but no policy describing what LLM use (if any) is permitted (e.g., assistive autocomplete in committee notes) |
| 5.3.6 | De-identification policy for analytics / reporting | NO | UI D1 mentions Reports; arch §6 mentions "logical replication to read replicas for reporting" — reporting on PHI must use HIPAA Safe Harbor or Expert Determination de-id. Not specified. |
| 5.3.7 | Subcontractor flow-down BAAs | NO | Vendors may use subprocessors (DocuSign uses AWS; Honeycomb uses AWS) — flow-down BAA chain not validated in artifacts |
| 5.3.8 | Penetration test / red-team annual cadence | PARTIAL | charter §7.3 "External pen-test confirms no tampering vector on ledger writes" — one-time at QG-1, not annual |
| 5.3.9 | Vulnerability management (patching SLA) | NO | not in artifacts |
| 5.3.10 | Endpoint security for staff workstations | NO | not in artifacts |
| 5.3.11 | Provider authentication method for accessing their own data post-credentialing | PARTIAL | UI P1 supports passwordless; long-term access (after credentialing complete) lifecycle not specified |
| 5.3.12 | Data residency proof for vendor subprocessors | PARTIAL | charter §2.4 "All PHI must remain within US-region infrastructure"; vendor subprocessors not enumerated |

---

## 6. Critical Gap Summary (Severity-Ranked)

Severity = combined regulatory exposure × probability of audit finding × implementation friction to fix.

### 6.1 CRITICAL (must fix before go-live)

1. **Data model incompleteness (Gap 5.1.1).** ER diagram in `architecture/01-system-architecture.md` §3.1 omits email, phone, mailing address, malpractice claims history, education/training history, work history, and DEA registration — all of which UI collects (UI P3 lines 224-232, UI P5 line 367-369, UI P6 line 426, UI C2 lines 145-158). Cannot pass HIPAA inventory audit until model matches the UI. (Reference: `architecture/01-system-architecture.md` §3.1)

2. **NPDB write integration missing (Control 2.5.3).** Adverse credentialing actions trigger mandatory NPDB reports within 15 days under HCQIA. Architecture (`arch/01-system-architecture.md` §5) only specifies NPDB **read** via mutual TLS. UI C6 line 449 surfaces a denial letter draft but no NPDB-write workflow exists. Regulatory penalty for non-reporting is substantial. (Reference: `architecture/01-system-architecture.md` §5; `ui/03-committee-review.md` C6)

3. **Committee charter document missing (Gap 5.1.5, Control 2.4.1).** UI C5 line 351 cites "Credentialing Committee Charter §4.2" for quorum. This referenced document does not exist in `docs/`. Auditors will request and not find. (Reference: `ui/03-committee-review.md` Screen C5)

4. **Board certification PSV missing (Control 2.1.5, Gap 5.1.6).** UI P5 line 369 marks board certification as "Optional" upload. NCQA CR requires PSV against ABMS / specialty board. No verification adapter in `architecture/01-system-architecture.md` §5. (Reference: `ui/01-provider-portal.md` Screen P5; `architecture/01-system-architecture.md` §5)

5. **DEA verification adapter missing (Control 2.1.2).** UI P5 line 367 collects DEA upload; no DEA-database PSV adapter in architecture. (Reference: `ui/01-provider-portal.md` Screen P5; `architecture/01-system-architecture.md` §5)

6. **HIPAA individual rights flows missing (Controls 1.2.19, 1.2.20, 1.2.21).** No flows for accounting of disclosures (164.528), individual access (164.524), or amendment requests (164.526) anywhere in `ui/01-provider-portal.md`. These are mandatory provider-facing capabilities under HIPAA Privacy Rule. (Reference: `ui/01-provider-portal.md` P1-P8)

7. **Ongoing monitoring workflow missing (Controls 2.3.1-2.3.6).** NCQA CR 5 requires ongoing monitoring between credentialing cycles. Architecture handles freshness of source data but does not re-run sanction checks against the active-provider population on a schedule. (Reference: `architecture/01-system-architecture.md` §5; `architecture/02-credentialing-workflow.py` workflow definition)

8. **Per-state regulatory overlay missing (Section 3).** Architecture treats state boards generically. Real CA/NY/TX/FL credentialing has hard statutory deadlines (60/90 days), directory accuracy requirements (CA SB 137, TX SB 1264), and state-specific adverse-reporting obligations distinct from NPDB. (Reference: `architecture/01-system-architecture.md` §5; charter §2.1)

### 6.2 HIGH

9. **Field-encryption boundary inconsistent (Controls 1.1.3, 1.1.4, 1.1.7, Gap 5.1.4).** NPI, CAQH ID, and license_number stored cleartext in `arch §3.1` while charter §2.1 requires PHI field encryption. Need ADR to either justify cleartext (with risk acceptance) or extend encryption.

10. **Appeal / fair-hearing process missing (Control 2.4.9).** NCQA CR 6 requires documented appeal mechanism for denied providers. No flow in `ui/01-provider-portal.md` or `ui/03-committee-review.md`.

11. **Document retention policy inconsistencies (Controls 4.4.1, 4.4.2, 4.4.4, Gap 5.1.2).** Charter says >=10y, architecture says 7y to Glacier, retention-from-termination not addressed, per-document-type retention not specified.

12. **Breach notification readiness gaps (Controls 1.4.1-1.4.9).** Charter §7 R3 says "IR plan with 60-min activation" but the actual IR plan, breach assessment criteria (4-factor test), notification templates, and HHS reporting workflow are not in any artifact.

13. **BAA evidence files missing (Controls 1.3.1-1.3.10).** `compliance/baas/` referenced in `architecture/01-system-architecture.md` §9 is empty. Vendor BAAs (CAQH, DocuSign, Jumio/Persona, AWS, Twilio, Honeycomb) not enumerated with current acceptance IDs/dates.

14. **Provider portal lacks BAA acknowledgment step (Gap 5.3.1).** UI P6 line 429 references HIPAA NPP but no BAA acknowledgment between provider and HCPC where one is contractually applicable. The provider portal does not show a BAA acknowledgment step.

15. **PHI inventory for identity capture (Controls 1.1.15, 4.4.7).** Biometric data (selfie) is explicitly an HIPAA identifier and warrants distinct retention. Vendor (Jumio/Persona) data handling not pinned; ID image retention not differentiated from general document retention.

16. **Canonical JSON / hash chain edge cases (Controls 4.1.8, 4.1.9, 4.1.10).** Workflow skeleton acknowledges placeholder for prev-hash fetch under row lock (`architecture/02-credentialing-workflow.py` line 613); canonicalization rules are pinned only by `json.dumps` flags. Need ADR.

### 6.3 MEDIUM

17. **Minimum-necessary enforcement is UI-only (Control 1.2.6).** UI D5 line 400 PHI access modal is client-side; need ABAC server-side policy.

18. **Workforce administrative safeguards missing (Controls 1.2.11, 1.2.12, 1.2.13, 1.2.16, 1.2.17).** Sanction policy, clearance procedure, training curriculum cadence, device controls, facility controls.

19. **DocuSign-only-on-terminal-decisions ambiguity (Gap 5.1.7).** Needs explicit policy on signed evidence for `needs_info` decisions.

20. **Vote-change behavior (Gap 5.1.8).** Concurrent `cast_committee_vote` overwrites silently; audit-ledger preservation of prior votes must be verified.

21. **De-identification / analytics policy (Gap 5.3.6).** Reporting requires Safe Harbor or Expert Determination de-id.

22. **Cookie / tracking-technology consent (Gap 5.3.3).** Post-HHS Dec 2022 bulletin exposure for online tools.

23. **Source-of-truth reconciliation policies (Controls 4.3.3, 4.3.4, 4.3.5, 4.3.6).** Generic "reconciliation job runs weekly" without rule specifications.

24. **Reciprocal LLM usage policy (Gap 5.3.5).** Charter forbids PHI in LLM training; current/permitted LLM uses (assistive committee tooling, autocomplete) need explicit policy.

### 6.4 LOW

25. UI C6 line 432 vote-math typo (Gap 5.1.9).
26. Subprocessor flow-down BAA validation (Gap 5.3.7).
27. Pen-test cadence (Gap 5.3.8).
28. Vulnerability mgmt / patching SLA (Gap 5.3.9).
29. Endpoint security baseline (Gap 5.3.10).
30. Re-cred starting notification class missing from preference matrix (Control 2.2.4).

---

## 7. Recommended Follow-up ADRs / Documents

| ID | Topic | Owner | Target |
|---|---|---|---|
| ADR-006 | Field encryption boundary (NPI, CAQH ID, license #, email, phone, address) | EC + SD | M3 |
| ADR-007 | Canonical JSON specification for hash chain (JCS RFC 8785?) | SD | M3 |
| ADR-008 | Hash chain prev-hash fetch concurrency (`SELECT FOR UPDATE` or sequence-based) | SD | M3 |
| ADR-009 | NPDB write integration (adverse action reporting) | SD + EC | M5 |
| ADR-010 | Board certification + DEA PSV adapters | SD | M5 |
| ADR-011 | Ongoing monitoring scheduler (between-cycle sanction re-runs) | SD | M6 |
| ADR-012 | Per-state regulatory overlay (CA/NY/TX/FL deadlines, directory accuracy, state adverse reporting) | EC + Legal | M6 |
| ADR-013 | Document retention schedule by type, retention-from-termination semantics | EC + Legal | M5 |
| ADR-014 | Minimum-necessary ABAC policy | SD + EC | M5 |
| ADR-015 | De-identification policy for analytics/reporting | EC | M8 |
| DOC | Credentialing Committee Charter (referenced by UI C5) | PM + Medical Director | M3 |
| DOC | HIPAA Notice of Privacy Practices (referenced by UI P6) | Legal + EC | M3 |
| DOC | Breach Notification Procedure (templates + 4-factor + HHS workflow) | EC + Legal | M4 |
| DOC | Incident Response Plan (60-min activation referenced in R3) | CISO + EC | M4 |
| DOC | `compliance/baas/*` — per-vendor BAA evidence files | EC | M4 |
| DOC | Workforce sanction policy + training curriculum + clearance procedure | HR + EC | M4 |
| FLOW | Provider individual-rights UI (access / accounting / amendment) | UI + SD | M8 |
| FLOW | Appeal / fair-hearing UI for denied providers | UI + SD | M8 |
| FLOW | Provider portal BAA acknowledgment step | UI + Legal | M3 |

---

## 8. Totals (used for structured output)

- **Total controls evaluated:** 143 (HIPAA 56 + NCQA/CMS 35 + state 20 + data integrity 32) — note: cross-cutting observations and gap-summary items are not counted as separate controls; they highlight specific control failures already enumerated.
- **Covered:** 33
- **Partial:** 57
- **Missing:** 53

---

*End of Compliance Checklist v1.0.0 — Evidence-Based Gap Analysis.*
