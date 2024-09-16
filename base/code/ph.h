#include <stdbool.h>
#include <stdint.h>

// This header file contains definitions for functions, variables, struct
// definitions, etc that are present in the base game.

extern void strcat(char *dest, char *src);
extern int strcmp(char *s1, char *s2);
extern int strncmp(char *s1, char *s2, int n);
extern void strcpy(char *dest, char *src);
extern void strncpy(char *dest, char *src, int n);
extern int32_t strlen(char *s);
extern char *strrchr(char *s, int c);
extern char *strstr(char *haystack, char needle);

// TODO: verify this is correct. I'm not sure if this
// function is really an implementation of sprintf.
extern void sprintf(char *string, char *format);

typedef struct {
  uint32_t id;
  void *baseAddr;
  int32_t textSize;
  int32_t bssSize;
  int32_t sinitStart;
  int32_t sinitEnd;
  int32_t fileId;
  int32_t fileSize;
} Overlay;

extern bool LoadOverlay(Overlay *overlay);

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

extern char *got_new_item_model_path_prefix;
extern char *item_id_to_string[];

typedef struct {
  int32_t mEquippedItem;
  int32_t mPrevEquippedItem;
  int32_t mForcedItem; // game crashes when any item besides this one is equipped
  uint32_t mHourglassSandFrames;
  int32_t mEquippedFairy;
  void *mFairies[3];
  uint16_t mEquipLoadTimer;
  uint16_t mNumRupees;
  uint8_t mNumGems[3];
  uint8_t mUnk_027; // padding?
  uint32_t mEquippedShipParts[8];
  int8_t mShipParts[8][9];
  int8_t mTreasure[8];
  uint8_t mUnk_098[6];  // max 99
  uint16_t mUnk_09e[6]; // max 9999, corresponds with mUnk_098
  uint16_t mUnk_0aa;    // padding?
  void *(*mEquipItems)[11];
  uint16_t (*mAmmo)[11];
  uint16_t mQuiverSize;
  uint16_t mBombBagSize;
  uint16_t mBombchuBagSize;
  uint16_t mUnk_0ba; // only between 0 and 9
  uint8_t mPotions[2];
  uint8_t mUnk_0be[2]; // padding?
  void *mItemModels[16];
  void *mDungeonItemModels[5]; // non-null in dungeons/caves
  void *mModelRender;
  int32_t mFanfareItemId;
  uint32_t mFanfareSfx;
  void *mFanfareItemModel;
  void *mUnk_124;
  uint32_t mItemFlags[4];
  uint32_t mSalvagedTreasureFlags;
  uint32_t mShipPartPricesShown[3];
  uint32_t mTreasurePriceShownFlag;
  bool mMuteNextFanfare;
  uint8_t mUnk_14d;
  uint8_t mUnk_14e[0x2]; // padding?
} ItemManager;

extern ItemManager *gItemManager;
extern void GiveItem(ItemManager *inventory, int32_t itemId);

typedef struct {
  uint16_t mMaxHealth;
  uint16_t mHealth;
  int16_t mMaxShipHealth;
  int16_t mShipHealth;
  uint16_t mSalvageArmHealth;
  int16_t mFlags;
  uint16_t mUnk_0c;
  uint8_t mUnk_0e;
  uint8_t mUnk_0f;
} HealthManager;

extern HealthManager *gHealthManager;
