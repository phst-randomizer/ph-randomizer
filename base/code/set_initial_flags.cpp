#include "ph.hpp"
#include "rando_settings.h"
#include <stdint.h>

extern "C" {

#define NO_SETTING -1, 0

typedef struct {
  uint16_t flag_offset;   // offset of the flag from the "base address" (see first
                          // arg of set_initial_flags() )
  uint8_t flag_bit;       // the bit within the value @ flag_offset that represents
                          // this flag
  int32_t setting_offset; // offset of the randomizer setting that this flag is
                          // gated behind, or -1 if it's not gated behind any
                          // settings. Make this a 32 bit uint to pad struct to
                          // 16 bytes
  uint8_t setting_bit;    // the bit within the value @ setting_offset that this
                          // represents this setting
} Flag;

/**

TODO: once the new overlay gets added and provides more space, re-enable these flags

 */

Flag flags[] = {
    /* Mercay Island */
    {0x28, 0x20, NO_SETTING}, // celia dialogue explaining how to open door in oshus sword cave
    {0x0, 0x2, NO_SETTING},   // celia dialogue after getting oshus sword
    {0x0, 0x4, NO_SETTING},   // completed oshus sword tutorial
    {0x0, 0x8, NO_SETTING},   // talked to mercay bartender about linebeck
    {0x0, 0x20, NO_SETTING},  // talked to oshus after seeing red chuchus
    {0x0, 0x40, NO_SETTING},  // showed linebeck the SW sea chart after ToTOK
    {0x0, 0x80, NO_SETTING},  // set sail for the first time (linebeck dialog)
    {0x20, 0x2, NO_SETTING},  // encountered sea trap for first time (linebeck dialog)
    {0x2, 0x2, MERCAY_BRIDGE_REPAIRED_FROM_START}, // mercay bridge repaired
    {0x18, 0x2, NO_SETTING},                       // talked to Oshus first time
    {0x2c, 0x1, NO_SETTING},                       // saw broken mercay bridge for first time
    {0x2, 0x4, NO_SETTING},                        // SS Linebeck admirer cutscene
    {0x18, 0x4, NO_SETTING},                       // 1st Linebeck trapped in ToTOK cutscene
    {0x9, 0x10, NO_SETTING},                       // 2nd Linebeck trapped in ToTOK cutscene
    {0x9, 0x20, NO_SETTING},                       // Linebeck warning about ToTOK sucking life
    {0x9, 0x40, NO_SETTING},                       // Linebeck escapes ToTOK after hitting switch

    {0x1c, 0x4, NO_SETTING}, // Linebeck introduction CS (after rescuing him)

    {0x1, 0x2, NO_SETTING}, // Got the SW sea chart

    {0x9, 0x80, NO_SETTING}, // Discovered Linebeck left ToTOK after getting SW Sea Chart

    {0x1f, 0x40, NO_SETTING}, // Rocks fell in Oshus's neighbor's yard (in vanilla, player gets a
                              // rupee if they pick them up)

    /* Isle of Ember */
    {0x8, 0x10, NO_SETTING}, // Arrived at Isle of Ember for first time
    {0x24, 0x1, NO_SETTING}, // Called out to Astrid after killing monsters in her basement
    {0x8, 0x1, NO_SETTING},  // Talked to Astrid after calling her with mic.
    {0x7, 0x80, NO_SETTING}, // Talked to Kayo's ghost
    {0x8, 0x8, NO_SETTING},  // Entered Astrid's basement after talking to Kayo
    {0x8, 0x20, NO_SETTING}, // After saving Astrid and agreeing to get your fortune told
                             // TODO: do we need this set?
    {0x8, 0x4, NO_SETTING},  // After getting fortune told by Astrid
                             // TODO: do we need this set?

    /* Molida Island */
    {0x3, 0x1, NO_SETTING}, // Romanos allows you into cave behind his house

    /* Uncharted Island */
    {0x26, 0x10, NO_SETTING}, // uncharted island bridge is extended

    /* Sea */
    {0x24, 0x20, NO_SETTING}, // blew dust off of NW sea chart
};

static void set_flag(uint32_t addr, uint8_t bit) {
  *((uint8_t *)addr) |= bit;
}

void set_initial_flags(uint32_t base_flag_address) {
  for (int i = 0; i < sizeof(flags) / sizeof(Flag); i++) {
    Flag f = flags[i];
    if (f.setting_offset == -1 || setting_is_enabled((uint8_t)f.setting_offset, f.setting_bit)) {
      set_flag(base_flag_address + f.flag_offset, f.flag_bit);
    }
  }
}

} // extern "C"
