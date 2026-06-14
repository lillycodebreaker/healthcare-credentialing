# Committee Review Interface — UI Mockups

**Document ID:** HCPC-UI-003
**Version:** 1.0.0
**Status:** Draft for Implementation
**Owner:** UI Designer
**Last Updated:** 2026-06-13
**Related:** HCPC-CHARTER-001 §3 (S6 Committee Review), §8.3 (QG-3), Milestone M3 (W3), M8 (W9), M11 (W11)

---

## 0. Design System Notes (applies to all screens)

### 0.1 Color Tokens — Decision Semantic

Committee decisions are legally consequential. Voting colors are deliberately distinct from general workflow status colors and reused across all committee screens.

| Token | Hex | Usage |
|---|---|---|
| `--vote-approve` | `#15803D` (darker than dashboard verified-green) | Approve vote, approved decision |
| `--vote-deny` | `#991B1B` (darker than dashboard failed-red) | Deny vote, denied decision |
| `--vote-defer` | `#A16207` (warm amber-brown) | Defer vote, deferred decision |
| `--vote-abstain` | `#52525B` | Abstain |
| `--vote-recuse` | `#6D28D9` | Recused (visible as distinct from abstain) |
| `--quorum-met` | `#047857` | Quorum status: met |
| `--quorum-unmet` | `#B45309` | Quorum status: not met |

All decision colors pass WCAG AA against both white and the surface-default color (`#F9FAFB`).

### 0.2 Typography

- Same scale as dashboard (text-h1 24/32, etc.) but committee screens use heavier visual hierarchy because decisions are deliberative — staff want to read carefully.
- Body line-height bumped to 26 (from 20) on summary screens to reduce decision fatigue.
- Decision verbs (Approve / Deny / Defer / Abstain / Recuse) use semibold + corresponding color token.

### 0.3 Layout

- Committee Meeting Dashboard uses an "agenda" metaphor: a vertical list of providers in order of review.
- Provider Summary uses a two-pane split: 60% summary, 40% evidence drawer (resizable).
- Voting interface is a modal-on-rails — irreversible action with required justification text.

### 0.4 Global Accessibility (WCAG 2.2 AA + ballot-specific)

- Vote buttons are large (min 56px height) and never disabled without explanation.
- Required justification textareas have visible label, required marker, and inline character counter announced via `aria-live`.
- Digital signature step provides three equivalent methods (typed, drawn, DocuSign) per WCAG 2.2 SC 2.5.7 (Dragging Movements).
- Quorum and recusal information is announced when it changes.
- All committee sessions are recorded in the audit ledger; UI displays a persistent "Session is being recorded for audit" indicator.

---

## Screen C1 — Committee Meeting Dashboard (Agenda)

### Information Architecture Rationale
A committee meeting can review 5–30 provider files in a single session. The dashboard is built around the meeting metaphor (agenda, attendees, quorum) rather than the individual provider. Order matters: harder cases first while the committee is fresh; recusal-heavy cases batched so recusing members don't churn in and out. The dashboard supports both pre-meeting prep (chair reviews order) and live meeting use (advance through agenda).

### Wireframe

```
+--------------------------------------------------------------------------------+
| HCPC > Committee > Meeting #M-2026-0623           [ Recording ON ]  Dr. Chen   |
+--------------------------------------------------------------------------------+
| Credentialing Committee — June 23, 2026, 4:00pm ET                             |
|                                                                                |
| Attendees (live)             Quorum: 5 of 7 required        STATUS: QUORUM MET |
|  Dr. Chen, Chair       PRESENT                                                 |
|  Dr. Patel, Vice       PRESENT                                                 |
|  Dr. Ahmed             PRESENT                                                 |
|  Dr. Okafor            PRESENT                                                 |
|  Dr. Singh             PRESENT                                                 |
|  Dr. Liu               EXCUSED (proxy: written ballot received)                |
|  Dr. Volkov            ABSENT                                                  |
|                                                                                |
| Agenda — 12 providers up for review                                            |
|                                                                                |
| +----+-----------+--------------------+---------+----------+---------------+   |
| | #  | File      | Provider           | Flags   | Recusals | Status        |   |
| +----+-----------+--------------------+---------+----------+---------------+   |
| | 1  | A-4691    | Park, Hyo-Jin      | --      | --       | UP NEXT >     |   |
| | 2  | A-4699    | Goldberg, Mira     | --      | Dr.Ahmed | Pending       |   |
| | 3  | A-4711    | Patel, Anita       | --      | Dr.Patel | Pending       |   |
| | 4  | A-4684    | Reyes, Maria       | --      | --       | Pending       |   |
| | 5  | A-4708    | Nguyen, Lan        | Disclo  | --       | Pending       |   |
| | 6  | A-4705    | Adeyemi, Femi      | --      | --       | Pending       |   |
| | 7  | A-4720    | Iwasaki, Ken       | Malpr   | --       | Pending       |   |
| | .. |           |                    |         |          |               |   |
| +----+-----------+--------------------+---------+----------+---------------+   |
|                                                                                |
| [ Start meeting ]   [ Reorder agenda ]   [ Pause recording ]   [ Adjourn ]    |
+--------------------------------------------------------------------------------+
```

### Key Components
- `AttendancePanel` — live presence list; PRESENT/EXCUSED/ABSENT; proxy/written-ballot status; updates in real time.
- `QuorumIndicator` — pill showing met/unmet; explains rule on hover ("5 of 7 voting members; chair counts toward quorum").
- `Agenda` — ordered list of files with flags (disclosures, malpractice), recusal list per file.
- `MeetingControls` — start, pause recording, reorder, adjourn.

### State Variations
- **Pre-meeting** (T-30min): "Meeting starts in 28 minutes. 2 attendees joined." Attendance shows joined ones.
- **Quorum not met**: red banner "Quorum not met (4 of 7). Cannot proceed with voting." Chair can still review files in read-only.
- **Recording paused**: amber banner across top "Recording paused — votes during pause are not auditable. Resume to vote." Voting buttons disabled.
- **Mid-meeting attendee leaves**: live alert "Dr. Patel has left — quorum re-checking…" with revised count.
- **Adjourn**: confirmation modal summarizes votes cast, files deferred, next meeting date.

### Accessibility Notes
- Quorum status announced via assertive live region (decision-blocking info).
- Attendance changes announced politely.
- Agenda rows keyboard-navigable; Enter opens provider summary (C2).
- Recording state shown with icon + text + ARIA label; visible from any committee screen.

### Copy Guidance
- "Up next" not "Current" — clarity about order.
- Flags use short codes with tooltip explanations: "Disclo" = disclosed adverse history; "Malpr" = malpractice claim in past 10y.
- Quorum rule shown plainly on hover, not buried in policy doc.

---

## Screen C2 — Side-by-Side Provider Summary with Verification Evidence

### IA Rationale
Committee members are physicians, not credentialing operators — their time is scarce and their cognitive load is high. The summary view distills the four verification streams (CAQH, Licenses, Sanctions, NPI) into a one-screen verdict-ready brief. Evidence is one click away in a drawer; the default view is the synthesis. This satisfies the charter target "Committee meeting prep time per file: <=5 min" (KPI in §1.2).

### Wireframe

```
+----------------------------------------------------------------------------------+
| < Back to agenda    1 of 12: Park, Hyo-Jin (A-4691)         [ Prev ]  [ Next ]   |
+----------------------------------------------------------------------------------+
| SUMMARY (60%)                                  | EVIDENCE (40%)                  |
+------------------------------------------------+---------------------------------+
|                                                | [ Verifications ] [ Documents ] |
| Park, Hyo-Jin, MD                              | [ History ]       [ Notes ]     |
| NPI 9876543210   DOB 1979-11-08                |                                 |
| Specialty: Cardiology                          | CAQH                            |
| Application: Initial credentialing             |  Retrieved 6/13 9:43a           |
|                                                |  Profile signed by provider     |
| Verifications: ALL CLEAR                       |  [ View full profile ]          |
|                                                |                                 |
|   CAQH        Verified   2026-06-13            | Licenses                        |
|   Licenses    3 states, all current            |  NY  MD-554431  exp 2027-07-01  |
|   Sanctions   No matches                       |  CA  A123456    exp 2026-09-30  |
|   NPI         Verified, Type 1                 |  FL  ME12345    exp 2028-03-15  |
|                                                |  [ View certificates ]          |
| Education & training                           |                                 |
|   MD: Johns Hopkins SoM, 2007                  | Sanctions / exclusions          |
|   Residency: Cleveland Clinic, 2010            |  OIG LEIE       CLEAR  6/13     |
|   Fellowship: UCSF Cardiology, 2013            |  SAM.gov        CLEAR  6/13     |
|   Board certified: ABIM Cardiology 2014, 2024  |  NPDB           CLEAR  6/13     |
|                                                |  OFAC           CLEAR  6/13     |
| Work history                                   |  50 state Medicaid  CLEAR       |
|   2013-2018  Stanford Medical Center           |  [ View source citations ]      |
|   2018-now   Park Cardiology Associates        |                                 |
|                                                | NPI                             |
| Malpractice                                    |  NPPES name match    OK         |
|   Carrier: Coverys                             |  Taxonomy match      OK         |
|   Coverage: $1M / $3M                          |  Active status       OK         |
|   Claims (past 10y): 0                         |                                 |
|                                                | History                         |
| Disclosures from provider attestations: NONE   |  6/13 9:41a  Submitted          |
|                                                |  6/13 9:43a  S2 complete        |
| Staff recommendation: APPROVE                  |  6/13 9:58a  S3 complete        |
| Notes from credentialing staff:                |  6/13 10:02a S4 complete        |
| "Clean file. All sources verified within SLA.  |                                 |
|  No discrepancies between CAQH and primary     | [ Open full audit log ]         |
|  sources. Recommend approval."                 |                                 |
|                                                |                                 |
|                              [ Open voting -> ]|                                 |
+------------------------------------------------+---------------------------------+
```

### Key Components
- `ProviderHeader` — name, NPI, DOB, specialty, application type.
- `VerificationSummary` — four-line top-level status, expandable.
- `BiographyBlock` — education, training, work history, malpractice.
- `StaffRecommendation` — explicit APPROVE/DENY/DEFER recommendation with rationale; flagged as "staff opinion, not binding."
- `EvidenceDrawer` (right) — tabbed: Verifications / Documents / History / Notes.
- `VotingCta` — single, prominent button "Open voting →" (only enabled when quorum met and recording active).

### State Variations
- **Recusal applied (current viewer)**: header banner "You are recused from this file. You may view but not vote." Voting button disabled with explanation.
- **Discrepancy detected**: red diff badge inline near affected fields (e.g., "Name on CAQH differs from NPPES").
- **Adverse finding**: explicit red panel "Disclosed malpractice claim 2021 — settled $250K. [View documents]."
- **Missing evidence**: blocked banner "Evidence missing for NJ license. Cannot vote until resolved." with "Send back to staff" action.
- **Recredentialing variant**: shows prior decision date + any changes since last cycle highlighted.

### Accessibility Notes
- Summary and Evidence are independent landmarks (`<section aria-label>`).
- Tab navigation in Evidence drawer follows ARIA Tabs pattern.
- Diff highlights use both color and icon.
- Provider photo, if present, has `alt=""` (decorative — name is the identifier) and is hidden when committee operates in "blinded review" mode (some committees blind demographic info).

### Copy Guidance
- Staff recommendation is labeled clearly: "Staff recommendation (advisory, not binding): APPROVE."
- Never use "candidate" — say "provider" or "applicant."
- Education listed school + year only on summary; full transcripts in Documents tab.

---

## Screen C3 — Voting Interface

### IA Rationale
Voting is the irreversible act. The UI must (1) prevent accidental votes, (2) require justification for every vote (not only denials — even approvals require rationale to satisfy auditor expectations under NCQA CR), (3) capture the vote in the audit ledger immediately, (4) handle recusals/abstentions without ambiguity. A confirm-step is required for Deny and Defer; Approve has a single-step confirm with mandatory justification.

### Wireframe (modal-on-rails — opened from C2 voting CTA)

```
+--------------------------------------------------------------------------------+
| Vote on file: Park, Hyo-Jin (A-4691)                                  [ X ]    |
+--------------------------------------------------------------------------------+
| You are voting as: Dr. Chen, Chair                                             |
|                                                                                |
| Choose one:                                                                    |
|                                                                                |
|   +------------------+   +------------------+   +------------------+           |
|   |    APPROVE       |   |     DENY         |   |     DEFER        |           |
|   |    Recommend     |   |   Reject this    |   |   Send back for  |           |
|   |    network add   |   |   application    |   |   more info      |           |
|   +------------------+   +------------------+   +------------------+           |
|                                                                                |
|   +------------------+   +------------------+                                  |
|   |    ABSTAIN       |   |    RECUSE        |                                  |
|   |    No vote       |   |    Conflict of   |                                  |
|   |                  |   |    interest      |                                  |
|   +------------------+   +------------------+                                  |
|                                                                                |
| Justification *Required (visible in audit ledger, may be reviewed in audits)  |
|                                                                                |
|  +--------------------------------------------------------------------------+ |
|  | Clean file. All primary sources verified. No disclosed adverse history.  | |
|  | Recommend approval for full network privileges.                          | |
|  |                                                                          | |
|  |                                                                          | |
|  +--------------------------------------------------------------------------+ |
|  152 / 2000 characters                                                         |
|                                                                                |
| [ Cancel ]                                              [ Continue to sign -> ]|
+--------------------------------------------------------------------------------+
```

### Key Components
- `VoteSelector` — five tiles; only one selectable; selection sets the form context.
- `Justification` — textarea, required, min 20 chars, max 2000, character counter.
- `ConfirmationChain` — Approve has one confirm step (signature); Deny/Defer have an extra "Are you sure?" intermediate step naming the consequence.
- `CancelGuard` — cancel button confirms loss of unsaved input.

### State Variations
- **Vote not chosen**: "Continue" disabled, helper text "Choose a vote option to continue."
- **Justification too short** (<20 chars): inline error; submit blocked.
- **Recusal selected**: justification placeholder shifts to "Describe the nature of the conflict (e.g., prior practice partnership)"; ledger entry tags as `RECUSAL`.
- **Network failure on submit**: modal stays open, banner "Couldn't record vote. Your selection is saved locally. [Retry]" — never silently lose a vote.
- **Vote already cast (concurrent edit)**: blocking modal "Another vote has been recorded for this file. Refresh to see current state."

### Accessibility Notes
- Vote tiles are `role="radio"` inside a `role="radiogroup"` with `aria-labelledby`.
- Justification has `aria-required="true"` and `aria-describedby` linking to character counter (announced on count milestones, not every keystroke).
- Modal traps focus; Escape triggers cancel guard, not silent close.
- Color is not the only differentiator — each tile has a distinct icon and bold verb.

### Copy Guidance
- Each tile has a one-line consequence ("Recommend network add", "Reject this application"). Voters should never have to guess.
- "Justification" not "Reason" — matches NCQA audit terminology.
- Character counter is informational, not restrictive (only enforce min/max with explicit messages).

---

## Screen C4 — Digital Signature Capture

### IA Rationale
After vote selection (C3), the signature step generates the legal artifact: a DocuSign envelope (primary) plus a DKIM-signed audit envelope (fallback / parallel, per charter QG-3). The UI provides three equivalent signature methods so members on any device or assistive technology can sign without coercion to a specific input modality.

### Wireframe

```
+--------------------------------------------------------------------------------+
| Sign your vote: APPROVE — Park, Hyo-Jin (A-4691)                  [ Back ]     |
+--------------------------------------------------------------------------------+
| Vote summary                                                                   |
|   Voter:          Dr. Chen, Chair                                              |
|   File:           A-4691 (Park, Hyo-Jin)                                       |
|   Vote:           APPROVE                                                      |
|   Meeting:        M-2026-0623, 4:00pm ET                                       |
|   Justification:  "Clean file. All primary sources verified. No disclosed      |
|                    adverse history. Recommend approval for full network        |
|                    privileges."                                                |
|                                                                                |
| Choose your signature method                                                   |
|                                                                                |
|   (o) Type my name as signature                                                |
|   ( ) Draw signature                                                           |
|   ( ) Sign with DocuSign (will open in new window)                             |
|                                                                                |
|   Type your full legal name:                                                   |
|   [ Daniel J. Chen____________________________ ]                               |
|                                                                                |
|   By signing, I attest that:                                                   |
|     - I have reviewed the verification evidence for this file.                 |
|     - I am not recused from this matter.                                       |
|     - My vote and justification accurately reflect my professional judgment.   |
|                                                                                |
| What happens when you sign:                                                    |
|   1. Vote is recorded in the audit ledger (immutable).                         |
|   2. DocuSign envelope is generated and archived.                              |
|   3. DKIM-signed audit envelope is archived alongside DocuSign certificate.    |
|   4. Decision is final once quorum-of-votes is reached.                        |
|                                                                                |
| [ Cancel ]                                                  [ Sign & submit ]  |
+--------------------------------------------------------------------------------+
```

### Key Components
- `VoteSummaryBlock` — read-only recap; reduces signing errors.
- `SignatureMethodRadio` — three options; selection reveals corresponding input.
- `TypedSignature` — must match the voter's name on file (system-known); case-insensitive.
- `DrawnSignature` — canvas; keyboard fallback "Type instead"; clear/redo.
- `DocuSignHandoff` — opens vendor flow in new window with `rel="noopener"`; returns with envelope ID.
- `AttestationBlock` — fixed attestations rendered above signature.

### State Variations
- **Typed name mismatch**: inline error "Name doesn't match our records (Daniel J. Chen)." Allow up to 3 attempts before requiring DocuSign or chair intervention.
- **DocuSign timeout / vendor outage**: amber banner "DocuSign is unavailable. You may use typed signature; envelope will sync when service restores." Falls back to DKIM-signed envelope as primary record.
- **Audit ledger write failure**: blocking error — never report success until ledger writes confirm. Retry with idempotency key.
- **Submitting**: full-modal blocking state "Recording vote and generating signed envelope…" with progress indicators.

### Accessibility Notes
- Canvas signature has keyboard alternative (Tab into "Type instead" link).
- Signature method selection persists across votes within session.
- After submit, focus returns to next agenda item (C2 Next button) — keeps committee moving.
- Success state announces vote recorded with ledger hash for screen-reader confirmation.

### Copy Guidance
- "Sign and submit" is the verb pair — single button, clear consequence.
- Attestation list is short and concrete; no boilerplate legalese.
- Always show what will happen after signing (the four-step list) — reduces anxiety and supports learnability.

---

## Screen C5 — Quorum & Recusal Tracking Panel

### IA Rationale
Quorum and recusals are easy to get wrong manually. The system enforces both rules but must show its work — committees and auditors need to trust the math. This panel is a persistent (collapsible) overlay accessible from any committee screen and is included in the audit packet as a screenshot/PDF export.

### Wireframe

```
+--------------------------------------------------------------------------------+
| Quorum & recusal — Meeting M-2026-0623                                  [ - ]  |
+--------------------------------------------------------------------------------+
| Voting members: 7                                                              |
| Quorum required: 5  (per Credentialing Committee Charter §4.2)                 |
|                                                                                |
| Live attendance                                                                |
|   Dr. Chen      PRESENT  (chair, counts toward quorum)                         |
|   Dr. Patel     PRESENT                                                        |
|   Dr. Ahmed     PRESENT                                                        |
|   Dr. Okafor    PRESENT                                                        |
|   Dr. Singh     PRESENT                                                        |
|   Dr. Liu       EXCUSED  (proxy written ballot received & verified)            |
|   Dr. Volkov    ABSENT                                                         |
|                                                                                |
| Current quorum: 6 of 7  -> QUORUM MET                                          |
|                                                                                |
| Per-file recusals (auto-detected + self-declared)                              |
|                                                                                |
| File     Provider           Recused           Reason                           |
| A-4699   Goldberg, Mira     Dr. Ahmed         Same group practice (auto)       |
| A-4711   Patel, Anita       Dr. Patel         Family member (self-declared)    |
| A-4720   Iwasaki, Ken       Dr. Singh         Prior expert witness (self)      |
|                                                                                |
| Effective quorum per file (after recusals):                                    |
|   A-4699: 5 of 6 voting members present  -> QUORUM MET                         |
|   A-4711: 5 of 6 voting members present  -> QUORUM MET                         |
|   A-4720: 5 of 6 voting members present  -> QUORUM MET                         |
|                                                                                |
| [ Export quorum/recusal report (PDF) ]                                         |
+--------------------------------------------------------------------------------+
```

### Key Components
- `QuorumRuleStatement` — shows configured rule with citation to committee charter.
- `AttendanceList` — same source as C1; redundant by design (visible during voting too).
- `RecusalTable` — auto-detected (from group-practice / employer match) and self-declared.
- `EffectiveQuorumCalculator` — per-file recalculation; reasoning shown.
- `ExportPdf` — auditor-formatted report; matches NCQA template.

### State Variations
- **Quorum lost mid-meeting**: assertive banner "Quorum lost. Voting paused. Resume when 5+ present." Voting buttons disabled across all open windows.
- **Auto-recusal disputed**: each auto-recusal has "Dispute (member is not actually in same group)" affordance; dispute logged + chair must approve override.
- **Self-recusal added mid-meeting**: live update of per-file quorum; system blocks recused member from voting tile (C3 RECUSE pre-selected and locked).

### Accessibility Notes
- Quorum status changes use assertive live region.
- Recusal table has full `<th scope>` semantics and is screen-reader readable.
- Export button announces estimated file size and format.

### Copy Guidance
- Always cite the charter section for the quorum rule — auditors look for this.
- Recusal reasons are concise (max 1 line) — full notes in audit ledger.
- "Auto-detected" vs "Self-declared" distinction is visible and persistent.

---

## Screen C6 — Post-Decision Audit Confirmation

### IA Rationale
Immediately after the final vote on a file (regardless of outcome), the system displays a confirmation screen that summarizes everything that was just recorded. This is the committee's last chance to spot an error in their own action while the vote is still mentally fresh, and it provides operators with the artifacts (ledger hash, envelope ID, decision date) they need for downstream actions (S7 onboarding or denial letter). It is also the screen that ends up screenshotted in audit binders.

### Wireframe

```
+--------------------------------------------------------------------------------+
| Decision recorded: APPROVE — Park, Hyo-Jin (A-4691)                            |
+--------------------------------------------------------------------------------+
|  [ check icon ]   Vote tally for this file                                     |
|                                                                                |
|     Approve:   5    Dr. Chen, Dr. Ahmed, Dr. Okafor, Dr. Singh, Dr. Liu(proxy) |
|     Deny:      0                                                               |
|     Defer:     0                                                               |
|     Abstain:   0                                                               |
|     Recused:   1    Dr. Patel (family member)                                  |
|     Required quorum: 5 voting (after recusal: 6 of 6 voting members voted)     |
|                                                                                |
|  Outcome:   APPROVED                                                           |
|  Effective: 2026-06-23 16:23:08 ET                                             |
|                                                                                |
|  Audit artifacts                                                               |
|     Ledger entries:    6 (one per vote + one decision close)                   |
|     Final block hash:  9c2d3f81a704b2... [copy]                                |
|     DocuSign envelope: dse-2026-06-23-04711a [view]                            |
|     DKIM envelope:     dkim-2026-06-23-04711a [view]                           |
|     Decision packet:   [ Download PDF ]                                        |
|                                                                                |
|  Downstream actions triggered                                                  |
|     S7 onboarding event published to Kafka topic `credentialing.decisions`     |
|     Event ID: evt-2026-06-23-04711a-approved                                   |
|     Consumers notified: HR (ack), EHR (pending), Payer (ack), Directory (ack)  |
|                                                                                |
| [ Next file: Goldberg, Mira -> ]    [ Return to agenda ]    [ Adjourn meeting ]|
+--------------------------------------------------------------------------------+
```

### Key Components
- `VoteTally` — full breakdown with named voters per category (transparency).
- `OutcomeBanner` — large, color-coded outcome statement.
- `AuditArtifactsList` — ledger hash, envelope IDs, decision packet — all copyable / linkable.
- `DownstreamActionTrail` — shows the S7 event publish in real time with consumer ack status.
- `NavigationFooter` — Next file (default), Return to agenda, Adjourn.

### State Variations
- **Decision: DENIED**: outcome banner red; additional panel "Denial letter draft ready for chair review — [Open draft]."
- **Decision: DEFERRED**: amber banner; required field "Information needed from provider before next review" with templated checklist; auto-sends request to provider portal.
- **S7 event publish failure**: visible alert "Downstream notification not yet confirmed. We will retry every 60s for 24h. [View event status]" — never block the committee from advancing.
- **Consumer ack pending**: per-consumer status with timestamp; OK to proceed even if some consumers still pending (charter §7 R7 contingency: outbox pattern handles).
- **Decision retract / correct** (rare): only available within meeting session via chair + 2/3 vote; produces a `DECISION_RETRACTED` ledger entry that does not erase the original (immutable).

### Accessibility Notes
- Outcome banner announces via assertive live region.
- Ledger hash and envelope IDs in monospace with copy-to-clipboard buttons; copy actions announce "copied to clipboard."
- Downstream consumer status updates politely (avoid flooding screen reader).
- Decision packet PDF tagged for accessibility (PDF/UA) and includes bookmarks.

### Copy Guidance
- Show *who* voted what — transparency is core to committee process integrity.
- "Effective" date/time uses both ET and UTC in tooltip.
- Never use the phrase "your decision" — say "the committee's decision" (single-vote screen is C3; this screen is collective).

---

## Screen Count Summary (this document)

Committee Review screens: **6** (C1, C2, C3, C4, C5, C6).

---

*End of Committee Review mockups.*
