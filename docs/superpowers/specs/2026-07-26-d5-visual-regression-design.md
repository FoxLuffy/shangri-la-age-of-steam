# D5 — E2E & Visual Regression Design

Roadmap item: **D5** (Technical Quality). Marked PARTIAL: "Playwright configured + specs +
CI job; expand visual-regression".

## Audit finding
The concrete D5 deliverable is **already implemented**:
- `toHaveScreenshot` visual regression for the three named screens — CharacterCreation
  (`character-creation.spec.ts`), ChatInterface + MarketUI (`market.spec.ts`).
- Both `-chromium-linux` and `-chromium-win32` baselines are committed.
- CI runs Playwright and uploads the HTML report (with diff images) `if: failure()`, so
  visual diffs surface on the PR.
- These specs have passed green in CI on every recent PR.

## Constraint
Expanding to more screens needs new **Linux** baselines (CI is ubuntu). Docker is installed
but not running here, and the Playwright Linux image lacks Python to boot the backend
`webServer`, so linux baselines can't be reliably generated on this win32 machine. Adding a
screenshot with no linux baseline would make CI red until it is generated in CI.

## Decision (confirmed)
Mark D5 complete with **small, non-pixel-changing hardening** rather than adding new
screenshots (which would risk red CI that can't be fixed here).

## Changes
- `.gitattributes`: declare binary assets (`*.png`, `*.jpg`, fonts, `*.db`, …) as `binary`
  so `core.autocrlf=true` / text filters never corrupt the visual-regression baselines
  (they must be byte-identical for comparison). No existing PNG is renormalized.
- `frontend/e2e/README.md`: document the e2e + visual-regression setup — what's covered,
  the `maxDiffPixelRatio: 0.1` tolerance, the CI diff-artifact flow, per-platform baselines,
  how to regenerate them (local win32 vs Linux/Docker/CI), and how to add a new screen.

## Verification
- No spec `.ts` files changed → the existing green visual-regression run is unaffected.
- Adding `.gitattributes` leaves existing PNG baselines unmodified in `git status`.
- Frontend unit suite stays green (97).
- CI (backend + frontend + E2E) confirms on the PR.

## Out of scope
- New screenshot screens (blocked by linux-baseline generation here), animation-freezing
  screenshot options (would require regenerating both baselines).

## Acceptance
- Visual regression covers the 3 named screens with CI diff flagging (already true); binary
  baselines are protected from corruption; the setup is documented. D5 → COMPLETE.
