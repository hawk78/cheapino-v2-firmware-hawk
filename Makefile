.PHONY: build build-native bootstrap clean distclean status

build:
	./scripts/build-container.sh

bootstrap:
	./scripts/bootstrap-vial-qmk.sh

build-native: bootstrap
	./scripts/build-firmware.sh

status:
	./scripts/status.sh

clean:
	rm -rf build

distclean: clean
	rm -rf .cache
