#include <stdbool.h>
#include <stdint.h>

#define OSHUS_SWORD_FLAG_OFFSET (0x21BA604)
#define OSHUS_SWORD_FLAG_BIT (0x1)
#define PHANTOM_SWORD_BLADE_FLAG_OFFSET (0x21B5550)
#define PHANTOM_SWORD_BLADE_FLAG_BIT (0x20)
#define PHANTOM_SWORD_FLAG_OFFSET (0x21BA608)
#define PHANTOM_SWORD_FLAG_BIT (0x20)

__attribute__((target("thumb"))) void progressive_sword_check() {
  // Address of oshus sword flag
  uint8_t *oshus_sword = (uint8_t *)(OSHUS_SWORD_FLAG_OFFSET);

  // Address of phantom sword blade flag
  uint8_t *phantom_sword_blade = (uint8_t *)(PHANTOM_SWORD_BLADE_FLAG_OFFSET);

  // Address of phantom sword flag
  uint8_t *phantom_sword = (uint8_t *)(PHANTOM_SWORD_FLAG_OFFSET);

  // Check if player has the oshus sword
  bool has_oshus_sword = (*oshus_sword & OSHUS_SWORD_FLAG_BIT) == OSHUS_SWORD_FLAG_BIT;

  bool has_phantom_sword_blade =
      (*phantom_sword_blade & PHANTOM_SWORD_BLADE_FLAG_BIT) == PHANTOM_SWORD_BLADE_FLAG_BIT;

  // If the player has the oshus sword already, give them the phantom sword blade.
  // If they have the phantom sword blade already, give them the phantom sword.
  // Otherwise, give them the oshus sword.
  if (has_oshus_sword && has_phantom_sword_blade) {
    *phantom_sword |= PHANTOM_SWORD_FLAG_BIT;
  } else if (has_oshus_sword) {
    *phantom_sword_blade |= PHANTOM_SWORD_BLADE_FLAG_BIT;
  } else {
    *oshus_sword |= OSHUS_SWORD_FLAG_BIT;
  }
}
