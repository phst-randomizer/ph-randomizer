#include "flags.h"
#include <stdint.h>

void set_flag(int addr, uint8_t bit) {
  uint32_t mask = 0xFFFFFFFF & (1 << bit);
  *((uint32_t *)addr) |= mask;
}

void set_initial_flags(uint32_t base_flag_address) {
  set_flag(base_flag_address + MERCAY_BRIDGE_REPAIRED);
  // TODO: finish documenting/setting the rest of the needed flags
}
