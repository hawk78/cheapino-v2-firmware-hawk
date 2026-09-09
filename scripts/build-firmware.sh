#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VIAL_DIR="$ROOT/.cache/vial-qmk"
VENV_DIR="$ROOT/.cache/venv"
OUT_DIR="$ROOT/build"
PIN="$(tr -d '[:space:]' < "$ROOT/VIAL_QMK_COMMIT")"
CHEAPINO_PIN="$(tr -d '[:space:]' < "$ROOT/UPSTREAM_CHEAPINO_COMMIT")"

for cmd in make arm-none-eabi-gcc sha256sum git; do
    command -v "$cmd" >/dev/null || { echo "missing required command: $cmd" >&2; exit 2; }
done

[[ -d "$VIAL_DIR/.git" ]] || { echo "run make bootstrap first" >&2; exit 2; }
[[ "$(git -C "$VIAL_DIR" rev-parse HEAD)" == "$PIN" ]] || { echo "Vial-QMK checkout is not at the pinned commit" >&2; exit 3; }

rm -rf "$VIAL_DIR/keyboards/cheapino"
cp -a "$ROOT/keyboard/cheapino" "$VIAL_DIR/keyboards/cheapino"

export PATH="$VENV_DIR/bin:$PATH"
make -C "$VIAL_DIR" cheapino:vial

mkdir -p "$OUT_DIR"
uf2=""
for candidate in \
    "$VIAL_DIR/cheapino_vial.uf2" \
    "$VIAL_DIR/.build/cheapino_vial.uf2"; do
    if [[ -f "$candidate" ]]; then
        uf2="$candidate"
        break
    fi
done
if [[ -z "$uf2" ]]; then
    uf2="$(find "$VIAL_DIR" -maxdepth 2 -type f -name '*cheapino*vial*.uf2' -print -quit)"
fi
[[ -n "$uf2" && -s "$uf2" ]] || { echo "build succeeded but no non-empty Cheapino Vial UF2 was found" >&2; exit 4; }

cp "$uf2" "$OUT_DIR/cheapino_vial.uf2"
{
    echo "vial_qmk_commit=$PIN"
    echo "cheapino_source_commit=$CHEAPINO_PIN"
    echo "uf2_sha256=$(sha256sum "$OUT_DIR/cheapino_vial.uf2" | awk '{print $1}')"
    echo "uf2_bytes=$(wc -c < "$OUT_DIR/cheapino_vial.uf2" | tr -d ' ')"
    echo "arm_gcc=$(arm-none-eabi-gcc --version | head -n1)"
    echo "python=$($VENV_DIR/bin/python --version 2>&1)"
    echo "make=$(make --version | head -n1)"
} > "$OUT_DIR/build-manifest.txt"

cat "$OUT_DIR/build-manifest.txt"
echo "UF2: $OUT_DIR/cheapino_vial.uf2"
