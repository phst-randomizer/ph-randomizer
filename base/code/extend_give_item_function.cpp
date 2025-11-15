#include "ph.hpp"

extern "C" {

void extend_give_item_function(ItemManager *inventory, s32 item_id) {
  switch (item_id) {
  case 0x45: // phantom sword
    inventory->mItemFlags.flags[1] = inventory->mItemFlags.flags[1] | 0x20;
    break;
  }
}

} // extern "C"
