#include <stdbool.h>
#include <stdint.h>

// RAM address of bitmap encoding randomizer settings
#define RANDO_SETTINGS_BITMAP_ADDR 0x2058180

/**
 * Check if the randomizer setting represented by the given offset/bit is
 * enabled.
 *
 * @param offset Offset from RANDO_SETTINGS_BITMAP_ADDR of the byte containing
 * the setting bit
 * @param bit The bit representing the setting within the
 * `RANDO_SETTINGS_BITMAP_ADDR[offset]` byte
 * @return true if setting is enabled, false if it is disabled
 */
bool setting_is_enabled(uint8_t offset, uint8_t bit);
