#include <stdint.h>

void faster_boat() {
  uint32_t boat_speed_offset = (*(uint32_t *)(0x20EE4B4) + 0xF7FFF5B4);

  uint32_t *boat_speed = (uint32_t *)(0x8000000 + boat_speed_offset);

  // Increase boat speed if R button is pressed and the current speed is less
  // than max speed
  if (((*((uint16_t *)0x4000130) >> 8) & 1) == 0 && *boat_speed < 0x540) {
    *boat_speed += 0x20;
  }

  // Decrease boat speed if L button is pressed and the current speed is greater
  // than zero
  if (((*((uint16_t *)0x4000130) >> 9) & 1) == 0 && *boat_speed > 0) {
    *boat_speed -= 0x20;
  }

  if (*boat_speed < 0) {
    *boat_speed = 0;
  }
  return;
}
