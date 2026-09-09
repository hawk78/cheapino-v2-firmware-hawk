#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="$(tr -d '[:space:]' < "$ROOT/QMK_CLI_IMAGE")"

if command -v podman >/dev/null 2>&1; then
    ENGINE=podman
    EXTRA=(--userns=keep-id)
elif command -v docker >/dev/null 2>&1; then
    ENGINE=docker
    EXTRA=()
else
    echo "missing container engine: install podman or docker" >&2
    exit 2
fi

mkdir -p "$ROOT/.cache" "$ROOT/build"

"$ENGINE" run --rm \
    "${EXTRA[@]}" \
    --entrypoint bash \
    -e HOME=/tmp/home \
    -v "$ROOT:/workspace" \
    -w /workspace \
    "$IMAGE" \
    -c '
set -euo pipefail
mkdir -p "$HOME"
git config --global --add safe.directory "*"

command -v qmk >/dev/null || {
    echo "qmk CLI missing from container PATH: $PATH" >&2
    exit 4
}
echo "qmk=$(command -v qmk)"
qmk --version

VIAL_PIN="$(tr -d "[:space:]" < VIAL_QMK_COMMIT)"
CHEAPINO_PIN="$(tr -d "[:space:]" < UPSTREAM_CHEAPINO_COMMIT)"
VIAL_DIR=.cache/vial-qmk

if [[ ! -d "$VIAL_DIR/.git" ]]; then
    rm -rf "$VIAL_DIR"
    git clone --no-checkout https://github.com/vial-kb/vial-qmk.git "$VIAL_DIR"
fi

if ! git -C "$VIAL_DIR" cat-file -e "${VIAL_PIN}^{commit}" 2>/dev/null; then
    git -C "$VIAL_DIR" fetch --depth=1 origin "$VIAL_PIN"
fi

git -C "$VIAL_DIR" checkout --detach --force "$VIAL_PIN"
git -C "$VIAL_DIR" submodule sync --recursive
git -C "$VIAL_DIR" submodule update --init --recursive --depth 1

rm -rf "$VIAL_DIR/keyboards/cheapino"
cp -a keyboard/cheapino "$VIAL_DIR/keyboards/cheapino"

make -C "$VIAL_DIR" cheapino:vial 2>&1 | tee build/build.log

UF2="$VIAL_DIR/cheapino_vial.uf2"
[[ -s "$UF2" ]] || UF2="$VIAL_DIR/.build/cheapino_vial.uf2"
[[ -s "$UF2" ]] || { echo "non-empty cheapino_vial.uf2 not found" >&2; exit 3; }
cp "$UF2" build/cheapino_vial.uf2

{
    echo "vial_qmk_commit=$VIAL_PIN"
    echo "cheapino_source_commit=$CHEAPINO_PIN"
    echo "qmk_cli_image=$(cat QMK_CLI_IMAGE)"
    echo "uf2_sha256=$(sha256sum build/cheapino_vial.uf2 | awk "{print \\$1}")"
    echo "uf2_bytes=$(wc -c < build/cheapino_vial.uf2 | tr -d " ")"
    echo "arm_gcc=$(arm-none-eabi-gcc --version | head -n1)"
    echo "git=$(git --version)"
} > build/build-manifest.txt

cat build/build-manifest.txt
'
