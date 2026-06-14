# ADR-0001: Orchestration Engine for Credentialing Workflow

- **Status:** Accepted
- **Date:** 2026-06-13
- **Deciders:** Senior Developer (A), Platform Lead (C), CISO (C), Privacy Officer (C)
- **Consulted:** SeniorProjectManager, Evidence Collector, Reality Checker
- **Informed:** Executive Sponsors, Credentialing Operations
- **Related:** HCPC-CHARTER-001, HCPC-ARCH-001

---

## Context

The Healthcare Provider Credentialing System executes a seven-step workflow (S1–S7) per provider application. Concrete forces shaping the orchestration choice:

1. **Long-running, human-in-loop.** S6 (committee review) routinely lasts 1–14 days while waiting on quorum, votes, and DocuSign signature collection. The orchestration engine must support durable timers, signals, and queries on a workflow that may sleep for two weeks.
2. **Heavy fan-out with per-step retry semantics.** S3 fans out one activity per state (up to ~25 states for some providers); S4 fans out ~54 sanction sources. Each adapter has distinct retry, backoff, circuit-breaker, and bulkhead requirements (arch doc Section 8.2). We need first-class per-activity retry policies and task-queue isolation.
3. **Deterministic replay for audit.** NCQA, CMS, and SOC2 auditors must be able to reconstruct, byte-for-byte, the decision path of any historical application. The engine must persist a complete history that survives code redeploys.
4. **HIPAA / PHI residency.** All execution data must remain in US-region infrastructure with vendor BAA coverage.
5. **Operational maturity required from day one.** Per the charter (M9, W10), we must demonstrate replay tooling, hypercare runbooks, and >=99.9% reliability before go-live.
6. **Team capability.** The credentialing engineering team is Python-first with some Go experience; the platform team has prior production experience with both Temporal and AWS Step Functions.
7. **Cost envelope.** Volume is modeled at ~12,000 applications/year initial, growing to ~40,000/year by year three. Cost should remain in the low five figures per year for orchestration.
8. **Vendor diversification.** The platform already depends heavily on AWS; an alternative-vendor durable-execution layer is a healthy diversification, particularly for ledger-adjacent workloads.

We need a single primary orchestrator for the credentialing workflow. We are not selecting per-activity job runners (which remain Python/FastAPI workers behind a task queue).

---

## Decision

**Adopt Temporal (Temporal Cloud, US-region) as the orchestration engine for the credentialing workflow.**

Specifically:

- Use Temporal Cloud namespace `credentialing` in `us-east-1`, with a DR namespace replica in `us-west-2`.
- Use the Temporal Python SDK in services that author and run activities.
- Use per-adapter task queues for bulkhead isolation (e.g., `license-ca`, `sanctions-leie`).
- Use Temporal signals for committee state transitions (start review, cast vote, finalize, request info) and Temporal queries for read-side state introspection.
- Set the workflow execution retention to 10 years to satisfy audit retention requirements; redundant evidence still lives in the audit ledger (S3 Object Lock) so Temporal retention is a convenience, not the legal record.

---

## Alternatives Considered

### Alternative A — AWS Step Functions (Standard Workflows)

**Pros**
- Native AWS service; same VPC, IAM, KMS, CloudWatch stack we already use.
- No additional vendor BAA — covered under existing AWS BAA.
- Pay-per-state-transition pricing is attractive at our volume.
- Good fan-out via Map states; integrates cleanly with Lambda and ECS.
- Well-understood operational story for the platform team.

**Cons**
- 1-year maximum execution duration is fine for credentialing, BUT the *25,000 events per execution* hard limit is uncomfortably close. A worst-case re-credential workflow with 25 license states + 54 sanction sources + heavy retries can approach this; we would need to redesign as nested workflows, complicating audit replay.
- Human-in-loop is via callbacks (`waitForTaskToken`), workable but ergonomically poor compared to Temporal signals — particularly for the multi-vote committee state machine.
- No deterministic local replay; investigating a year-old decision means reading CloudWatch and ASL together, not stepping through code.
- ASL (Amazon States Language) is JSON; complex credentialing logic ends up in Lambda anyway, with state-machine logic split awkwardly between ASL and code.
- Per-activity retry policy granularity is weaker than Temporal's (especially `non_retryable_error_types`).

**Why rejected:** Event limit risk and weak human-in-loop ergonomics for the committee step. The 14-day committee step plus ~80 verification fan-out activities plus retries is a regime where Temporal's mental model fits noticeably better.

### Alternative B — Apache Airflow (managed via MWAA)

**Pros**
- Open ecosystem; many operators.
- Familiar to data engineers.

**Cons**
- Designed for batch DAGs on a schedule, not per-request long-lived workflows.
- Per-application instance would create thousands of DAG runs; UI and scheduler are not designed for this access pattern.
- Human-in-loop is not a first-class concept.
- No durable signal/query primitives.

**Why rejected:** Wrong tool for transactional, per-application, human-in-loop workflows.

### Alternative C — Camunda 8 (Zeebe) / Cloud

**Pros**
- Strong BPMN modelling; appealing for committee workflow visualization.
- First-class human-task support.
- US-region hosted option available.

**Cons**
- BPMN-first approach pulls business logic into XML/BPMN models that diverge from code; harder to version-control and unit-test deterministically.
- Smaller Python SDK maturity than Temporal.
- BAA story less mature for HIPAA than Temporal Cloud or AWS.
- Adds an additional vendor to the security review pipeline at a moment when timeline is fixed.

**Why rejected:** Worse fit for code-first engineering culture; BAA maturity concern; vendor onboarding cost in a fixed-budget project.

### Alternative D — Build it ourselves (Postgres-backed state machine + Celery/RQ workers)

**Pros**
- No vendor lock-in.
- Cheap to operate at small scale.

**Cons**
- Reinventing durable execution, retries, timers, signals, history retention.
- Engineering team burns months on infrastructure instead of credentialing features.
- Auditability and deterministic replay would have to be built from scratch — this is *the* critical-path requirement for NCQA/CMS.
- High operational risk for a regulated workload.

**Why rejected:** Build cost exceeds Temporal Cloud cost by an order of magnitude over three years, and the operational risk is unacceptable for a HIPAA-regulated, audit-critical workload.

### Alternative E — Temporal self-hosted (on EKS)

**Pros**
- Same engine semantics as Temporal Cloud.
- No vendor BAA needed (we host).
- Lower per-action cost at high volume.

**Cons**
- Operating Temporal at production grade requires running Cassandra or PostgreSQL backends with careful tuning, dedicated SRE capacity, regular history-archival, and a 24/7 on-call rotation we do not have to spare in the 12-week window.
- Adds a new persistence tier to threat-model and patch.
- Defers go-live; charter does not permit.

**Why rejected for v1:** Cost of operations exceeds Temporal Cloud cost at our forecast volume through year three; revisit in year four if growth exceeds projection.

---

## Decision Drivers Scorecard

| Criterion (weight) | Temporal Cloud | Step Functions | Airflow | Camunda 8 | DIY | Temporal self-host |
|---|---|---|---|---|---|---|
| Human-in-loop ergonomics (high) | 5 | 3 | 1 | 5 | 2 | 5 |
| Deterministic replay for audit (high) | 5 | 3 | 1 | 3 | 1 | 5 |
| Long-running (14-day) workflow fit (high) | 5 | 4 | 1 | 4 | 3 | 5 |
| Fan-out + per-activity retry granularity (high) | 5 | 3 | 2 | 3 | 2 | 5 |
| HIPAA / BAA readiness (high) | 5 | 5 | 4 | 3 | 5 | 5 |
| Operational burden through W12 (high) | 5 | 5 | 3 | 3 | 2 | 2 |
| 3-year cost (medium) | 4 | 5 | 3 | 3 | 5 | 5 |
| Team skill match (medium) | 4 | 5 | 3 | 2 | 3 | 3 |
| Vendor diversification from AWS (low) | 4 | 1 | 2 | 4 | 5 | 5 |
| **Weighted total** | **Highest** | mid | low | low | low | second |

(Scores 1–5; higher is better.)

---

## Consequences

### Positive

- Committee state machine is expressed in idiomatic Python with signals, vastly improving readability and audit traceability.
- Per-activity retry policies (CAQH, NPI, license, sanctions) are first-class and easy to tune as we observe production error rates.
- Deterministic replay gives auditors and engineers a reproducible decision-path forensic tool.
- Bulkhead isolation via per-state, per-source task queues directly addresses risks R1 (CAQH outage) and R2 (state-board brittleness).
- Workflow signals enable the digital-signature step to be modelled as a single durable state machine rather than a chain of webhook callbacks.

### Negative

- Adds a new vendor (Temporal.io) requiring BAA execution and security review (~3 weeks; not on critical path if started by W1).
- Increases per-application infrastructure cost vs. Step Functions at our volume; modelled at ~$0.20/application in year one — acceptable.
- Team must invest 1–2 weeks in Temporal training (mitigated: platform team has prior experience; we will hold a workshop in W1).
- Workflow code must be deterministic (no `random.random()` outside activities, no wall-clock reads outside activities). Mitigation: lint rules and code-review checklist in `architecture/development-standards.md`.

### Follow-up Actions

1. Procurement: execute Temporal Cloud order + BAA by **W1 end**. (Owner: PM)
2. Security review of Temporal Cloud against threat model + data-residency requirements by **W2**. (Owner: CISO + SD)
3. Author `architecture/development-standards.md` covering Temporal determinism rules by **W2**. (Owner: SD)
4. Stand up `credentialing` namespace + DR replica by **W2**. (Owner: Platform Lead)
5. Quarterly cost review against year-one forecast; if growth exceeds 50,000 applications/year, open ADR-XXXX to evaluate self-host migration.
6. Build replay-harness tooling for verification adapters by **W6** (M6). (Owner: SD)

### ADR-Level Risks

- **Temporal.io vendor risk.** Mitigation: workflow code is portable to self-hosted Temporal (same engine, same SDK); migration path is well-trodden. We will keep our deployment within idiomatic, non-Cloud-specific Temporal usage.
- **Determinism-violation production incidents.** Mitigation: linter (`temporal-strict` style) + replay tests in CI on every PR touching workflow code.
- **Skill concentration.** Mitigation: at least three engineers Temporal-certified by W6; on-call runbook includes Temporal-specific troubleshooting.

---

## Compliance Impact

- **HIPAA:** Temporal Cloud BAA must be executed before any PHI flows through workflow history. Workflow payloads containing PHI use envelope encryption with our KMS keys; Temporal stores only ciphertext. Implementation enforced via a Temporal `PayloadCodec` configured at the SDK level (also a determinism-safe layer).
- **NCQA CR / CMS CoP:** Workflow history (10-year retention) supplements but does NOT replace the hash-chained audit ledger. Auditors are told the canonical record is the audit ledger; Temporal history is an operational convenience.
- **SOC 2:** Temporal Cloud is SOC 2 Type II attested; their report is added to the vendor evidence file.
- **Data residency:** Temporal Cloud US-region only; namespace configuration enforced via IaC and verified by quarterly access review.

---

*Status changes will be appended below as the ADR evolves.*
