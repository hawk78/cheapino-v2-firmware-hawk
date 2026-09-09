# Provenance

## Cheapino-specific source

The initial `keyboard/cheapino/` tree is imported without semantic changes from:

- repository: `bleys43/cheapinov2-vial-qmk-firmware`
- revision: `8ec1e329cfff13ef6f206b55ff4af1b42e6ec778`

That tree incorporates Cheapino work originating from Thomas Haukland (`tompi`) and later encoder/Vial-QMK integration work discussed in `tompi/cheapino#155`, including changes based on work by `schuay` and other contributors.

The Vial keymap configuration in the imported tree contains:

- Vial UID bytes: `{0x79, 0xED, 0x40, 0xBB, 0x09, 0x8B, 0xC1, 0x9E}`
- corresponding exported `.vil` UID: `0x9EC18B09BB40ED79`
- dynamic layer count: 10
- encoder and encoder-map support enabled

This UID match is the main evidence that this source family corresponds to the firmware currently used with the user's Vial configuration.

## Vial-QMK base

The initial pinned Vial-QMK revision is:

`vial-kb/vial-qmk@dd43959ae5c08d8a28d38a1acf7b04e86b14a344`

It was the latest upstream Vial-QMK revision found before the stated 2026-08-06 build date of the imported firmware source. This is a reconstruction pin, not yet a claim of byte-for-byte identity with the binary currently flashed on the keyboard.

Exact build/toolchain provenance will be recorded after the first successful local reproduction.

## Licensing

The imported firmware is derived from QMK/Cheapino code distributed under GPL-2.0-or-later/GPL-2.0 terms. Original copyright and SPDX notices are retained where present. The repository includes the GPL v2 license text in `LICENSE`.
