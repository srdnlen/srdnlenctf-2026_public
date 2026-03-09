#ifndef BN_REGULAR_BG_ITEMS_ARENA_H
#define BN_REGULAR_BG_ITEMS_ARENA_H

#include "bn_regular_bg_item.h"

//{{BLOCK(arena_bn_gfx)

//======================================================================
//
//	arena_bn_gfx, 256x256@8, 
//	+ palette 240 entries, not compressed
//	+ 412 tiles (t|f reduced) not compressed
//	+ regular map (flat), not compressed, 32x32 
//	Total size: 480 + 26368 + 2048 = 28896
//
//	Time-stamp: 2026-02-26, 15:54:27
//	Exported by Cearn's GBA Image Transmogrifier, v0.9.2
//	( http://www.coranac.com/projects/#grit )
//
//======================================================================

#ifndef GRIT_ARENA_BN_GFX_H
#define GRIT_ARENA_BN_GFX_H

#define arena_bn_gfxTilesLen 26368
extern const bn::tile arena_bn_gfxTiles[824];

#define arena_bn_gfxMapLen 2048
extern const bn::regular_bg_map_cell arena_bn_gfxMap[1024];

#define arena_bn_gfxPalLen 480
extern const bn::color arena_bn_gfxPal[240];

#endif // GRIT_ARENA_BN_GFX_H

//}}BLOCK(arena_bn_gfx)

namespace bn::regular_bg_items
{
    constexpr inline regular_bg_item arena(
            regular_bg_tiles_item(span<const tile>(arena_bn_gfxTiles, 824), bpp_mode::BPP_8, compression_type::NONE), 
            bg_palette_item(span<const color>(arena_bn_gfxPal, 240), bpp_mode::BPP_8, compression_type::NONE),
            regular_bg_map_item(arena_bn_gfxMap[0], size(32, 32), compression_type::NONE, 1, false));
}

#endif

