#include "ph.h"
#include <stdint.h>

#define MAX_HEALTH_ADDR 0x021BA348
#define CURRENT_HEALTH_ADDR 0x021BA34A
#define PLAYER_HEALTH_PTR_ADDR 0x2146470

void custom_salvage_item(uint32_t item_id_with_flag) {
  uint16_t item_id = item_id_with_flag & 0x7FFF; // Unset the most significant bit

  // The salvage arm "get item" code doesn't properly set memory values for items
  // that it was never intended to give, so we need to manually set them here.
  switch (item_id) {
  case 0xA:                          // heart container
    gHealthManager->mMaxHealth += 4; // Increment max health by 4 (one heart container)
    gHealthManager->mHealth =
        gHealthManager->mMaxHealth; // Restore the player's health to the new maximum
    break;
  case 0x45: // phantom sword
    gItemManager->mItemFlags[1] = gItemManager->mItemFlags[1] | 0x20;
    break;
  }

  uint32_t *player_health_ptr = (uint32_t *)PLAYER_HEALTH_PTR_ADDR;
  uint32_t player_data = *player_health_ptr;
  *((uint16_t *)(player_data + 0xEC)) = item_id; // Store the item ID in the specified offset
}
