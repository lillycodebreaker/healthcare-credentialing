# Healthcare Provider Credentialing System — Deployment Plan

**Document ID:** HCPC-DEPLOY-001
**Version:** 1.0.0
**Status:** Conditional — assumes Production Readiness Review (HCPC-READINESS-001) blockers are addressed
**Owner:** SeniorProjectManager (with SD + Platform Lead + EC as joint operators)
**Last Updated:** 2026-06-13
**Related:** HCPC-CHARTER-001, HCPC-ARCH-001, HCPC-WORKFLOW-001, HCPC-READINESS-001

---

## 0. Scope and Preconditions

This plan describes how to take the Healthcare Provider Credentialing System (HCPC) to production **assuming all blockers from `readiness/01-production-readiness-review.md` §4 are remediated and verified**. This plan does **not** authorize go-live on its own. Go-live requires:

- Sign-off on `HCPC-READINESS-001` re-assessment with verdict "conditional-go" or "go-live."
- Sign-off on Phase A and Phase B of the remediation plan (`HCPC-READINESS-001` §5.1, §5.2).
- Completed Phase C operationalization (§5.3) and Phase D dress rehearsal (§5.4).

If any precondition is not met, this plan is paused. There is no "ship now and finish later" pattern in regulated healthcare.

---

## 1. Pre-Launch Checklist

Each row must be **green** (signed-off, dated, evidence linked in audit ledger) before phased rollout begins. Yellow or red anywhere blocks rollout.

### 1.1 Security Review

| ID | Item | Owner | Evidence | Status gate |
|---|---|---|---|---|
| SEC-1 | Threat model finalized (STRIDE) at `architecture/threat-model.md`; covers Temporal, audit ledger, identity vendor, provider portal, committee console, Kafka outbox | CISO + SD | Threat model doc + walkthrough minutes | Green |
| SEC-2 | External penetration test completed by reputable firm; scope includes web portals, API surface, audit ledger tamper attempts, IAM lateral movement, vendor BAA boundary | CISO + SD | Pen-test report + remediation evidence | Green; zero critical, zero high open |
| SEC-3 | Clean re-test after remediation | CISO + SD | Re-test report | Green |
| SEC-4 | IAM access analyzer review; least-privilege audit on every service role and human role | CISO | Access Analyzer findings cleared; quarterly review scheduled | Green |
| SEC-5 | KMS CMK inventory + 90-day rotation evidence | SD + CISO | KMS rotation log; CMK-per-env documented | Green |
| SEC-6 | TLS scan (mozilla observatory or equivalent) on all public endpoints; TLS 1.3 only; deprecated ciphers disabled | SD | Scan output archived | Green |
| SEC-7 | mTLS validation for NPDB and Kafka; cert rotation runbook published | SD + Platform | Cert inventory; runbook link | Green |
| SEC-8 | Secrets scan in CI; signed-commits enforced on protected branches | SD | CI policy evidence | Green |
| SEC-9 | SBOM generation in CI (Syft); CVE feed integration; critical-CVE patch SLA defined and met | SD + CISO | SBOM artifacts; CVE remediation log | Green |
| SEC-10 | Vulnerability management policy authored; patching SLA (critical <7d, high <30d, medium <90d) committed | CISO | `compliance/policies/vulnerability-management.md` | Green |

### 1.2 HIPAA Risk Assessment

| ID | Item | Owner | Evidence | Status gate |
|---|---|---|---|---|
| HIPAA-1 | HIPAA Security Rule risk assessment performed against `compliance/01-compliance-checklist.md` Section 1.2 — all 22 administrative/physical/technical safeguards COVERED with evidence | Privacy Officer + EC | Risk assessment report | Green |
| HIPAA-2 | PHI inventory complete; ER diagram matches UI-collected fields; field-encryption boundary ADR (ADR-006) accepted | EC + SD | Updated `architecture/01-system-architecture.md` §3.1; ADR file | Green |
| HIPAA-3 | Individual rights flows live: 164.524 access, 164.526 amendment, 164.528 accounting | UI + SD + EC | Provider portal screens P9/P10/P11 deployed | Green |
| HIPAA-4 | Notice of Privacy Practices authored, versioned, surfaced in UI P6, acknowledgment audit-logged | Legal + EC + UI | `compliance/policies/01-notice-of-privacy-practices.md` + audit sample | Green |
| HIPAA-5 | PHI-redaction CI test enforced; property-based fuzz coverage on logging paths | SD + EC | CI run; sample blocked PR | Green |
| HIPAA-6 | Workforce training delivered and attested for credentialing operators and committee members | EC + HR | Attestation log | Green |
| HIPAA-7 | Workforce sanction policy, clearance/background-check policy, device-controls baseline published | EC + HR + CISO | `compliance/workforce/*.md` | Green |
| HIPAA-8 | Session timeout policy ratified (15 min idle for PHI workstations) and enforced; UI P2 timer reflects | SD + EC | ADR + screenshot evidence | Green |
| HIPAA-9 | Minimum-necessary ABAC policy in production; server-side enforcement on every PHI-bearing endpoint | SD + EC | Policy doc + integration test | Green |

### 1.3 Business Associate Agreement (BAA) Execution

| ID | Vendor | Owner | Evidence | Status gate |
|---|---|---|---|---|
| BAA-1 | AWS (covers RDS, S3, KMS, MSK, Cognito, Secrets Manager, SES, CloudWatch, EKS if used) | EC + Procurement | AWS BAA acceptance ID + scope mapping | Green |
| BAA-2 | Temporal Cloud | EC + Procurement | Executed BAA at `compliance/baas/temporal.md` | Green |
| BAA-3 | CAQH ProView (enterprise tier ≥500 req/min) | EC + Procurement | BAA + service contract | Green |
| BAA-4 | DocuSign (HIPAA tier) | EC + Procurement | Executed BAA | Green |
| BAA-5 | Identity verification vendor (Jumio or Persona — selected per ADR-004) | EC + Procurement | BAA + DPA + biometric retention SLA | Green |
| BAA-6 | Twilio (SMS) — only if SMS notifications launched | EC + Procurement | BAA + TCPA opt-in workflow | Green if SMS in scope, N/A otherwise |
| BAA-7 | Observability backend (Honeycomb with BAA OR alternative BAA-covered tracing solution) | EC + SD | BAA + subprocessor flow-down | Green |
| BAA-8 | Confluent Schema Registry — clarify Cloud (BAA needed) vs self-hosted on MSK (AWS BAA covers) | EC + SD | Resolution documented in ADR | Green |
| BAA-9 | NPDB Data Use Restrictions agreement (federal DUR, not BAA) | EC + Legal | Executed DUR | Green |
| BAA-10 | Subprocessor flow-down evidence per vendor (e.g., DocuSign's AWS sub) | EC | Per-vendor subprocessor list archived | Green |

### 1.4 NCQA Pre-Audit

| ID | Item | Owner | Evidence | Status gate |
|---|---|---|---|---|
| NCQA-1 | Internal mock audit against NCQA CR 1–7 standards | EC + PM | Internal audit report at `compliance/audits/01-internal-mock.md` | Green; zero critical; ≤1 minor remediated |
| NCQA-2 | 25 randomly-selected staged provider files audited end-to-end against NCQA file template | EC | Per-file checklist results | Green |
| NCQA-3 | Per-credential PSV evidence verified: license (state board), DEA, board cert (ABMS), education (CAQH-as-PSV or direct), residency, work history (5y direct verification), malpractice (NPDB + carrier), federal sanctions, state Medicaid exclusions, NPI, identity | EC | Evidence pack per file | Green |
| NCQA-4 | Committee charter, quorum rule, recusal policy, appeal process, emergency credentialing process documented | PM + MD + Legal | `docs/03-committee-charter.md` | Green |
| NCQA-5 | Re-credentialing cycle (36-month) automation evidence; ongoing monitoring (NCQA CR 5) scheduler live | SD + EC | Scheduler runbook + sample re-cred file | Green |
| NCQA-6 | Adverse action workflow with NPDB write integration tested in staging; DCN tracking entity in DB | SD + EC | Staging report + DCN sample | Green |
| NCQA-7 | Appeal / fair-hearing UI + workflow live | UI + SD + EC | Demo + sample case | Green |

### 1.5 Operational Readiness

| ID | Item | Owner | Evidence | Status gate |
|---|---|---|---|---|
| OPS-1 | Runbooks published: CAQH outage, NPDB mTLS rotation, DocuSign reconciler, identity vendor outage, audit ledger chain break, committee quorum loss, outbox/Debezium lag, Kafka DLQ redrive, KMS rotation, cross-region failover, top-10 state-board adapters | SD + Platform | `docs/runbooks/*.md` | Green |
| OPS-2 | On-call rotation active for 14 days pre-launch (shadow); 24/7 coverage with primary + secondary | PM + SD + Platform | Rotation schedule + first-page-drill log | Green |
| OPS-3 | SLO/SLI dashboards live; alerts wired to PagerDuty (or equivalent); error-budget burn alerts validated | SD + Platform | Dashboard URLs + alert test log | Green |
| OPS-4 | Capacity model published; load test passes at 2x forecast peak; 7-day soak test green per QG-4 | SD + Platform | `architecture/capacity-model.md` + test reports | Green |
| OPS-5 | DR exercise completed: cross-region failover (us-east-1 → us-west-2) with in-flight workflows; RTO ≤4h, RPO ≤15m proven | SD + Platform + CISO | DR runbook + exercise report | Green |
| OPS-6 | Audit ledger verify-chain API returns `is_chain_intact=true` against 30 days of staging data | SD + EC | Verify-chain output | Green |
| OPS-7 | External RFC 3161 timestamping authority selected and integrated; first quarterly attestation receipt archived | EC + SD | Attestation receipt | Green |
| OPS-8 | Reconciliation jobs (daily Kafka↔DB, weekly stale sanction) operational with 14 consecutive days of zero drift | SD + EC | Reconciliation reports | Green |
| OPS-9 | Replay tooling per Kafka topic exercised in staging within last 30 days | SD | Replay log | Green |
| OPS-10 | Per-state legal scraping allowlist published; per-state runbook stubs for 50 states; top 10 fully filled | Legal + EC + SD | `compliance/state-scraping-allowlist.md` + runbooks | Green |

### 1.6 Communication and Legal

| ID | Item | Owner | Evidence | Status gate |
|---|---|---|---|---|
| LEG-1 | Cyber insurance policy in force; coverage limits documented; breach-response carrier-side workflow validated | Legal + EC | Policy reference | Green |
| LEG-2 | Privacy Notice (NPP), terms of service, accessibility statement, cookie/tracking-tech notice published | Legal + UI | Live URLs | Green |
| LEG-3 | Breach Notification Procedure (4-factor assessment, individual/HHS/media templates, 60-day SLA) ratified | PO + Legal + EC | `compliance/ir/breach-notification.md` | Green |
| LEG-4 | Decision-letter templates (approval, denial with appeal rights, deferral) Legal-reviewed | Legal + EC | Template files | Green |
| LEG-5 | Communication plan for go-live (executive sponsors, credentialing ops, committee, providers in pilot cohort) | PM | Comms plan | Green |
| LEG-6 | Out-of-scope items from charter §2.2 (hospital privileges, IMG ECFMG, paper-file migration) explicitly handed off with documented seam owners | PM + Legal | Hand-off memos | Green |

---

## 2. Phased Rollout Strategy

Rollout proceeds in four phases. Each phase gate requires explicit go/no-go from PM + EC + PO + CISO + MD. No phase auto-advances.

### 2.1 Phase 0 — Shadow Mode (4 weeks)

**Purpose:** Validate end-to-end correctness without affecting any real provider. System runs in parallel with current manual process; results are compared, not acted on.

**Configuration**
- Production infrastructure stood up (us-east-1 primary, us-west-2 DR).
- All integrations live with **real** CAQH, NPPES, NPDB, sanction sources, state boards (read-only).
- Identity vendor in production mode but provider applications NOT created; instead, current ops team feeds anonymized intake-equivalent data into a shadow workflow.
- Committee workflow runs against shadow files; no DocuSign envelopes issued externally (DKIM envelopes generated for the audit ledger only).
- Kafka outbox emits to a `*.shadow.v1` topic family; downstream consumers do not subscribe.
- Real audit ledger writes; real freshness monitors; real reconciliation jobs.

**Entry gate**
- All §1 pre-launch checklist rows green.
- Re-assessment by Reality Checker says "conditional-go."

**Exit criteria (must hold for 4 consecutive weeks)**
- ≥50 shadow files processed end-to-end without engineering intervention.
- Sanction-detection recall = 100% on daily synthetic-positive injections.
- Audit ledger completeness = 100% (ratio of state transitions to ledger writes).
- PHI leakage incidents = 0.
- p95 verification latency ≤15 min per source.
- Daily Merkle root produced and timestamped; verify-chain green daily.
- Reconciliation drift = 0 for 14 consecutive days.
- No P0 or P1 incident.
- Operators report dashboard usability is sufficient (qualitative survey).
- Committee dress rehearsal results carried forward: zero blocking defects from dress rehearsal still open.

**Exit decision**
- Joint go/no-go: PM (A), EC, PO, CISO, MD, SD. Decision recorded in audit ledger with rationale.

### 2.2 Phase 1 — 5% Canary (4 weeks)

**Purpose:** Real providers credentialed by the system, at a volume that limits blast radius.

**Configuration**
- ~6 new applications/week (5% of 120 forecast).
- Cohort selection: re-credentials only (lower risk than initial credentials), single specialty (e.g., internal medicine), single state (e.g., NY).
- DocuSign envelopes issued externally; Kafka events emitted to production topics; downstream consumers subscribed.
- Manual ops backup: every canary file is also tracked by a credentialing specialist who can intervene at any step.
- Daily review of canary outcomes by Compliance Lead + PM.

**Entry gate**
- Phase 0 exit criteria all met.
- Joint go/no-go signed.
- Communication to canary-cohort providers sent (their experience may differ from norm).

**Exit criteria (must hold for 4 consecutive weeks)**
- Zero auto-approvals reversed (Experiment E4 not yet active — auto-approval predicate disabled in Phase 1).
- Zero NPDB-write deadline misses on any adverse decision.
- Zero state-statutory-deadline misses (CA 60d, NY 90d, etc.) — at 5% volume in one state this is bounded.
- Median cycle time ≤45 days (improvement target; not the full 28-day charter goal yet).
- p95 portal latency ≤2s; p95 verification ≤15 min/source.
- Audit-ledger completeness 100%; chain-integrity verified daily.
- No HIPAA-reportable event.
- No critical SEV (P0/P1) incidents; any P2 incidents have post-mortems published.
- Provider satisfaction survey (canary cohort) ≥4.0 / 5.0.
- Operator survey ≥4.0 / 5.0.

**Exit decision**
- Joint go/no-go as Phase 0.

### 2.3 Phase 2 — 25% (6 weeks)

**Purpose:** Stress the system at non-trivial volume; broaden cohort to expose state and specialty heterogeneity.

**Configuration**
- ~30 new applications/week (25%).
- Cohort selection: still initial cred + re-cred mixed; expand to top 5 states (NY, CA, TX, FL, NJ) and 4–5 specialties.
- All features live except auto-approval (E4 remains shadow-mode if running at all).
- Daily review by Compliance Lead + PM continues; weekly steering committee.

**Entry gate**
- Phase 1 exit criteria all met.
- Per-state SLA tracker shows green for the 5 expanded states.
- Per-state runbooks for the 5 expanded states fully filled in.

**Exit criteria (must hold for 6 consecutive weeks)**
- All Phase 1 criteria still met.
- Median cycle time ≤35 days.
- p95 cycle time ≤60 days.
- Per-state freshness SLA passing for all 5 in-scope states.
- Re-credentialing automation rate ≥70% on in-scope files.
- Zero NCQA-finding-class defects; CR-aligned audit on a 10-file sample passes.
- DR exercise repeated in production with no impact to in-flight workflows.

**Exit decision**
- Joint go/no-go plus Executive Sponsor (CMO + CIO) sign-off.

### 2.4 Phase 3 — 100% (steady-state)

**Purpose:** Full production volume across all 50 states + DC + 5 territories.

**Configuration**
- All forecast volume.
- Auto-approval predicate (Experiment E4) considered for activation as a separate experiment with its own go/no-go (Privacy Officer + Compliance Lead + Committee Chair + General Counsel sign-off per `experiments/01-experiment-plan.md` §9).
- All 50-state adapters live; per-state runbooks complete.
- Ongoing monitoring (NCQA CR 5) active.

**Entry gate**
- Phase 2 exit criteria all met.
- All 50 state adapters have ≥30 days of green freshness data (sourced from shadow + canary observation).
- All 50-state runbooks at minimum-stub completion.

**Steady-state KPIs (per `docs/01-project-charter.md` §1.2)**
- Median credentialing cycle time ≤28 days.
- ≥85% of files with zero manual primary-source verification.
- Audit findings per quarterly review: 0 critical, ≤1 minor.
- Committee meeting prep time ≤5 min/file.
- Re-credentialing automation rate ≥90%.

---

## 3. Rollback Procedures

Rollback is a first-class operation. The system is built around immutable audit and idempotent consumers; rolling back is about **routing**, not data destruction.

### 3.1 Rollback Triggers (any of)

- **R-P0** Sanction-detection recall <100% in any 24-hour window (any false negative on synthetic injection).
- **R-P0** Any auto-approval of a provider later found to be sanctioned/excluded (in Phase 3 with E4 active).
- **R-P0** Audit ledger chain-integrity check fails.
- **R-P0** PHI breach (per breach notification procedure 4-factor assessment).
- **R-P0** Loss of vendor BAA (vendor revokes or expires).
- **R-P1** SLO error budget exhausted (e.g., portal availability <99.9% over 7 days).
- **R-P1** Provider directory data corruption (per CA SB 137 / TX SB 1264 risk).
- **R-P1** Multiple state-board adapters concurrently red for >24h with no manual fallback capacity.
- **R-P1** Committee unable to convene a quorum for >14 days (operational, not software, but rollback may still apply if software cause).
- **R-P2** NCQA pre-audit findings during quarterly review of "critical" class.

### 3.2 Rollback Modes

**Mode A — Pause new intake.** The application service stops accepting `POST /v1/applications`. In-flight files continue. Provider portal P1 shows a maintenance notice. This is the most common, lowest-impact mode.

**Mode B — Pause specific workflow step.** Operators flip a feature flag that pauses S3 / S4 / S5 / S6 / S7. In-flight workflows pause at the gate via Temporal signals. Used when a specific integration (e.g., NPDB) has failed in a way that requires investigation.

**Mode C — Drain S7 and stop event emission.** Stop the outbox publisher; downstream systems continue to process previously-emitted events but no new onboarding events flow. Used when there is a concern about a particular cohort of approved providers (e.g., suspect of a sanction-data staleness).

**Mode D — Revert to previous release.** Standard blue/green or canary revert at the deployment level. Audit ledger is forward-only; revert does not delete entries. Outbox events written by the bad release are retained but consumers must be idempotent.

**Mode E — Roll back to previous phase.** Move from Phase 2 → Phase 1, etc. Requires routing logic in the application service to refuse intake from cohorts outside the previous phase's scope.

**Mode F — Full hard stop.** Stop the system entirely; revert to manual process. Last resort. Pre-positioned: the manual workflow runbook from before HCPC is preserved and accessible.

### 3.3 Rollback Authority

| Trigger class | Authority required to invoke | Authority required to resume |
|---|---|---|
| R-P0 | Any of PM, SD on-call, CISO, PO, EC | Joint sign-off: PM + EC + PO + CISO + (MD if patient-safety implicated) |
| R-P1 | PM or SD on-call | PM + EC + SD |
| R-P2 | PM | PM |

### 3.4 Rollback Mechanics

- All rollback actions emit audit-ledger events tagged `OPERATIONAL_ROLLBACK_<MODE>` with actor, reason, scope.
- Provider-facing communication: a templated notice is published within 30 min of Mode A, B, or C; within 60 min for Mode D, E, F.
- Post-mortem: required for every R-P0 and R-P1. Published within 5 business days.
- Audit ledger is never rewound. State machines may transition to `paused_due_to_rollback` (new state added to APPLICATION state enum if not present).

---

## 4. Day-2 Operations

### 4.1 Monitoring

Three-tier observability:

1. **Business metrics (Grafana + reporting DB):** weekly applications, median cycle time, % automated, committee throughput, re-cred cycle compliance, per-state SLA compliance.
2. **System SLOs (Prometheus + Grafana):** availability, latency, error rate per service; outbox lag; Temporal task queue depths per state and per sanction source; Kafka consumer lag; RDS read/write latency; cache hit rates.
3. **Audit/compliance health (custom):** daily Merkle root status, chain-integrity result, freshness per sanction source, freshness per state license source, PHI-redaction CI pass rate, BAA expiration tracking, KMS rotation status.

Each SLO from `architecture/01-system-architecture.md` §8.4 has a corresponding SLI definition, dashboard panel, and alert threshold:

| SLO | SLI | Alert burn rate |
|---|---|---|
| Provider Portal 99.9% availability | 5xx + non-200 / total requests | 2% over 1h pages on-call |
| Committee Console 99.5% | Same | 5% over 1h pages on-call |
| Audit ledger write 99.99% | Failed inserts / total | Any failure pages on-call immediately |
| Kafka emit 99.99% | Outbox→topic delivery success | >0.01% gap pages SRE |
| Verification activities | Queue depth, age | Depth >100 OR age >30m pages SRE |

### 4.2 Alerting

- **P0 (immediate page, 24/7):** audit ledger chain break; KMS unavailable; BAA-protected vendor outage with no manual fallback; sanction-detection synthetic-injection miss; portal unavailable >5 min.
- **P1 (page during business hours, on-call after):** any single SLO breach; per-state adapter red for >2h; CAQH error rate >25%; Kafka consumer lag >1h.
- **P2 (ticket, next-business-day):** per-source freshness in amber band; non-blocking dashboard data freshness lag; minor latency regressions.
- **P3 (weekly review):** business metric drifts; capacity trend deviations.

PHI must not appear in any alert payload. Alert templates reviewed for PHI before deploy; outbound alert content scanned at runtime.

### 4.3 On-Call Rotation

- 24/7 primary + secondary engineering on-call, weekly rotation.
- Separate Privacy on-call (Privacy Officer or designee) for HIPAA-classified incidents; on-call SLA 60 min.
- Separate Committee/Compliance on-call (Compliance Lead) for credentialing-decision-level incidents.
- Escalation path per `docs/01-project-charter.md` §9.3.
- Runbook-first culture: every page must reference a runbook URL. New alert types require a runbook before deploy.

### 4.4 Incident Response

- IR plan owned by `compliance/ir/01-incident-response-plan.md` (Phase A deliverable).
- Severity classification, communication, evidence preservation, breach 4-factor assessment, regulatory notification clocks (HIPAA 60-day, state-specific shorter clocks, NPDB 15-day for adverse actions).
- Tabletop exercise quarterly; post-mortem cadence enforced.

### 4.5 Change Management

- Two-person review on production-impacting changes; one reviewer must be from a different team (separation of duties).
- Deploys outside business hours discouraged; emergency deploys require explicit approval.
- Every deploy emits audit-ledger event with commit SHA, deployer, approver, rollback handle.
- Schema changes (Postgres, Kafka schema registry) require migration plan + rollback plan + dry-run in staging.
- Workflow code changes (Temporal) require replay test against production-shape history before merge.

### 4.6 Capacity Management

- Quarterly capacity review; forecast vs actual.
- Re-evaluate Temporal Cloud vs self-host (per ADR-001 follow-up #5) at year three or when volume exceeds 50,000 applications/year.
- Per-state adapter cost monitored; expensive adapters (paid APIs) tracked against budget.

### 4.7 Vendor Management

- Annual BAA review; renewal SLA tracked.
- Subprocessor notification list per vendor; flow-down BAA confirmed.
- Vendor security questionnaire (SIG or equivalent) annually.
- Vendor outage playbooks linked from runbooks.

### 4.8 Audit & Compliance Cadence

- **Daily:** Merkle root computed and timestamped; freshness monitors per source; reconciliation drift report.
- **Weekly:** stale-sanction reconciliation; per-state adapter health summary; CR-checklist sample (5 random files).
- **Monthly:** OIG LEIE re-run on active population; Medicare opt-out re-run on active population; license-action subscription poll; access review.
- **Quarterly:** external RFC 3161 timestamping attestation; tabletop IR exercise; NCQA-style internal audit (25-file sample); quarterly capacity review; access analyzer; SOC 2 evidence collection.
- **Annual:** HIPAA risk assessment; pen test; BAA renewals; SOC 2 audit; workforce training refresh; committee bylaws review.

---

## 5. Re-Credentialing Automation Cadence

Re-credentialing is the largest day-2 workload (charter §1.2 KPI: ≥90% automation rate; 36-month cycle).

### 5.1 Trigger Sources

| Trigger | Cadence | Owner activity |
|---|---|---|
| 36-month cycle anniversary | Scheduler fires at T-90d, T-60d, T-30d | Auto-create re-cred application; notify provider |
| License-expiration window | T-90d, T-30d, T-7d | Renewal notice per UI D4 + P8 |
| Adverse event on monitored channel (LEIE, Medicare opt-out, state license action, NPDB Continuous Query) | Within 24h of source refresh | Immediate file flag; route to committee per `compliance/01-compliance-checklist.md` §2.3 |
| Material change reported by provider | On submission | Re-cred or delta application |

### 5.2 Scheduling Implementation

- Re-credentialing scheduler runs as a Temporal cron workflow (per `compliance/01-compliance-checklist.md` Control 2.2.2 follow-up; ADR-011 to be authored in Phase A).
- T-90d: scheduler creates a re-credentialing application in `pending_provider_action` state; provider is notified to confirm/update profile.
- T-60d: if provider has not started, escalation notice + cred-specialist outreach.
- T-30d: if still no action, file is paused and routed to operations; this should be rare given automation.
- T-0d: cycle anniversary; re-credentialing must be complete or the provider's network status transitions to `recredentialing_overdue` (event emitted to downstream consumers).

### 5.3 Re-Credentialing Workflow Differences vs Initial

- Same NCQA CR elements required (Control 2.2.5).
- Identity verification: re-confirmation rather than full liveness (per ADR-004 outcome; identity vendor BAA covers retention/refresh semantics).
- CAQH delta polling rather than full retrieval where possible.
- License + sanction PSV re-runs against fresh sources (workflow `_guard_no_stale` semantics enforce freshness).
- Committee path: eligible to auto-approval predicate (Experiment E4) once that experiment ships and is signed off.

### 5.4 Volume Forecast

| Year | Initial apps/yr | Re-cred apps/yr | Total | Approx weekly |
|---|---|---|---|---|
| Year 1 | 12,000 | ~3,100 (year-1 cohort entering cycle 3 years later contributes ≈0 in year 1; re-creds are existing population on 36-month cycle: ~9,300/3 ≈ 3,100/yr) | ~15,100 | ~290 |
| Year 2 | 20,000 | ~7,000 | 27,000 | ~520 |
| Year 3 | 40,000 | ~15,000 | 55,000 | ~1,060 |

Capacity model (Phase C deliverable OPS-4) must validate that the system sustains the Year 3 weekly throughput at p95 latencies stated in arch §8.4 with no more than 1.5x infrastructure cost vs Year 1 baseline.

### 5.5 Ongoing Monitoring Between Cycles (NCQA CR 5)

- Monthly OIG LEIE refresh → automated re-run of S4 LEIE against entire active-provider population; any new hit triggers alert + file pause.
- Daily SAM.gov + OFAC refresh → same.
- Weekly state Medicaid refresh per state → same; per-state SLA tracked.
- NPDB Continuous Query subscription → real-time event consumption; new entry triggers committee referral within 5 business days.
- State-license action subscriptions where available → ditto.

Failure of any ongoing-monitoring source for >2x freshness SLA produces a compliance alert visible in UI D3a; if unresolved within 24h, automatic suspension of affected providers from new patient assignment (downstream consumers responsible for honoring the event).

---

## 6. Go/No-Go Sign-Off (Final Production Cut)

Final go-live signature block (all required):

| Role | Name | Sign-off basis |
|---|---|---|
| Executive Sponsor (CMO) | _________ | Patient safety, clinical workflow |
| Executive Sponsor (CIO) | _________ | Technical readiness, operational maturity |
| Privacy Officer | _________ | HIPAA risk assessment, BAA execution, breach readiness |
| Compliance Lead | _________ | NCQA/CMS readiness; pre-audit clean |
| CISO | _________ | Security review, pen test, IAM, IR plan |
| Medical Director | _________ | Committee readiness, clinical correctness |
| General Counsel | _________ | Legal review, ToS/NPP/BAA, state overlay |
| Project Manager | _________ | Pre-launch checklist, comms, schedule |
| Senior Developer | _________ | Engineering readiness, runbooks, on-call |
| Reality Checker | _________ | Independent re-assessment supports conditional-go or go-live |

Sign-offs entered in audit ledger with ISO 8601 UTC timestamps.

---

## 7. Notes on This Plan

- This plan **assumes** the production readiness blockers are addressed. It does not authorize launching without them.
- Phase durations (4 / 4 / 6 weeks for Phases 0–2) are minimums; bad signals extend them.
- "Production ready" is not a state achieved at the end of Phase 3 — it is a state maintained continuously through Day-2 operations. Drop any of §4 cadences and the system drifts toward not-ready quickly.
- The realistic earliest go-live, assuming Phase A remediation starts immediately and runs in parallel where possible, is **W26–W32** from the original charter kickoff. The charter's W12 target is not achievable.

---

*End of Deployment Plan v1.0.0*
