# Production Readiness Review — Healthcare Provider Credentialing System

**Document ID:** HCPC-READINESS-001
**Version:** 1.0.0
**Status:** Final — Reality-Based Assessment
**Owner:** Reality Checker (TestingRealityChecker)
**Assessment Date:** 2026-06-13
**Verdict (overall):** **NOT-READY** — substantial paper architecture, no implementation evidence, multiple regulatory blockers
**Re-assessment:** required after blocker remediation; expect 2–3 cycles before conditional-go is plausible

---

## 0. How I Read These Artifacts

This is a **design-stage** project. The repo contains:

- A charter (`docs/01-project-charter.md`) describing what the system will do.
- An architecture baseline (`architecture/01-system-architecture.md`) with C4-ish components, a data model, an integration matrix, an SLO table.
- A workflow skeleton (`architecture/02-credentialing-workflow.py`) in which every activity is a `raise NotImplementedError` stub (see e.g. lines 374, 403, 435, 465, 487, 506, 529, 548, 572).
- One ADR (`architecture/03-adr-orchestration.md`).
- Three UI mockup documents.
- A self-acknowledged-incomplete compliance checklist (`compliance/01-compliance-checklist.md`) that rates the project itself **33 covered / 57 partial / 53 missing across 143 controls**.
- An experiment plan that explicitly depends on milestones M4–M9 ("Earliest Launch" column in `experiments/01-experiment-plan.md` §8.3) that have not happened.

There are **no implementation artifacts** in the repo: no service code, no Terraform, no Temporal worker binary, no Postgres migrations, no test results, no pen-test report, no executed BAAs, no IR plan, no runbooks, no SOC 2 evidence pack, no NCQA pre-audit, no committee charter document. Every "evidence required" column in the compliance checklist is unfulfilled.

A production-readiness review at this stage is a review of **design intent**, not delivered software. I score accordingly: even where the design is excellent (it is, in places), nothing has been *built* and nothing has been *audited*. The compliance checklist's own author rated 12 controls "MISSING" as critical-must-fix-before-go-live (§6.1). Those are not the only blockers.

---

## 1. Executive Verdict

**Overall: NOT-READY.**

Even granting that every word of the design is sound, the system has not been built, not been tested, not been pen-tested, not been BAA-papered with each vendor, not been pre-audited by NCQA, and not run a single real provider end-to-end. The charter targets a W12 go-live (`docs/01-project-charter.md` §4 milestone M12). Today is W0 from the perspective of executable code.

Beyond the obvious build-it-first problem, there are **six categorical blockers** that would still prevent a go-live even if the code were written exactly as designed:

1. **NPDB write integration is entirely missing** — adverse-action reporting to NPDB within 15 days under HCQIA §11131 is mandatory; the architecture only specifies NPDB *reads*. (`compliance/01-compliance-checklist.md` §6.1 item 2; `architecture/01-system-architecture.md` §5.)
2. **Board certification and DEA verification adapters do not exist** — NCQA CR requires PSV for both; current design treats both as document uploads. (`compliance/01-compliance-checklist.md` §6.1 items 4–5; `ui/01-provider-portal.md` Screen P5 line 367–369.)
3. **HIPAA individual-rights flows (164.524 access, 164.526 amendment, 164.528 accounting of disclosures) are absent from the provider portal** — these are not optional. (`compliance/01-compliance-checklist.md` §6.1 item 6.)
4. **The data model in `architecture/01-system-architecture.md` §3.1 omits email, phone, mailing address, malpractice history, work history, education, DEA** — the very fields the UI collects (`ui/01-provider-portal.md` Screens P3–P6). The data model and the UI describe different systems.
5. **The Credentialing Committee Charter is cited but does not exist** — `ui/03-committee-review.md` Screen C5 line 351 references "Credentialing Committee Charter §4.2"; no such file is in `docs/`. Auditors will request it.
6. **No appeal / fair-hearing flow** — NCQA CR 6 mandates one; nothing in the UI design provides one. (`compliance/01-compliance-checklist.md` Control 2.4.9; §6.1 item 10.)

Add to this: no breach-notification readiness materials exist (IR plan, 4-factor breach assessment, HHS notification workflow, templates — all "MISSING" in §1.4 of the compliance checklist); no BAA evidence files (`compliance/baas/` is empty per the checklist §1.3); the committee workflow only generates DocuSign envelopes on terminal approve/deny, ambiguously leaving `needs_info` decisions unsigned (Gap 5.1.7); and the architecture commits to Honeycomb and Twilio without confirming BAAs (compliance checklist §1.3.6–1.3.7).

The charter target of a 12-week build to production is, charitably, aggressive. Read against the reality of the gaps surfaced by the project's own compliance checklist, it is **not survivable without scope reduction** (e.g., phased state coverage, deferred re-cred automation, manual NPDB write while integration is built).

---

## 2. Dimension Verdicts at a Glance

| Dimension | Verdict | One-line basis |
|---|---|---|
| Production readiness | **BLOCKER** | No code; multiple regulatory flows missing; charter target W12 unrealistic |
| Scalability | **NEEDS WORK** | Design has sound primitives (bulkhead task queues, outbox) but capacity math, load test plan, and Temporal cost model at 10x are unverified |
| HIPAA compliance | **BLOCKER** | Data model incomplete vs UI; individual rights absent; BAA folder empty; breach playbook missing; PHI redaction CI test undefined |
| Audit defensibility | **BLOCKER** | NPDB write missing; committee charter missing; appeal flow missing; per-state regulatory overlay missing; canonical-JSON spec not pinned |
| Failure mode coverage | **NEEDS WORK** | Per-integration retry/circuit-breaker matrix is thoughtful; runbooks, replay tooling, DLQ procedures not yet authored; reconciliation jobs described, not designed |
| Operational maturity | **BLOCKER** | No runbooks; no on-call rotation; no SLO/SLI dashboards; no IR plan; no DR exercise; no observability validation |

Ready dimensions: **none**. Not-ready dimensions: all six.

---

## 3. Per-Dimension Findings

### 3.1 Production Readiness — BLOCKER

**Citations**

- `docs/01-project-charter.md` §4: M12 "Production go-live + 30-day hypercare plan" by W12.
- `architecture/02-credentialing-workflow.py` lines 374, 403, 435, 465, 487, 506, 529, 548, 572: every activity is `raise NotImplementedError`.
- `architecture/03-adr-orchestration.md` §"Follow-up Actions": four actions still target W1/W2/W6, none marked done.
- `compliance/01-compliance-checklist.md` §0 admits "first-draft artifacts ALWAYS have gaps" and totals 53 missing controls.

**Findings**

1. The system exists on paper. The workflow is a typed skeleton that would not run a single activity if started. A skeleton is the right artifact at this stage — but it is not a production-readiness artifact.
2. Every charter milestone M4–M12 (`docs/01-project-charter.md` §4) is forward-dated. None have execution evidence.
3. Quality gates QG-1 through QG-5 (`docs/01-project-charter.md` §8) have *unchecked* checkboxes throughout: pen test, freshness monitor 30-consecutive-day stability, dress rehearsal with 10 real files, 7-day soak test, daily reconciliation 14-consecutive-day zero drift. None of these can be true today.
4. The 12-week timeline cannot absorb the discovery of 12 critical-severity compliance gaps (`compliance/01-compliance-checklist.md` §6.1) plus building seven verification adapters per state, plus per-source sanction integration, plus committee tooling, plus dress rehearsal, plus pen test, plus NCQA pre-audit, plus 50-state legal allowlist. Pick three.
5. Charter §3.1 lists S1–S7 with "Avg Duration (Automated)" estimates as if measured; the values are aspirational. There is no telemetry data anywhere in the repo.

**Verdict basis:** No code, no audit, no pen test, no real-data rehearsal, no go-live evidence. BLOCKER.

---

### 3.2 Scalability — NEEDS WORK

**Citations**

- `architecture/01-system-architecture.md` §6 (tech stack), §8 (resilience), §8.4 (SLO table).
- `architecture/03-adr-orchestration.md` §"Context" point 7 (volume forecast: 12k→40k apps/year by year 3).
- `compliance/01-compliance-checklist.md` (no load-test references found anywhere).

**What's good**

- Per-state and per-source task queues for bulkhead isolation (`architecture/01-system-architecture.md` §8.1, `architecture/02-credentialing-workflow.py` lines 845, 861). This will absorb a single-state outage without starving CAQH.
- Outbox + Debezium for event delivery (`architecture/01-system-architecture.md` §4.2). Right pattern for at-least-once with idempotent consumers.
- Async verification activities with Temporal retry policies (`architecture/02-credentialing-workflow.py` lines 259–310). Reasonable defaults.
- Volume math in `architecture/03-adr-orchestration.md` Context point 7 modeled to 40,000/year by year three.

**What's missing for 10x**

1. **No capacity model.** Charter assumes ~120 initial/week + 60 re-cred/week (`experiments/01-experiment-plan.md` §0.1). At 10x that's 1,200/week initial. Each application fans out to ~50–60 verification activities (4 federal sanctions + up to 50 state Medicaid + up to 25 state licenses + CAQH + NPI). Peak burst load is `1,200 × 60 = 72,000` activity executions/week, or ~12,000/business-day. No artifact analyzes whether Temporal Cloud namespace `credentialing` can sustain this, what task-queue worker counts are needed, what Postgres write rates are needed, or what CAQH rate-limit headroom remains.
2. **No load-test plan.** Charter §8 lists Definitions of Done but no row mentions a load test. The experiment plan does not include a scalability experiment. There is no synthetic-traffic harness specified.
3. **CAQH is a hard external bottleneck.** Charter §2.3 says "enterprise tier (>=500 req/min)". At 10x volume during burst (say 200 apps/hour processed in parallel), CAQH calls alone could approach that ceiling, and that's before retries. `architecture/01-system-architecture.md` §8.2 mentions a token-bucket client but provides no math relating bucket size to forecast volume.
4. **Per-state scrapers are the most fragile link** (`docs/01-project-charter.md` §7 R2 severity 20). State boards rate-limit aggressively and change schemas without notice. At 10x volume, the probability of any single state's adapter being amber on any given day approaches 1. The design has the right concepts (per-state runbook, schema-drift detection) but no SLI for "fraction of states healthy this hour" and no automated state-degradation handling beyond "switch to scraper" → "switch to manual queue."
5. **Postgres write rate.** The outbox pattern writes one row per state transition per application — `architecture/01-system-architecture.md` §3.1 LICENSE + VERIFICATION_RESULT + AUDIT_EVENT + outbox_events all rows-per-event. At 10x with ~60 verifications/app, write-amplification approaches 4x. No analysis of RDS instance class, Multi-AZ failover behavior under sustained write load, or whether logical replication keeps up.
6. **Audit ledger hash chain is a global serialization point per application** (`architecture/01-system-architecture.md` §7.2). Concurrent activities racing to write events on one application must serialize on `SELECT prev_event_sha256 FOR UPDATE` (acknowledged as a placeholder in `architecture/02-credentialing-workflow.py` line 613). Under 10x volume, intra-application contention is bounded, but global insert rate on `audit_event` and the daily-Merkle-root job must scale; no analysis.
7. **Re-credentialing scheduler at scale.** Charter §1.2 targets >=90% automation rate. With ~9,300 active providers on a 36-month cycle, the scheduler must dispatch ~258 re-creds/month. At 10x population (93,000 providers), that's ~2,580/month — manageable, but the scheduler design is not in the architecture (`compliance/01-compliance-checklist.md` Control 2.2.2 calls this out).

**Verdict basis:** Design primitives are correct; capacity math, load-test artifacts, and degradation behavior under sustained 10x are all missing. NEEDS WORK.

---

### 3.3 HIPAA Compliance — BLOCKER

**Citations**

- `compliance/01-compliance-checklist.md` §1 (HIPAA controls): the project's own evidence collector counts the HIPAA section as 11 covered / 24 partial / 21 missing across 56 controls.
- `architecture/01-system-architecture.md` §3.1 (data model), §9 (security & compliance hooks).
- `ui/01-provider-portal.md` P3 lines 224–232 (fields collected by UI), P6 line 429 (NPP reference).

**Findings**

1. **Data model is not HIPAA-inventory-complete.** Email, phone, mailing address, malpractice claims history, education, work history, DEA — all collected by UI, none modeled in the ER diagram (`architecture/01-system-architecture.md` §3.1; gap raised explicitly at `compliance/01-compliance-checklist.md` §5.1.1 marked HIGH). Until data model = collected data, you cannot pass a HIPAA inventory audit.
2. **Field-encryption boundary is inconsistent with charter policy.** Charter §2.1 commits to AES-256 field encryption for PHI. The arch §3.1 ER diagram marks `npi`, `caqh_id`, `license_number` as plain string fields. NPI alone is arguably a public registry value; paired with name, it is a unique identifier under HIPAA identifier #18. There is no ADR pinning the policy. (`compliance/01-compliance-checklist.md` Controls 1.1.3, 1.1.4, 1.1.7; Gap 5.1.4.)
3. **No BAA evidence files exist.** `compliance/baas/` is referenced (`architecture/01-system-architecture.md` §9) but empty (compliance checklist §1.3 marks all 10 vendor rows PARTIAL or MISSING). Going live without filed BAAs is a per-vendor regulatory violation.
4. **Individual rights flows missing.** 164.524 (right of access), 164.526 (right to amend), 164.528 (accounting of disclosures) — none addressed in the provider portal (`compliance/01-compliance-checklist.md` Controls 1.2.19–1.2.21; §6.1 item 6). HHS investigates complaints under these provisions routinely.
5. **PHI redaction in logs has no enforcement.** `architecture/01-system-architecture.md` §9 says "CI test verifies no PHI tokens leak." The CI test does not exist in this repo. `compliance/01-compliance-checklist.md` §5.3.4 notes "regex-only is insufficient." If logs leak PHI to Honeycomb, that is a vendor breach (and `compliance/01-compliance-checklist.md` §1.3.6 also flags Honeycomb's BAA as unconfirmed).
6. **Identity images (selfie + gov ID) retention undefined.** Biometric identifiers under HIPAA identifier #15 + photographic image #16 (`compliance/01-compliance-checklist.md` §1.1.15) — vendor BAA clauses + retention SLA not pinned. Standard practice is "as short as necessary"; current design implies the generic 10-year document retention.
7. **Breach notification readiness is absent.** No IR plan file, no 4-factor breach risk assessment template, no HHS notification workflow, no individual notification template, no media notification process (`compliance/01-compliance-checklist.md` §1.4 marks 7 of 9 breach-readiness controls MISSING). Charter §7 R3 says "IR plan with 60-min activation" — the plan that is supposed to activate is itself not written.
8. **Session timeout undefined.** UI P2 line 176 shows "Session expires in 27:14" and warns at T-2min, but no ADR sets the policy. HIPAA industry baseline is 15 min idle for PHI workstations (`compliance/01-compliance-checklist.md` Control 1.2.5).
9. **No minimum-necessary enforcement server-side.** UI D5 line 400 has a "PHI access modal" that is client-side only (`compliance/01-compliance-checklist.md` Control 1.2.6). ABAC policy server-side does not exist.
10. **NPP itself is not in the repo.** UI P6 line 429 references "HIPAA Notice of Privacy Practices PDF" with a link; the PDF is not authored anywhere in the repo (`compliance/01-compliance-checklist.md` Control 1.2.22).

**Verdict basis:** Inventory not complete, individual rights absent, BAAs unpapered, breach playbook absent, redaction unenforced. Any one would block; together they are categorical. BLOCKER.

---

### 3.4 Audit Defensibility — BLOCKER

The audit ledger design is the strongest part of the architecture and an embarrassing fraction of what passing an NCQA / CMS audit actually requires. I will not let one strong subsystem mask the gaps elsewhere.

**Citations**

- `architecture/01-system-architecture.md` §7 (audit trail design).
- `compliance/01-compliance-checklist.md` §2 (NCQA/CMS), §4 (data integrity), §6.1 (critical gaps).
- `architecture/02-credentialing-workflow.py` lines 575–632 (`emit_audit_event` activity).

**What is well-designed (and would survive audit if implemented)**

- Hash chain construction (arch §7.2), daily Merkle root with S3 Object Lock + RFC 3161 timestamping (§7.3), separation of duties on DB roles (§7.3), verify-chain API (§7.4 + UI D5 line 354). All thoughtful, all required.
- The 10-year retention statement (charter §8.1) and the explicit choice to treat Temporal history as operational and the S3-locked ledger as the legal record (`architecture/03-adr-orchestration.md` §"Compliance Impact").
- Idempotency keys derived from `application_id:step:attempt` (workflow line 330).

**What will fail an audit**

1. **NPDB write missing.** As soon as the committee denies its first physician, HCPC has 15 days under HCQIA §11131 to report. The arch has no NPDB-write integration (`compliance/01-compliance-checklist.md` §6.1 item 2). A first denial without an NPDB report is a federal reporting violation.
2. **Committee Charter document does not exist** (`compliance/01-compliance-checklist.md` §5.1.5 marked HIGH; §6.1 item 3). UI C5 cites it for the quorum rule. An auditor will ask "show me the committee charter." There will be no document. This is binary.
3. **Appeal / fair-hearing process missing** (Control 2.4.9). NCQA CR 6 requires this; nothing in UI design provides it. First denied provider will request an appeal; HCPC will have no process.
4. **Per-state regulatory deadlines unmonitored.** CA Knox-Keene (60 days), NY DOH (90 days), CA SB 137, TX SB 1264 directory accuracy, CA 805 reports — `compliance/01-compliance-checklist.md` §3 lists these as MISSING. UI D1 SLA timer is a generic 28-day target, not bound to per-state statutes.
5. **Ongoing monitoring (NCQA CR 5) not designed.** Monthly LEIE re-checks on active-provider population, NPDB Continuous Query enrollment, state-license action subscriptions — all MISSING (`compliance/01-compliance-checklist.md` §2.3, §6.1 item 7).
6. **Board certification PSV missing** (Control 2.1.5). NCQA CR finding waiting to happen on first audit.
7. **DEA verification missing** (Control 2.1.2). Same.
8. **Work-history verification missing** (Control 2.1.6). NCQA requires direct verification of last-5-years work history with explanations for gaps >6 months. Not designed.
9. **Hospital privileges verification missing** (Control 2.1.12). Charter §2.2 declared this out of scope; NCQA still requires evidence. Tension unresolved.
10. **Canonical JSON spec not pinned** (Control 4.1.8). Workflow line 322 uses `json.dumps(sort_keys=True, separators=(",", ":"), default=str)` — the `default=str` for datetime is fragile across Python versions and serializer implementations. JCS RFC 8785 should be specified in an ADR so future verifiers byte-match the original chain.
11. **Hash chain prev-fetch concurrency is a placeholder** (Control 4.1.10; workflow line 613). Production needs `SELECT … FOR UPDATE` or sequence-based ordering. The skeleton acknowledges this; the ADR-008 listed in the compliance follow-ups (`compliance/01-compliance-checklist.md` §7) does not yet exist.
12. **`needs_info` decisions are unsigned** (Gap 5.1.7). `_run_committee` (workflow lines 894–956) skips DocuSign and DKIM envelope creation when state is `needs_info`. Auditors will ask: what is the signed evidence that the committee, in session and with quorum, decided this file needs information? Today: ledger entries only, no envelope.
13. **Vote-change behavior overwrites silently** (Gap 5.1.8). `cast_committee_vote` (workflow lines 790–795) replaces a voter's prior vote in `self.committee.votes` directly. Whether the prior vote survives in the audit ledger depends on whether the implementation emits an audit event on every signal — the skeleton does not show this. Documented expectation must be: every vote-change is a separate immutable ledger entry.
14. **UI C6 line 432 vote math is wrong** (Gap 5.1.9). The committee-confirmation screen ships a math error. It is a small thing on its own; for a screen that ends up in audit binders it is corrosive.
15. **External RFC 3161 timestamping cadence is "quarterly"** (arch §7.3). Quarterly is adequate for many auditors; some prefer monthly. No commitment to which third-party timestamping authority — picking one is part of audit defensibility.

**Verdict basis:** Strong ledger primitives are necessary but not sufficient. NPDB-write absence alone is a federal reporting violation; the committee-charter absence makes the quorum claim unprovable; the appeal process absence is an NCQA blocker. BLOCKER.

---

### 3.5 Failure Mode Coverage — NEEDS WORK

**Citations**

- `architecture/01-system-architecture.md` §8 (failure modes and resilience), §8.2 (per-integration failure matrix), §8.3 (saga compensation), §8.4 (SLOs).
- `docs/01-project-charter.md` §7 (risk register).
- `architecture/02-credentialing-workflow.py` retry policies lines 259–310.

**What's good**

- The per-integration retry/circuit-breaker matrix (`architecture/01-system-architecture.md` §8.2) is one of the more carefully constructed parts of the design. Per-source retry policies (workflow 259–310) line up with the matrix.
- Bulkhead via per-state, per-source task queues (workflow lines 845, 861).
- Stale-detection guard (workflow `_guard_no_stale` lines 873–879) blocks S7 if any artifact is past 2x freshness SLA. This is the right semantics.
- Auto-deny on sanction hit (workflow `_guard_no_hard_fail` lines 881–892) — failure of LEIE/SAM/NPDB/OFAC/MEDICAID is non-retryable and hard-fails the workflow. Correct.
- Outbox + Debezium + DLQ for events (arch §8.2 S7 row).
- Saga compensation for S7 partial fan-out failure (arch §8.3) — chooses "do not retract" + reconciliation, which is the right call for credentialing.

**What's missing or unverified**

1. **No replay harness exists in the repo.** Architecture §6 mentions "WireMock (external sources) + Pact (contracts)" and "Fixture replay harness per external source supports R1/R2 mitigation." No fixtures, no harness code. Replay-harness existence is the prerequisite for the M6 milestone in the charter.
2. **No DLQ runbook.** Arch §8.1 mentions DLQ topic per consumer group with "redrive tooling" but the tooling is not specified and no runbook exists for "what an operator does at 3am when the EHR DLQ has 200 messages."
3. **CAQH outage manual-lookup runbook is referenced, not written** (arch §8.2 S2 row). Same for state-board scraper failover (§8.2 S3 rows).
4. **No chaos / game-day plan.** Charter §8.4 says outbox publisher must achieve 99.99% delivery in a 7-day soak test. No soak test design. No chaos plan to simulate CAQH down for 6 hours, NY DOH down for 24 hours, Kafka partition.
5. **Schema-drift detection on scrapers** (arch §8.2 S3 scraper row) is asserted but undesigned. What constitutes "drift"? A new HTML element? A removed field? An ID change? No spec; no canary.
6. **Reconciliation jobs are mentioned, not designed** (charter §7 R4 contingency "Reconciliation job runs weekly"; arch §8.4 daily reconciliation SLO; `compliance/01-compliance-checklist.md` Controls 4.3.1–4.3.6 mostly PARTIAL or MISSING). What does reconciliation compare against? What's the source of truth when they disagree?
7. **Quorum loss mid-meeting** is a UI state (UI C1 "Quorum lost — voting paused") but the workflow side has no signal-handling for mid-meeting quorum changes. The `_run_committee` waits on `_committee_finalized` with a 14-day timeout; if quorum drops mid-vote, nothing in the workflow code reacts.
8. **`CommitteeTimeoutError`** (workflow line 925) raises after 14 days. There is no handler for this exception in the workflow `run` method (workflow `run` ends at line 779; the exception propagates out and the workflow terminates). What is the operator experience for a 14-day-old committee timeout? Not specified.
9. **`StaleEvidence` and `VerificationFailed`** (workflow lines 648, 644) raise out of `_guard_no_stale` and `_guard_no_hard_fail`. Same lack of explicit catch in `run`. Means the workflow surfaces these as failed workflow executions in Temporal — fine, but the operator surfaces (UI D2 for an "auto-deny" state) are not aligned to that exception path.
10. **Identity vendor outage** (`docs/01-project-charter.md` §7 R6) has a manual-review queue and 3-attempt cap (UI P3 state variation), but the workflow code has no S1 retry/fallback logic — `s1_persist_intake` just persists; the identity transaction is handled separately. The hand-off from identity webhook → workflow signal is not modeled.
11. **NPDB mTLS cert rotation** is not addressed anywhere. mTLS certs expire; if NPDB cert rotation is missed, S4 NPDB hard-fails for all in-flight files. No alerting SLI; no rotation runbook.

**Verdict basis:** The per-integration matrix is good; everything that turns the matrix into operational reality (runbooks, replay harness, soak test, chaos plan, reconciliation design) is undone. NEEDS WORK.

---

### 3.6 Operational Maturity — BLOCKER

**Citations**

- `docs/01-project-charter.md` §4 (milestones — runbooks expected at M12); §5 RACI ("Runbooks + on-call rotation" — accountable PM, responsible SD); §8.4 SLOs (arch).
- `architecture/01-system-architecture.md` §6 (observability: OTEL + Honeycomb + Prometheus + Grafana), §9.

**Findings**

1. **No runbooks exist.** Charter RACI assigns runbook responsibility to SD with PM accountable. Repo `docs/` contains the charter and nothing else. Pre-launch needs runbooks for: CAQH outage; per-state scraper degradation (50× — at minimum a template + filled-in for top 10); NPDB mTLS cert rotation; DocuSign webhook reconciler; identity-vendor outage; audit ledger chain-break (worst case); committee quorum loss mid-meeting; outbox/Debezium lag; Kafka DLQ redrive; KMS key rotation; cross-region failover.
2. **No on-call rotation specified.** Who pages whom at 3am when CAQH is degraded? Not in the repo. The charter §9 escalation path covers project-management escalation, not operational pager.
3. **No SLI/SLO dashboards.** Arch §8.4 specifies SLOs as targets; the corresponding SLIs, dashboards, and alert thresholds are not specified. "Error budget burn alert: 2% over 1 h" is a sentence, not an alert.
4. **PHI-redacted observability not validated.** Charter §2.1 forbids PHI in third-party telemetry; arch §6 sends OTEL traces to Honeycomb. No proof that Honeycomb has BAA coverage (`compliance/01-compliance-checklist.md` §1.3.6); no proof that the redaction processor scrubs every PHI-bearing field; no automated test enforcing it.
5. **No DR exercise plan.** Temporal Cloud + RDS Multi-AZ + cross-region (us-east-1, us-west-2) is described (arch §9); no DR runbook, no RTO/RPO commitment (`compliance/01-compliance-checklist.md` Control 1.2.14 marked PARTIAL).
6. **No hypercare plan beyond the milestone name.** Charter M12 says "30-day hypercare plan"; no plan exists.
7. **No training records.** Charter §8.5 says workforce training records are archived; M11 dress rehearsal trains committee. No curriculum, no attestation tracking (`compliance/01-compliance-checklist.md` Control 1.2.13).
8. **No incident classification policy.** What's a P0? A P1? Charter §9.3 says "Privacy/security incidents -> Privacy Officer + CISO (within 60 minutes)" but does not define what reaches that bar.
9. **No change-management policy** for production. Who approves a deploy? What gates a hotfix? Charter §6.5 mentions release notes; CHANGELOG.md is not in the repo.
10. **No vulnerability management or patch SLA** (`compliance/01-compliance-checklist.md` §5.3.9 marked NO).

**Verdict basis:** Every operational artifact that day-2 production requires is missing. The project is pre-operational. BLOCKER.

---

## 4. Top 10 Blockers (Ordered by Severity)

Severity = regulatory exposure × probability × time-to-remediate.

| # | Title | Dimension | Severity | Owner |
|---|---|---|---|---|
| 1 | NPDB write integration (HCQIA adverse-action reporting) is missing | Audit defensibility | blocker | Senior Developer + Evidence Collector |
| 2 | Data model in arch §3.1 omits email, phone, address, malpractice history, education, work history, DEA — all collected by UI | HIPAA compliance | blocker | Senior Developer + Evidence Collector |
| 3 | Credentialing Committee Charter referenced but not authored; quorum rule cites a phantom document | Audit defensibility | blocker | Project Manager + Medical Director |
| 4 | HIPAA individual-rights flows (164.524 access, 164.526 amendment, 164.528 accounting) missing from provider portal | HIPAA compliance | blocker | UI Designer + Senior Developer + Evidence Collector |
| 5 | Appeal / fair-hearing process (NCQA CR 6) missing from UI and workflow | Audit defensibility | blocker | UI Designer + Senior Developer + Evidence Collector |
| 6 | Board certification PSV and DEA verification adapters do not exist; UI marks them as optional uploads | Audit defensibility | blocker | Senior Developer + Evidence Collector |
| 7 | Breach notification readiness absent (IR plan, 4-factor assessment, HHS workflow, templates, cyber insurance evidence) | HIPAA compliance | blocker | Privacy Officer + CISO + Evidence Collector |
| 8 | No vendor BAA evidence files (`compliance/baas/` empty); Honeycomb / Twilio / Confluent BAA status unconfirmed; PHI flows to telemetry undefended | HIPAA compliance | blocker | Evidence Collector + Procurement |
| 9 | No runbooks, no on-call rotation, no SLO dashboards, no DR exercise, no chaos/soak test plan | Operational maturity | blocker | Senior Developer + Platform Lead |
| 10 | Per-state regulatory overlay (CA Knox-Keene 60d, NY DOH 90d, CA SB 137, TX SB 1264, CA 805 reports) entirely unmodeled in SLA tracker and workflow | Audit defensibility | blocker | Evidence Collector + Legal + Senior Developer |

**Just below the top 10** (still must-fix; either high-severity but easier to remediate, or high-effort but slightly less immediately exposing):

- Ongoing monitoring (NCQA CR 5) — monthly LEIE re-runs against active providers, NPDB Continuous Query, state-license action subscriptions.
- Field-encryption boundary inconsistency for NPI / CAQH ID / license number; ADR needed.
- Canonical-JSON spec not pinned (JCS RFC 8785); hash-chain prev-fetch concurrency is a placeholder; needs_info decisions are unsigned.
- Workflow activities are all `NotImplementedError`; no service code exists.
- No load-test plan; no capacity model at 10x.
- Document-retention conflict (charter 10y vs arch lifecycle 7y; retention-from-termination not addressed).
- PHI redaction in logs has no CI test design.
- Session timeout policy not pinned; UI shows 27:14 without ADR.
- Cookie / tracking-tech consent missing (post-HHS Dec 2022 bulletin exposure).
- Hospital-privileges scope tension between charter §2.2 and NCQA CR.
- UI C6 vote-math typo (small but in an audit-binder screen).

---

## 5. Remediation Plan

Owner abbreviations: PM = SeniorProjectManager, SD = Senior Developer, UI = UI Designer, ET = Experiment Tracker, EC = Evidence Collector, RC = Reality Checker, PO = Privacy Officer, CISO = CISO, MD = Medical Director, Legal = General Counsel.

### 5.1 Phase A — Stop the Bleeding (weeks 1–3 of a re-planned timeline)

| # | Action | Owner role | Exit criteria |
|---|---|---|---|
| A1 | Author the Credentialing Committee Charter document (committee composition, quorum rules, recusal rules, meeting cadence, emergency credentialing, appeal process) | PM + MD + Legal | Document at `docs/03-committee-charter.md`; UI C5 §4.2 citation resolves to a real section |
| A2 | Author the Incident Response Plan (60-min activation criteria, classification, IR team roster, breach 4-factor assessment template, HHS/individual/media notification workflows, templates) | PO + CISO + EC + Legal | `compliance/ir/01-incident-response-plan.md`; `compliance/ir/templates/*.md`; tabletop exercise scheduled |
| A3 | Populate `compliance/baas/` with executed BAA evidence for AWS, CAQH, DocuSign, Jumio, Persona, Twilio, AWS SES, Confluent, Honeycomb (or replace Honeycomb with a BAA-covered tracing backend) | EC + Procurement | One markdown file per vendor with BAA effective date, version, contact, subprocessor flow-down attestation |
| A4 | Fix the data model: add encrypted columns for email, phone, mailing address, DEA, malpractice history entity, education/training entity, work history entity. Update ER diagram. Mark NPI/CAQH ID/license number per resolved ADR | SD + EC | Updated `architecture/01-system-architecture.md` §3.1; ADR-006 (field encryption boundary) accepted; Postgres migrations drafted |
| A5 | Pin canonical-JSON spec (JCS RFC 8785), hash-chain prev-fetch concurrency strategy, and `needs_info` signed-envelope rule | SD + EC | ADR-007, ADR-008 accepted; workflow `_canonical_json` updated to JCS-compliant; `_run_committee` creates an envelope on `needs_info` |
| A6 | Author Privacy Notice (HIPAA NPP) and surface it as versioned, audit-ledger-tracked document in UI P6 line 429 | Legal + EC + UI | `compliance/policies/01-notice-of-privacy-practices.md`; provider acknowledgment writes audit event with NPP version hash |
| A7 | Author per-state regulatory overlay design: enumerated table of CA/NY/TX/FL deadlines + state-specific PSV sources + state adverse-reporting obligations (CA 805, FL Code 15) + SLA tracker hook | EC + Legal + SD | ADR-012 accepted; `compliance/state-overlay.md` with at minimum the top 10 states by provider volume |

### 5.2 Phase B — Build the Missing Subsystems (weeks 4–10)

| # | Action | Owner role | Exit criteria |
|---|---|---|---|
| B1 | Build NPDB write integration (adverse-action reporting). Includes DCN tracking entity, 15-day SLA monitor, evidence archiving | SD + EC | ADR-009 accepted; service deployed in staging; sample report submitted; DCN archived to ledger |
| B2 | Build Board Certification PSV adapter (ABMS Certification Matters API or specialty board APIs as needed) | SD | ADR-010-A accepted; adapter under `verification/adapters/board-cert/`; contract tests green |
| B3 | Build DEA verification adapter (DEA database or state controlled-substance registry per provider state) | SD | ADR-010-B accepted; adapter under `verification/adapters/dea/`; contract tests green |
| B4 | Build Work History verification (direct verification with gap-explanation flow >6mo) | SD + UI | Adapter or workflow step; UI affordance for gap explanation in P5; CR-aligned packet field |
| B5 | Build HIPAA individual-rights flows: download-my-data (164.524), amendment requests (164.526), accounting of disclosures report (164.528) — surfaces in provider portal | UI + SD + EC | New UI screens P9 (data export), P10 (amendment), P11 (disclosure accounting); audit events for every access |
| B6 | Build appeal / fair-hearing UI and workflow per NCQA CR 6 | UI + SD + EC | Provider-portal appeal flow; staff-side hearing case management; documented decision letter elements (reason, appeal rights, fair hearing) |
| B7 | Build ongoing monitoring scheduler: monthly LEIE/Medicare opt-out re-runs against active providers; NPDB Continuous Query enrollment; state-license action subscription | SD + EC | ADR-011 accepted; scheduler deployed; SLA monitor on dashboard D3a |
| B8 | Implement workflow activities in `architecture/02-credentialing-workflow.py` (real adapters, not stubs); register Temporal worker; integrate replay harness | SD | All `raise NotImplementedError` replaced; replay harness fixtures per integration; unit + contract tests green |
| B9 | Implement audit ledger persistence layer with `SELECT … FOR UPDATE` prev-hash fetch; daily Merkle-root job; RFC 3161 timestamping; verify-chain API | SD + EC | Integration test with concurrent writers shows no chain fork; sample daily root etag; verify-chain returns is_chain_intact=true |
| B10 | Implement PHI-redaction logging middleware with CI test enforcement (token catalogue + property-based fuzz) | SD + EC | CI job blocks merges where PHI-shaped tokens (NPI, DOB patterns, email) reach the logging stream |

### 5.3 Phase C — Operationalize (weeks 8–14, overlapping B)

| # | Action | Owner role | Exit criteria |
|---|---|---|---|
| C1 | Author runbooks: CAQH outage, NPDB mTLS rotation, DocuSign reconciler, identity vendor outage, audit ledger chain break, committee quorum loss, outbox/Debezium lag, Kafka DLQ redrive, KMS rotation, cross-region failover. Plus 50 state-board runbook stubs (top 10 fully filled in) | SD + Platform Lead | `docs/runbooks/*.md`; each runbook linked from Grafana alert |
| C2 | Stand up on-call rotation; define paging policy; define incident classification (P0–P3); 24/7 coverage validated | PM + SD + CISO | PagerDuty (or equivalent) configured; rotation published; first-week shadow-page exercise |
| C3 | Build SLO/SLI dashboards in Grafana + Honeycomb (or BAA-covered alternative); alert thresholds tied to error budget burn; PHI-redaction validation as a deploy-blocking test | SD + Platform Lead | Dashboards live; first deploy gated by SLO regression tests |
| C4 | Capacity model + load test plan + soak test plan; document Temporal Cloud sizing, RDS instance class, CAQH token-bucket configuration | SD + Platform Lead | `architecture/capacity-model.md`; 7-day soak test green per QG-4 |
| C5 | DR exercise: simulate cross-region failover (us-east-1 → us-west-2) end-to-end with credentialing workflows in flight; RTO/RPO documented | SD + Platform Lead | DR runbook tested; RTO ≤4h, RPO ≤15m (proposal — to be ratified by leadership) |
| C6 | Author CHANGELOG.md + release-management policy + production change-approval workflow | PM + SD | First production-class release tagged through the new process |
| C7 | Per-state legal allowlist file populated for all 50 states (ADR-005) | Legal + EC | `compliance/state-scraping-allowlist.md` populated; per-state ToS evidence archived |
| C8 | Workforce policies: sanction policy, clearance procedure, training curriculum + cadence, device controls baseline, facility controls | EC + HR + CISO | Policy documents in `compliance/workforce/`; first training round attested |
| C9 | Penetration test (external) covering: provider portal auth, audit ledger tamper attempts, PHI-in-logs, IAM lateral movement, vendor BAA boundaries | CISO + SD | Pen-test report received; critical/high findings remediated; clean re-test |
| C10 | NCQA pre-audit (internal mock against CR 1–7) with sample of 25 randomly selected staged files | EC + PM | Internal audit report; zero critical findings; ≤1 minor finding remediated |

### 5.4 Phase D — Dress Rehearsal and Go-Live Gate (weeks 14–16)

| # | Action | Owner role | Exit criteria |
|---|---|---|---|
| D1 | Process 10 real provider files end-to-end in staging with real committee, real DocuSign, real CAQH (sandbox where available), real NPDB | RC + PM + MD | Per QG-3: zero blocking defects; per QG-1: 100% audit-ledger completeness on sample |
| D2 | 30-day pre-launch run with daily Merkle root, freshness monitors, reconciliation jobs, on-call rotation active in shadow | SD + Platform Lead | 30 consecutive days of green freshness monitors per QG-2; reconciliation 0 drift 14 consecutive days per QG-4 |
| D3 | Go/no-go review by Executive Sponsors, Privacy Officer, Compliance Lead, CISO, Committee Chair | PM + EC + PO + CISO + MD | Signed go/no-go decision in audit ledger; if no, return to Phase B/C |

### 5.5 Realistic Timeline

The charter targets 12 weeks. Honest reading of these gaps suggests a minimum of **20–26 weeks** to a defensible go-live, possibly with a phased rollout (see deployment plan). Pretending otherwise — declaring W12 "production ready" — would be a fantasy approval.

---

## 6. What I Could Not Verify

These items are gaps in the artifacts, not necessarily gaps in intent. I list them so the next-iteration team knows where to produce evidence.

1. **Whether any code has been written outside the workflow skeleton.** No service code, no Terraform, no Postgres migrations, no Temporal worker, no UI implementation, no test results are committed. If they exist elsewhere, they need to be in the repo and reviewed.
2. **Whether Temporal Cloud BAA is actually executed.** ADR-001 §"Follow-up Actions" #1 schedules it for W1 end. No BAA evidence file exists.
3. **Whether CAQH enterprise tier is actually procured at ≥500 req/min.** Charter §2.3 asserts as assumption; no contract evidence.
4. **Whether the 50-state legal allowlist for scraping has been reviewed.** Charter §2.3 asserts; no allowlist file exists.
5. **Whether the credentialing committee exists, is appointed, and has bylaws.** UI implies a 7-member committee with chair; bylaws/charter not authored.
6. **Whether identity-vendor BAA is executed** (Jumio vs Persona). ET-tracked bake-off (ADR-004) pending; both BAAs are stated assumptions.
7. **Whether Honeycomb's BAA tier is in scope.** `compliance/01-compliance-checklist.md` §1.3.6 flags this; no resolution.
8. **Whether Confluent Schema Registry runs on Confluent Cloud (needs BAA) or self-hosted on MSK (under AWS BAA).** Compliance checklist §1.3.5 flags; no resolution.
9. **What the actual NPP content will be.** UI P6 line 429 references PDF; PDF is not authored.
10. **What the production retention schedule per document type looks like.** Charter says ≥10y, arch says 7y to Glacier, retention-from-termination not addressed. No reconciled retention matrix.
11. **What the load test SLA is.** Charter §8 mentions soak test for 7 days for the outbox but no full-system load profile or pass criteria.
12. **What the AI/LLM usage policy is.** Charter forbids PHI in LLM training; permitted internal LLM uses (committee-note assistive autocomplete, etc.) not specified.
13. **Whether the experiments E1–E7 are still valid given the design gaps.** E2 (proactive CAQH lookup before consent) in particular requires Privacy Officer + Legal pre-launch sign-off; impossible to evaluate without those documents existing.
14. **Whether the audit-writer DB role grants will actually pass the separation-of-duties review.** Arch §7.3 asserts; no IaC excerpt; no proof that operators don't have super-user via break-glass.
15. **What the cyber insurance policy actually covers.** Charter §7 R3 says "cyber insurance confirmed"; no policy reference.

---

## 7. Conclusion

This is a thoughtful design with strong primitives (Temporal-based orchestration, hash-chained audit ledger with WORM + RFC 3161 timestamping, per-source bulkhead task queues, transactional outbox pattern) and serious credentialing-domain literacy (NCQA CR alignment, freshness SLAs per sanction source, structured committee voting with quorum and recusal).

It is also a design that, on its own admission via the compliance checklist, has 53 missing controls and 57 partial controls across 143 evaluated. The workflow code is a typed skeleton. There are no runbooks, no executed BAAs in the repo, no IR plan, no pen test, no NCQA pre-audit, no committee charter document, no NPP, no per-state legal allowlist, no DR exercise, no load test, no soak test result, and no record of a single real provider file processed end-to-end.

The charter's W12 go-live target is not achievable without scope reduction. A defensible go-live requires at minimum the Phase A and Phase B work above, plus operationalization (Phase C) and dress rehearsal (Phase D). Realistically 20–26 weeks.

Default verdict, as stated at the outset: **NOT-READY**. This will need re-assessment after the blocker remediation work above is materially complete. Expect 2–3 cycles before conditional-go is plausible.

---

*End of Production Readiness Review v1.0.0*
