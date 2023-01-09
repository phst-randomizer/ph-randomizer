#include "_flags.h"
#include "ph.h"
#include "rando_settings.h"
#include <stdint.h>

static void set_flag(uint32_t addr, uint8_t bit) {
  *((uint8_t *)addr) |= bit;
}

static int strcmp(char *X, char *Y) {
  // TODO: replace with PH's native strcmp
  while (*X) {
    if (*X != *Y) {
      break;
    }

    // move to the next pair of characters
    X++;
    Y++;
  }

  return *(const unsigned char *)X - *(const unsigned char *)Y;
}

void set_initial_flags(uint32_t base_flag_address) {
  Flag *f = (Flag *)(0x23DF24C);

  while (1) {
    char *current = (char *)f;
    if (strcmp(current, "RANDOMIZER_DATA_END") == 0) {
      break;
    }

    if (f->setting_offset == -1 || setting_is_enabled((uint8_t)f->setting_offset, f->setting_bit)) {
      set_flag(base_flag_address + f->flag_offset, f->flag_bit);
    }

    f = (Flag *)(((uint32_t)f) + sizeof(*f));
  }
}
