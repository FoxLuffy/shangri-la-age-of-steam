# End-to-End & Visual Regression Tests

Playwright drives the full stack (backend on :8003 + Vite dev server on :5173, both
auto-started by `playwright.config.ts`'s `webServer`).

```bash
cd frontend
npx playwright test              # run all e2e specs
npx playwright test --ui         # interactive UI mode
npx playwright show-report       # open the last HTML report
```

## Visual regression

The suite screenshots the three most visually complex screens and compares them against
committed baselines via `expect(page).toHaveScreenshot(...)`:

| Screen            | Spec                          | Baseline name            |
|-------------------|-------------------------------|--------------------------|
| CharacterCreation | `character-creation.spec.ts`  | `character-creation.png` |
| ChatInterface     | `market.spec.ts`              | `chat-interface.png`     |
| MarketUI          | `market.spec.ts`              | `market-ui.png`          |

Comparisons use `maxDiffPixelRatio: 0.1` to tolerate minor rendering noise. When a
screenshot differs, the Playwright **HTML report (with the diff image) is uploaded as a CI
artifact** (`.github/workflows/ci.yml`, `if: failure()`), so reviewers can see the visual
change on the PR.

### Baselines are per-platform

Playwright suffixes baselines with the OS (`*-chromium-linux.png`, `*-chromium-win32.png`).
**CI runs on Linux**, so the `-linux` baselines are the ones that gate merges; the `-win32`
copies are for local runs on Windows. Both are committed and are marked `binary` in
`.gitattributes` so line-ending filters never corrupt them.

### Regenerating baselines

- **Local (win32):** `npx playwright test --update-snapshots` — regenerates the `-win32`
  PNGs only.
- **Linux (the CI-gating ones):** generate them in a Linux environment — either the CI job
  run with `--update-snapshots`, or the official Playwright container:
  ```bash
  docker run --rm -v "$PWD/..":/work -w /work/frontend \
    mcr.microsoft.com/playwright:v1.61.1-jammy \
    sh -c "npm ci && npx playwright test --update-snapshots"
  ```
  (The backend `webServer` needs Python available in that environment.)

### Adding a new screen to visual regression

Add a `toHaveScreenshot('<name>.png', { fullPage: true, maxDiffPixelRatio: 0.1 })` at the
right point in a spec, then generate **both** `-win32` and `-linux` baselines (see above)
and commit them. A new screenshot with no `-linux` baseline will fail CI until the Linux
baseline exists.
