# Firmware takeover tasks

## FW-01 — Capture baseline source
Status: DONE

Import the matching Cheapino/Vial source and pin the Vial-QMK base without changing behavior.

Acceptance: source provenance, UID, Vial-QMK pin and no-CI policy are versioned.

Evidence:
- Cheapino source pin: `8ec1e329cfff13ef6f206b55ff4af1b42e6ec778`;
- Vial-QMK pin: `dd43959ae5c08d8a28d38a1acf7b04e86b14a344`;
- Vial UID match: `0x9EC18B09BB40ED79`.

## FW-02 — Reproduce baseline locally
Status: IN PROGRESS

Build `cheapino:vial` from a clean local checkout using the pinned inputs.

Current evidence:
- the exact pinned upstream source pair has compiled successfully with QMK CLI image digest `sha256:b7d7fa8fb4432b569931de5ad59098cb788f440ed61a62c5126746b71aee0f4a` and `arm-none-eabi-gcc 15.2.0`;
- reconstructed UF2: 113664 bytes, SHA-256 `632cb9dcf8640828e87c2f854ef2e22e660c888914cdb0f94b108d0a5d326937`;
- published encoder-enabled reference: 115200 bytes, SHA-256 `8920c6a8137e1283780731c46712ccbea39664fe7f249ca238110dd1a053cc3f`;
- exact binary match: no;
- `make build` now provides a local-only Podman/Docker reproduction path using the pinned toolchain container.

Acceptance:
- `make build` succeeds on a normal local checkout;
- generated UF2 is non-empty;
- SHA-256, size and toolchain versions are recorded;
- build does not depend on GitHub Actions;
- no firmware behavior is intentionally changed;
- the delta from the published reference is classified before exact binary provenance is claimed.

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
