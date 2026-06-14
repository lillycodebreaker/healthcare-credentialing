# Healthcare Provider Credentialing System — Project Charter

**Document ID:** HCPC-CHARTER-001
**Version:** 1.0.0
**Status:** Approved for Execution
**Charter Owner:** SeniorProjectManager
**Last Updated:** 2026-06-13
**Project Code:** HCPC-2026

---

## 1. Executive Summary

The Healthcare Provider Credentialing System (HCPC) automates the end-to-end credentialing of healthcare providers from initial application through network onboarding. The system replaces a manual, paper-driven workflow (avg 90-120 days per provider) with an automated, audit-ready pipeline targeting a 21-30 day median turnaround while maintaining HIPAA, CMS, and state-board compliance.

### 1.1 Business Objectives

- Reduce average credentialing turnaround time by >=70%.
- Eliminate manual primary-source verification for CAQH/NPI/license/sanction checks.
- Produce immutable, audit-ready credentialing records for every applicant.
- Provide a digitally signed committee approval workflow that satisfies NCQA, URAC, and CMS auditor expectations.
- Emit standardized onboarding events to downstream HR, EHR, payer enrollment, and directory systems.

### 1.2 Success Metrics

| KPI | Baseline | Target |
|---|---|---|
| Median credentialing cycle time | 95 days | <=28 days |
| % files with zero manual primary-source verification | 0% | >=85% |
| Audit findings per quarterly review | 4-6 | 0 critical, <=1 minor |
| Committee meeting prep time per file | 45 min | <=5 min |
| Re-credentialing automation rate | 0% | >=90% |

---

## 2. Scope Statement

### 2.1 In-Scope

**Functional Scope**
- Provider intake portal with identity capture (government ID OCR + selfie liveness).
- CAQH ProView API integration for profile retrieval and delta polling.
- License Verification Service supporting all 50 states + DC + 5 territories (API where available; sanctioned scraping fallback per state-board ToS).
- Sanctions/Exclusions checks against OIG LEIE, SAM.gov, all 50 state Medicaid exclusion lists, NPDB, and OFAC.
- NPI verification via NPPES NPI Registry (Type 1 individual + Type 2 organizational).
- Committee Review Workflow: file packet generation, quorum tracking, digital signature collection (DocuSign + DKIM-signed audit envelope), motion/vote/minutes capture.
- Onboarding Event Publisher emitting to enterprise event bus (Kafka + outbox pattern).
- Immutable audit ledger (append-only, hash-chained, WORM-compliant storage).
- Re-credentialing scheduler (36-month cycle with mid-cycle monitoring).
- Provider self-service portal for status visibility and document upload.

**Non-Functional Scope**
- HIPAA Privacy + Security Rule compliance (PHI encryption at rest AES-256, in transit TLS 1.3).
- CMS Conditions of Participation compliance for credentialing files.
- NCQA CR standards and URAC core standards alignment.
- SOC 2 Type II readiness by end of project.
- 99.9% uptime SLA for provider-facing portal; 99.5% for back-office workflows.
- p95 latency <=2s for portal interactions; verification jobs async with SLA-tracked queues.

### 2.2 Out-of-Scope

- Provider contracting / fee schedule negotiation (handled by Payer Contracts system).
- Privileging at hospital/facility level (handled by facility Medical Staff Offices).
- Claims adjudication or payment integration.
- Provider data analytics dashboards beyond credentialing operations metrics.
- Mobile native applications (responsive web only in v1).
- International medical graduate ECFMG re-verification beyond CAQH-supplied data.
- Migration of historical paper files >7 years old (separate archival project).

### 2.3 Assumptions

- CAQH ProView API access has been procured with enterprise tier (>=500 req/min).
- DocuSign Enterprise tenant is provisioned with HIPAA BAA executed.
- Enterprise event bus (Kafka) is operational and team has producer credentials.
- Identity verification vendor (Jumio or Persona) BAA is in place.
- Legal has reviewed state-board scraping for each of the 50 states and produced an allowlist.
- WORM-compliant object storage (AWS S3 Object Lock or equivalent) is available.
- Credentialing committee members are appointed and trained on the new tool by W8.
- A dedicated Privacy Officer and Compliance lead are available for consultation (>=4 hrs/week).

### 2.4 Constraints

- All PHI must remain within US-region infrastructure (data residency).
- No PHI in third-party logging, telemetry, or LLM training pipelines.
- State-board scrapers must respect robots.txt and ToS; legal allowlist is binding.
- Budget envelope and headcount are fixed; scope changes require change-control board approval.

---

## 3. Workflow Steps and Dependency Graph

### 3.1 The Seven Workflow Steps

| Step | Name | Type | Avg Duration (Automated) |
|---|---|---|---|
| S1 | Provider Applies (intake + identity) | Sync, user-driven | 15-30 min |
| S2 | Retrieve CAQH Profile | Async API | 30s-5 min |
| S3 | Verify Licenses (per state) | Async, parallel-per-state | 1-15 min |
| S4 | Check Sanctions/Exclusions | Async, parallel-per-source | 1-10 min |
| S5 | Verify NPI and Contracting Eligibility | Async API | 10s-2 min |
| S6 | Committee Review and Approval | Human-in-loop | 1-14 days |
| S7 | Add to Network + Trigger Onboarding | Event publish | <30s |

### 3.2 Dependency Graph

```
                    [S1: Intake + Identity]
                            |
                            v
                    [S2: CAQH Retrieval]
                            |
              +-------------+-------------+
              |             |             |
              v             v             v
        [S3: Licenses] [S4: Sanctions] [S5: NPI]
         (parallel,     (parallel,     (independent
          fan-out         fan-out       of S3/S4)
          per state)     per source)
              |             |             |
              +-------------+-------------+
                            |
                            v
                  [Verification Aggregator]
                            |
                            v
                  [S6: Committee Review]
                            |
                            v
                  [S7: Network Add + Onboard Event]
```

### 3.3 Parallelism Rules

- **Strictly sequential:** S1 -> S2 (CAQH lookup needs verified identity + NPI hint).
- **Parallelizable after S2:** S3, S4, S5 run concurrently. Each fans out further:
  - S3 fans out one job per state where the provider holds (or claims) a license.
  - S4 fans out one job per sanction source (LEIE, SAM.gov, NPDB, OFAC, 50 state Medicaid).
  - S5 is a single NPPES call but may be retried independently.
- **Aggregator gate:** S6 cannot start until S3, S4, S5 all reach terminal state (success or documented exception).
- **Sequential after S6:** S7 fires only on approved committee outcome.

### 3.4 Critical Path

`S1 -> S2 -> max(S3 slowest state, S4 slowest source, S5) -> S6 -> S7`

S6 (committee review) is the dominant critical-path contributor because it includes human scheduling. Project schedule must front-load committee tooling readiness to avoid late-cycle blockage.

---

## 4. Milestones (W1..W12 from Kickoff)

| ID | Milestone | Target Week | Owner | Exit Criteria |
|---|---|---|---|---|
| M1 | Charter signed, environments provisioned | W1 | PM | Charter approved; AWS accounts, Kafka, DocuSign sandbox live |
| M2 | Architecture baseline + ADR-001 through ADR-005 | W2 | Senior Developer | C4 diagrams, threat model v1, data classification map signed off |
| M3 | UI design system + intake flow prototype | W3 | UI Designer | Figma library, accessibility audit (WCAG 2.2 AA) on intake flow |
| M4 | S1 Intake + Identity Capture live in staging | W4 | Senior Developer | E2E happy path, identity vendor BAA validated |
| M5 | S2 CAQH integration + S5 NPI integration in staging | W5 | Senior Developer | Contract tests green; replay harness for CAQH outages |
| M6 | S3 License Verification (top 10 states) + S4 Sanctions (LEIE + SAM.gov + NPDB) | W7 | Senior Developer | Per-state runbooks; sanction source freshness monitors |
| M7 | S3 remaining 40 states + S4 50 state Medicaid lists | W8 | Senior Developer | Coverage matrix 100%; scraper resilience tests pass |
| M8 | S6 Committee Workflow + digital signatures | W9 | Senior Developer | DocuSign envelope, quorum logic, audit ledger writes verified |
| M9 | S7 Onboarding event bus integration | W10 | Senior Developer | Outbox publisher, downstream consumer acks, replay tooling |
| M10 | Compliance evidence pack assembled | W10 | Evidence Collector | HIPAA/NCQA/SOC2 control mappings, audit ledger sample, policies |
| M11 | Reality Check + dress rehearsal with real committee | W11 | Reality Checker | 10 real provider files processed end-to-end; defects triaged |
| M12 | Production go-live + 30-day hypercare plan | W12 | PM | Go/no-go signed; runbooks published; on-call rotation active |

**Milestone count: 12.**

---

## 5. RACI Matrix

Legend: **R** = Responsible (does the work), **A** = Accountable (signs off, single owner), **C** = Consulted (two-way), **I** = Informed (one-way).

Roles: **PM** = SeniorProjectManager, **SD** = Senior Developer, **UI** = UI Designer, **ET** = Experiment Tracker, **EC** = Evidence Collector, **RC** = Reality Checker.

| Deliverable | PM | SD | UI | ET | EC | RC |
|---|---|---|---|---|---|---|
| Project Charter (this doc) | A,R | C | C | I | C | C |
| Architecture + ADRs | I | A,R | C | C | C | C |
| Threat model + data classification | C | A,R | I | I | R | C |
| UI design system + intake flows | C | C | A,R | I | I | C |
| Accessibility audit (WCAG 2.2 AA) | I | C | A,R | I | C | R |
| S1 Intake + Identity Capture | A | R | C | C | I | C |
| S2 CAQH integration | A | A,R | I | C | C | C |
| S3 License Verification (per state) | A | A,R | I | C | C | R |
| S4 Sanctions/Exclusions checks | A | A,R | I | C | R | C |
| S5 NPI verification | A | A,R | I | C | C | C |
| S6 Committee workflow + e-signatures | A | A,R | C | I | R | C |
| S7 Onboarding event bus integration | A | A,R | I | C | I | C |
| Audit ledger (immutable, hash-chained) | I | A,R | I | I | C | C |
| Experiment tracking (vendor bake-offs, A/B) | I | C | C | A,R | I | C |
| Compliance evidence pack (HIPAA, NCQA, SOC2) | C | C | I | I | A,R | C |
| Risk register maintenance | A,R | C | I | C | C | C |
| Reality check / dress rehearsal | C | C | C | C | C | A,R |
| Go/no-go decision | A,R | C | C | C | C | C |
| Stakeholder communications | A,R | I | I | I | I | I |
| Runbooks + on-call rotation | A | A,R | I | I | C | C |
| Change-log + release notes | A,R | C | C | C | C | C |

---

## 6. Documentation Standards

### 6.1 Repository Layout

```
projects/healthcare-credentialing/
  docs/           # Charter, PRDs, runbooks, release notes
  architecture/   # ADRs, C4 diagrams, sequence diagrams, threat models
  compliance/     # HIPAA/NCQA/SOC2 control mappings, audit evidence
  experiments/    # Experiment briefs, vendor bake-off results
  readiness/      # Reality-check reports, dress-rehearsal logs
  ui/             # Design tokens, component specs, accessibility audits
```

### 6.2 Markdown Conventions

- Filenames: `NN-kebab-case-title.md` where `NN` is a two-digit sort prefix.
- Every doc begins with a metadata header: Document ID, Version (semver), Status, Owner, Last Updated.
- Use ATX headings (`#`), max depth 4.
- Tables for any matrix data; fenced code blocks with language hints.
- Internal links use repo-relative paths; never absolute URLs to local files.
- Mermaid is permitted for diagrams; static PNG fallback committed beside source.

### 6.3 ADR Format (Architecture Decision Records)

Stored under `architecture/adr/NNNN-title.md`, sequential numbering, never deleted (status flips to `Superseded`).

```
# ADR-NNNN: <Decision Title>

- Status: Proposed | Accepted | Superseded by ADR-XXXX | Deprecated
- Date: YYYY-MM-DD
- Deciders: <names/roles>
- Consulted: <names/roles>
- Informed: <names/roles>

## Context
<problem statement, forces, constraints>

## Decision
<the choice made, in active voice>

## Alternatives Considered
<options A/B/C with pros/cons>

## Consequences
<positive, negative, follow-up actions, ADR-level risks>

## Compliance Impact
<HIPAA / NCQA / state-board implications, if any>
```

### 6.4 Change-Log Conventions

- Project-level `CHANGELOG.md` follows Keep a Changelog format.
- Sections: Added, Changed, Deprecated, Removed, Fixed, Security.
- Each release tagged with semver; breaking changes require ADR reference.
- PHI-touching changes additionally tagged `[PHI]` and reviewed by Evidence Collector.
- Every PR appends an `Unreleased` entry; release cuts move entries under a dated version header.

### 6.5 Code Documentation

- Public API endpoints documented via OpenAPI 3.1; spec lives in `architecture/api/`.
- Event payloads documented in AsyncAPI 2.6; one file per topic.
- Each service repo contains `README.md`, `RUNBOOK.md`, `SECURITY.md`.

---

## 7. Risk Register (Top 8)

Scoring: Likelihood (1-5) x Impact (1-5) = Severity (1-25).

| ID | Risk | Likelihood | Impact | Severity | Owner | Mitigation | Contingency |
|---|---|---|---|---|---|---|---|
| R1 | **CAQH API rate limits or outage** stalls verification pipeline | 4 | 5 | 20 | SD | Negotiate enterprise tier; implement token-bucket client; cache with TTL aligned to CAQH refresh; circuit breaker with documented fallback to manual lookup | Daily snapshot replication; alert ops within 5 min of >2% error rate; manual lookup runbook with SLA |
| R2 | **State-board scraper brittleness** as state sites change | 5 | 4 | 20 | SD | Per-state adapter pattern; daily canary tests; alert on schema drift; legal-reviewed scraping allowlist; prefer official APIs where available | Hot-swap to manual primary-source verification per state; weekly scraper-health dashboard |
| R3 | **PHI handling / HIPAA breach** during dev, logs, or third-party calls | 3 | 5 | 15 | EC | Data classification map; PHI redaction middleware on logs; BAAs with every vendor; field-level encryption; quarterly access reviews; least-privilege IAM | IR plan with 60-min activation; breach notification template pre-approved by Legal; cyber insurance confirmed |
| R4 | **Sanction list staleness** causes provider added to network despite exclusion | 3 | 5 | 15 | EC | Freshness SLA per source (LEIE monthly, SAM.gov daily, state Medicaid weekly); freshness monitors; block S7 if any source > 2x SLA stale | Auto-flag-for-review when staleness threshold breached; reconciliation job runs weekly |
| R5 | **Committee quorum or signature failure** delays approvals | 4 | 3 | 12 | SD | Quorum config with alternates; DocuSign + DKIM-signed fallback envelope; 72-hr escalation policy; weekly committee dashboard | Async voting mode with explicit chair approval; emergency credentialing process for urgent files |
| R6 | **Identity verification false negatives** block legitimate providers | 3 | 3 | 9 | SD | Tune liveness thresholds with pilot data; document manual review path; vendor bake-off (Jumio vs Persona) tracked by ET | Human-review queue with 24-hr SLA; provider-facing status messaging |
| R7 | **Event bus delivery loss** causes downstream onboarding desync | 2 | 5 | 10 | SD | Transactional outbox pattern; idempotent consumers; end-to-end correlation IDs; daily reconciliation against credentialing DB | Replay tooling per topic; reconciliation report to ops daily |
| R8 | **Audit ledger tampering or gap** undermines NCQA/CMS audit | 2 | 5 | 10 | EC | Hash-chained append-only ledger; WORM storage with Object Lock; quarterly external attestation; separation of duties for ledger admin | Forensic chain-of-custody procedure; legal hold tooling pre-built |

### 7.1 Top 3 Risks (by Severity)

1. **R1 - CAQH API rate limits or outage** (Severity 20)
2. **R2 - State-board scraper brittleness** (Severity 20)
3. **R3 - PHI handling / HIPAA breach** (Severity 15) *(tied with R4; R3 prioritized due to regulatory penalty ceiling)*

---

## 8. Definition of Done — per Quality Gate

### 8.1 QG-1: Audit-Ready Credentialing Records

- [ ] Every state transition produces a ledger entry with timestamp (UTC, RFC 3339), actor, action, before/after state hash.
- [ ] Ledger entries are hash-chained and stored on WORM-locked object storage.
- [ ] Records retrievable via stable provider ID for >=10 years.
- [ ] Sample of 25 randomly selected files passes internal audit checklist (NCQA CR template).
- [ ] External pen-test confirms no tampering vector on ledger writes.

### 8.2 QG-2: Automated CAQH / NPI / License Verification

- [ ] CAQH retrieval succeeds without manual intervention on >=95% of attempts (rolling 30-day).
- [ ] NPI verification: 100% automated lookup, with documented exception path for NPPES outages.
- [ ] License verification covers 50 states + DC + 5 territories with per-state adapters under test.
- [ ] Per-state freshness monitor passes for 30 consecutive days pre-launch.
- [ ] All adapters have contract tests, replay harnesses, and runbooks.

### 8.3 QG-3: Committee Approval Workflow with Digital Signatures

- [ ] DocuSign envelope template approved by Legal and Compliance.
- [ ] DKIM-signed envelope archived alongside DocuSign certificate in audit ledger.
- [ ] Quorum logic verified against committee charter (configurable per committee).
- [ ] Voting record (motion, votes, abstentions, recusals) captured in structured form.
- [ ] Dress rehearsal with real committee processes >=10 files end-to-end with zero blocking defects.

### 8.4 QG-4: Onboarding Event Bus Integration

- [ ] Outbox publisher achieves >=99.99% delivery in 7-day soak test.
- [ ] Downstream consumers (HR, EHR, payer enrollment, directory) ack within agreed SLA.
- [ ] Event schema versioned and published to schema registry.
- [ ] Replay tooling exercised in staging within last 30 days pre-launch.
- [ ] Reconciliation job runs daily and reports zero drift for 14 consecutive days.

### 8.5 QG-5: HIPAA / CMS / State-Board Compliance

- [ ] HIPAA Security Rule controls mapped 1:1 to system controls; evidence pack assembled.
- [ ] CMS Conditions of Participation credentialing requirements traced to test cases.
- [ ] All state-board scraping reviewed by Legal; allowlist signed; ToS compliance documented.
- [ ] Annual risk assessment scheduled and owner assigned.
- [ ] Workforce training records for committee members and operators archived.

---

## 9. Stakeholder Communication Plan

### 9.1 Stakeholder Register

| Group | Representative Roles | Interest | Influence |
|---|---|---|---|
| Executive Sponsor | CMO, CIO | Strategic | High |
| Credentialing Operations | Director of Credentialing, Specialists | Daily users | High |
| Credentialing Committee | Medical Director, Committee Members | Approval authority | High |
| Compliance / Privacy | Privacy Officer, Compliance Lead | Regulatory adherence | High |
| Legal | General Counsel | Contracts, scraping ToS | Medium |
| Information Security | CISO, Sec Eng | Threat model, IR | High |
| Engineering Platform | Platform Lead, SRE | Infra dependencies | Medium |
| Downstream Consumers | HR, EHR, Payer Enrollment, Directory | Onboarding events | Medium |
| Providers (Applicants) | Applying clinicians | UX, status visibility | Medium |
| External Auditors | NCQA, URAC, CMS, SOC2 | Audit findings | High |

### 9.2 Cadence and Channels

| Audience | Channel | Cadence | Owner | Content |
|---|---|---|---|---|
| Executive Sponsors | Steering committee deck | Bi-weekly (W2, W4, W6, W8, W10, W12) | PM | Milestone status, RAG, top 3 risks, decisions needed |
| Credentialing Ops | Working group sync | Weekly | PM | Backlog grooming, demo of in-progress flows |
| Committee | Email digest + monthly demo | Monthly + dress rehearsal at W11 | PM | Workflow changes, training schedule |
| Compliance / Privacy | Async memo + monthly review | Monthly | EC | Evidence pack updates, control mappings |
| Legal | Ad-hoc + scraping allowlist review | At M2, M6, M7 | PM | ToS updates, vendor BAAs |
| InfoSec | Security review gate | At M2, M5, M9, pre-launch | SD | Threat model, pen-test, IR readiness |
| Downstream Consumers | Integration sync | Weekly from W6 | SD | Event schema, replay tooling, SLAs |
| Providers | Status portal + email | Real-time + transactional | UI/SD | Application status, next steps |
| External Auditors | Evidence pack + walkthrough | Pre-launch + quarterly post-launch | EC | Control evidence, ledger samples |
| Project Team | Daily standup + weekly retro | Daily / Weekly | PM | Tactical coordination |
| All Hands | Newsletter | Monthly | PM | Highlights, wins, upcoming milestones |

### 9.3 Escalation Path

1. Team member -> PM (same day for blockers).
2. PM -> Executive Sponsor (within 24h for milestone-impacting risk).
3. Privacy/security incidents -> Privacy Officer + CISO (within 60 minutes; activates IR plan).
4. Audit findings -> Compliance Lead + PM + Executive Sponsor (within 1 business day).

### 9.4 Decision Log

All decisions material to scope, schedule, budget, compliance, or architecture are recorded in `docs/decisions/decision-log.md` with date, decision, alternatives considered, decision-maker, and linked ADR (if applicable).

---

## 10. Approval

| Role | Name | Signature | Date |
|---|---|---|---|
| Executive Sponsor (CMO) | _________ | _________ | _________ |
| Executive Sponsor (CIO) | _________ | _________ | _________ |
| Privacy Officer | _________ | _________ | _________ |
| Project Manager | SeniorProjectManager | _________ | 2026-06-13 |

---

*End of Charter*
