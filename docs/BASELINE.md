# Baseline build evidence

This document records the first successful reconstruction of the firmware source family used by the Cheapino V2.

## Inputs

- Vial-QMK: `dd43959ae5c08d8a28d38a1acf7b04e86b14a344`
- Cheapino source: `8ec1e329cfff13ef6f206b55ff4af1b42e6ec778`
- Vial UID: `0x9EC18B09BB40ED79`
- build target: `cheapino:vial`

## Successful clean build evidence

A clean build of the exact two upstream revisions above completed successfully with:

- QMK CLI container image digest: `sha256:b7d7fa8fb4432b569931de5ad59098cb788f440ed61a62c5126746b71aee0f4a`
- `arm-none-eabi-gcc 15.2.0`
- command: `make cheapino:vial`

The generated UF2 was:

- size: `113664` bytes
- SHA-256: `632cb9dcf8640828e87c2f854ef2e22e660c888914cdb0f94b108d0a5d326937`

The build compiled the custom Cheapino matrix implementation, Cheapino keyboard code, Vial, VIA, QMK settings and encoder support without compiler errors.

## Published reference binary

The encoder-enabled UF2 published in `bleys43/cheapinov2-vial-qmk-firmware@8ec1e329...` is:

- size: `115200` bytes
- SHA-256: `8920c6a8137e1283780731c46712ccbea39664fe7f249ca238110dd1a053cc3f`

Therefore the first reconstructed binary is **not byte-for-byte identical** to the published reference.

This does not mean the firmware behavior differs. Likely causes include a different compiler/toolchain, a different Vial-QMK revision than the reconstruction pin, or other build-environment differences. The mismatch remains open and must be explained before claiming exact binary provenance.

## Local reproduction

`make build` is intentionally local-only. It uses Podman when available, otherwise Docker, and pins the same QMK CLI container digest used by the successful build evidence above.

No GitHub Actions workflow is part of this repository. CI must not be introduced or run without explicit user approval.
