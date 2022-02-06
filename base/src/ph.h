#include <stdint.h>

typedef struct {
  uint32_t npc_id;
  uint32_t (*spawn_function)(void);
  uint32_t unknown1;
  uint32_t unknown2;
  struct NPC *next;
} NPC;

// searches the list of NPC structs in memory for the given NPC and returns its
// address.
extern NPC *get_npc_address(uint32_t npc_id); // 203e824
