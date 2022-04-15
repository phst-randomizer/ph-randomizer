#include "ph.h"
#include <stdint.h>

uint32_t execute_npc_spawner(void *param_1, uint32_t npc_id) {
  NPC *npc = get_npc_address(npc_id);
  if (npc != 0x0) {
    return npc->spawn_function();
  }
  return 0;
}
