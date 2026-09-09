#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
printf 'Cheapino source pin: %s\n' "$(tr -d '[:space:]' < "$ROOT/UPSTREAM_CHEAPINO_COMMIT")"
printf 'Vial-QMK pin:       %s\n' "$(tr -d '[:space:]' < "$ROOT/VIAL_QMK_COMMIT")"
if [[ -d "$ROOT/.cache/vial-qmk/.git" ]]; then
    printf 'Local Vial-QMK:     %s\n' "$(git -C "$ROOT/.cache/vial-qmk" rev-parse HEAD)"
else
    echo 'Local Vial-QMK:     not bootstrapped'
fi
if [[ -f "$ROOT/build/build-manifest.txt" ]]; then
    echo
    cat "$ROOT/build/build-manifest.txt"
fi
