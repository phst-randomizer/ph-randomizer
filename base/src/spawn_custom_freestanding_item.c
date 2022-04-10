#include <stdint.h>

#define RUPY 0x52555059

/**
 * @param param_1 - original function arg, don't modify
 * @param npc_type - 4 character string representing NPC type.
 * @param param_3 - original function arg, don't modify
 * @param param_4 - original function arg, don't modify
 */
uint16_t spawn_custom_freestanding_item(void *param_1, uint32_t npc_type,
                                        void *param_3, uint16_t *param_4) {
  // declare pointer to the game's `spawn_npc` function
  uint16_t (*spawn_npc)(void *, uint32_t, void *, uint16_t *) =
      (void *)0x20C3FE8;

  uint16_t *item_id_address;
  // pull the base address of the NPCA entry's item_id off of the stack
  asm volatile("ldr %0, [sp, #0x4]" : "=r"(item_id_address) :);

  // get the item id
  uint16_t item_id = item_id_address[0x10];

  // if item_id is 0x1, continue as the vanilla game does.
  if (item_id == 0x1) {
    return (*spawn_npc)(param_1, npc_type, param_3, param_4);
  }
  // Otherwise, set rupy_type to the item_id and spawn a RUPY NPC:
  // (see `extend_RUPY_npc.c` to see how this value is used)
  *param_4 = item_id;
  return (*spawn_npc)(param_1, RUPY, param_3, param_4);
}
