# Cheapino V2 — migration to a modern Vial-QMK baseline

Status: engineering/provenance record for the current `main` branch.

Current `main` tip when this document was written:

```text
2420a17c22aeaf219a1dcd306468fddfd3e552dd
Modern Cheapino tree on clean modern vial baseline.
```

This document records the process used to get from the older Cheapino V2 firmware lineage to the current modern Vial-QMK-based tree. It is intentionally detailed: the goal is to preserve not only the final answer, but also the source provenance, the intermediate approaches that were tested, the incompatibilities discovered during the port, and the reasons for the final architectural choices.

It does **not** document the typing-telemetry experiment. That work is intentionally isolated on a separate feature branch/project.

---

## 1. Goal and constraints

The starting goal was not simply "make a Cheapino firmware that compiles". The intended end state was:

1. identify the source lineage of the firmware actually in use;
2. reproduce that firmware as closely as possible;
3. understand what is Cheapino-specific and what belongs to QMK/Vial;
4. move to a modern Vial-QMK base without carrying unnecessary core patches;
5. preserve hardware behavior, especially:
   - custom Cheapino matrix scanning;
   - Cheapino ghost suppression;
   - the matrix-intersection rotary encoder;
   - the physical encoder push button;
   - Vial compatibility and keyboard identity;
6. keep rollback possible before flashing experimental firmware;
7. keep the source history meaningful enough to understand where the implementation came from;
8. avoid treating the old binary as the only source of truth when source-level provenance could be recovered.

The work therefore became a provenance + migration exercise, not just a build exercise.

---

## 2. The source repositories that matter

Four upstream/fork lines turned out to be relevant.

```text
tompi/qmk_firmware
    └── cheapinov2        Cheapino on Tompi's QMK fork

tompi/vial-qmk
    ├── vial              Tompi's historical Vial base
    └── cheapinov2        Tompi's Cheapino V2 + Vial development line

vial-kb/vial-qmk
    └── vial              modern/current Vial-QMK base

schuay/qmk_firmware
    └── cheapino          newer Cheapino hardware implementation

bleys43/cheapinov2-vial-qmk-firmware
    └── main              practical modern Vial adaptation, largely based on
                          schuay's newer Cheapino hardware implementation
```

The final result is best understood as:

```text
modern vial-kb/vial-qmk
        +
modern Cheapino hardware implementation from the schuay/Bley line
        +
Vial Cheapino identity/keymap configuration
        +
selected compatibility decisions made during this migration
```

Tompi remains important because it provides the historical Cheapino/Vial lineage and explains several behaviors that would otherwise look arbitrary.

---

## 3. Identifying the firmware lineage from the existing Vial configuration

One of the strongest provenance clues was the existing saved Vial configuration.

The Vial keyboard UID in use was:

```text
0x9EC18B09BB40ED79
```

or, as bytes in the firmware:

```c
#define VIAL_KEYBOARD_UID {0x79, 0xED, 0x40, 0xBB, 0x09, 0x8B, 0xC1, 0x9E}
```

The existing layout also used the Cheapino-specific unlock positions:

```c
#define VIAL_UNLOCK_COMBO_ROWS { 6, 2 }
#define VIAL_UNLOCK_COMBO_COLS { 11, 5 }
```

A very strong source match was found in:

```text
bleys43/cheapinov2-vial-qmk-firmware
8ec1e329cfff13ef6f206b55ff4af1b42e6ec778
```

That revision contains the same UID and Cheapino Vial configuration family.

The important Bley encoder-enablement commit is:

```text
559e25a04ead99c34bdb4f59f11237a06a16bf98
```

Its commit message explicitly documents the main ingredients of the working encoder port:

- replacement of the older Cheapino tree with the newer `schuay`-derived tree;
- use of Tompi's Vial keymap as a basis;
- enabling VIA/Vial encoder support;
- moving the encoder push keycode to the correct physical position in `LAYOUT`;
- adapting the matrix/debounce integration for the Vial tree used by Bley;
- producing an encoder-enabled UF2.

This was the first indication that the firmware in use was not just "Tompi Cheapino on stock Vial", but belonged to a later convergence of Tompi + schuay + Bley work.

---

## 4. First reproducibility experiment: pin Bley + a modern Vial base

Before restructuring the repository, a build experiment was used to answer a narrow question:

> Does the identified Cheapino source compile when placed on a specific modern Vial-QMK revision?

The Vial-QMK revision selected as the modern baseline was:

```text
vial-kb/vial-qmk
branch: vial
commit: dd43959ae5c08d8a28d38a1acf7b04e86b14a344
```

This is the modern Vial base retained in the final history.

The Cheapino source candidate was:

```text
bleys43/cheapinov2-vial-qmk-firmware
commit: 8ec1e329cfff13ef6f206b55ff4af1b42e6ec778
```

The pair compiled successfully.

### 4.1 Binary comparison result

A published Bley encoder-enabled reference UF2 was available:

```text
file: cheapino_vial-encoder-enabled.uf2
size: 115200 bytes
sha256: 8920c6a8137e1283780731c46712ccbea39664fe7f249ca238110dd1a053cc3f
```

The early pinned reproduction build produced a different binary:

```text
size: 113664 bytes
sha256: 632cb9dcf8640828e87c2f854ef2e22e660c888914cdb0f94b108d0a5d326937
```

Therefore the conclusion was deliberately limited:

```text
source pair compiles:       yes
exact binary reproduction:  no
```

This mattered. The build established compatibility, but did **not** prove the exact historical toolchain or exact source provenance of the published UF2.

### 4.2 Toolchain note

The historical experimental build used an Arm GCC 15.2-era toolchain in a QMK CLI container.

Later local development used a Nix shell with approximately:

```fish
nix shell \
  nixpkgs#qmk \
  nixpkgs#gcc-arm-embedded \
  nixpkgs#gnumake \
  nixpkgs#git \
  --command fish
```

Observed locally during the migration:

```text
qmk CLI:              1.2.0
Arm GNU Toolchain:    15.3.Rel1 / GCC 15.3.1
Vial/QMK tree report: QMK Firmware 0.15.18
```

The toolchain difference is another reason the early binary mismatch was not treated as evidence that the source identification was wrong.

---

## 5. The first repository structure was intentionally abandoned

An early repository attempt treated the project as a thin overlay/wrapper:

```text
small repository
    ├── Cheapino files
    ├── scripts
    └── build wrapper
            ↓
        clone Vial-QMK into cache
```

That structure was rejected for this project.

The main reasons were:

- the real firmware source/history was hidden behind build-time cloning;
- it made provenance harder to inspect with normal Git tools;
- it made rebases and upstream comparisons unnecessarily indirect;
- it encouraged treating the Cheapino subtree as a payload instead of part of the actual firmware history;
- it complicated debugging of environment and PATH behavior in wrappers.

The project was restarted as a real Vial-QMK source tree with meaningful upstream history.

The old overlay history was retained only as backup branches and is not the architectural basis of `main`.

---

## 6. Reconstructing the original Tompi Vial lineage

A key correction during the investigation was discovering that Bley was **not** the original Vial port of Cheapino V2.

Tompi maintains a separate Vial-QMK fork with a real Cheapino V2 branch:

```text
tompi/vial-qmk:vial
    ↓
tompi/vial-qmk:cheapinov2
```

The branch relationship was measured as:

```text
tompi-vial/vial ... tompi-vial/cheapinov2
0  14
```

Meaning the Cheapino branch was 14 commits ahead of Tompi's Vial base and not behind it.

The merge base with the modern official Vial line was:

```text
2772f52fa548c48ae3abbe4784eaadbef063b4f2
```

At the time of the migration, the distance from Tompi's historical Vial base to the selected modern official Vial baseline was very large:

```text
tompi-vial/cheapinov2 ... vial/vial
14  2578
```

This made the problem concrete: we were not moving a keyboard across a handful of commits. We were porting a Cheapino-specific series across more than two thousand Vial/QMK commits.

---

## 7. Tompi Cheapino commit series

The relevant Cheapino commits on Tompi's historical `cheapinov2` line were, in order:

```text
dfe472bf1b  Add support for Cheapino 2
0d054118c3  Remove layers > 4
29e0e5fdd3  Full encoder support for Cheapino 2
4ddd893fc5  Enable 8 layers and remover compile warnings
1c8b6644c1  Fix row displacement on save
ee72e32281  Attempt to fix ghosting: issue 33
1315dd975c  Fix more ghosting: issue 33
48f5fc6eb3  Use unsigned short instead of ushort
6aea49fd1b  Added NKRO support
73708a3f80  Increasing layers from 8 to 14
433fbbd016  Fix default searing LED brightness
539b9cf4cc  Configure shared EP to allow mods for extra keys
27ae52eea1  Merge branch 'cheapinov2' ...
9100f29f3e  More usable default keymap
```

The merge commit did not contain a meaningful manual semantic merge resolution for the Cheapino port, so the useful series for a normal rebase was the 13 non-merge commits.

---

## 8. Rebase of Tompi Cheapino onto modern Vial-QMK

A dedicated port branch was created from Tompi's Cheapino V2 branch and rebased onto the modern official Vial baseline:

```fish
git switch -c port/tompi-cheapinov2-modern-vial tompi-vial/cheapinov2
git rebase --onto vial/vial tompi-vial/vial
```

Conceptually:

```text
old:
2772f52  Tompi Vial base
    └── Cheapino commits

new:
dd43959  modern official Vial base
    └── rebased Cheapino commits
```

The current repository history still preserves the rebased Tompi series immediately after `dd43959`.

Original → rebased mapping visible in this repository:

| Original Tompi commit | Rebased commit in this repository | Meaning |
|---|---|---|
| `dfe472bf1b` | `e919f1d05f` | Add Cheapino V2 |
| `0d054118c3` | `48033afc27` | Remove layers > 4 |
| `29e0e5fdd3` | `1f099f8511` | Full encoder support |
| `4ddd893fc5` | `5492e10c1b` | Enable 8 layers / warning cleanup |
| `1c8b6644c1` | `e2ee00ea30` | Row displacement fix |
| `ee72e32281` | `89acdaf8d1` | Initial ghosting fix |
| `1315dd975c` | `fb93c71c96` | More ghosting fixes |
| `48f5fc6eb3` | `dd528f2156` | `ushort` cleanup |
| `6aea49fd1b` | `63b384f779` | NKRO support |
| `73708a3f80` | `ce2753bb88` | Increase to 14 layers |
| `433fbbd016` | `b69d195ba7` | Default LED brightness |
| `539b9cf4cc` | `21bb8bc2eb` | Shared EP configuration |
| `9100f29f3e` | `ace4161e00` | More usable default keymap |

This intermediate port was useful even though it was not the final keyboard tree. It exposed exactly which historical Cheapino assumptions no longer matched modern Vial/QMK.

---

## 9. Encoder API conflict and the modern solution

The important rebase conflict occurred in the old encoder integration.

Tompi's historical implementation had needed a Vial/QMK core modification so keyboard code could invoke the encoder mapping path directly. The old port used an `encoder_exec_mapping()`-style integration.

Modern Vial-QMK already provides a proper encoder event queue API:

```c
bool encoder_queue_event(uint8_t index, bool clockwise);
```

The migration rule became:

```text
Do not revive the old core patch.
Use the modern public encoder queue from keyboard-specific code.
```

During the Tompi rebase, the core `quantum/encoder.c` and `quantum/encoder.h` were restored to the modern upstream versions, while the Cheapino encoder path was adapted to queue events with:

```c
encoder_queue_event(0, clockwise);
```

This was a major architectural improvement because it removed a Cheapino-specific modification from generic QMK/Vial core.

---

## 10. Metadata modernization discovered during the Tompi port

The rebased historical Cheapino tree still used several legacy QMK configuration patterns.

The port was progressively modernized.

### 10.1 `info.json` → `keyboard.json`

The Cheapino keyboard metadata was moved to the modern data-driven form expected by current QMK/Vial.

### 10.2 Encoder pin metadata

Legacy defines such as:

```c
#define ENCODERS_PAD_A { ... }
#define ENCODERS_PAD_B { ... }
```

were replaced with data-driven encoder metadata in `keyboard.json` during the intermediate Tompi port.

A later discovery changed how those pins should be interpreted for the final implementation: the modern schuay/Bley Cheapino driver uses matrix intersections for the real encoder signals, so its declared rotary pins are intentionally dummy pins needed only to satisfy QMK's encoder feature model.

### 10.3 RGB metadata

Legacy WS2812/RGB count, pin, and default HSV definitions were moved into `keyboard.json` where appropriate.

Cheapino-specific low-level settings that still belong in C configuration, such as:

```c
#define WS2812_PIO_USE_PIO1
#define WS2812_BYTE_ORDER WS2812_BYTE_ORDER_RGB
```

were kept in `config.h`.

### 10.4 Vial security

The migration removed the idea of relying on globally insecure Vial operation.

The keyboard keeps the explicit unlock combo and UID instead.

---

## 11. Header collision found by the modern build

The historical Cheapino tree had a keyboard-local file named:

```text
keyboards/cheapino/encoder.h
```

On the modern codebase this collided with QMK's own encoder header resolution.

The intermediate fix was to remove the obsolete Cheapino-local header and use an explicit declaration for the Cheapino helper needed by the matrix code.

The important lesson was broader than the specific fix:

```text
Do not keep historical local filenames when they shadow modern QMK core headers.
```

The final schuay/Bley-derived tree no longer needs the old split `encoder.c` / `encoder.h` arrangement at all; encoder handling lives with the modern keyboard implementation.

---

## 12. VIA on Vial-QMK: an important dead end

An intermediate attempt tried to keep a standalone `cheapino:via` target building inside Vial-QMK.

That was the wrong direction.

Modern Vial-QMK explicitly rejects compiling ordinary VIA-only keymaps unless Vial support is enabled. The relevant source contains an intentional guard equivalent to:

```c
#ifndef VIAL_ENABLE
#    error "Compiling VIA keymaps is not supported with the vial-qmk repo ..."
#endif
```

The correct architecture is therefore:

```text
Vial-QMK tree:
    cheapino:default
    cheapino:vial

upstream QMK tree, if/when needed separately:
    Cheapino VIA-only target
```

Temporary ideas to patch `dynamic_keymap.c` around this restriction were discarded. Generic Vial core was restored instead.

This distinction matters for future maintenance: a pure VIA target belongs on a QMK-based branch/repository, not by forcing Vial-QMK to act like upstream QMK.

---

## 13. Why the rebased Tompi tree was not kept as the final hardware implementation

The Tompi rebase successfully taught us what needed adaptation, and supported working `default`/`vial` builds after the modernization fixes.

However, deeper source archaeology showed that a cleaner modern Cheapino hardware implementation already existed.

Tompi issue #155 documents work by `schuay` to modernize the Cheapino implementation and, importantly, to make the encoder integration behave correctly with modern tap-hold processing.

The later Bley repository then combined that modern hardware implementation with a practical Vial setup.

Comparisons showed that Bley's top-level Cheapino implementation is largely the same modern hardware tree as schuay's Cheapino branch, including the modern:

- `cheapino.c` structure;
- `config.h` structure;
- `keyboard.json` data-driven configuration;
- `rules.mk` structure;
- matrix-intersection encoder model.

This made the final choice straightforward:

> Preserve the useful historical Tompi/Vial lineage in Git history, but use the newer schuay/Bley hardware implementation instead of maintaining a pile of compatibility patches on the old Tompi keyboard tree.

---

## 14. The encoder push layout bug and why the layout shape matters

A particularly important detail from the newer implementation is the physical encoder push key.

The Cheapino V2 layout is not just two 3x5+3 halves. There is an additional matrix position for the encoder push:

```text
matrix position: [3, 0]
```

In the modern Bley layout this position appears as the **sixth argument** in the `LAYOUT_split_3x5_3` ordering, between the left and right top rows.

This ordering is significant.

If the encoder push keycode is omitted or placed at the wrong argument position, keycodes after the left `T` position shift by one logical slot. This was one of the concrete fixes documented by the Bley encoder port.

The current `keyboard.json` therefore deliberately contains the `[3,0]` encoder-button position in the layout definition.

---

## 15. Matrix-intersection encoder model

Cheapino does not have enough dedicated conductors through the interconnect to treat the rotary encoder as a conventional pair of independent GPIO inputs.

The modern implementation therefore uses intersections of the keyboard matrix.

The current keyboard code:

1. scans the Cheapino matrix;
2. examines the matrix bits corresponding to encoder A/B state;
3. reconstructs rotation direction;
4. queues a normal QMK encoder event with `encoder_queue_event()`;
5. clears only the encoder A/B bits from the matrix row;
6. leaves the encoder push button bit intact so normal matrix/keymap handling processes it like a key.

This is an important improvement over the older approach where encoder actions were hard-coded per layer.

The encoder is now a QMK/Vial encoder source rather than a collection of hard-coded `tap_code()` calls.

Consequences:

- encoder CW/CCW can be mapped through Vial;
- encoder behavior participates in modern QMK event processing;
- the push button remains a real key position;
- the firmware does not need a generic core encoder patch.

---

## 16. Ghost suppression remains Cheapino-specific

The Cheapino hardware has known ghost patterns that are handled in firmware.

The current implementation retains the Cheapino-specific suppression logic rather than pretending the modern Vial migration makes the electrical behavior disappear.

The matrix path is conceptually:

```text
raw Cheapino matrix scan
        ↓
extract encoder intersection state
        ↓
Cheapino ghost suppression
        ↓
return matrix state to generic QMK processing
```

The migration therefore modernized the integration without deleting the board-specific behavior that exists for a hardware reason.

---

## 17. Final replacement with the modern Cheapino tree

After the Tompi rebase and compatibility investigation, the working branch replaced the historical Cheapino keyboard implementation with the modern Bley/schuay-derived tree.

That final consolidation is the current `main` tip:

```text
2420a17c22aeaf219a1dcd306468fddfd3e552dd
Modern Cheapino tree on clean modern vial baseline.
```

The parent of that commit is the end of the rebased Tompi historical series:

```text
ace4161e001481ae08fe7e1e6f97a9b614d93932
More usable default keymap
```

So the resulting history intentionally tells both stories:

```text
vial-kb/vial-qmk history
        ↓
dd43959                 selected modern Vial baseline
        ↓
rebased Tompi Cheapino/Vial historical commits
        ↓
ace4161                  end of historical Tompi series
        ↓
2420a17                  switch to the modern schuay/Bley Cheapino tree
```

This is preferable to an opaque snapshot because it preserves why the keyboard exists in its current form.

---

## 18. Current `main` configuration

At the time this document was written, the current Cheapino tree on `main` contains:

### Vial keymap features

`keyboards/cheapino/keymaps/vial/rules.mk`:

```make
VIAL_ENABLE = yes
VIA_ENABLE = yes
ENCODER_MAP_ENABLE = yes
ENCODER_ENABLE = yes
```

### Vial identity

```c
#define VIAL_KEYBOARD_UID {0x79, 0xED, 0x40, 0xBB, 0x09, 0x8B, 0xC1, 0x9E}
#define VIAL_UNLOCK_COMBO_ROWS { 6, 2 }
#define VIAL_UNLOCK_COMBO_COLS { 11, 5 }
```

### Dynamic layer count currently committed on `main`

```c
#define DYNAMIC_KEYMAP_LAYER_COUNT 10
```

This is worth stating explicitly because the historical Tompi line had previously been increased to 14 layers.

The first post-migration Vial layout-restore test exposed this difference: a saved configuration containing encoder data beyond layer 9 causes Vial to try to access an encoder layout entry for layer 10 while the current firmware only exposes layers 0–9.

Therefore:

```text
current main source: 10 dynamic layers
historical Tompi configuration: 14 dynamic layers
```

If compatibility with an existing 14-layer saved layout is required, increasing the current Vial keymap back to 14 is a separate explicit compatibility change. It should not be silently assumed to already be part of `main`.

### Tapping term in current keyboard metadata

The current modern `keyboard.json` carries:

```json
"tapping": {
    "term": 230
}
```

This is a source default. Runtime/Vial/QMK settings and later tap-hold tuning are separate topics.

---

## 19. Current matrix/debounce detail that should not be misremembered

One migration detail caused confusion during investigation, so it is recorded here explicitly.

The current Bley-derived Cheapino `matrix.c` on `main` calls:

```c
debounce_init(MATRIX_ROWS);
```

inside `matrix_init_custom()`.

The generic modern matrix code also owns the normal debounce lifecycle.

This call is part of the current source as imported from the Bley adaptation; this document does **not** claim that Bley converted the code to a no-argument `debounce_init()` form.

If the debounce initialization model is revisited later, it should be reviewed against the exact Vial/QMK API in the then-current baseline instead of relying on historical assumptions.

---

## 20. Local build validation

The modern source was built locally using the Nix-provided QMK/Arm toolchain.

Primary targets:

```fish
make cheapino:default
make cheapino:vial
```

The supported Vial-QMK architecture is these targets, not a forced `cheapino:via` target.

At one point the locally built Vial UF2 used for hardware testing had:

```text
sha256:
b359304c73eabf8e51449c1352c226535d38a26124e465485d6c19e3097b001d
```

`picotool info` recognized the file as an RP2040 UF2. The absence of an optional "Program Information" section was not treated as a build failure.

---

## 21. Rollback preparation before flashing

Before replacing the firmware on the physical keyboard, a full RP2040 flash backup was taken with `picotool`.

The useful command was:

```fish
picotool save -a ../backups/<timestamp>/current-full-flash.uf2
```

The tool reported saving the complete 4 MiB flash payload:

```text
4194304 bytes
```

This full-flash backup is the rollback artifact, including firmware and persistent flash contents.

A program-only `picotool save -p` attempt could not determine the installed program size, so the full-flash path was used instead.

The planned verification flow was:

```fish
sha256sum current-full-flash.uf2
picotool save -a -v current-full-flash-verified.uf2
sha256sum current-full-flash.uf2 current-full-flash-verified.uf2
```

The historical notes do not contain a captured result proving that the two hashes matched, so this document deliberately does not claim that duplicate-save equality was verified.

That distinction is intentional: successful backup and independently verified-identical backup are two different claims.

---

## 22. Flash and first hardware validation

The instrument used for flashing was `picotool` in RP2040 BOOTSEL mode.

Typical flow:

```fish
picotool load -v cheapino_vial.uf2
picotool reboot
```

Rollback flow:

```fish
picotool load -v ../backups/<timestamp>/current-full-flash.uf2
picotool reboot
```

The migrated firmware reached normal USB/Vial operation on the real Cheapino V2.

The hardware validation exercised the important board-specific paths:

- USB enumeration;
- keys on both halves;
- thumb keys;
- encoder push;
- encoder rotation in both directions;
- physical Vial unlock combo;
- Vial recognition of the keyboard UID/layout.

The subsequent Vial restore attempt then revealed the 10-vs-14 dynamic-layer compatibility issue described above. That was useful evidence: the migrated hardware path was alive far enough for Vial to enumerate the keyboard and operate on its dynamic keymap, while also exposing a real configuration-compatibility boundary that still needs to be treated explicitly.

---

## 23. What was gained by moving to the modern Vial baseline

The migration was not only source cleanup.

Moving from the historical Tompi Vial base to the selected modern Vial-QMK baseline brings in a large amount of newer QMK/Vial behavior.

Of particular interest for future Cheapino tuning:

### Chordal Hold

Modern QMK/Vial includes Chordal Hold, which can classify same-hand tap-hold rolls differently from plausible cross-hand modifier chords.

This is directly relevant to home-row modifiers and slow pinky behavior.

### Flow Tap

Modern QMK/Vial includes Flow Tap, which can settle eligible tap-hold keys as taps immediately during sufficiently fast typing sequences.

This can reduce both accidental modifier activation and apparent tap latency.

### Repeat / Alt Repeat

The modern Vial line includes Repeat Key and Alt Repeat Key support, including Vial-side dynamic support for Alt Repeat behavior.

### Modern encoder integration

The Cheapino rotary encoder now integrates through the current QMK encoder event path instead of maintaining historical hard-coded actions or generic core patches.

These features are capabilities of the new baseline. They are not automatically equivalent to "enabled and tuned for this keyboard". Tap-hold policy tuning is intentionally a separate activity.

---

## 24. What was deliberately *not* carried forward

The migration explicitly avoided several tempting but undesirable choices.

### No permanent overlay/wrapper architecture

The firmware repository is a real source tree, not a small wrapper that downloads the real source during every build.

### No resurrection of the old encoder core patch

Modern QMK already exposes the correct event queue mechanism.

### No generic `dynamic_keymap.c` hacks to force a VIA-only build

The Vial repository's intended architecture is respected.

### No claim of exact binary reproducibility without evidence

A successful source build is not the same as reproducing the exact historical UF2 hash.

### No assumption that every Bley setting is automatically preferable

The Bley/schuay tree was selected primarily for the modern hardware implementation and Vial integration. Configuration values such as USB identity, NKRO, LED brightness, dynamic layer count, and personal keymap choices must still be treated as explicit policy decisions.

---

## 25. Remaining compatibility / policy items

The current `main` branch is a modern, buildable hardware baseline, but it is not the end of all keyboard policy work.

Items intentionally left for separate changes include:

1. decide whether dynamic Vial layers should remain at 10 or return to 14 for saved-layout compatibility;
2. tune tap-hold behavior using the modern core rather than historical workarounds;
3. evaluate Chordal Hold and Flow Tap on the actual typing style;
4. decide whether rare modifiers such as GUI should remain on home-row/pinky tap-hold keys at all;
5. if a pure QMK/VIA target is desired, build that on a proper QMK line rather than forcing it into Vial-QMK;
6. pin a fully reproducible Nix development environment if exact toolchain reproducibility becomes a release requirement;
7. optionally document/review the duplicate debounce initialization in the current imported matrix implementation.

These are follow-up design decisions, not blockers to understanding the provenance of `main`.

---

## 26. Practical build summary

For the current Vial tree:

```fish
# enter a local tool environment
nix shell \
  nixpkgs#qmk \
  nixpkgs#gcc-arm-embedded \
  nixpkgs#gnumake \
  nixpkgs#git \
  --command fish

# supported builds
make cheapino:default
make cheapino:vial
```

Do not run `qmk setup` against this repository merely to build it; the repository itself is already the firmware source tree.

---

## 27. Short provenance summary

The migration can be reduced to the following chain:

```text
1. Existing .vial configuration / keyboard UID
        ↓
2. Identify Bley 8ec1... as a strong source match
        ↓
3. Prove Bley Cheapino can compile on modern Vial dd43959
        ↓
4. Discover and reconstruct Tompi's original Cheapino Vial lineage
        ↓
5. Rebase Tompi Cheapino commits from old Vial base 2772f52
   onto modern official Vial dd43959
        ↓
6. Resolve modern API incompatibilities without patching generic core
        ↓
7. Modernize metadata / encoder / RGB / Vial integration
        ↓
8. Discover VIA-only target does not belong in Vial-QMK
        ↓
9. Discover schuay/Bley already provide a cleaner modern Cheapino
   hardware implementation
        ↓
10. Replace the rebased historical keyboard tree with the modern
    schuay/Bley-derived Cheapino tree
        ↓
11. Keep the rebased Tompi lineage in history for provenance
        ↓
12. Build locally, back up full RP2040 flash, flash and validate hardware
        ↓
13. Current main: 2420a17
```

The important architectural result is that Cheapino-specific behavior now lives where it should: in the Cheapino keyboard implementation, on top of a modern, mostly unmodified Vial-QMK core.
