#include "flags.h"
#include "rando_settings.h"
#include <stdint.h>

static void set_flag(int addr, uint8_t bit) {
  *((uint8_t *)addr) |= bit;
}

void set_initial_flags(uint32_t base_flag_address) {
  if (setting_is_enabled(MERCAY_BRIDGE_REPAIRED_FROM_START)) {
    set_flag(base_flag_address + MERCAY_BRIDGE_REPAIRED);
  }
  // TODO: finish documenting/setting the rest of the needed flags
}
