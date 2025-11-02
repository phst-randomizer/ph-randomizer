#include "ph.hpp"
#include <stdint.h>

extern "C" {

void extend_give_item_function(ItemManager *inventory, int32_t item_id) {
  switch (item_id) {
  case 0x45: // phantom sword
    inventory->mItemFlags[1] = inventory->mItemFlags[1] | 0x20;
    break;
  }
}

} // extern "C"
