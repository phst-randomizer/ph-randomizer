#include "ph.hpp"

#define MAX_HEALTH_ADDR 0x021BA348
#define CURRENT_HEALTH_ADDR 0x021BA34A
#define PLAYER_HEALTH_PTR_ADDR 0x2146470

extern "C" {

void custom_salvage_item(u32 item_id_with_flag) {
  u16 item_id = item_id_with_flag & 0x7FFF; // Unset the most significant bit

  // The salvage arm "get item" code doesn't properly set memory values for items
  // that it was never intended to give, so we need to manually set them here.
  switch (item_id) {
  case 0xA:                          // heart container
    gPlayerManager->mMaxHealth += 4; // Increment max health by 4 (one heart container)
    gPlayerManager->mHealth =
        gPlayerManager->mMaxHealth; // Restore the player's health to the new maximum
    break;
  case 0x45: // phantom sword
    gItemManager->mItemFlags.flags[1] = gItemManager->mItemFlags.flags[1] | 0x20;
    break;
  }

  u32 *player_health_ptr = (u32 *)PLAYER_HEALTH_PTR_ADDR;
  u32 player_data = *player_health_ptr;
  *((u16 *)(player_data + 0xEC)) = item_id; // Store the item ID in the specified offset
}

} // extern "C"
