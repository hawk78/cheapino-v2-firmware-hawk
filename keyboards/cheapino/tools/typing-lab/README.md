# Cheapino Typing Telemetry Lab

Minimal host tooling for the firmware telemetry protocol described in `BLUEPRINT.md`.

## Firmware

Telemetry is excluded from normal builds. Build an instrumented Vial image explicitly:

```sh
make cheapino:vial CHEAPINO_TELEMETRY_ENABLE=yes
```

The firmware is still runtime-disabled after boot. `START` arms capture; `STOP` disarms it. Events live only in a bounded RAM ring. When full, the newest event is dropped and a counter is incremented; host capture treats any drop as invalid by default.

## Host

Python 3.9+ is sufficient for protocol tests and the CLI. Real keyboard access additionally needs `hidapi`:

```sh
python -m pip install -e '.[hid]'
cheapino-typing-lab doctor
cheapino-typing-lab info
cheapino-typing-lab status
cheapino-typing-lab capture --seconds 30 --output capture.jsonl
```

Do not run Vial at the same time as the lab tool: they share the Raw HID interface.

## Automated tests

From this directory:

```sh
./run-tests.sh
```

That command compiles and executes the ring buffer and firmware command/hook layer against a small native QMK stub with strict warnings. It also builds a native firmware bridge that runs the real `telemetry.c`/`ring.c` implementation behind a 32-byte stdin/stdout transport; the Python `TelemetryClient` is exercised against that process, so C/Python wire-format drift is caught without a keyboard. The remaining protocol, HID-discovery and client tests run against focused fakes, all Python modules are compile-checked, and the CLI entry point gets a smoke test.

The dedicated GitHub Actions workflow runs those native tests and then builds `cheapino:vial` with telemetry enabled inside the pinned QMK toolchain container. That full firmware build is the integration gate for real QMK hook signatures and RP2040/ChibiOS compilation.

An RP2040 emulator is intentionally not part of the default gate: at this stage it would mostly re-run code already covered by the native bridge while still not reproducing the physical matrix or USB timing of a real Cheapino. Hardware-in-the-loop Raw HID testing remains the only useful next layer for device-specific behavior.
