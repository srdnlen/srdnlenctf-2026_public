#ifndef BN_SPRITE_ITEMS_DIALOG_FONT_H
#define BN_SPRITE_ITEMS_DIALOG_FONT_H

#include "bn_sprite_item.h"

//{{BLOCK(dialog_font_bn_gfx)

//======================================================================
//
//	dialog_font_bn_gfx, 8x880@4, 
//	+ palette 16 entries, not compressed
//	+ 110 tiles not compressed
//	Total size: 32 + 3520 = 3552
//
//	Time-stamp: 2026-02-26, 15:54:27
//	Exported by Cearn's GBA Image Transmogrifier, v0.9.2
//	( http://www.coranac.com/projects/#grit )
//
//======================================================================

#ifndef GRIT_DIALOG_FONT_BN_GFX_H
#define GRIT_DIALOG_FONT_BN_GFX_H

#define dialog_font_bn_gfxTilesLen 3520
extern const bn::tile dialog_font_bn_gfxTiles[110];

#define dialog_font_bn_gfxPalLen 32
extern const bn::color dialog_font_bn_gfxPal[16];

#endif // GRIT_DIALOG_FONT_BN_GFX_H

//}}BLOCK(dialog_font_bn_gfx)

namespace bn::sprite_items
{
    constexpr inline sprite_item dialog_font(sprite_shape_size(sprite_shape::SQUARE, sprite_size::SMALL), 
            sprite_tiles_item(span<const tile>(dialog_font_bn_gfxTiles, 110), bpp_mode::BPP_4, compression_type::NONE, 110), 
            sprite_palette_item(span<const color>(dialog_font_bn_gfxPal, 16), bpp_mode::BPP_4, compression_type::NONE));
}

#endif

