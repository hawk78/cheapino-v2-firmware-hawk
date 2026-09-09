# Firmware takeover tasks

## FW-01 — Capture baseline source
Status: DONE

Import the matching Cheapino/Vial source and pin the Vial-QMK base without changing behavior.

Acceptance: source provenance, UID, Vial-QMK pin and no-CI policy are versioned.

## FW-02 — Reproduce baseline locally
Status: IN PROGRESS

Build `cheapino:vial` from a clean local checkout using the pinned inputs.

Acceptance:
- clean local build succeeds;
- generated UF2 is non-empty;
- SHA-256, size and toolchain versions are recorded;
- build does not depend on GitHub Actions;
- no firmware behavior is intentionally changed.

## FW-03 — Hardware baseline validation
Status: TODO

Flash the reproduced UF2, restore/import the existing `.vil`, and verify keyboard, encoder and Vial connectivity.

## FW-04 — Current Vial/QMK assessment
Status: TODO

Compare baseline against current Vial/QMK and current Cheapino upstream work. Classify upstream fixes, obsolete patches, migration risks and new debug/tap-hold capabilities.

## FW-05 — Upgrade
Status: TODO

Migrate only after FW-03 and FW-04. Preserve rollback to the reproduced baseline.

## FW-06 — Custom behavior and tracing
Status: TODO

Only after the modern baseline is stable, evaluate low-level physical-event/tap-hold/HID tracing and per-key tap-hold policy.
