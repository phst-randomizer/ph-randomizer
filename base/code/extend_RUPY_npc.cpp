#include "ph.hpp"

extern "C" {

u32 extend_RUPY_npc(u32 *addr) {
  u32 rupy_type = addr[0x56];
  switch (rupy_type) {
  case 3:
    return 9;
  case 4:
    return 0x1a;
  case 5:
    return 0x1b;
  case 6:
    return 0x81;
  case 7:
    return 0x82;
  default:
    // This allows the RUPY NPC to take the form of any item.
    // Given an item id `id`, set rupy_type to `id | 0x8000` to make the RUPY
    // NPC drop it.
    // For example, to drop a sword (id = 3), set rupy_type to 0x8003.
    if (rupy_type > 2 && rupy_type < 0xFFFF) {
      return rupy_type & 0x7FFF;
    }
    return 0xffffffff;
  }
}

} // extern "C"
