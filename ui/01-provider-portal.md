# Provider Portal — UI Mockups

**Document ID:** HCPC-UI-001
**Version:** 1.0.0
**Status:** Draft for Implementation
**Owner:** UI Designer
**Last Updated:** 2026-06-13
**Related:** HCPC-CHARTER-001, Milestone M3 (W3)

---

## 0. Design System Notes (applies to all screens)

### 0.1 Color Tokens (status / semantic)

| Token | Hex | Usage | Contrast on white |
|---|---|---|---|
| `--color-primary-600` | `#1D4ED8` | Primary actions, focus | 8.59:1 (AA/AAA) |
| `--color-primary-100` | `#DBEAFE` | Selected backgrounds | n/a (bg) |
| `--color-success-600` | `#047857` | Verified, approved | 5.79:1 (AA) |
| `--color-warning-600` | `#B45309` | Pending, action needed | 4.83:1 (AA) |
| `--color-danger-600` | `#B91C1C` | Errors, sanctions | 6.36:1 (AA) |
| `--color-neutral-900` | `#111827` | Body text | 17.7:1 (AAA) |
| `--color-neutral-600` | `#4B5563` | Secondary text | 7.56:1 (AA) |
| `--color-neutral-300` | `#D1D5DB` | Borders | n/a |
| `--color-neutral-50` | `#F9FAFB` | Surface alt | n/a (bg) |
| `--color-info-600` | `#0369A1` | Informational badges | 5.89:1 (AA) |

Status semantic mapping (used across steps):
- **Not started** → neutral-300 outline, neutral-600 text
- **In progress** → primary-600 fill, white text
- **Awaiting you** → warning-600 fill, white text
- **Verified / Approved** → success-600 fill, white text
- **Failed / Action required** → danger-600 fill, white text

### 0.2 Typography Scale

| Token | Size / Line | Usage |
|---|---|---|
| `--text-display` | 36 / 44 | Page hero |
| `--text-h1` | 30 / 38 | Screen title |
| `--text-h2` | 24 / 32 | Section heading |
| `--text-h3` | 20 / 28 | Card title |
| `--text-body-lg` | 18 / 28 | Lead body |
| `--text-body` | 16 / 24 | Default body |
| `--text-small` | 14 / 20 | Helper, captions |
| `--text-micro` | 12 / 16 | Legal, timestamps |

Font family: `Inter`, system-ui fallback. Min body size: 16px. Min touch target: 44x44px.

### 0.3 Layout Tokens

- Container max-width: 1120px desktop, 720px form pages.
- Grid: 12-col desktop, 8-col tablet, 4-col mobile, 16px gutter.
- Base spacing scale: 4, 8, 12, 16, 24, 32, 48, 64.
- Border radius: 4 (input), 8 (card), 12 (modal).

### 0.4 Global Accessibility (WCAG 2.2 AA) Defaults

- Skip-to-content link as first focusable element on every page.
- Visible focus ring: 2px solid `--color-primary-600`, 2px offset, never removed.
- All form errors announced via `aria-live="polite"` regions.
- Required fields marked with `aria-required="true"` AND visible "*Required" label (no color-only signal).
- Time-outs (session) display warning at T-2min with extend button (WCAG 2.2 SC 2.2.1).
- Drag-and-drop file upload has an equivalent click-to-browse path (WCAG 2.2 SC 2.5.7).
- Authentication does not require cognitive function tests (WCAG 2.2 SC 3.3.8) — magic link or passkey supported.
- `prefers-reduced-motion` honored for all transitions.

---

## Screen P1 — Landing / Sign-In

### Information Architecture Rationale
This is the first touchpoint and must do three jobs: (1) reassure a clinician that this is the right portal for their hospital/payer, (2) provide an unambiguous "start new application" vs "continue existing" choice, (3) authenticate with the lowest-cognitive-load method first (passkey or email magic link) to satisfy WCAG 2.2 SC 3.3.8.

### Wireframe

```
+------------------------------------------------------------------------------+
| [Skip to content]                                                  [EN | ES] |
+------------------------------------------------------------------------------+
| [HCPC logo]   Provider Credentialing Portal              Help  |  Status     |
+------------------------------------------------------------------------------+
|                                                                              |
|     Credentialing made straightforward.                                      |
|     Apply once. Track every step. Audit-ready by design.                     |
|                                                                              |
|   +----------------------------------+   +-------------------------------+   |
|   |  Continue your application       |   |  Start a new application      |   |
|   |                                  |   |                               |   |
|   |  Email address                   |   |  Begin the 7-step credential- |   |
|   |  [________________________]      |   |  ing process. Takes 15-30 min |   |
|   |                                  |   |  to submit; verification is   |   |
|   |  [ Send sign-in link ]           |   |  automated after that.        |   |
|   |                                  |   |                               |   |
|   |  or  [ Sign in with passkey ]    |   |  [ Start application -> ]     |   |
|   |                                  |   |                               |   |
|   +----------------------------------+   +-------------------------------+   |
|                                                                              |
|   Need help?  Call 1-800-CRED-HLP (M-F 8am-8pm ET)  |  chat@hcpc.example     |
|                                                                              |
|   This portal handles Protected Health Information (PHI). Your session is    |
|   encrypted (TLS 1.3) and HIPAA-compliant.   [ Privacy ]  [ Accessibility ]  |
+------------------------------------------------------------------------------+
```

### Key Components
- `AuthCard` (passwordless): email input + magic-link button + passkey option.
- `LangSwitcher` (EN/ES at minimum, lang attribute on `<html>` updated).
- `TrustStrip` (footer) — HIPAA, TLS, privacy/accessibility links.
- `HelpChannel` panel (phone + chat + hours).

### State Variations
- **Loading** (after submit): button shows spinner + `aria-busy="true"`, helper text "Sending link…".
- **Empty / first visit**: shown as drawn above.
- **Error** (invalid email): inline error below field in `--color-danger-600`, focus moves to field, `role="alert"`.
- **Rate-limited**: message "Too many attempts. Try again in 5 minutes." + CAPTCHA-free fallback (call center).
- **Magic-link expired** (deep-link variant): hero swaps to "That link expired" + re-send button.

### Accessibility Notes
- `<h1>` is "Credentialing made straightforward." — single H1 per page.
- Form label is `<label for="email">`, not placeholder-as-label.
- "Sign in with passkey" button uses WebAuthn; falls back to magic link if unsupported (announced via live region).
- Color is never the only differentiator — buttons have icons + text.
- Language switcher updates `lang` attribute and reloads localized strings without full navigation.

### Copy Guidance
- Headline ≤ 6 words; sub-head plain-language Flesch ≥ 60.
- Avoid jargon: say "sign-in link" not "OTP" or "magic link" in user-visible text. (Use "Passkey" because Apple/Google/Microsoft have normalized the term.)
- Never use "click here." Buttons describe the result ("Send sign-in link").

---

## Screen P2 — Multi-Step Application (Wizard Shell)

### Information Architecture Rationale
The seven workflow steps (S1–S7) are system-internal. The provider only fills out S1 and then waits. To match the charter's "Provider Applies (intake + identity)" scope, S1 itself decomposes into five user-facing sub-steps that map to data sources downstream:

1. Personal Info → identity + demographics
2. NPI Lookup → S5 prefill
3. CAQH Consent + Auth → S2 unlock
4. Licenses + Documents → S3 + uploads to ledger
5. Attestations + Sign → S6 packet seed

Progressive disclosure: each step is its own page, never a single long form. A persistent stepper on the left shows progress and supports backward navigation (forward only when current step is valid).

### Wireframe — Wizard Shell (left rail stepper, right pane content)

```
+------------------------------------------------------------------------------+
| [Logo]  Application #A-2026-04711   Saved 14s ago        Dr. Patel  [Sign out]|
+------------------------------------------------------------------------------+
| Steps                          | Step 2 of 5 — NPI Lookup                    |
|                                |                                             |
|  (1) Personal info   Done  v   |  We use your NPI (National Provider         |
|  (2) NPI lookup      ACTIVE *  |  Identifier) to pull your registered name,  |
|  (3) CAQH consent              |  taxonomy, and practice locations from     |
|  (4) Licenses & docs           |  NPPES. This data is shown back to you for |
|  (5) Attestations & sign       |  confirmation before we proceed.            |
|                                |                                             |
|  ----                          |  NPI (10 digits) *Required                  |
|  Need help? [Open chat]        |  [ 1____ _____ ]   [ Look up ]              |
|                                |                                             |
|                                |  +---- Match found --------------------+    |
|                                |  | Name:     Anita R. Patel, MD        |    |
|                                |  | Taxonomy: 207R00000X (Internal Med) |    |
|                                |  | Status:   Active                    |    |
|                                |  | Updated:  2026-04-02                |    |
|                                |  |                                     |    |
|                                |  | [ ] This information is correct.    |    |
|                                |  +-------------------------------------+    |
|                                |                                             |
|                                |  [ <- Back ]          [ Save & continue -> ]|
+------------------------------------------------------------------------------+
| Privacy  |  Accessibility  |  Session expires in 27:14  [ Extend ]            |
+------------------------------------------------------------------------------+
```

### Key Components
- `Stepper` (vertical on desktop, horizontal collapsed on mobile) — uses `<ol>` with `aria-current="step"` on active.
- `AutoSaveIndicator` (top bar) — "Saved 14s ago" / "Saving…" / "Offline — will retry".
- `WizardNav` — Back always enabled (except step 1); forward disabled until validation passes; explains *why* in inline helper.
- `SessionTimer` — visible always; warning modal at T-2min.

### State Variations
- **Loading match** (NPI lookup in flight): inline skeleton in match card + spinner; submit disabled.
- **No match**: error region with options "Re-enter NPI" or "Continue without — we'll verify manually" (links to S5 manual exception flow).
- **NPPES outage**: yellow banner "NPI Registry is temporarily unavailable. You can continue; we'll verify within 24 hours." (per charter R-section contingency.)
- **Validation error**: field-level red border + `role="alert"` text below field; focus jumps to first error on submit.
- **Resumed session**: top banner "Welcome back — you left off on Step 2."

### Accessibility Notes
- Stepper items have `aria-current="step"` (active) and `aria-disabled` on future steps; checkmarks have `aria-label="completed"`.
- NPI input uses `inputmode="numeric"` and `autocomplete="off"`; no max-length trick — explicit "10 digits" helper text.
- Confirmation checkbox is NOT pre-checked; required attribute set.
- Session timer announced every 60s via polite live region (not every second — would be hostile to screen readers).

### Copy Guidance
- Always say what happens next: "We use your NPI to pull your registered name…"
- Errors say what to do, not what failed: "Enter a 10-digit NPI" not "Invalid input."

---

## Screen P3 — Step 1 of 5: Personal Info + Identity Capture

### IA Rationale
Identity capture (gov ID OCR + selfie liveness, per charter S1) is the highest-friction part of the flow. Front-load demographic fields (low cognitive load) and defer the camera/upload step to the bottom — once the user is invested, drop-off is lower. Identity vendor (Jumio/Persona) is embedded as an iframe SDK; we wrap it with our own progress affordance.

### Wireframe

```
+------------------------------------------------------------------------------+
| Step 1 of 5 — Personal info                              Saved just now      |
+------------------------------------------------------------------------------+
| Legal name (as on government ID) *Required                                   |
| First [ Anita_______ ]  Middle [ R.__ ]  Last [ Patel_______ ]  Suffix [MD ] |
|                                                                              |
| Preferred display name (optional)                                            |
| [ Dr. Anita Patel______________________ ]                                    |
|                                                                              |
| Date of birth *Required                                                      |
| [ MM ] / [ DD ] / [ YYYY ]      Format: 01 / 15 / 1985                       |
|                                                                              |
| Contact                                                                      |
| Email * [ anita.patel@example.org_____ ]                                     |
| Phone * [ +1 (___) ___-____ ]  [x] OK to text re: application status         |
|                                                                              |
| Mailing address *Required                                                    |
| Street 1 [_______________________________________________________ ]          |
| Street 2 [_______________________________________________________ ]          |
| City [______________ ]  State [ v ]  ZIP [______ ]                           |
|                                                                              |
| ---- Identity verification --------------------------------------------------|
|                                                                              |
|  We use Persona (HIPAA-compliant) to verify your identity. Your ID image     |
|  and selfie are encrypted and never used for marketing or AI training.       |
|                                                                              |
|  Step A — Upload government ID                                               |
|    +-------------------------+  Drop a photo of your driver's license,       |
|    |   [drop file here]      |  passport, or state ID. PNG/JPG/PDF, < 10MB.  |
|    |       or                |  Or [ Browse files ]                          |
|    |   [ Use device camera ] |  Or [ Continue on phone -> QR ]               |
|    +-------------------------+                                               |
|                                                                              |
|  Step B — Selfie + liveness check                                            |
|    [ Start liveness check ]   (Will open camera; takes ~20 seconds.)         |
|                                                                              |
| [ <- Cancel ]                                       [ Save & continue -> ]   |
+------------------------------------------------------------------------------+
```

### Key Components
- `NameGroup` (4 sub-inputs with `autocomplete="given-name"`, etc.).
- `DateInput` — three-segment with combined `aria-describedby` to format hint, NOT a date-picker (clinicians type DOBs faster than they click).
- `AddressGroup` — state as combobox, ZIP triggers async city/state prefill.
- `IdentityWidget` — wraps vendor SDK; we own the outer label, vendor owns iframe.
- `MobileHandoff` — QR code to switch device for camera step.

### State Variations
- **Camera permission denied**: clear instructions to re-grant + "upload photo instead" path.
- **Liveness failed (1st try)**: friendly retry with lighting tips; max 3 attempts before routing to manual review queue (per R6 contingency).
- **OCR low confidence**: editable fields populated with `aria-describedby` "Auto-filled from ID — please verify."
- **Save & continue while ID still processing**: button label changes to "Save & continue (ID will verify in background)" with explanatory tooltip.

### Accessibility Notes
- Drag-drop has equivalent button per WCAG 2.2 SC 2.5.7 (Dragging Movements).
- Camera step provides alternative: upload pre-taken photo (no required motor task).
- Liveness instructions in both text and audio (audio captions toggle).
- Field labels are above inputs (never floating-label-only).

### Copy Guidance
- Identity copy is reassuring and concrete: name the vendor, name what *won't* happen ("never used for marketing or AI training").
- Avoid the word "scan" (sounds invasive); use "photo of your ID."

---

## Screen P4 — Step 3 of 5: CAQH Consent + Authorization

### IA Rationale
CAQH ProView is the system-of-record for most US providers. The consent step has two distinct asks: (a) authorize HCPC to retrieve the CAQH profile (legal consent), (b) confirm CAQH ID or trigger a new CAQH profile creation. We separate these visually so the legal consent is not buried.

### Wireframe

```
+------------------------------------------------------------------------------+
| Step 3 of 5 — Authorize CAQH ProView                                         |
+------------------------------------------------------------------------------+
| Most of the data we need is already in your CAQH ProView profile.            |
| With your consent, we will retrieve it directly — no re-typing.              |
|                                                                              |
| Your CAQH ProView ID                                                         |
|   [ 12345678 ]   [ I don't have one yet ]                                    |
|                                                                              |
| +------------------------------------------------------------------------+   |
| | Authorization                                                          |   |
| |                                                                        |   |
| | I, Anita R. Patel, authorize HCPC and its credentialing staff to       |   |
| | retrieve and verify my CAQH ProView profile, including:                |   |
| |  - Education and training history                                      |   |
| |  - Work history and references                                         |   |
| |  - State license details                                               |   |
| |  - Malpractice insurance and claims history                            |   |
| |                                                                        |   |
| | This authorization is valid for 36 months and can be revoked in        |   |
| | writing at any time. Revocation does not affect prior retrievals.      |   |
| |                                                                        |   |
| | [ ] I have read and authorize the retrieval described above. *Required|   |
| |                                                                        |   |
| | Electronic signature                                                   |   |
| | Type your full legal name:  [ ____________________________ ]           |   |
| | Today's date: 2026-06-13                                               |   |
| +------------------------------------------------------------------------+   |
|                                                                              |
| [ <- Back ]                                  [ Sign & continue -> ]          |
+------------------------------------------------------------------------------+
```

### Key Components
- `CAQHIdField` — 7-digit number with formatting; "I don't have one yet" routes to CAQH-account-creation help page (external link with `rel="noopener"`).
- `ConsentBlock` — full text rendered in a scroll region (not a modal); checkbox must be in viewport when checked (WCAG 2.2 SC 2.4.11 Focus Not Obscured).
- `TypedSignature` — must match name on file (case-insensitive); rejects with helpful error if mismatch.

### State Variations
- **No CAQH ID**: branching panel with link out + reassurance ("You can keep going; we'll catch up once your CAQH ID is set.").
- **CAQH retrieval (background)**: shown later in tracker as "S2: pulling your CAQH profile…"
- **Consent text mid-update**: version pinned to user's session; if a new version is published mid-session, banner: "Our authorization text was updated. Review and re-confirm to continue."

### Accessibility Notes
- Consent text is real DOM, not an embedded PDF (screen-reader navigable).
- Typed signature field uses `autocomplete="off"` (don't suggest from autofill).
- Document version, hash, and timestamp captured in audit ledger (per QG-1).

### Copy Guidance
- Plain-language consent at 8th-grade reading level (Hemingway editor target).
- Never use "click here." "Read full CAQH authorization (PDF, 3 pages)."

---

## Screen P5 — Step 4 of 5: Licenses & Document Upload

### IA Rationale
Providers often hold multiple state licenses; the UI must support add/edit/remove without forcing them to leave the screen. Documents are scoped per-license (e.g., license certificate per state) plus global docs (DEA, malpractice COI). All uploads stream to WORM-locked S3 with hash chained into audit ledger.

### Wireframe

```
+------------------------------------------------------------------------------+
| Step 4 of 5 — Licenses & documents                                           |
+------------------------------------------------------------------------------+
| State licenses                                                               |
|                                                                              |
| +--------------------------------------------------------------------+       |
| | NY - MD-123456     Issued 2014-07-01  Expires 2027-07-01           |       |
| | [ Upload certificate ]   Status:  Not uploaded                     |       |
| | [ Edit ]  [ Remove ]                                               |       |
| +--------------------------------------------------------------------+       |
|                                                                              |
| +--------------------------------------------------------------------+       |
| | NJ - 25MA01234500  Issued 2018-03-15  Expires 2026-09-30           |       |
| | certificate-nj.pdf  uploaded 2026-06-13   [ Replace ] [ View ]     |       |
| +--------------------------------------------------------------------+       |
|                                                                              |
| [ + Add another state license ]                                              |
|                                                                              |
| ---- Other documents -------------------------------------------------------|
|                                                                              |
| DEA registration   [ Upload ]   Required                                     |
| Malpractice COI    [ Upload ]   Required                                     |
| Board certification [ Upload ]  Optional                                     |
| CV (PDF)            [ Upload ]   Required                                    |
|                                                                              |
| Each file: PDF/PNG/JPG, < 25 MB. We store files encrypted (AES-256) on      |
| HIPAA-compliant storage and never share them outside the credentialing       |
| committee and verification process.                                          |
|                                                                              |
| [ <- Back ]                                      [ Save & continue -> ]      |
+------------------------------------------------------------------------------+
```

### Key Components
- `LicenseCard` — collapsible; shows state, number, dates, upload state.
- `LicenseEditor` (modal) — fields: state combobox, license number (state-specific mask), issue date, expiration date, taxonomy.
- `FileDrop` — drag/drop with click-to-browse alternative; per-file progress bar with `aria-valuenow`.
- `DocChecklist` — required vs optional documents with status badges.

### State Variations
- **Empty**: large empty-state callout — "Add your first state license to continue."
- **Upload in progress**: per-file progress with cancel button; multi-file queue.
- **Upload failed (virus scan, format)**: red status with reason and "Try again" / "Choose different file."
- **License about to expire (< 90 days)**: warning badge "Expires in 73 days — we'll prompt renewal."
- **Save & continue with missing required docs**: blocking modal lists exactly what's missing.

### Accessibility Notes
- File input has visible label and visible filename after selection (don't hide native filename).
- Progress bars have `role="progressbar"` and `aria-valuenow`.
- Each license card is a `<section>` with `aria-labelledby` to its state heading.
- Remove action triggers confirmation dialog (`aria-modal="true"`); focus returns to "Add license" on close.

### Copy Guidance
- File-size limit and formats stated *before* selection, not after rejection.
- Storage reassurance is one sentence and links to longer privacy page.

---

## Screen P6 — Step 5 of 5: Attestations & E-Signature

### IA Rationale
This step generates the audit-ready packet (QG-1). Each attestation is a separate, individually-checked statement with its own audit ledger entry. Bundling them violates legal-counsel guidance and prevents granular revocation.

### Wireframe

```
+------------------------------------------------------------------------------+
| Step 5 of 5 — Attestations & signature                                       |
+------------------------------------------------------------------------------+
| Please review each statement. Each requires a separate confirmation.         |
|                                                                              |
| [ ] I have never had a state medical license suspended, revoked, or         |
|     restricted, except as disclosed in this application.                     |
|     [ Add disclosure ]                                                       |
|                                                                              |
| [ ] I have no pending or unresolved sanctions, exclusions, or debarments    |
|     from any federal or state program (OIG, SAM, Medicaid).                  |
|     [ Add disclosure ]                                                       |
|                                                                              |
| [ ] I have no malpractice claims in the past 10 years except as disclosed.  |
|     [ Add disclosure ]                                                       |
|                                                                              |
| [ ] I have read and agree to HCPC's HIPAA Notice of Privacy Practices       |
|     ( [view PDF, 4 pages] ).                                                 |
|                                                                              |
| [ ] All information I have provided in this application is true and        |
|     complete to the best of my knowledge. I understand that false or        |
|     misleading information may result in denial or termination.             |
|                                                                              |
| ---- Sign your application -------------------------------------------------|
|                                                                              |
| Signing as:  Anita R. Patel, MD                                              |
| Today's date: 2026-06-13                                                     |
|                                                                              |
| Choose your signature method:                                                |
|   (o) Type my name as my signature                                           |
|   ( ) Draw my signature                                                      |
|   ( ) Sign with DocuSign (will redirect)                                     |
|                                                                              |
|   Signature: [ Anita R. Patel____________ ]                                  |
|                                                                              |
| [ <- Back ]                                  [ Submit application ]          |
+------------------------------------------------------------------------------+
```

### Key Components
- `AttestationItem` — checkbox + statement + optional `[Add disclosure]` reveal that opens a textarea (audit logged separately).
- `SignaturePad` — draw mode uses canvas with keyboard fallback ("Type instead").
- `DocuSignHandoff` — opens vendor flow; returns with envelope ID stored on application.

### State Variations
- **Disclosure required but empty**: cannot submit; inline error "Provide details for the disclosed item."
- **Submitting**: full-page status with "Submitting securely…" + spinner + reassurance "Do not close this tab."
- **Submit failed (server)**: stay on form; banner "Couldn't submit. Your answers are saved. Try again."
- **Already submitted (navigated back)**: read-only view with link "View your application status."

### Accessibility Notes
- Canvas signature provides keyboard alternative AND clears on Escape.
- Each attestation is independently focusable; no nested checkbox traps.
- After submit, focus moves to "Application submitted" landmark on confirmation screen.

### Copy Guidance
- Each attestation is one sentence, present tense, first person.
- Avoid double negatives (don't write "I do not have no claims").

---

## Screen P7 — Application Status Tracker

### IA Rationale
The seven workflow steps are visible to the provider here — but framed in their language ("We're checking your licenses") rather than internal codes (S3). The user's mental model is "where is my application?" so the tracker is the primary surface. Sub-jobs (per-state, per-source) are revealed on demand without dominating the screen.

### Wireframe

```
+------------------------------------------------------------------------------+
| Application #A-2026-04711                            Dr. Patel  [Sign out]   |
+------------------------------------------------------------------------------+
| Submitted 2026-06-13 09:41 ET                       Estimated decision: 28d  |
|                                                                              |
| Overall progress: 4 of 7 steps complete                                      |
| [=========================================----------------]  57%             |
|                                                                              |
| +---- Step timeline ----------------------------------------------------+    |
| |                                                                       |    |
| |  1  Application received               Done   Jun 13, 9:41am           |    |
| |  2  CAQH profile retrieved              Done   Jun 13, 9:43am           |    |
| |  3  Licenses verified                   Done   Jun 13, 9:58am  [details]|    |
| |  4  Sanctions & exclusions checked     Done   Jun 13, 10:02am [details]|    |
| |  5  NPI verified                        Done   Jun 13, 9:44am          |    |
| |  6  Committee review                    IN PROGRESS  ETA Jun 24        |    |
| |  7  Network onboarding                  --                              |    |
| |                                                                       |    |
| +------------------------------------------------------------------------+    |
|                                                                              |
| Action required from you: none                                               |
|                                                                              |
| [ Open messages (2) ]   [ Upload additional documents ]                      |
+------------------------------------------------------------------------------+

When [details] expanded on Step 3:

  Step 3 - Licenses verified
   New York    DOH               Verified   Jun 13, 9:55am
   New Jersey  State Board       Verified   Jun 13, 9:58am
   Florida     State Board       Verified   Jun 13, 9:53am

When step 6 is the current step, an explanatory note appears:

  "The credentialing committee meets every other Tuesday. Your file is on
   the agenda for Jun 23. You don't need to do anything — we'll email you
   the decision within 24 hours of the meeting."
```

### Key Components
- `ProgressBar` (overall) — labeled by `aria-valuetext` ("57 percent, 4 of 7 steps complete").
- `StepTimeline` — ordered list with semantic step states.
- `StepDetailDrawer` — per-step expandable showing sub-jobs (states for S3, sources for S4).
- `ActionBanner` — only renders if `actionRequired === true`; otherwise hidden (not "no actions" noise).

### State Variations
- **Loading**: skeleton timeline; never blank.
- **Step failed (e.g., license mismatch)**: red status + action banner with explicit task ("Upload corrected NY license").
- **Decision: approved**: top hero turns success-green with "Welcome to the network" + next-step CTA.
- **Decision: denied**: respectful, neutral framing with appeal pathway and contact information.
- **Decision: deferred**: explains what info is needed and by when.
- **Long-running S6**: countdown to next committee meeting; never a vague "soon."

### Accessibility Notes
- Live region announces status changes (polite, debounced to avoid noise).
- Step states use both icon and text — never color-only.
- Date/time strings include timezone abbreviation and full ISO date in `<time datetime>`.

### Copy Guidance
- Avoid system jargon: "Sanctions & exclusions checked" not "S4 complete."
- Provide ETAs whenever possible; vague waits erode trust.
- For denials, never use auto-generated language; surface human contact.

---

## Screen P8 — Notification Preferences

### IA Rationale
Notifications are a frequent support pain point. Allow per-event channel selection (email / SMS / portal-only) but never let the user opt out of legally-required notices (e.g., decision letters). Sensible defaults; everything reversible.

### Wireframe

```
+------------------------------------------------------------------------------+
| Notification preferences                                                     |
+------------------------------------------------------------------------------+
| Channels                                                                     |
|                                                                              |
|   Email     [x]  anita.patel@example.org           [ Change ]                |
|   SMS       [x]  +1 (212) 555-0188                 [ Change ]                |
|   Portal    [x]  Always on (cannot disable)                                  |
|                                                                              |
| What we notify you about                                                     |
|                                                                              |
|                                            Email   SMS   Portal              |
|   Application step completed                [x]    [ ]    [x]                |
|   Action required from you                  [x]    [x]    [x]                |
|   Document expiration warning (90/30/7d)    [x]    [x]    [x]                |
|   Committee decision *required               [x]    [x]    [x]                |
|   Marketing & product news                  [ ]    [ ]    [ ]                |
|                                                                              |
|   * Required by policy — cannot be disabled.                                 |
|                                                                              |
| Quiet hours (SMS only)                                                       |
|   From [ 9:00 PM v ]  to [ 7:00 AM v ]   Timezone: America/New_York          |
|                                                                              |
| Language for notifications:  [ English v ]                                   |
|                                                                              |
| [ Save preferences ]                                                         |
+------------------------------------------------------------------------------+
```

### Key Components
- `ChannelList` — email, SMS, portal — each with verification state ("Change" triggers re-verify).
- `PreferenceMatrix` — events × channels grid, with required rows visually flagged.
- `QuietHoursPicker` — paired time selects + timezone.

### State Variations
- **Unverified email/phone after change**: "Verification sent — check your inbox." Cannot save preferences using unverified channel.
- **Save success**: toast "Preferences saved" + last-saved timestamp displayed.
- **Required toggle attempt to disable**: tooltip explains why; checkbox visibly locked with `aria-disabled`.

### Accessibility Notes
- Matrix uses real `<table>` with `<th scope>` headers.
- Disabled required rows have explanatory `aria-describedby`.
- Time pickers are native `<input type="time">` for screen-reader/keyboard reliability.

### Copy Guidance
- Be explicit about what's mandatory ("Required by policy"), not just disabling controls.
- Show last save timestamp, not just a fleeting toast.

---

## Screen Count Summary (this document)

Provider Portal screens: **8** (P1 through P8).

---

*End of Provider Portal mockups.*
