#ifndef BN_SPRITE_ITEMS_GERIONE_H
#define BN_SPRITE_ITEMS_GERIONE_H

#include "bn_sprite_item.h"

//{{BLOCK(gerione_bn_gfx)

//======================================================================
//
//	gerione_bn_gfx, 64x64@4, 
//	+ palette 16 entries, not compressed
//	+ 64 tiles Metatiled by 8x8 not compressed
//	Total size: 32 + 2048 = 2080
//
//	Time-stamp: 2026-02-26, 15:54:27
//	Exported by Cearn's GBA Image Transmogrifier, v0.9.2
//	( http://www.coranac.com/projects/#grit )
//
//======================================================================

#ifndef GRIT_GERIONE_BN_GFX_H
#define GRIT_GERIONE_BN_GFX_H

#define gerione_bn_gfxTilesLen 2048
extern const bn::tile gerione_bn_gfxTiles[64];

#define gerione_bn_gfxPalLen 32
extern const bn::color gerione_bn_gfxPal[16];

#endif // GRIT_GERIONE_BN_GFX_H

//}}BLOCK(gerione_bn_gfx)

namespace bn::sprite_items
{
    constexpr inline sprite_item gerione(sprite_shape_size(sprite_shape::SQUARE, sprite_size::HUGE), 
            sprite_tiles_item(span<const tile>(gerione_bn_gfxTiles, 64), bpp_mode::BPP_4, compression_type::NONE, 1), 
            sprite_palette_item(span<const color>(gerione_bn_gfxPal, 16), bpp_mode::BPP_4, compression_type::NONE));
}

#endif

