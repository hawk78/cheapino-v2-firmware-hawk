.PHONY: bootstrap build clean distclean status

bootstrap:
	./scripts/bootstrap-vial-qmk.sh

build: bootstrap
	./scripts/build-firmware.sh

status:
	./scripts/status.sh

clean:
	rm -rf build

distclean: clean
	rm -rf .cache
