#include "ph.h"
#include <stdbool.h>
#include <stdint.h>

__attribute__((target("thumb"))) void set_starting_items(void) {
  gItemManager->mItemFlags[1] |= 0x2; // start player with SW sea chart
}
