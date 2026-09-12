#!/usr/bin/env bash
set -euo pipefail

here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
firmware="$here/../../features/telemetry"
build="${TMPDIR:-/tmp}/cheapino-typing-lab-tests"
mkdir -p "$build"

cc -std=c11 -Wall -Wextra -Werror -pedantic \
  -DCHEAPINO_TELEMETRY_RING_CAPACITY=4 \
  -I"$firmware" \
  "$here/tests/test_ring.c" "$firmware/ring.c" \
  -o "$build/test_ring"
"$build/test_ring"

cc -std=c11 -Wall -Wextra -Werror -pedantic \
  -DCHEAPINO_TELEMETRY_RING_CAPACITY=16 \
  -I"$here/tests/firmware-stubs" -I"$firmware" \
  "$here/tests/test_telemetry.c" "$firmware/telemetry.c" "$firmware/ring.c" \
  -o "$build/test_telemetry"
"$build/test_telemetry"

PYTHONPATH="$here/src${PYTHONPATH:+:$PYTHONPATH}" \
  python3 -m unittest discover -s "$here/tests" -p 'test_*.py' -v

PYTHONPATH="$here/src${PYTHONPATH:+:$PYTHONPATH}" \
  python3 -m compileall -q "$here/src"
