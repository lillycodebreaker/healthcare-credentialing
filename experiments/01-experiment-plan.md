# Healthcare Credentialing System — Experiment Plan (v1)

**Document ID:** HCPC-EXP-001
**Version:** 1.0.0
**Status:** Proposed for Compliance + PM Review
**Owner:** Experiment Tracker
**Last Updated:** 2026-06-13
**Related:** HCPC-CHARTER-001, HCPC-ARCH-001, HCPC-UI-001

---

## 0. Purpose and Methodology

This plan defines the initial portfolio of seven controlled experiments to measure
**onboarding efficiency** (time-to-credential, intake conversion, committee throughput)
and **automation accuracy** (verification correctness, sanction-detection recall,
auto-approval safety). Each experiment is hypothesis-driven, statistically powered,
and instrumented with guardrail metrics so we never trade compliance accuracy for
throughput.

### 0.1 Baseline Assumptions (used across power calculations)

| Parameter | Value | Source |
|---|---|---|
| Expected weekly intake (initial applications) | 120 / week | Charter Sec 1.1 + ops history |
| Re-credentialing weekly volume | 60 / week | 36-month cycle on ~9,300 active providers |
| Baseline median cycle time | 95 days | Charter Sec 1.1 |
| Baseline intake-completion (P2 wizard) | 64% | Pre-launch UX research benchmark |
| Baseline committee meeting prep time | 45 min/file | Charter Sec 1.1 |
| Baseline manual-PSV rate | 100% (today) -> target 15% | Charter Sec 1.1 |
| Statistical confidence | 95% (alpha = 0.05, two-tailed) | Standard |
| Statistical power | 80% (beta = 0.20) | Standard |
| Multiple-comparison correction | Holm-Bonferroni on guardrails per family | Standard |

### 0.2 Cross-Cutting Guardrail Metrics (apply to ALL experiments)

- **Sanction-detection recall** (S4): proportion of *known-positive* test injections
  (synthetic providers seeded in shadow traffic) that are flagged. Floor = 100%
  (any miss is a P0 incident; experiment auto-pauses).
- **Audit-ledger completeness**: ratio of state transitions to ledger writes,
  measured per variant. Floor = 100% (per QG-1).
- **PHI leakage events**: count of PHI tokens in logs/telemetry per variant.
  Floor = 0.
- **WCAG 2.2 AA regressions**: automated axe-core score per variant. Floor = no
  new violations vs. control.

These guardrails are **shared** across experiments rather than restated in each
section.

---

## 1. Experiment E1 — Single-Page vs. Multi-Step Application Form (S1 intake)

### Hypothesis
**If** we collapse the five-sub-step intake wizard (P2..P6) into a single
progressively-disclosed page that defers identity capture to the end (single-page
variant with inline section accordions), **then** intake-completion rate will
increase by >=6 absolute percentage points among initial applicants, **because**
reducing perceived friction (no inter-page latency, fewer "Save & continue"
context switches) lowers abandonment in onboarding flows of this complexity.

### Primary Metric and Target Effect Size
- **Primary metric:** Intake-completion rate = `submitted_applications / started_applications`
  within 7 days of `started_at`.
- **Baseline:** 64% completion (P2 multi-step wizard).
- **MDE (Minimum Detectable Effect):** +6 percentage points (relative lift ~9.4%).
- **Rationale:** A 6pp lift on 120 starts/week yields ~7 additional completed
  intakes/week (~360/year), worth roughly $1.8M in expedited network revenue at
  the charter's assumed marginal-provider value.

### Variants
- **Control (A):** P2 wizard exactly as drawn — five named sub-steps, left-rail
  stepper, page navigation between steps.
- **Treatment (B):** Single-page form with the same five sections rendered as
  inline accordions; identity capture (Persona iframe) is the final accordion;
  autosave fires per accordion close; identical field set and validation rules.

Both variants share back-end S1..S5 logic — only the front-end IA differs.

### Guardrails (in addition to cross-cutting)
- Field-level validation-error rate (per submitted intake) — floor = no >20%
  relative increase.
- Identity-verification first-try pass rate — floor = no decrease (deferring
  identity capture must not increase liveness failures).
- Time-to-submit p95 — floor = no >25% regression (large forms can stall older
  devices).

### Sample Size and Duration
- Two-proportion z-test, p1=0.64, p2=0.70, alpha=0.05, power=0.80.
- Required n per arm ~= **1,050 started applications** (rounded up for early-look
  alpha-spending).
- At 120 starts/week and 50/50 random assignment by `application_id` hash:
  **~18 weeks** to power. We instead plan a **6-week** run + **bridge with
  re-credentialing intakes** (which use the same wizard) to reach n in ~7 weeks.

### Stopping Rules
- **Early stop for harm:** if any of (a) intake-completion in treatment < control - 4pp
  with z < -2.5, (b) identity first-try pass rate drops > 5pp, or (c) any guardrail
  trips, auto-pause within 30 minutes via experiment-config flag.
- **Early stop for success:** O'Brien-Fleming boundary at 50% and 75% information
  fractions; ship if z > 2.96 (50%) or z > 2.36 (75%).
- **No early stop on completion rate alone if cycle-time downstream regresses**
  (require both primary + cycle-time direction to align before declaring success).

### Risks and Ethical Considerations
- **Cognitive load on long single page** for accessibility users with screen
  readers — mitigate by ensuring each accordion has its own landmark and is
  collapsible by keyboard; axe-core must score green on both variants.
- **Identity capture moved to end** may increase last-mile drop-off; mitigate by
  showing per-section progress visible at all times so users know they're 90%
  done before camera step.
- **No PHI is varied** — both variants store identical fields.

---

## 2. Experiment E2 — Proactive CAQH Lookup Before vs. After Consent

### Hypothesis
**If** we *proactively* fetch a cached CAQH profile preview immediately after NPI
lookup (S5 prefill) and display it inside the consent screen (P4) so the user can
see what we will retrieve **before** they sign, **then** consent-screen completion
will increase by >=5pp **and** S2 wall-clock latency (perceived) drops by >=60s,
**because** seeing concrete data reduces consent hesitation and the network
fetch overlaps user reading time. The lookup is "preview-only" (no profile is
persisted, no audit event is written) until consent is captured.

### Primary Metric and Target Effect Size
- **Primary metric:** P4 (CAQH consent) screen completion rate
  = `consent_signed / consent_screen_viewed`.
- **Baseline:** 88% (estimated from comparable consent flows).
- **MDE:** +5 pp (88% -> 93%).
- **Secondary metric:** Median user-perceived time from P4 entry to seeing
  retrieved CAQH data on P7 status tracker — target reduction from ~5 min to <30 s.

### Variants
- **Control (A):** Today's flow — user signs CAQH authorization, system fires
  `/v1/applications/{id}/verifications/CAQH` *after* signature; data appears on
  P7.
- **Treatment (B):** On entry to P4, system issues a *preview* CAQH call (no
  persistence) keyed by NPI + DOB; the consent box shows a card with retrieved
  name/taxonomy/work history fields ("This is what we will save once you
  authorize"); upon signature, the preview is promoted to persistent verification
  result.

### Guardrails
- **PHI handling:** preview must NOT be written to `verification_result` table,
  audit ledger, or any persistent store until consent timestamp. Implementation
  reviewed by Privacy Officer before launch. Floor = 0 pre-consent writes.
- **CAQH rate-limit budget:** preview calls must consume <15% additional
  request-budget at peak (per R1 mitigation; token-bucket monitored live).
- **Consent withdrawal rate:** if more users withdraw *after* seeing preview,
  treatment fails on this guardrail.

### Sample Size and Duration
- Two-proportion z-test, p1=0.88, p2=0.93, alpha=0.05, power=0.80.
- Required n per arm ~= **560 consent-screen views**.
- At ~95 consent-screen views/week (76% of starts reach P4), 50/50 split:
  **~12 weeks**. Accelerate to ~8 weeks by adding re-credentialing applicants
  (who also see P4) to the eligible pool.

### Stopping Rules
- **Early stop for harm:** any pre-consent persistence event found in audit
  tooling -> immediate stop + Privacy Officer notification (incident-class).
- **Early stop for harm:** CAQH 429 rate > baseline by >3 standard deviations
  -> rollback within 15 minutes.
- **Early stop for success:** O'Brien-Fleming at 50% / 75%.

### Risks and Ethical Considerations
- **Legal risk:** preview must be characterized in Legal review as a permitted
  "transitory technical retrieval" under the user's already-granted intake
  consent (T&C on P1). Privacy Officer + General Counsel sign-off required
  before launch.
- **PHI exposure window:** even transitory retrieval increases blast radius if
  the preview cache is compromised; mitigate with in-memory-only (no Redis,
  no log) preview path.
- **Consent quality risk:** showing data may bias users toward signing without
  reading. Mitigate by keeping the legal text equally prominent and tracking
  scroll-depth on the consent block as a secondary metric.

---

## 3. Experiment E3 — Committee Review: Batch-Mode UI vs. Individual-Mode UI (S6)

### Hypothesis
**If** committee members review files in a **batch-mode** console (queue view
with bulk-status pre-screening and side-by-side packets) instead of the
individual one-file-at-a-time review pages, **then** median committee meeting
prep time drops from 45 min/file toward the <=5 min/file charter target while
quorum-vote correctness (no spurious approvals) stays flat, **because**
information foraging across similar low-risk files benefits from comparison and
batch context.

### Primary Metric and Target Effect Size
- **Primary metric:** Median committee prep time per file (measured as time from
  committee member opening a packet to casting a vote, excluding "needs_info"
  branches).
- **Baseline:** 45 min/file (Charter Sec 1.1).
- **MDE:** Reduce to 20 min/file (median); target trajectory toward 5 min/file
  long-term but a single experiment cycle aims for halving plus margin.
- **Rationale:** 25 min/file saved x ~120 files/cycle x 26 cycles/yr = ~13,000
  reviewer-hours/yr recovered.

### Variants
- **Control (A):** Today's committee console (single-file review page,
  next/prev nav) as described in HCPC-ARCH-001 Sec 2.
- **Treatment (B):** Batch console — left rail with all files on agenda
  pre-scored by risk band (low / medium / high based on completed
  verifications); right pane shows three packets stacked vertically for the
  active risk band; voting is per-file but adjacency enables comparison.

### Guardrails
- **Vote-correctness audit:** randomly sample 5% of votes from each variant for
  blinded re-review by a second committee member; require >=99% concordance.
- **Quorum-rule violations:** must be zero in both variants (quorum logic is
  shared, not varied).
- **Time-per-vote standard deviation:** must not increase >50% (we want faster,
  not chaotic).
- **Recusal handling correctness:** 100% in both variants (recusal logic is
  shared).

### Sample Size and Duration
- Mann-Whitney U test on time-per-file (non-normal distribution).
- Effect size d ~= 0.45 (medium), alpha=0.05, power=0.80.
- Required n per arm ~= **150 file-reviews**.
- At ~120 committee files/cycle and 2 cycles/month: **~6 weeks** total runtime
  with within-committee randomization (each member sees both variants on
  alternating cycles, with washout) to control for member-level variance.

### Stopping Rules
- **Early stop for harm:** vote-concordance audit < 97% triggers stop +
  full-file re-review of treatment-arm decisions.
- **Early stop for harm:** any post-decision reversal attributable to UI-induced
  oversight in treatment -> stop.
- **Early stop for success:** if median time drops below 15 min and concordance
  stays >=99% at midpoint, request stakeholder sign-off to ship early.

### Risks and Ethical Considerations
- **Cognitive risk of batch comparison:** committee members may anchor on the
  first file in a batch and under-scrutinize subsequent ones. Mitigate by
  randomizing order within risk band and surfacing per-file "fresh-eyes" prompts.
- **Cannot batch high-risk files:** any file with `risk_band = high` (e.g.,
  prior sanction history, active malpractice claim) is routed to the
  individual-mode review path regardless of variant. Hard-coded; not subject
  to randomization.
- **Auditor optics:** external auditors may interpret batching as a reduction
  in care. Document the methodology in the audit ledger (annotation per
  decision: "reviewed in batch mode v1") so auditors can trace.

---

## 4. Experiment E4 — Auto-Approve Threshold for Low-Risk Providers (S6)

### Hypothesis
**If** we auto-approve recredentialing files (not initial credentials) where
ALL of the following are true: (a) all S3..S5 results are `passed` with green
freshness, (b) no sanction hits across any source, (c) no malpractice
disclosures in the attestation step, (d) no license expiring within 12 months,
(e) provider has >=2 prior clean credentialing cycles, **and** we route them
through a human-in-the-loop sampling audit where the committee chair must
sign off on a random 20% sample plus 100% of any auto-approval the system
later flags as anomalous, **then** median recredentialing cycle time drops
from 95 days to <=10 days while sanction-detection recall stays at 100% and
zero auto-approvals are later overturned, **because** these files are
deterministically verifiable and the committee's marginal contribution on
them is procedural ratification.

### Primary Metric and Target Effect Size
- **Primary metric:** Median recredentialing cycle time (`submitted_at` ->
  `network_added_at`) for files matching the eligibility predicate.
- **Baseline:** 95 days.
- **MDE:** <=10 days (89% reduction); MDE on the underlying daily distribution
  is 7 days at the 95% CI level.
- **Secondary:** % of recredentialing volume auto-approved (expect 35-45% of
  recreds qualify).

### Variants
- **Control (A):** All recredentialing files go through full committee review
  (current path).
- **Treatment (B):** Eligible files auto-approve via `auto_approval_v1` rule
  engine; a structured `COMMITTEE_DECISION` record is still created (state =
  `approved_auto`, `quorum_required=0`, `motion_text="Auto-approved per rule
  set v1"`), DocuSign + DKIM envelope generated, audit ledger entries written
  identically to human-approved files. 20% of auto-approvals randomly sampled
  for human chair review within 5 business days; chair can reverse the
  decision (which fires `deactivation_requested.v1`).

### Guardrails
- **Sanction-detection recall:** 100% on shadow-injection synthetic providers.
  Auto-approval rule explicitly requires no sanction hits, so this is checked
  at predicate evaluation; recall = recall of S4, not of the rule.
- **Audit-ledger completeness:** every auto-approval must have the same set of
  ledger events as a human approval (verified by automated reconciler).
- **Reversal rate:** floor at 0 reversed auto-approvals (any reversal pauses
  the experiment).
- **Sample-audit concordance:** chair must concur with auto-decision on >=99%
  of the 20% audit sample; if <99%, halt.
- **Equity check:** auto-approval rate must not differ by provider taxonomy or
  state license region by more than 5pp (to avoid encoding bias against
  rural-state providers, etc.).

### Sample Size and Duration
- Mann-Whitney U on cycle-time; expected effect is enormous (months vs days)
  so statistical power is not the binding constraint — **safety sampling**
  is.
- Safety sample target: 200 auto-approvals reviewed by chair (= 20% sample of
  1000 auto-approvals).
- At ~60 recreds/week and ~40% eligibility = 24 auto-approvals/week:
  **~42 weeks** to hit 1000 auto-approvals. We launch in **canary mode** for
  the first 8 weeks (100% chair-sample), then step down to 20% sampling if
  zero discordance.

### Stopping Rules
- **Hard stop on any reversal** of an auto-approval that resulted in a
  sanctioned/excluded provider being added to network. (This is also an
  incident; runs the IR plan.)
- **Hard stop on >1% discordance** in the chair-audit sample.
- **Soft stop on stakeholder request** — Privacy Officer, Compliance Lead,
  or Committee Chair can unilaterally pause for review (no quorum needed).
- **No early stop for success** — must complete the full safety-sample n
  regardless of how strong the speedup signal looks.

### Risks and Ethical Considerations
- **Patient safety:** an auto-approval of an excluded provider is a
  reportable event under NCQA and may trigger CMS sanctions. Mitigations:
  predicate is conservative (passed + no malpractice + 2 prior clean
  cycles), shadow injection of known-bad synthetic providers runs daily,
  chair sample = 20% (well above audit norms).
- **Cannot apply to initial credentials:** no prior clean cycles exist, so
  the predicate fails by construction.
- **Cannot apply to providers with any pending state-board investigation,
  even if sanctions check is clean** — rule explicitly excludes anyone with
  open NPDB queries or recent (<= 18 month) license restoration events.
- **Compliance review required before launch:** Privacy Officer, Compliance
  Lead, Committee Chair, and General Counsel must sign off on the predicate
  in writing. The signed predicate version is stored in the audit ledger and
  any future change requires a new sign-off cycle (auto-approval predicates
  are config-as-evidence).

---

## 5. Experiment E5 — Email-Only vs. Email + SMS Status Notifications

### Hypothesis
**If** we send transactional status notifications via SMS in addition to email
for the events `action_required`, `document_expiration_warning`, and
`committee_decision`, **then** time-to-action on action-required events drops
from a median 18 h to <=6 h, **because** SMS is read within minutes by 90%+ of
users where email is delayed by inbox triage. Marketing and product-news
events remain email-only per opt-in.

### Primary Metric and Target Effect Size
- **Primary metric:** Median time from `action_required_emitted_at` to provider
  performing the required action (document upload, response, etc.).
- **Baseline:** 18 hours (estimated from sector benchmarks; will be measured
  precisely in the first 2 weeks pre-launch as control-only telemetry).
- **MDE:** Reduce to <=6 hours (3x speedup).
- **Secondary:** Reduction in stalled applications (action-required events
  unresolved >48h) — target 40% reduction.

### Variants
- **Control (A):** Email-only for all transactional events (matches default
  notification preferences from P8 with SMS toggled off).
- **Treatment (B):** Email + SMS for the three action-class events listed
  above; respects user-set quiet hours from P8; respects per-user opt-out;
  uses Twilio with TCPA-compliant short codes.

### Guardrails
- **Opt-out rate:** SMS unsubscribe rate must stay <2%; >2% triggers redesign.
- **Complaint rate (carrier-flagged spam):** Twilio complaint rate <0.1%.
- **PHI in SMS body:** zero PHI in SMS text (use generic "Action required on
  your application — open the portal" + portal link). Automated lint test
  on outbound SMS templates pre-launch; runtime PHI scanner samples 100%
  of outbound messages.
- **Cost per resolved action:** must not exceed 1.5x email-only cost or
  benefit doesn't justify ongoing spend.
- **TCPA compliance:** explicit SMS opt-in captured during P8; receipts in
  audit ledger.

### Sample Size and Duration
- Mann-Whitney U on time-to-action; effect size d ~= 0.6 (large).
- Required n per arm ~= **80 action-required events**.
- At ~50 action-required events/week (mixed initial + recreds), 50/50:
  **~3.5 weeks** to power. Plan: **4-week** run with weekly check-ins.

### Stopping Rules
- **Hard stop on any PHI-in-SMS event detected by runtime scanner** ->
  incident-class.
- **Hard stop on opt-out rate >5%** (well above guardrail) or TCPA
  complaint.
- **Early stop for success:** O'Brien-Fleming at 50%/75%; if treatment
  median <8 h with no guardrail trip, ship at 75%.

### Risks and Ethical Considerations
- **TCPA / 10DLC regulatory risk:** explicit opt-in is mandatory; cannot
  randomize users into SMS without opt-in. Randomization is over the *set
  of opted-in users only*; users who haven't opted in stay on email-only
  by definition.
- **Quiet hours respect:** treatment arm must enforce user-set quiet hours
  from P8 — no SMS between 21:00-07:00 local; messages queued for delivery
  at the open of quiet hours.
- **Notification fatigue:** if treatment-arm users opt out at higher rates
  than expected, future experiments cannot use SMS as a channel. Hence the
  conservative 2% guardrail.

---

## 6. Experiment E6 — Identity Verification Vendor Bake-Off (Jumio vs. Persona)

### Hypothesis
**If** we route identity-capture traffic (S1, P3 widget) 50/50 between Jumio
and Persona for 4 weeks, **then** we will identify the vendor with higher
first-try pass rate AND lower median capture time AND no significant
difference in liveness false-negative rate on a controlled gold-set,
**because** vendor performance on real provider demographics differs and
can only be revealed by parallel testing. The outcome drives ADR-004.

### Primary Metric and Target Effect Size
- **Primary metric:** First-try identity-verification pass rate
  (`identity.verified == true` on first webhook).
- **Baseline:** unknown (this experiment establishes it).
- **MDE:** 4 pp difference between vendors (sufficient to make a procurement
  decision).
- **Secondary metrics:** median capture time (P3 widget mount -> webhook
  resolution); cost per successful verification; liveness false-negative
  rate on gold-set; demographic-parity index (pass rate across age/ethnicity
  bands declared in self-ID survey, opt-in).

### Variants
- **Control (A):** Jumio (current incumbent per Charter Sec 2.3 / R6).
- **Treatment (B):** Persona.
- Assignment: hashed `application_id`, 50/50, sticky (a user retries with
  the same vendor on repeat attempts).

### Guardrails
- **PHI handling:** both vendors are BAA-covered (Charter Sec 2.3); BAA
  status verified pre-launch.
- **Demographic-parity gap:** if either vendor's pass-rate gap between the
  highest- and lowest-performing demographic band exceeds 8 pp, escalate
  to Privacy Officer + Legal — potential disparate-impact issue.
- **Manual-review queue growth:** neither vendor may push >20% of attempts
  into the manual queue (R6 contingency exists but shouldn't be the norm).

### Sample Size and Duration
- Two-proportion z-test on first-try pass rate; assume baseline p=0.85
  (industry-typical), MDE 4pp, alpha=0.05, power=0.80.
- Required n per arm ~= **1,400 identity attempts**.
- At ~120 starts/week, ~80% reach identity step = ~96 identity attempts/week.
  50/50 split: **~30 weeks** to power on the primary metric alone.
- **Compress to 6 weeks** by pooling with re-credential identity re-verification
  (every 36 months, ~9300/36/12 = ~22/wk additional) and by accepting an
  interim **descriptive** read-out (no formal decision) at week 6 if the
  effect is >=7pp with z>2.5 — this becomes a **fast-decision lane** in
  ADR-004 v1, with full readout deferred to week 30.

### Stopping Rules
- **Hard stop on either vendor:** if any guardrail is breached on a single
  vendor, that vendor is removed from rotation (100% to the other vendor)
  while the issue is investigated.
- **Early stop for success:** if absolute pass-rate gap exceeds 10pp by week
  4 with z>3.0, declare and ship.

### Risks and Ethical Considerations
- **Cannot randomize liveness-failure handling:** both vendors route failures
  to the same manual-review path (R6 contingency); the failure path is
  shared.
- **Demographic survey is opt-in only;** non-respondents are tracked as
  "declined" and not assigned to any demographic bucket for the parity
  analysis (no inference, no proxies).
- **Vendor lock-in risk:** experiment outcome feeds ADR-004; even if Persona
  wins, contractual exit costs for Jumio must be in the decision matrix.

---

## 7. Experiment E7 — Status Tracker Real-Time Push vs. On-Open Refresh (P7)

### Hypothesis
**If** the application-status tracker (P7) pushes Livewire/WebSocket updates
in real time as verifications complete **instead of** refreshing only on
page load, **then** support-call volume related to "what's happening with my
application" drops by >=25% **and** mean session count per application drops
by >=15%, **because** ambient awareness of progress reduces anxiety-driven
re-checks. (Hypothesized to *also* reduce inbound calls, freeing ops capacity
for exception handling.)

### Primary Metric and Target Effect Size
- **Primary metric:** Inbound status-related calls/chats per 100 active
  applications, weekly.
- **Baseline:** 24 contacts per 100 active apps/week (from current ops dashboard).
- **MDE:** Reduce to 18 / 100 / week (25% reduction).
- **Secondary:** Mean P7-page sessions per application before final decision;
  target 15% reduction.

### Variants
- **Control (A):** P7 refreshes step states only on page load/manual refresh.
- **Treatment (B):** P7 subscribes to a per-application channel; verification
  completions push step updates to the tracker within 5 seconds; respects
  `prefers-reduced-motion` (no animation, just text/icon swap).

### Guardrails
- **Real-time push must not leak PHI** to channels — channel auth enforces
  the application is owned by the authenticated session; security review
  required.
- **WebSocket connection failure rate** <1% (fall back to polling on failure).
- **Server cost:** WebSocket overhead at peak <2x baseline.
- **A11y:** screen-reader users get a `polite` live-region announcement on
  step change, debounced to <=1 announcement per 10 s.

### Sample Size and Duration
- Poisson rate comparison; baseline rate 0.24, MDE 0.06.
- Required n ~= **3,000 application-weeks** per arm.
- At ~120 starts/wk + ~500 active recreds in flight at any time =
  ~620 active applications/week, 50/50: **~5 weeks** to power.

### Stopping Rules
- **Early stop for harm:** any PHI-in-channel finding -> stop within 15 min.
- **Early stop for harm:** WebSocket-related portal availability dips below
  99.9% SLO -> stop.
- **Early stop for success:** Poisson z > 2.96 at 50% information fraction.

### Risks and Ethical Considerations
- **Push must not increase anxiety** (e.g., flapping states from retried
  verifications appearing/disappearing). Treatment debounces transitions
  and never shows "failed" until terminal exception state is reached.
- **Real-time UX must degrade gracefully** on flaky mobile networks (fall
  back to polling).

---

## 8. Experimentation Hygiene

### 8.1 Steps and Behaviors that MUST NOT be A/B Tested

| Step / Behavior | Why It Cannot Be Randomized |
|---|---|
| **S4 — Sanction / exclusion checks** against OIG LEIE, SAM.gov, NPDB, OFAC, all 50 state Medicaid lists | These are **required by federal regulation** (CMS Conditions of Participation, 42 CFR § 422.204) and by NCQA CR standards. Skipping or weakening any source for an experimental arm would expose the organization to regulatory penalties, mandatory reporting, and patient-safety risk. Variants on the *underlying sources or thresholds* are forbidden. (Variants on *UI presentation* of completed sanction results are allowed.) |
| **Audit-ledger writes** (every state transition emits an `AUDIT_EVENT` with hash chain) | Per QG-1 and the immutable-by-design contract (Architecture Sec 7), every state transition in every variant of every experiment MUST write to the ledger. There is no "lite" audit variant. Ledger writes are part of the cross-cutting guardrail family. |
| **PHI encryption at rest and in transit** (AES-256, TLS 1.3) | HIPAA Security Rule technical safeguards. No experimental arm may degrade encryption. |
| **PHI redaction in logs / telemetry** | HIPAA + Charter Sec 1.2.4 ("No PHI in third-party logging, telemetry, or LLM training pipelines"). No experimental arm may bypass redaction middleware. |
| **DocuSign + DKIM dual-signed committee decision envelopes** | Required by QG-3 and the audit-evidence contract. The DKIM duplicate is the tamper-evidence backstop independent of DocuSign; removing it in a variant breaks the audit story. |
| **License-verification source-of-truth selection per state** | Each state's verification source is fixed by the legally-reviewed scraping allowlist (Charter assumption R-section, Architecture Sec 5). UI presentation of license verification results can be varied; the source cannot. |
| **NPDB queries** | NPDB queries are themselves auditable events with mTLS evidence; you cannot randomize who gets an NPDB check. Every initial credential gets one. |
| **Quorum logic, motion/vote/minutes capture, recusal handling** | These are committee-governance requirements bound by the committee charter. UI presentation of the committee console can vary (see E3) but vote-counting math, quorum thresholds, and recusal rules cannot. |
| **Re-credentialing cycle interval (36 months)** | Set by NCQA standard; not negotiable in an experiment. |
| **Identity verification REQUIREMENT** | Both Jumio and Persona arms in E6 do identity verification; you cannot have a "no identity verification" arm. The bake-off is *which* vendor, not *whether*. |
| **WORM-locked storage retention** (>=10 years) | SOC 2 + NCQA + state-board evidence requirement. No "shorter-retention" variant. |
| **Stale-verification block on S7** | The stale-detection logic that prevents S7 from running with any `stale` artifact (R4 mitigation) is a hard safety property, not a UX choice. No "ship anyway" experimental arm. |
| **Auto-approval predicates for initial credentials** | E4 explicitly excludes initial credentials from auto-approval. Auto-approval predicates apply only to re-credentialing with the documented prior-cycle history requirement; no experiment may relax that. |
| **Notification of legally-required events** (committee decision, document-expiration warnings) | Per P8, these are "Required by policy — cannot be disabled." No experimental arm may suppress them. |
| **Cross-vendor BAA coverage** | Every vendor in every arm must have an executed BAA. No "BAA-pending" experimental arm. |

### 8.2 Hygiene Practices that Apply to ALL Experiments

1. **Assignment service is the only source of truth.** A central
   `experiment-config` service returns variant assignments keyed by stable
   IDs (`application_id`, `provider_id`, or `committee_member_id`).
   Hard-coded variant logic in services is forbidden.
2. **Assignments are emitted to the audit ledger** with the experiment ID,
   variant, and version. Auditors can reconstruct which variant any file
   experienced.
3. **Every experiment has a registered metric definition** in the metrics
   catalog before launch; no post-hoc metric invention.
4. **No more than two concurrent experiments on the same surface** (e.g., two
   on P4 simultaneously) to limit interference. Interaction tests required
   when surfaces overlap.
5. **All experiments require Privacy Officer review** if they touch PHI flow.
   E2, E4, E6 in this plan require explicit pre-launch sign-off.
6. **Pre-registered analysis plan** lodged in `experiments/` directory before
   launch; primary metric, MDE, sample size, stopping rules immutable post-launch.
7. **Stop-button is one-click.** Any experiment can be paused by toggling its
   `experiment-config` flag; rollback is the absence of treatment (control
   logic is always live).
8. **Post-experiment readout** is a separate document
   (`experiments/02-readouts/<exp-id>.md`) with results, decision, and
   organizational learning. Negative results are written up the same as
   positive ones.

### 8.3 Calendar Considerations

| Experiment | Earliest Launch | Dependency |
|---|---|---|
| E1 (single vs. multi-step intake) | M4 (W4) | P2 implemented |
| E2 (proactive CAQH lookup) | M5 (W5) | S2 integration live |
| E3 (committee batch vs. individual) | M8 (W9) | S6 workflow live |
| E4 (auto-approve re-creds) | Post-launch + 60 days | Need baseline re-cred volume |
| E5 (email vs. email + SMS) | M9 (W10) | Notification service live; TCPA opt-in flow live |
| E6 (Jumio vs. Persona) | M4 (W4) | S1 identity integration live; both BAAs executed |
| E7 (real-time tracker push) | M5 (W5) | P7 + Livewire infra live |

---

## 9. Approvals Required Before Launch

| Experiment | Privacy Officer | Compliance Lead | Committee Chair | Legal | PM | SD |
|---|---|---|---|---|---|---|
| E1 | I | I | I | I | A | R |
| E2 | **A** | C | I | **C** | A | R |
| E3 | I | C | **A** | I | A | R |
| E4 | **A** | **A** | **A** | **C** | A | R |
| E5 | C | C | I | **C** | A | R |
| E6 | **A** | C | I | C | A | R |
| E7 | C | I | I | I | A | R |

A = Accountable sign-off required, R = Responsible, C = Consulted, I = Informed.

---

*End of Experiment Plan v1.0.0*
