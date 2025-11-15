#include "rando_settings.h"

extern "C" {

bool setting_is_enabled(u8 offset, u8 bit) {
  u8 *base_addr = (u8 *)RANDO_SETTINGS_BITMAP_ADDR;
  return (base_addr[offset] & bit) == bit;
}

} // extern "C"
