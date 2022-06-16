#include "rando_settings.h"

bool setting_is_enabled(uint8_t offset, uint8_t bit) {
  uint8_t *base_addr = (uint8_t *)RANDO_SETTINGS_BITMAP_ADDR;
  return (base_addr[offset] & bit) == bit;
}
