#include <stdint.h>

uint32_t get_npc_model_offset(uint32_t item_id) {
  // These values are offsets that are used to calculate the char* that contains
  // the name of the .bin
  //  file (see: Npc/ directory in the rom) of the NPC being spawned. The exact
  //  way it is used is:
  // char *npc = 20ddf40 + (<return_value> * 0xC)
  switch (item_id) {
  case 0x1: // key
    return 0xC;
  case 0x3: // oshus sword
    return 0xE3;
  }
  // TODO: calculate values for rest of items
}
