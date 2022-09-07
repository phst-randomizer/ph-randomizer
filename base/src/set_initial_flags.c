#include "flags.h"
#include "rando_settings.h"
#include <stdint.h>

static void set_flag(uint32_t addr, uint8_t bit) {
  *((uint8_t *)addr) |= bit;
}

void set_initial_flags(uint32_t base_flag_address) {
  if (setting_is_enabled(MERCAY_BRIDGE_REPAIRED_FROM_START)) {
    set_flag(base_flag_address + MERCAY_BRIDGE_REPAIRED);
  }

  set_flag(base_flag_address + TALKED_TO_OSHUS_FIRST_TIME);
  set_flag(base_flag_address + SAW_BROKEN_MERCAY_BRIDGE_FIRST_TIME);
  set_flag(base_flag_address + CELIA_TEXT_AFTER_GETTING_OSHUS_SWORD);
  set_flag(base_flag_address + COMPLETED_OSHUS_SWORD_TUTORIAL);
  set_flag(base_flag_address + TALKED_TO_BARTENDER_ABOUT_LINEBECK);
  set_flag(base_flag_address + TALKED_TO_OSHUS_AFTER_SEEING_RED_CHU_CHUS);
  set_flag(base_flag_address + SHOWED_LINEBECK_SW_SEA_CHART);
  set_flag(base_flag_address + SET_SAIL_FOR_THE_FIRST_TIME);
  set_flag(base_flag_address + UNCHARTED_ISLAND_BRIDGE_EXTENDED);
  // TODO: finish documenting/setting the rest of the needed flags
}
