#include <stdint.h>

#define MAX_HEALTH_ADDR 0x021BA348
#define CURRENT_HEALTH_ADDR 0x021BA34A
#define PLAYER_HEALTH_PTR_ADDR 0x2146470

void custom_salvage_item(uint32_t item_id_with_flag) {
  uint16_t item_id = item_id_with_flag & 0x7FFF; // Unset the most significant bit

  if (item_id == 0xA) { // Check if the item is a heart container
    uint8_t *max_health_ptr = (uint8_t *)MAX_HEALTH_ADDR;
    uint8_t *current_health_ptr = (uint8_t *)CURRENT_HEALTH_ADDR;

    uint8_t max_health = *max_health_ptr;
    max_health += 4; // Increment max health by 4 (one heart container)

    *max_health_ptr = max_health;     // Update the max health
    *current_health_ptr = max_health; // Restore the player's health to the new maximum
  }

  uint32_t *player_health_ptr = (uint32_t *)PLAYER_HEALTH_PTR_ADDR;
  uint32_t player_data = *player_health_ptr;
  *((uint16_t *)(player_data + 0xEC)) = item_id; // Store the item ID in the specified offset
}
