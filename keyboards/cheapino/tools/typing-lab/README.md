# Cheapino Typing Telemetry Lab

Minimal host tooling for the firmware telemetry protocol described in `BLUEPRINT.md`.

## Firmware

Telemetry is excluded from normal builds. Build an instrumented Vial image explicitly:

```sh
make cheapino:vial CHEAPINO_TELEMETRY_ENABLE=yes
```

The firmware is still runtime-disabled after boot. `START` arms capture; `STOP` disarms it. Events live only in a bounded RAM ring. When full, the newest event is dropped and a counter is incremented; host capture treats any drop as invalid by default.

## Host

Python 3.11+ is sufficient for protocol tests. Real keyboard access additionally needs `hidapi`:

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

That command compiles and executes both the ring buffer and the firmware command/hook layer against a small native QMK stub with strict warnings, runs protocol/client integration tests against a fake HID transport, and compile-checks all Python modules. It requires no keyboard and no ARM toolchain.

The dedicated GitHub Actions workflow runs the same native tests and then builds `cheapino:vial` with telemetry enabled inside the pinned QMK toolchain container. That full firmware build is the integration gate for real QMK hook signatures and RP2040/ChibiOS compilation.
