#pragma once
#include <stdbool.h>
#define ATOMIC_BLOCK_RESTORESTATE for (bool _atomic_once = true; _atomic_once; _atomic_once = false)
