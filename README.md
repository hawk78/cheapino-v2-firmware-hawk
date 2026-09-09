# Cheapino V2 firmware

Owned build workspace for the Cheapino V2 firmware used with Vial.

The first milestone is intentionally conservative: reproduce the firmware currently in use before upgrading Vial/QMK or changing behavior.

## Baseline

Cheapino-specific source provenance:

- `bleys43/cheapinov2-vial-qmk-firmware`
- source revision: `8ec1e329cfff13ef6f206b55ff4af1b42e6ec778`
- matching Vial UID: `0x9EC18B09BB40ED79`

Pinned Vial-QMK base:

- `vial-kb/vial-qmk`
- revision: `dd43959ae5c08d8a28d38a1acf7b04e86b14a344`

The Vial-QMK tree is not vendored. Our Cheapino-specific source lives in `keyboard/cheapino/` and is overlaid onto the pinned Vial-QMK checkout for each clean build.

## Local build only

No GitHub Actions workflow is provided. CI must not be introduced or run without explicit approval.

The default build uses a pinned QMK CLI container and prefers Podman, falling back to Docker:

```sh
make build
```

This produces:

```text
build/cheapino_vial.uf2
build/build.log
build/build-manifest.txt
```

A native toolchain path is also kept for development:

```sh
make build-native
```

The container image, Vial-QMK revision and Cheapino source provenance are all pinned in versioned files.

## Current state

The pinned source pair has already been shown to compile successfully. The first reconstructed UF2 is not byte-for-byte identical to the encoder-enabled reference binary published by `bleys43`; this difference is tracked rather than hidden. See `docs/BASELINE.md`.

At this stage we intentionally do not change key behavior, tapping policy, Vial settings, or the user's dynamic layout stored in EEPROM.

## Roadmap

1. reproduce the baseline locally with `make build`;
2. explain or classify the binary delta against the published reference;
3. validate the reproduced firmware on the real keyboard;
4. compare the baseline with current Vial/QMK and current Cheapino upstream work;
5. migrate while preserving behavior and rollback;
6. add custom debugging or tap/hold behavior only if still useful after the migration.

## Licensing and provenance

The Cheapino/QMK-derived firmware is GPL-2.0-or-later/GPL-2.0 as applicable to the upstream files. Original copyright and SPDX notices are retained where present. See `PROVENANCE.md` and `LICENSE`.
