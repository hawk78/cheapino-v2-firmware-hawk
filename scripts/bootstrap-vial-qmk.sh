#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VIAL_DIR="$ROOT/.cache/vial-qmk"
VENV_DIR="$ROOT/.cache/venv"
PIN="$(tr -d '[:space:]' < "$ROOT/VIAL_QMK_COMMIT")"

for cmd in git python3; do
    command -v "$cmd" >/dev/null || { echo "missing required command: $cmd" >&2; exit 2; }
done

mkdir -p "$ROOT/.cache"

if [[ ! -d "$VIAL_DIR/.git" ]]; then
    rm -rf "$VIAL_DIR"
    mkdir -p "$VIAL_DIR"
    git -C "$VIAL_DIR" init
    git -C "$VIAL_DIR" remote add origin https://github.com/vial-kb/vial-qmk.git
fi

if ! git -C "$VIAL_DIR" cat-file -e "${PIN}^{commit}" 2>/dev/null; then
    git -C "$VIAL_DIR" fetch --depth=1 origin "$PIN"
fi

git -C "$VIAL_DIR" checkout --detach "$PIN"
git -C "$VIAL_DIR" submodule sync --recursive
git -C "$VIAL_DIR" submodule update --init --recursive --depth 1

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
    python3 -m venv "$VENV_DIR"
fi
"$VENV_DIR/bin/python" -m pip install --disable-pip-version-check -r "$VIAL_DIR/requirements.txt"

actual="$(git -C "$VIAL_DIR" rev-parse HEAD)"
[[ "$actual" == "$PIN" ]] || { echo "Vial-QMK pin mismatch: $actual != $PIN" >&2; exit 3; }

echo "Vial-QMK ready at $actual"
