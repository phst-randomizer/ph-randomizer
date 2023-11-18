#include <stdint.h>

// This header file contains definitions for functions, variables, struct
// definitions, etc that are present in the base game.

extern int memcmp(void *s1, void *s2, int size);
extern void strcat(char *dest, char *src);
extern int strcmp(char *s1, char *s2);
extern void strcpy(char *dest, char *src);
extern void strncpy(char *dest, char *src, int n);
extern int32_t strlen(char *s);
extern char *strrchr(char *s, int c);
extern char *strstr(char *haystack, char needle);

// TODO: verify this is correct. I'm not sure if this
// function is really an implementation of sprintf.
extern void sprintf(char *string, char *format);

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
