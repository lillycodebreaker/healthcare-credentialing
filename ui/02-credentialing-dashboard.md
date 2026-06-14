# Credentialing Staff Dashboard — UI Mockups

**Document ID:** HCPC-UI-002
**Version:** 1.0.0
**Status:** Draft for Implementation
**Owner:** UI Designer
**Last Updated:** 2026-06-13
**Related:** HCPC-CHARTER-001, Milestone M3 (W3)

---

## 0. Design System Notes (applies to all screens)

### 0.1 Color Tokens — Workflow Status Mapping

Credentialing staff scan 100+ files/week. Status colors must be unambiguous at a glance and pass color-blind safety (Deutan/Protan/Tritan tested in addition to WCAG 2.2 AA).

| Status | Token | Hex | Icon | Notes |
|---|---|---|---|---|
| Queued | `--status-queued` | `#6B7280` | clock | Neutral, awaiting auto-pickup |
| Running | `--status-running` | `#1D4ED8` | spinner | Verification in flight |
| Verified | `--status-verified` | `#047857` | check | Auto-verified, no human action |
| Action required | `--status-action` | `#B45309` | flag | Staff intervention needed |
| Failed | `--status-failed` | `#B91C1C` | x | Definitive failure (e.g., sanction hit) |
| On hold | `--status-hold` | `#7C3AED` | pause | Manually paused / awaiting provider |
| Approved | `--status-approved` | `#047857` | shield-check | Committee approved |
| Denied | `--status-denied` | `#7F1D1D` | shield-x | Darker red, distinct from "failed" |

SLA timer color thresholds:
- Green: < 50% of SLA consumed
- Amber: 50–80%
- Red: > 80%

### 0.2 Typography Scale

| Token | Size / Line | Usage |
|---|---|---|
| `--text-display` | 30 / 38 | Dashboard hero number |
| `--text-h1` | 24 / 32 | Page title |
| `--text-h2` | 20 / 28 | Section heading |
| `--text-h3` | 16 / 24 (semibold) | Card title |
| `--text-body` | 14 / 20 | Default — denser than provider portal |
| `--text-table` | 13 / 18 (tabular-nums) | Tables |
| `--text-mono` | 13 / 18 monospace | IDs, hashes, timestamps |

Density mode toggle: "Comfortable" (default) vs "Compact" (-2px row padding). Persisted per user.

### 0.3 Layout

- Three-region shell: left nav (240px collapsible to 64px), top bar (56px), main canvas.
- Main canvas uses 12-col grid, 16px gutter, max-width 1440px.
- Detail views use 8/4 split (main 8 cols, side rail 4 cols).
- Density-aware row heights: 48px comfortable / 36px compact.

### 0.4 Global Accessibility (WCAG 2.2 AA) Defaults

- All tables use real `<table>` + `<th scope>`; sortable columns expose `aria-sort`.
- Filter chips are buttons with `aria-pressed`.
- Bulk-select uses standard checkbox semantics; shift-click range select with keyboard equivalent (Shift+Space).
- Keyboard shortcuts are documented in an in-app `?` overlay and configurable (WCAG 2.2 SC 2.1.4 character key shortcuts — must be remappable or disable-able).
- All timestamps include timezone; user's timezone displayed prominently in top bar.
- Dark mode supported; status colors retested for dark surface contrast.

---

## Screen D1 — Queue View

### Information Architecture Rationale
The queue is the operational heartbeat. Staff need to: (1) see what's overdue *right now*, (2) filter by status/assignee/SLA, (3) take bulk actions (assign, escalate, snooze). Default sort is "SLA risk descending" — the file most in danger of breaching SLA appears first, because amber/red items demand attention more than chronological order. A persistent SLA-at-a-glance strip across the top shows aggregate health.

### Wireframe

```
+--------------------------------------------------------------------------------+
| HCPC  |  Queue   Providers   Calendar   Audit   Reports         Bell  Jane S.  |
+--------+----------------------------------------------------------------------+
|        |                                                                      |
| Queue  |  Credentialing queue                              [ + New file ]     |
| Calend |                                                                      |
| Audit  |  SLA health  ==>   Green 142   Amber 18    Red 4    Total 164        |
| Reports|                                                                      |
| Setting|  Filters: [Status: All v] [Assignee: All v] [Step: All v]            |
|        |           [SLA: All v]  [Sanctions flag: any v]   [Clear] [Save view]|
| ---    |                                                                      |
| Saved  |  Selected: 0    Bulk: [Assign v] [Escalate] [Snooze] [Export CSV]   |
| views  |                                                                      |
|        | +--+--------+-----------------+-------+----------+--------+--------+  |
|  My q. | |[]| File   | Provider        | Step  | SLA      | Owner  | Action |  |
|  Red   | +--+--------+-----------------+-------+----------+--------+--------+  |
|  Today | |[]| A-4711 | Patel, Anita    | S6    | 18d  RED | Jane S | Open > |  |
|  Sancti| |[]| A-4708 | Nguyen, Lan     | S3    | 4d AMBER | Tom R  | Open > |  |
|        | |[]| A-4705 | Adeyemi, Femi   | S4    | 2h GREEN | (auto) | Open > |  |
|        | |[]| A-4699 | Goldberg, Mira  | S6    | 1d GREEN | Jane S | Open > |  |
|        | |[]| A-4691 | Park, Hyo-Jin   | S3    | 9h AMBER | Tom R  | Open > |  |
|        | |[]| A-4684 | Reyes, Maria    | S2    | 22m GRN  | (auto) | Open > |  |
|        | +--+--------+-----------------+-------+----------+--------+--------+  |
|        |                                                                      |
|        |  Showing 1-25 of 164    [ Prev ]  Page 1 of 7   [ Next ]            |
+--------+----------------------------------------------------------------------+
```

### Key Components
- `SlaSummaryStrip` — counts by SLA tier, clickable to filter.
- `FilterBar` — chip-style with overflow menu; saved-view selector.
- `BulkActionBar` — appears when at least one row selected.
- `QueueTable` — sortable columns, multi-select, keyboard nav (j/k or arrows; Enter opens).
- `SidebarSavedViews` — pinned named filters per user.

### State Variations
- **Empty (no queue)**: empty-state illustration + copy "All clear. Nothing in queue." (Rare but possible after-hours.)
- **Empty (filter)**: "No files match these filters. [Reset filters]"
- **Loading**: skeleton rows, never blank.
- **Error (backend)**: persistent banner "Unable to load queue. Last refreshed 2 min ago. [Retry]" — table shows last good cache.
- **Realtime update**: new rows fade in at top; "3 new files" pill appears if user has scrolled past top.
- **Bulk action confirmation**: modal summarizing affected files; for irreversible actions, requires typing "CONFIRM."

### Accessibility Notes
- Sortable columns have `<button>` in header with `aria-sort` ascending/descending/none.
- Bulk select-all checkbox in header has `aria-label="Select all on this page"` and `aria-checked` (mixed for partial).
- Status cells show icon + text + color; SLA timers announce remaining time via `aria-label`.
- Keyboard shortcuts: `?` opens shortcut help; `/` focuses filter; `j/k` row nav; all rebindable.

### Copy Guidance
- "File" not "case" (matches NCQA terminology).
- SLA cells show remaining time relative to deadline ("4d", "22m"), never absolute deadline (avoids timezone confusion in scan-mode).
- Action column verbs are imperative: "Open", "Assign", "Escalate."

---

## Screen D2 — Provider Detail (Verification Results Side-by-Side)

### IA Rationale
The provider detail view is where staff resolve action-required files. Verification evidence from S2 (CAQH), S3 (Licenses), S4 (Sanctions), and S5 (NPI) must be visible *in parallel* — staff frequently cross-reference (e.g., does CAQH license number match the state board?). A four-pane verification panel + a left rail with provider summary + a right rail with actions/timeline is the established mental model for credentialing tools (matches existing operator habit from MD-Staff, symplr).

### Wireframe

```
+----------------------------------------------------------------------------------+
| < Back to queue  Patel, Anita  A-4711   Step 6   18d in step   [ Assign to me ]  |
+----------------------------------------------------------------------------------+
| LEFT RAIL (240)          | MAIN (700)                          | RIGHT (340)     |
+--------------------------+-------------------------------------+-----------------+
| Provider                 | Verifications                       | Timeline        |
|                          |                                     |                 |
| Anita R. Patel, MD       | +---- CAQH (S2) -- Verified ----+   | Today           |
| NPI 1234567890           | | Profile retrieved 6/13 9:43a   |   |  Jane S note    |
| DOB 1985-01-15           | | Last updated 2026-04-02        |   |   "Awaiting NJ  |
| File A-4711              | | [ View profile ]               |   |   board reply"  |
|                          | +--------------------------------+   |                 |
| Stage: S6 Committee      |                                     | 6/13 10:02a     |
| In stage: 18d            | +---- Licenses (S3) -- Verified -+   |  S4 complete    |
| SLA: BREACHED (red)      | | NY  DOH        OK   exp 2027   |   |                 |
|                          | | NJ  Board      OK   exp 2026   |   | 6/13 9:58a      |
| Assignee:  Jane S.       | | FL  Board      OK   exp 2028   |   |  S3 complete    |
|                          | +--------------------------------+   |                 |
| Tags:                    |                                     | 6/13 9:44a      |
|  [Internal med]          | +---- Sanctions (S4) -- Verified+   |  S5 complete    |
|  [Re-cred 2026]          | | OIG LEIE       CLEAR  6/13     |   |                 |
|                          | | SAM.gov        CLEAR  6/13     |   | 6/13 9:43a      |
| Documents (4) [view]     | | NPDB           CLEAR  6/13     |   |  S2 complete    |
| Messages (2) [view]      | | OFAC           CLEAR  6/13     |   |                 |
| Notes (5)     [view]     | | Medicaid (50)  CLEAR  6/13     |   | 6/13 9:41a      |
|                          | +--------------------------------+   |  S1 submitted   |
|                          |                                     |                 |
|                          | +---- NPI (S5) -- Verified ----+    | [ Full history ]|
|                          | | NPPES: Anita R. Patel          |   |                 |
|                          | | Type 1, Active, taxonomy match |   |                 |
|                          | +--------------------------------+   | Actions         |
|                          |                                     | [ Send message ]|
|                          | +---- Committee (S6) -- In prog +   | [ Add note    ] |
|                          | | Scheduled: Jun 23 meeting       |   | [ Request info] |
|                          | | Packet:    [ View / download ]  |   | [ Escalate    ] |
|                          | +--------------------------------+   | [ Place on hold]|
+--------------------------+-------------------------------------+-----------------+
```

### Key Components
- `ProviderSummary` (left rail) — sticky; identity, stage, assignee, tags.
- `VerificationPanel` (main) — five cards (CAQH, Licenses, Sanctions, NPI, Committee). Each card has status header, evidence table, "View full" affordance.
- `Timeline` (right rail) — newest first; mixes system events and human notes.
- `ActionMenu` (right rail) — common actions surfaced; overflow in menu.
- `EvidenceDetailModal` — when "View profile" or per-state license clicked, opens a modal with full payload (JSON + human-readable view), source URL, retrieval timestamp, ledger hash.

### State Variations
- **Pending verification**: card shows blue spinner state + "Checking NY State Board… avg 4 min."
- **Action required** (e.g., license expired): card flips to amber with explicit task + CTA "Request renewal from provider."
- **Failed** (sanction hit): card turns red, locks downstream steps, surfaces "Sanction hit on OIG LEIE 2024-03-12" with full source citation. Top of page shows blocking banner; S7 cannot proceed.
- **Discrepancy** (CAQH name ≠ NPPES name): inline diff highlight with "Resolve discrepancy" action.
- **Stale data**: badge "Last verified 14d ago — [Re-check now]."

### Accessibility Notes
- Verification cards are `<section>` with `aria-labelledby`; status announcements via live region when state changes.
- Sticky left rail does not trap keyboard focus (Skip-to-main link present).
- Evidence modal traps focus per WCAG 2.2; Escape closes and returns focus to trigger.
- Diff highlighting uses both color and an icon (no color-only meaning).

### Copy Guidance
- Always cite the source: "OIG LEIE, retrieved 2026-06-13 10:02 ET, ledger hash a3f9…"
- Use neutral language for sanctions: "Match found" not "Provider is sanctioned" until confirmed.

---

## Screen D3 — Sanctions / Exclusion Alerts Panel

### IA Rationale
A sanction hit is the single most consequential signal in credentialing. Staff need a dedicated, low-noise feed isolated from the general queue. Alerts include both new hits (from S4 runs) and freshness/staleness alerts (per charter R4) so that operators can act on stale-data risk before a provider is approved against incomplete information.

### Wireframe

```
+--------------------------------------------------------------------------------+
| Sanctions & exclusions                                                         |
+--------------------------------------------------------------------------------+
|  New alerts (3)    Recent (12)    Resolved (47)    Source health               |
|                                                                                |
|  Filters: [Severity: All v] [Source: All v] [Provider tag: All v]              |
|                                                                                |
|  +--------------------------------------------------------------------------+ |
|  | HIGH  OIG LEIE match   A-4712  Smith, John D.    Detected 6/13 10:14a    | |
|  | Match score: 0.94                                                        | |
|  | OIG name:     John D. Smith                                              | |
|  | OIG date:     2023-08-14                                                 | |
|  | OIG specialty: Internal medicine                                         | |
|  | Action:       File auto-paused at S6.                                    | |
|  | [ Review match ]  [ Mark false positive ]  [ Confirm exclusion ]         | |
|  +--------------------------------------------------------------------------+ |
|                                                                                |
|  +--------------------------------------------------------------------------+ |
|  | MED   SAM.gov match    A-4691  Park, Hyo-Jin     Detected 6/13 9:55a     | |
|  | Match score: 0.71  (name + DOB)                                          | |
|  | [ Review match ]  [ Mark false positive ]  [ Confirm exclusion ]         | |
|  +--------------------------------------------------------------------------+ |
|                                                                                |
|  +--------------------------------------------------------------------------+ |
|  | INFO  Source staleness  NY Medicaid exclusion list 9d old (SLA: 7d)      | |
|  | All NY-licensed files flagged for re-check after refresh.                | |
|  | [ Trigger refresh ]   [ Snooze 24h ]                                     | |
|  +--------------------------------------------------------------------------+ |
+--------------------------------------------------------------------------------+
```

### Key Components
- `AlertTabs` — New / Recent / Resolved / Source health (matches charter QG-2 + R4).
- `AlertCard` — severity, source, provider, score, evidence summary, action buttons.
- `SourceHealthTab` — separate view showing per-source freshness and last successful sync (see D3a).
- `BulkActions` — multi-select alerts; "snooze," "assign," "escalate."

### State Variations
- **Empty (all clear)**: positive empty state "No active sanction alerts. Last source sync: see Source health." — never a celebratory message (this is regulated work).
- **Source down**: tab badge red; "OIG LEIE has not refreshed for 48 hours."
- **Auto-paused files cascade**: linked banner "12 files at S6 are paused pending alert resolution."
- **High-severity, undisclosed**: alert escalates after 4 hours without action — emails Compliance Officer.

### Accessibility Notes
- Severity uses both color and a textual prefix ("HIGH", "MED", "INFO").
- Match scores use `aria-label="match confidence 0.94 out of 1.0"`.
- Action buttons grouped in `<div role="group" aria-label="Actions for this alert">`.

### Copy Guidance
- "Match found" never "Excluded" until confirmed. Legal liability for premature labeling is real.
- Score is shown alongside evidence so staff don't trust raw numbers blindly.

### Screen D3a — Source Health (sub-tab of D3)

```
| Source           | Freshness SLA  | Last sync           | Status           |
| OIG LEIE         | Monthly        | 2026-06-01 (12d)    | OK (within SLA)  |
| SAM.gov          | Daily          | 2026-06-13 06:00    | OK               |
| NPDB             | Per-query      | n/a                 | OK               |
| OFAC SDN         | Daily          | 2026-06-13 06:02    | OK               |
| NY Medicaid      | Weekly         | 2026-06-04 (9d)     | STALE (SLA 7d)   |
| ... 49 more states ...                                                      |
|                                                                             |
| [ Force resync ] [ Acknowledge stale ] [ Generate compliance report ]       |
```

---

## Screen D4 — License Expiration Calendar

### IA Rationale
Re-credentialing operates on a 36-month cycle (charter §2.1), but state licenses expire on their own schedules. Staff need a forward-looking calendar to plan renewal outreach — 90/30/7-day pre-expiration windows correspond to provider notification cadence (P8). The calendar view is the planning surface; the table view is the action surface.

### Wireframe

```
+--------------------------------------------------------------------------------+
| License expirations                                  [ Calendar ] [ Table ]    |
+--------------------------------------------------------------------------------+
| Date range: [ Jun 2026 v ] - [ Aug 2026 v ]    State: [ All v ]                |
|                                                                                |
|       Mon       Tue       Wed       Thu       Fri       Sat       Sun         |
|     +--------+--------+--------+--------+--------+--------+--------+           |
|     | Jun 16 | Jun 17 | Jun 18 | Jun 19 | Jun 20 | Jun 21 | Jun 22 |           |
|     |        |        |        | 2 lic. |        |        |        |           |
|     |        |        |        | AMBER  |        |        |        |           |
|     +--------+--------+--------+--------+--------+--------+--------+           |
|     | Jun 23 | Jun 24 | Jun 25 | Jun 26 | Jun 27 | Jun 28 | Jun 29 |           |
|     |        | 1 lic. |        |        | 5 lic. |        |        |           |
|     |        | GREEN  |        |        | RED    |        |        |           |
|     +--------+--------+--------+--------+--------+--------+--------+           |
|     | Jun 30 | Jul 1  | Jul 2  | Jul 3  | Jul 4  | Jul 5  | Jul 6  |           |
|     |        | 14 lic |        |        | HOLI   |        |        |           |
|     |        | AMBER  |        |        |        |        |        |           |
|     +--------+--------+--------+--------+--------+--------+--------+           |
|                                                                                |
| Legend:   RED <=7d    AMBER 8-30d    GREEN 31-90d                              |
|                                                                                |
| Today's actions: 5 renewal notices to send  [ Send batch ]                     |
+--------------------------------------------------------------------------------+

When a day cell is selected, side drawer opens:

  Jun 27 (Fri) — 5 licenses expiring
   * Goldberg, Mira     NY MD-554431     90d window expired   [ Send notice ]
   * Park, Hyo-Jin      CA A123456       30d window today     [ Send notice ]
   * Reyes, Maria       FL ME12345       30d window today     [ Send notice ]
   * Nguyen, Lan        NJ 25MA098765    7d window today      [ Send urgent ]
   * Adeyemi, Femi      TX K9876         7d window today      [ Send urgent ]
```

### Key Components
- `Calendar` — month grid with per-day badge for expiration count + severity color.
- `DayDrawer` — opens on day click; lists providers, license details, status of renewal outreach.
- `BatchSendButton` — sends pre-templated 90/30/7-day notices; respects provider notification preferences (P8).
- `ViewToggle` — Calendar / Table.

### State Variations
- **No expirations in range**: "No license expirations in this range — try a wider window."
- **Holidays**: federal/state holidays marked; affects "business days remaining" calculation.
- **Notice already sent**: provider name shown with checkmark + sent timestamp; button changes to "Re-send."
- **Provider unresponsive**: red badge after 14d of no response post-notice; auto-routes to escalation queue.

### Accessibility Notes
- Calendar grid uses `<table>` with `<th scope="col">` for weekdays.
- Each day cell is a `<button>` with `aria-label="Friday June 27, 5 licenses expiring, red severity"`.
- Color is supplemented by count + label.

### Copy Guidance
- "Renewal notice" not "Expiration warning" (action-oriented).
- Always show how many business days remain, not just calendar days.

---

## Screen D5 — Audit Log Viewer

### IA Rationale
The audit ledger is the canonical record for NCQA/CMS/SOC2 audits (charter QG-1). Staff and compliance officers must be able to: (1) inspect any provider's full chronology, (2) filter by actor/action/date, (3) export an auditor-ready PDF or CSV, (4) verify hash chain integrity. The UI must surface immutability — this is not editable data and every entry shows its ledger hash.

### Wireframe

```
+--------------------------------------------------------------------------------+
| Audit log                                          [ Verify chain integrity ]  |
+--------------------------------------------------------------------------------+
| Filters                                                                        |
|   Provider: [ A-4711 Patel, A. v ]   Date: [ 2026-06-13 v ] - [ Today v ]      |
|   Actor:    [ All v ]   Action: [ All v ]   PHI access only: [ ]              |
|   [ Apply ]   [ Reset ]   [ Export CSV ]   [ Export PDF ]                      |
|                                                                                |
| 47 entries shown of 47 matching                                                |
|                                                                                |
| +--------------+----------+--------------------+------------------+----------+ |
| | Timestamp    | Actor    | Action             | Resource         | Hash    | |
| +--------------+----------+--------------------+------------------+----------+ |
| | 6/13 10:14a  | system   | SANCTION_MATCH     | A-4712 / OIG     | a3f9... | |
| | 6/13 10:02a  | system   | S4_COMPLETE        | A-4711           | b7c1... | |
| | 6/13 9:58a   | system   | S3_COMPLETE        | A-4711           | 88de... | |
| | 6/13 9:55a   | jane.s   | NOTE_ADDED         | A-4711           | 4421... | |
| | 6/13 9:54a   | jane.s   | PHI_VIEW           | A-4711           | f1a0... | |
| | 6/13 9:43a   | system   | S2_COMPLETE        | A-4711           | 0c8e... | |
| | 6/13 9:41a   | provider | APPLICATION_SUBMIT | A-4711           | 11ef... | |
| +--------------+----------+--------------------+------------------+----------+ |
|                                                                                |
| Chain integrity: VERIFIED 6/13 10:15a   Block height: 18,447                   |
+--------------------------------------------------------------------------------+

Selecting an entry expands a detail drawer:

  6/13 10:02a   S4_COMPLETE   A-4711   hash b7c1...
   Actor:        system (verification-worker-prod-04)
   Correlation:  corr-2026-06-13-09414a
   Before hash:  88de2c91...
   After hash:   b7c1f032...
   Payload diff: [view JSON]   Source citation: [view]
   Ledger position: 18,442   WORM-locked: YES
```

### Key Components
- `LogFilters` — provider, date range, actor, action type, PHI filter.
- `LogTable` — chronological, monospaced timestamps and hashes.
- `ChainIntegrityBanner` — shows last verification time and block height; runs verification on demand.
- `EntryDetailDrawer` — shows full before/after, payload diff, ledger position, WORM status.
- `ExportControls` — CSV (raw), PDF (auditor-formatted with cover sheet and chain proof).

### State Variations
- **Chain integrity check in progress**: spinner with progress ("verifying block 14,201 of 18,447").
- **Chain integrity FAILED**: red banner with explicit escalation path ("Contact Compliance Officer immediately. Do not proceed with affected files.") — this triggers IR plan per charter §9.3.
- **No matching entries**: empty state with hint ("Try widening date range or removing filters").
- **PHI view access**: confirmation modal "This will create an audit entry for your PHI access. Continue?" — meeting HIPAA minimum-necessary principle.

### Accessibility Notes
- Hash column wraps responsibly; full hash on hover/click.
- Each row is keyboard-navigable; Enter opens detail drawer.
- Export buttons announce file size estimate before download.
- Detail drawer focus management: focus enters drawer on open, returns to row on close.

### Copy Guidance
- Action names are UPPER_SNAKE (system-canonical); stable across releases for auditor familiarity.
- Hashes are truncated for display but full value copyable.
- Never use "log entry" — use "ledger entry" (matches charter terminology and signals immutability).

---

## Screen Count Summary (this document)

Credentialing Dashboard screens: **6** (D1, D2, D3, D3a, D4, D5).

---

*End of Credentialing Dashboard mockups.*
