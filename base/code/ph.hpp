#ifndef PH_RANDOMIZER_H
#define PH_RANDOMIZER_H

#ifdef __cplusplus
extern "C" {
#endif
#include "types.h"
#include "string.h"
#ifdef __cplusplus
}
#endif

#include "Actor/ActorType.hpp"
#include "Item/ItemManager.hpp"
#include "Player/PlayerManager.hpp"

// This header file contains definitions for functions, variables, struct
// definitions, etc that are present in the base game.

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
  u32 id;
  void *baseAddr;
  s32 textSize;
  s32 bssSize;
  s32 sinitStart;
  s32 sinitEnd;
  s32 fileId;
  s32 fileSize;
} Overlay;

extern bool LoadOverlay(Overlay *overlay);

extern char *got_new_item_model_path_prefix;
extern char *item_id_to_string[];

#ifdef __cplusplus
}
#endif

#endif // PH_RANDOMIZER_H
