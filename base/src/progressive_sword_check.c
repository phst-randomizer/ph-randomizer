#include <stdbool.h>
#include <stdint.h>

#define OSHUS_SWORD_FLAG_OFFSET (0x128)
#define OSHUS_SWORD_FLAG_BIT (0x1)
#define PHANTOM_SWORD_FLAG_OFFSET (0x12C)
#define PHANTOM_SWORD_FLAG_BIT (0x20)

__attribute__((target("thumb"))) void
progressive_sword_check(const uint32_t base_address) {
  // Address of oshus sword flag
  uint8_t *oshus_sword = (uint8_t *)(base_address + OSHUS_SWORD_FLAG_OFFSET);

  // Address of phantom sword flag
  uint8_t *phantom_sword =
      (uint8_t *)(base_address + PHANTOM_SWORD_FLAG_OFFSET);

  // Check if player has the oshus sword
  bool has_oshus_sword =
      (*oshus_sword & OSHUS_SWORD_FLAG_BIT) == OSHUS_SWORD_FLAG_BIT;

  // If the player has the oshus sword already, give them the phantom sword.
  // Otherwise, give them the oshus sword
  if (has_oshus_sword) {
    *phantom_sword |= PHANTOM_SWORD_FLAG_BIT;
  } else {
    *oshus_sword |= OSHUS_SWORD_FLAG_BIT;
  }
}
