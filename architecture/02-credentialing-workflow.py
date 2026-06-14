"""
Credentialing Workflow — Temporal-style orchestration skeleton.

Document ID: HCPC-WORKFLOW-001
Version:     1.0.0
Status:      Skeleton (M2 baseline)
Owner:       Senior Developer
Related:     HCPC-ARCH-001, ADR-001

Implements the seven-step credentialing pipeline:

    S1 Provider Applies (intake + identity)
    S2 Retrieve CAQH Profile
    S3 Verify Licenses (per state, parallel fan-out)
    S4 Check Sanctions/Exclusions (per source, parallel fan-out)
    S5 Verify NPI and Contracting Eligibility
    S6 Committee Review and Approval (human-in-loop signal-driven)
    S7 Add Provider to Network + Trigger Onboarding Events

Design notes:
- Activities are stubs with realistic signatures, docstrings, and retry policies.
- Idempotency keys are derived as `f"{application_id}:{step}:{attempt}"`.
- Audit events are emitted at every state transition via `emit_audit_event`.
- The committee approval state machine (pending -> in_review -> approved | denied
  | needs_info) is driven by Temporal signals.
- This file is intentionally framework-agnostic in the *imports* it uses; real
  implementation imports `temporalio` and decorates accordingly.  Comments mark
  exactly where each decorator/signal lives.

Run-time framework: Temporal Python SDK (>= 1.7).
"""

from __future__ import annotations

import dataclasses
import enum
import hashlib
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Literal, Optional, Protocol

# ---------------------------------------------------------------------------
# In production these come from the temporalio SDK.  Imported lazily here so
# this skeleton is readable in any environment.
#
#   from temporalio import workflow, activity
#   from temporalio.common import RetryPolicy
#
# Stubs below let the file be type-checked without the SDK installed.
# ---------------------------------------------------------------------------


class _WorkflowStub:
    """Lightweight stand-in for `temporalio.workflow` so the skeleton imports cleanly."""

    @staticmethod
    def defn(cls):  # noqa: D401 - decorator pass-through
        return cls

    @staticmethod
    def run(fn):
        return fn

    @staticmethod
    def signal(fn=None, *, name: Optional[str] = None):
        def _wrap(f):
            f.__temporal_signal__ = name or f.__name__
            return f

        return _wrap if fn is None else _wrap(fn)

    @staticmethod
    def query(fn):
        fn.__temporal_query__ = fn.__name__
        return fn

    @staticmethod
    async def execute_activity(*args, **kwargs):  # pragma: no cover - stub
        raise NotImplementedError("Real Temporal SDK required at runtime.")

    @staticmethod
    async def wait_condition(*args, **kwargs):  # pragma: no cover - stub
        raise NotImplementedError("Real Temporal SDK required at runtime.")


class _ActivityStub:
    @staticmethod
    def defn(fn=None, *, name: Optional[str] = None):
        def _wrap(f):
            f.__temporal_activity__ = name or f.__name__
            return f

        return _wrap if fn is None else _wrap(fn)


workflow = _WorkflowStub()
activity = _ActivityStub()


@dataclasses.dataclass(frozen=True)
class RetryPolicy:
    """Mirror of `temporalio.common.RetryPolicy` for skeleton readability."""

    initial_interval: timedelta = timedelta(seconds=1)
    backoff_coefficient: float = 2.0
    maximum_interval: timedelta = timedelta(minutes=1)
    maximum_attempts: int = 5
    non_retryable_error_types: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# Type definitions
# ---------------------------------------------------------------------------


VerificationSource = Literal[
    "CAQH",
    "NPI",
    "LICENSE",       # actual source string is LICENSE_<ST>, see VerificationResult.source
    "LEIE",
    "SAM",
    "NPDB",
    "OFAC",
    "MEDICAID",      # MEDICAID_<ST>
]


VerificationStatus = Literal["passed", "failed", "exception", "stale"]


CommitteeState = Literal["pending", "in_review", "approved", "denied", "needs_info"]


@dataclasses.dataclass(frozen=True)
class Provider:
    """A clinician applying for, or already in, the network.

    PHI fields are represented here as cleartext for the workflow's in-memory
    use only; persistence layers MUST store these as encrypted envelopes (see
    architecture doc Section 3).
    """

    provider_id: str                 # UUIDv7
    npi: Optional[str]               # 10-digit NPI; may be unknown at intake
    caqh_id: Optional[str]
    full_name: str
    date_of_birth: str               # ISO 8601 date
    primary_taxonomy: Optional[str]
    licensed_states: tuple[str, ...]  # e.g. ("CA", "OR", "WA")


@dataclasses.dataclass(frozen=True)
class IntakePayload:
    application_id: str
    provider: Provider
    submitted_at: datetime
    identity_evidence_id: str        # opaque ref to Jumio/Persona transaction
    document_ids: tuple[str, ...]    # S3-backed
    idempotency_key: str             # client-supplied; checked at AppSvc


@dataclasses.dataclass(frozen=True)
class VerificationResult:
    verification_id: str
    application_id: str
    source: str                       # "CAQH" | "NPI" | "LICENSE_CA" | "LEIE" | ...
    status: VerificationStatus
    evidence_sha256: str              # hash of canonical evidence payload
    fetched_at: datetime
    expires_at: datetime              # used to mark `stale`
    attempt_count: int
    notes: Optional[str] = None


@dataclasses.dataclass(frozen=True)
class CommitteeVote:
    voter_id: str
    vote: Literal["aye", "nay", "abstain", "recuse"]
    comment: Optional[str]
    cast_at: datetime


@dataclasses.dataclass
class CommitteeDecision:
    """State machine: pending -> in_review -> approved | denied | needs_info.

    Mutable because Temporal workflow state evolves through signals.
    """

    decision_id: str
    application_id: str
    committee_id: str
    quorum_required: int
    state: CommitteeState = "pending"
    votes: list[CommitteeVote] = dataclasses.field(default_factory=list)
    motion_text: Optional[str] = None
    rationale: Optional[str] = None
    docusign_envelope_id: Optional[str] = None
    dkim_signature: Optional[str] = None
    decided_at: Optional[datetime] = None

    # --- state-machine guards ----------------------------------------------

    _ALLOWED_TRANSITIONS: dict[CommitteeState, set[CommitteeState]] = dataclasses.field(
        default_factory=lambda: {
            "pending": {"in_review"},
            "in_review": {"approved", "denied", "needs_info"},
            "needs_info": {"in_review"},
            "approved": set(),
            "denied": set(),
        },
        init=False,
        repr=False,
    )

    def transition(self, target: CommitteeState) -> None:
        allowed = self._ALLOWED_TRANSITIONS[self.state]
        if target not in allowed:
            raise ValueError(
                f"Illegal committee transition {self.state} -> {target}; allowed={allowed}"
            )
        self.state = target

    @property
    def quorum_present(self) -> int:
        return sum(1 for v in self.votes if v.vote in ("aye", "nay", "abstain"))

    @property
    def aye_count(self) -> int:
        return sum(1 for v in self.votes if v.vote == "aye")

    @property
    def nay_count(self) -> int:
        return sum(1 for v in self.votes if v.vote == "nay")


@dataclasses.dataclass(frozen=True)
class AuditEvent:
    event_id: str
    application_id: str
    actor_id: str
    actor_type: Literal["provider", "operator", "committee", "system"]
    action: str
    occurred_at: datetime
    correlation_id: str
    before_state_hash: Optional[str]
    after_state_hash: Optional[str]
    prev_event_sha256: Optional[str]
    event_sha256: str


# ---------------------------------------------------------------------------
# Retry policies (per integration; mirrors architecture doc Section 8.2)
# ---------------------------------------------------------------------------


RETRY_CAQH = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(seconds=60),
    maximum_attempts=5,
    non_retryable_error_types=("AuthError", "PermanentlyDeletedProfile"),
)

RETRY_NPI = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(seconds=30),
    maximum_attempts=5,
    non_retryable_error_types=("InvalidNPIFormat",),
)

RETRY_LICENSE_API = RetryPolicy(
    initial_interval=timedelta(seconds=2),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(minutes=5),
    maximum_attempts=8,
    non_retryable_error_types=("UnsupportedState", "LegalAllowlistViolation"),
)

RETRY_SANCTIONS = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(seconds=60),
    maximum_attempts=5,
)

RETRY_DOCUSIGN = RetryPolicy(
    initial_interval=timedelta(seconds=2),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(seconds=60),
    maximum_attempts=5,
    non_retryable_error_types=("EnvelopeRejected",),
)

RETRY_EVENT_EMIT = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(seconds=30),
    maximum_attempts=10,  # outbox + Debezium make this safe to be aggressive
)

RETRY_AUDIT = RetryPolicy(
    initial_interval=timedelta(milliseconds=200),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(seconds=10),
    maximum_attempts=10,  # audit must not be lost
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _idempotency_key(application_id: str, step: str, attempt: int) -> str:
    return f"{application_id}:{step}:{attempt}"


class AuditEmitter(Protocol):
    """Injected at activity layer; defined in architecture doc Section 7.2."""

    async def emit(self, event: AuditEvent) -> None: ...


# ---------------------------------------------------------------------------
# Activity stubs (S1..S7)
#
# Real implementations live in services/credentialing/activities/*.py and are
# registered with the Temporal worker.  Each stub documents:
#   - inputs
#   - outputs
#   - retry policy (selected at workflow.execute_activity time)
#   - external dependency
#   - idempotency considerations
# ---------------------------------------------------------------------------


@activity.defn(name="s1.persist_intake")
async def s1_persist_intake(payload: IntakePayload) -> str:
    """S1 — Persist intake form + identity capture; returns application_id.

    Inputs:
        payload: IntakePayload (PHI; encrypted in storage layer).

    Outputs:
        application_id (UUID string).

    Retry policy:
        RetryPolicy(initial=1s, max=30s, attempts=5). Non-retryable on
        duplicate-idempotency-key (treated as success after fetch).

    Dependencies:
        Application Service -> Postgres + S3 (documents).

    Idempotency:
        On `payload.idempotency_key` conflict, return the prior application_id.
    """

    raise NotImplementedError


@activity.defn(name="s2.retrieve_caqh_profile")
async def s2_retrieve_caqh_profile(
    application_id: str, provider_npi: Optional[str], caqh_id: Optional[str]
) -> VerificationResult:
    """S2 — Retrieve CAQH ProView profile.

    Inputs:
        application_id, provider_npi (optional), caqh_id (optional).

    Outputs:
        VerificationResult with source='CAQH'.

    Retry policy:
        RETRY_CAQH — exp backoff to 60s, 5 attempts, retry on 5xx/429.

    Circuit breaker:
        Opens at 5 consecutive failures or 25% error rate; fallback is the
        manual-lookup runbook (a `MANUAL_REVIEW_QUEUE` Kafka topic).

    Dependencies:
        CAQH ProView OAuth2 client; Redis token-bucket; encrypted profile cache.

    Idempotency:
        Caller passes idempotency key; CAQH adapter dedupes within 24h cache TTL.
    """

    raise NotImplementedError


@activity.defn(name="s3.verify_state_license")
async def s3_verify_state_license(
    application_id: str, provider_id: str, state: str, license_number: Optional[str]
) -> VerificationResult:
    """S3 — Verify a single state license.  Fan-out one activity per state.

    Inputs:
        application_id, provider_id, state ('CA', 'OR', ...), license_number (optional;
        if absent, adapter performs name+DOB lookup).

    Outputs:
        VerificationResult with source=f'LICENSE_{state}'.

    Retry policy:
        RETRY_LICENSE_API — 8 attempts to absorb flaky state portals.

    Fallbacks:
        1. State Board API
        2. Sanctioned scraper (per legal allowlist)
        3. MANUAL_REVIEW_QUEUE entry

    Dependencies:
        Per-state adapter under verification/adapters/state_board/<ST>.py.

    Idempotency:
        Adapter caches successful results by (provider_id, state, license_number)
        for 24h to absorb workflow retries.
    """

    raise NotImplementedError


@activity.defn(name="s4.check_sanction_source")
async def s4_check_sanction_source(
    application_id: str, provider: Provider, source: str
) -> VerificationResult:
    """S4 — Check a single sanction/exclusion source.

    Sources include: LEIE, SAM, NPDB, OFAC, and MEDICAID_<ST> for all 50 states.
    Fan-out: one activity per source (~54 per application).

    Inputs:
        application_id, provider, source (e.g., 'LEIE', 'MEDICAID_NY').

    Outputs:
        VerificationResult with the source's status. A `passed` result means
        provider was NOT found on the exclusion list.

    Retry policy:
        RETRY_SANCTIONS.

    Freshness:
        Each source has a freshness SLA (see arch doc Section 5). If the
        snapshot used is older than 2x SLA, status='stale' and S7 is blocked.

    Dependencies:
        verification/adapters/sanctions/<source>.py.
    """

    raise NotImplementedError


@activity.defn(name="s5.verify_npi")
async def s5_verify_npi(application_id: str, provider: Provider) -> VerificationResult:
    """S5 — Verify NPI via NPPES and confirm contracting eligibility.

    Inputs:
        application_id, provider.

    Outputs:
        VerificationResult with source='NPI'; payload includes taxonomy and
        deactivation reason if any.

    Retry policy:
        RETRY_NPI — 5 attempts, exp backoff to 30s.

    Dependencies:
        NPPES NPI Registry (public REST).  Weekly bulk snapshot is used as
        circuit-breaker fallback.
    """

    raise NotImplementedError


@activity.defn(name="s6.create_committee_packet")
async def s6_create_committee_packet(
    application_id: str, verification_results: list[VerificationResult]
) -> str:
    """S6 — Assemble committee packet (PDF + structured summary).

    Inputs:
        application_id, list of VerificationResult.

    Outputs:
        S3 object key for the assembled packet.

    Retry policy:
        Default (5 attempts, exp backoff to 60s).
    """

    raise NotImplementedError


@activity.defn(name="s6.create_docusign_envelope")
async def s6_create_docusign_envelope(
    application_id: str, decision: CommitteeDecision, packet_s3_key: str
) -> tuple[str, str]:
    """S6 — Create DocuSign envelope; also produce DKIM-signed backup envelope.

    Inputs:
        application_id, decision, packet_s3_key.

    Outputs:
        (docusign_envelope_id, dkim_signature_base64).

    Retry policy:
        RETRY_DOCUSIGN.  Non-retryable: 'EnvelopeRejected'.

    Idempotency:
        DocuSign envelope creation is idempotent on `clientUserId` =
        `f"{application_id}:committee_decision"`.
    """

    raise NotImplementedError


@activity.defn(name="s7.add_provider_to_network")
async def s7_add_provider_to_network(
    application_id: str, provider_id: str, effective_date: str
) -> None:
    """S7 — Mark provider active in network registry; transactional write.

    Inputs:
        application_id, provider_id, effective_date (YYYY-MM-DD).

    Outputs:
        None (idempotent).

    Retry policy:
        Default with 10 attempts (this is the durable "commit").
    """

    raise NotImplementedError


@activity.defn(name="s7.publish_onboarding_event")
async def s7_publish_onboarding_event(
    application_id: str, provider_id: str, effective_date: str
) -> None:
    """S7 — Emit credentialing.provider.onboarding_requested.v1 via outbox.

    Inputs:
        application_id, provider_id, effective_date.

    Outputs:
        None.

    Retry policy:
        RETRY_EVENT_EMIT.

    Notes:
        Writes to `outbox_events` in the SAME transaction as the network-add.
        Debezium ships to Kafka; downstream consumers (HR, EHR, Payer, Directory)
        are responsible for their own idempotency keyed by event_id.
    """

    raise NotImplementedError


@activity.defn(name="audit.emit")
async def emit_audit_event(
    application_id: str,
    actor_id: str,
    actor_type: Literal["provider", "operator", "committee", "system"],
    action: str,
    correlation_id: str,
    before_state: Optional[dict[str, Any]] = None,
    after_state: Optional[dict[str, Any]] = None,
) -> AuditEvent:
    """Append a hash-chained audit event.

    Inputs:
        application_id, actor_id, actor_type, action, correlation_id,
        before_state (optional), after_state (optional).

    Outputs:
        The persisted AuditEvent (with hash chain links populated).

    Retry policy:
        RETRY_AUDIT — aggressive because audit MUST NOT be lost.

    Notes:
        The activity is the *only* writer to the audit_event table; the DB
        role enforces INSERT-only.  Hash chain logic mirrors arch doc Section
        7.2 — pseudo-implementation shown below for the skeleton.
    """

    payload = {
        "application_id": application_id,
        "actor_id": actor_id,
        "actor_type": actor_type,
        "action": action,
        "correlation_id": correlation_id,
        "occurred_at": _utcnow().isoformat(),
        "before_state_hash": _sha256_hex(_canonical_json(before_state or {})),
        "after_state_hash": _sha256_hex(_canonical_json(after_state or {})),
    }
    # In production, fetch prev hash from DB under row lock.
    prev_event_sha256: Optional[str] = None  # placeholder
    event_sha256 = _sha256_hex((prev_event_sha256 or "") + _canonical_json(payload))

    event = AuditEvent(
        event_id=str(uuid.uuid4()),
        application_id=application_id,
        actor_id=actor_id,
        actor_type=actor_type,
        action=action,
        occurred_at=datetime.fromisoformat(payload["occurred_at"]),
        correlation_id=correlation_id,
        before_state_hash=payload["before_state_hash"],
        after_state_hash=payload["after_state_hash"],
        prev_event_sha256=prev_event_sha256,
        event_sha256=event_sha256,
    )
    # Persistence intentionally omitted in skeleton.
    logging.getLogger("audit").info("audit_event_emitted", extra={"event_id": event.event_id})
    return event


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class CredentialingError(Exception):
    """Base class for credentialing workflow errors."""


class VerificationFailed(CredentialingError):
    """A verification source returned `failed`; not retryable at workflow level."""


class StaleEvidence(CredentialingError):
    """At least one verification artifact is past 2x its freshness SLA."""


class CommitteeTimeoutError(CredentialingError):
    """Committee did not decide within the configured SLA."""


# ---------------------------------------------------------------------------
# Workflow definition
# ---------------------------------------------------------------------------


COMMITTEE_DECISION_TIMEOUT = timedelta(days=14)


class CommitteeOutcome(str, enum.Enum):
    APPROVED = "approved"
    DENIED = "denied"
    NEEDS_INFO = "needs_info"


@workflow.defn
class CredentialingWorkflow:
    """Temporal workflow for one provider credentialing application.

    Lifecycle:
        S1 -> S2 -> parallel(S3 fan-out per state, S4 fan-out per source, S5)
                 -> Aggregator gate -> S6 (committee, signal-driven) -> S7.

    Signals:
        start_committee_review()
        cast_committee_vote(vote: CommitteeVote)
        finalize_committee_decision(motion_text: str, rationale: str)
        request_additional_info(reason: str)

    Queries:
        get_state() -> dict  (current workflow + committee state)
    """

    def __init__(self) -> None:
        self.application_id: Optional[str] = None
        self.correlation_id: str = str(uuid.uuid4())
        self.committee: Optional[CommitteeDecision] = None
        self._committee_finalized: bool = False
        self._needs_info_reason: Optional[str] = None

    # --- main entry point ---------------------------------------------------

    @workflow.run
    async def run(self, intake: IntakePayload, committee_id: str, quorum_required: int) -> str:
        """Execute the credentialing workflow.  Returns final outcome string."""

        # S1
        self.application_id = await workflow.execute_activity(
            s1_persist_intake,
            intake,
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=RetryPolicy(maximum_attempts=5),
        )
        await self._audit("system", "system", "s1.intake.persisted", after={"application_id": self.application_id})

        # S2
        caqh = await workflow.execute_activity(
            s2_retrieve_caqh_profile,
            self.application_id,
            intake.provider.npi,
            intake.provider.caqh_id,
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=RETRY_CAQH,
        )
        await self._audit("system", "system", "s2.caqh.retrieved", after={"status": caqh.status})

        # S3, S4, S5 in parallel
        license_results = await self._fan_out_licenses(intake.provider)
        sanction_results = await self._fan_out_sanctions(intake.provider)
        npi_result = await workflow.execute_activity(
            s5_verify_npi,
            self.application_id,
            intake.provider,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RETRY_NPI,
        )

        all_results: list[VerificationResult] = [caqh, npi_result, *license_results, *sanction_results]
        self._guard_no_stale(all_results)
        self._guard_no_hard_fail(all_results)

        await self._audit(
            "system",
            "system",
            "aggregator.passed",
            after={"verification_count": len(all_results)},
        )

        # S6 — committee
        outcome = await self._run_committee(all_results, committee_id, quorum_required, intake)

        if outcome is not CommitteeOutcome.APPROVED:
            await self._audit(
                "committee",
                "committee",
                f"s6.committee.{outcome.value}",
                after={"outcome": outcome.value},
            )
            return outcome.value

        # S7 — network add + onboarding events
        effective_date = _utcnow().date().isoformat()
        await workflow.execute_activity(
            s7_add_provider_to_network,
            self.application_id,
            intake.provider.provider_id,
            effective_date,
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=RetryPolicy(maximum_attempts=10),
        )
        await workflow.execute_activity(
            s7_publish_onboarding_event,
            self.application_id,
            intake.provider.provider_id,
            effective_date,
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=RETRY_EVENT_EMIT,
        )
        await self._audit(
            "system",
            "system",
            "s7.onboarding.requested",
            after={"effective_date": effective_date},
        )
        return CommitteeOutcome.APPROVED.value

    # --- signals ------------------------------------------------------------

    @workflow.signal
    async def start_committee_review(self) -> None:
        if self.committee is None:
            return
        self.committee.transition("in_review")

    @workflow.signal
    async def cast_committee_vote(self, vote: CommitteeVote) -> None:
        if self.committee is None or self.committee.state != "in_review":
            raise ValueError("Cannot vote outside in_review state")
        # de-dupe by voter
        self.committee.votes = [v for v in self.committee.votes if v.voter_id != vote.voter_id]
        self.committee.votes.append(vote)

    @workflow.signal
    async def finalize_committee_decision(self, motion_text: str, rationale: str) -> None:
        if self.committee is None:
            raise ValueError("No committee in flight")
        if self.committee.quorum_present < self.committee.quorum_required:
            raise ValueError("Quorum not met; cannot finalize")
        self.committee.motion_text = motion_text
        self.committee.rationale = rationale
        target: CommitteeState = "approved" if self.committee.aye_count > self.committee.nay_count else "denied"
        self.committee.transition(target)
        self.committee.decided_at = _utcnow()
        self._committee_finalized = True

    @workflow.signal
    async def request_additional_info(self, reason: str) -> None:
        if self.committee is None:
            raise ValueError("No committee in flight")
        self.committee.transition("needs_info")
        self._needs_info_reason = reason
        self._committee_finalized = True  # exits the wait; workflow returns NEEDS_INFO

    # --- queries ------------------------------------------------------------

    @workflow.query
    def get_state(self) -> dict[str, Any]:
        return {
            "application_id": self.application_id,
            "correlation_id": self.correlation_id,
            "committee_state": self.committee.state if self.committee else None,
            "quorum_present": self.committee.quorum_present if self.committee else 0,
            "quorum_required": self.committee.quorum_required if self.committee else 0,
        }

    # --- helpers ------------------------------------------------------------

    async def _fan_out_licenses(self, provider: Provider) -> list[VerificationResult]:
        # In real Temporal, use asyncio.gather over execute_activity calls; for
        # the skeleton we model the loop structure clearly.
        results: list[VerificationResult] = []
        for state in provider.licensed_states:
            result = await workflow.execute_activity(
                s3_verify_state_license,
                self.application_id,
                provider.provider_id,
                state,
                None,
                start_to_close_timeout=timedelta(minutes=30),
                retry_policy=RETRY_LICENSE_API,
                task_queue=f"license-{state.lower()}",  # per-state bulkhead
            )
            results.append(result)
        return results

    async def _fan_out_sanctions(self, provider: Provider) -> list[VerificationResult]:
        sources = self._sanction_sources_for(provider)
        results: list[VerificationResult] = []
        for source in sources:
            result = await workflow.execute_activity(
                s4_check_sanction_source,
                self.application_id,
                provider,
                source,
                start_to_close_timeout=timedelta(minutes=15),
                retry_policy=RETRY_SANCTIONS,
                task_queue=f"sanctions-{source.lower()}",
            )
            results.append(result)
        return results

    @staticmethod
    def _sanction_sources_for(provider: Provider) -> Iterable[str]:
        federal = ("LEIE", "SAM", "NPDB", "OFAC")
        state_medicaid = tuple(f"MEDICAID_{s}" for s in provider.licensed_states)
        return (*federal, *state_medicaid)

    @staticmethod
    def _guard_no_stale(results: list[VerificationResult]) -> None:
        stale = [r for r in results if r.status == "stale"]
        if stale:
            raise StaleEvidence(
                "Stale verification evidence; cannot proceed to committee: "
                + ", ".join(r.source for r in stale)
            )

    @staticmethod
    def _guard_no_hard_fail(results: list[VerificationResult]) -> None:
        hard_fail = [r for r in results if r.status == "failed"]
        if hard_fail:
            # Hard-fail surfaces in the committee packet; workflow continues so
            # the committee can formally deny.  We only RAISE here for sanction
            # hits which are auto-deny.
            if any(r.source.startswith(("LEIE", "SAM", "NPDB", "OFAC", "MEDICAID_")) for r in hard_fail):
                raise VerificationFailed(
                    "Auto-deny: sanction/exclusion match — "
                    + ", ".join(r.source for r in hard_fail)
                )

    async def _run_committee(
        self,
        verifications: list[VerificationResult],
        committee_id: str,
        quorum_required: int,
        intake: IntakePayload,
    ) -> CommitteeOutcome:
        packet_key = await workflow.execute_activity(
            s6_create_committee_packet,
            self.application_id,
            verifications,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=5),
        )
        self.committee = CommitteeDecision(
            decision_id=str(uuid.uuid4()),
            application_id=self.application_id or "",
            committee_id=committee_id,
            quorum_required=quorum_required,
        )
        await self._audit(
            "system",
            "system",
            "s6.committee.packet_ready",
            after={"packet_s3_key": packet_key, "decision_id": self.committee.decision_id},
        )

        # Wait for chair to start review, then for finalization or timeout.
        try:
            await workflow.wait_condition(lambda: self._committee_finalized, timeout=COMMITTEE_DECISION_TIMEOUT)
        except TimeoutError as exc:  # Temporal raises TimeoutError on wait_condition timeout
            raise CommitteeTimeoutError(
                f"Committee did not decide within {COMMITTEE_DECISION_TIMEOUT}"
            ) from exc

        assert self.committee is not None
        if self.committee.state == "needs_info":
            return CommitteeOutcome.NEEDS_INFO

        # Create DocuSign + DKIM evidence only on terminal approve/deny.
        envelope_id, dkim_sig = await workflow.execute_activity(
            s6_create_docusign_envelope,
            self.application_id,
            self.committee,
            packet_key,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RETRY_DOCUSIGN,
        )
        self.committee.docusign_envelope_id = envelope_id
        self.committee.dkim_signature = dkim_sig
        await self._audit(
            "committee",
            "committee",
            f"s6.committee.{self.committee.state}",
            after={
                "decision_id": self.committee.decision_id,
                "outcome": self.committee.state,
                "docusign_envelope_id": envelope_id,
                "aye": self.committee.aye_count,
                "nay": self.committee.nay_count,
            },
        )
        return CommitteeOutcome.APPROVED if self.committee.state == "approved" else CommitteeOutcome.DENIED

    async def _audit(
        self,
        actor_id: str,
        actor_type: Literal["provider", "operator", "committee", "system"],
        action: str,
        after: Optional[dict[str, Any]] = None,
        before: Optional[dict[str, Any]] = None,
    ) -> None:
        await workflow.execute_activity(
            emit_audit_event,
            self.application_id or "unknown",
            actor_id,
            actor_type,
            action,
            self.correlation_id,
            before,
            after,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RETRY_AUDIT,
        )


# ---------------------------------------------------------------------------
# Worker entry point (skeletal)
# ---------------------------------------------------------------------------


async def run_worker() -> None:  # pragma: no cover - skeleton
    """Bootstrap the Temporal worker.

    Real implementation:

        from temporalio.client import Client
        from temporalio.worker import Worker

        client = await Client.connect("temporal.us-east-1.internal:7233", namespace="credentialing")
        worker = Worker(
            client,
            task_queue="credentialing-main",
            workflows=[CredentialingWorkflow],
            activities=[
                s1_persist_intake,
                s2_retrieve_caqh_profile,
                s3_verify_state_license,
                s4_check_sanction_source,
                s5_verify_npi,
                s6_create_committee_packet,
                s6_create_docusign_envelope,
                s7_add_provider_to_network,
                s7_publish_onboarding_event,
                emit_audit_event,
            ],
        )
        await worker.run()
    """

    raise NotImplementedError("Wire up Temporal client + Worker in services/credentialing/worker.py")


if __name__ == "__main__":  # pragma: no cover
    import asyncio

    asyncio.run(run_worker())
