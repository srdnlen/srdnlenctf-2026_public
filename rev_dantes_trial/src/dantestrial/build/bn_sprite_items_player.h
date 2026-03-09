#ifndef BN_SPRITE_ITEMS_PLAYER_H
#define BN_SPRITE_ITEMS_PLAYER_H

#include "bn_sprite_item.h"

//{{BLOCK(player_bn_gfx)

//======================================================================
//
//	player_bn_gfx, 32x32@8, 
//	+ palette 32 entries, not compressed
//	+ 16 tiles Metatiled by 4x4 not compressed
//	Total size: 64 + 1024 = 1088
//
//	Time-stamp: 2026-02-26, 15:54:27
//	Exported by Cearn's GBA Image Transmogrifier, v0.9.2
//	( http://www.coranac.com/projects/#grit )
//
//======================================================================

#ifndef GRIT_PLAYER_BN_GFX_H
#define GRIT_PLAYER_BN_GFX_H

#define player_bn_gfxTilesLen 1024
extern const bn::tile player_bn_gfxTiles[32];

#define player_bn_gfxPalLen 64
extern const bn::color player_bn_gfxPal[32];

#endif // GRIT_PLAYER_BN_GFX_H

//}}BLOCK(player_bn_gfx)

namespace bn::sprite_items
{
    constexpr inline sprite_item player(sprite_shape_size(sprite_shape::SQUARE, sprite_size::BIG), 
            sprite_tiles_item(span<const tile>(player_bn_gfxTiles, 32), bpp_mode::BPP_8, compression_type::NONE, 1), 
            sprite_palette_item(span<const color>(player_bn_gfxPal, 32), bpp_mode::BPP_8, compression_type::NONE));
}

#endif

