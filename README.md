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

The Vial-QMK tree is not vendored. `make bootstrap` clones the pinned revision into `.cache/`; our Cheapino source is then overlaid from `keyboard/cheapino/`.

## Local build only

No GitHub Actions workflow is provided. CI must not be introduced or run without explicit approval.

```sh
make bootstrap
make build
```

The resulting UF2 and build metadata are copied to `build/`.

At this stage the build intentionally does not change key behavior, tapping policy, Vial settings, or the layout stored in EEPROM.

## Roadmap

1. reproduce the current firmware locally;
2. record the exact build/toolchain requirements;
3. compare the baseline with current Vial/QMK and current Cheapino upstream work;
4. migrate while preserving behavior;
5. add custom debugging or tap/hold behavior only if still useful after the migration.

## Licensing and provenance

The Cheapino/QMK-derived firmware is GPL-2.0-or-later. Original copyright and SPDX notices are retained in imported source files. See `PROVENANCE.md` and `LICENSE`.
