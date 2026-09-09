# Agent rules

This repository owns the Cheapino V2 Vial/QMK firmware build.

## Hard rules

- Builds and tests are local by default.
- Never create, enable, or run GitHub Actions/CI without the user's explicit approval for that specific run.
- Preserve the current firmware behavior until the baseline build has been reproduced and hardware-tested.
- Keep Vial-QMK pinned by commit. Never build from a mutable branch as evidence.
- Treat `keyboard/cheapino/` as the owned Cheapino-specific source.
- Do not copy the user's dynamic `.vil` layout into firmware source as a second source of truth.
- Upgrades and custom behavior must be separate, reviewable changes from the reproduced baseline.

## Work order

1. reproduce the current baseline locally;
2. record toolchain/build evidence;
3. assess migration to current Vial/QMK;
4. migrate while preserving behavior;
5. add custom debug/tap-hold behavior only if needed.
