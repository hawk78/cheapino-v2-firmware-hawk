SRC += matrix.c

ifeq ($(strip $(CHEAPINO_TELEMETRY_ENABLE)), yes)
    SRC += features/telemetry/telemetry.c features/telemetry/ring.c
    OPT_DEFS += -DCHEAPINO_TELEMETRY_ENABLE
endif
