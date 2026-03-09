#include "bn_core.h"
#include "bn_keypad.h"
#include "bn_fixed.h"

#include "bn_sprite_ptr.h"
#include "bn_sprite_items_player.h"
#include "bn_sprite_items_gerione.h"

#include "bn_regular_bg_ptr.h"
#include "bn_regular_bg_items_arena.h"

#include "bn_sprite_text_generator.h"
#include "bn_sprite_font.h"
#include "bn_sprite_items_dialog_font.h"

#include "bn_vector.h"
#include "bn_string.h"
#include "bn_string_view.h"

#include "gerione.hpp"

namespace
{
    enum class mode
    {
        play,
        dialogue
    };

    constexpr char charset[] =
        " !\"#$%&'()*+,-./"
        "0123456789:;<=>?"
        "@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_"
        "`abcdefghijklmnopqrstuvwxyz{|}~";
    constexpr int charset_len = int(sizeof(charset)) - 1;


    bn::fixed clamp(bn::fixed v, bn::fixed lo, bn::fixed hi)
    {
        if(v < lo) return lo;
        if(v > hi) return hi;
        return v;
    }

    void clear_text(bn::vector<bn::sprite_ptr, 128>& text_sprites)
    {
        text_sprites.clear();
    }

    void draw_text(
        bn::sprite_text_generator& tg,
        bn::fixed x, bn::fixed y,
        const bn::string_view& str,
        bn::vector<bn::sprite_ptr, 128>& out)
    {
        tg.generate(x, y, str, out);
    }

    struct vm_ctx
    {
        const char* in = nullptr;
        int in_len = 0;
        int pos = 0;
        bn::string<256>* out = nullptr;
    };

    static void vm_putc(int ch, void* user)
    {
        auto* ctx = static_cast<vm_ctx*>(user);
        if(!ctx || !ctx->out) return;

        if(ctx->out->size() < ctx->out->max_size())
            ctx->out->push_back(char(ch & 0xFF));
    }

    static int vm_getc(void* user)
    {
        auto* ctx = static_cast<vm_ctx*>(user);
        if(!ctx || !ctx->in) return -1;

        if(ctx->pos < ctx->in_len)
            return int(static_cast<unsigned char>(ctx->in[ctx->pos++]));

        return -1; // EOF
    }

}

int main()
{
    bn::core::init();

    // constexpr const char default_vm_input[] = "W1H31l";
    // constexpr int default_vm_len = int(sizeof(default_vm_input)) - 1;

    bn::regular_bg_ptr bg = bn::regular_bg_items::arena.create_bg(0, 0);

    bn::sprite_ptr player = bn::sprite_items::player.create_sprite(-40, 0);
    bn::sprite_ptr gerione = bn::sprite_items::gerione.create_sprite(0, -40);

    bn::sprite_font font(bn::sprite_items::dialog_font);
    bn::sprite_text_generator text_gen(font);
    text_gen.set_center_alignment();

    bn::vector<bn::sprite_ptr, 128> ui_sprites;

    mode m = mode::play;

    int cursor = 0;
    bn::string<512> typed;

    const bn::fixed speed = 1;
    const bn::fixed half_w = 8;
    const bn::fixed half_h = 8;
    const bn::fixed min_x = -120 + half_w;
    const bn::fixed max_x =  120 - half_w;
    const bn::fixed min_y =  -80 + half_h;
    const bn::fixed max_y =   80 - half_h;

    bn::string<256> mb_output;

    while(true)
    {
        if(m == mode::play)
        {
            bn::fixed x = player.x();
            bn::fixed y = player.y();

            if(bn::keypad::left_held())  x -= speed;
            if(bn::keypad::right_held()) x += speed;
            if(bn::keypad::up_held())    y -= speed;
            if(bn::keypad::down_held())  y += speed;

            x = clamp(x, min_x, max_x);
            y = clamp(y, min_y, max_y);
            player.set_position(x, y);

            bn::fixed dx = player.x() - gerione.x();
            bn::fixed dy = player.y() - gerione.y();
            bn::fixed dist2 = dx * dx + dy * dy;

            constexpr bn::fixed interact_radius = 20;
            constexpr bn::fixed interact_radius2 = interact_radius * interact_radius;

            if(dist2 <= interact_radius2 && bn::keypad::a_pressed())
            {
                m = mode::dialogue;
                cursor = 0;
                mb_output.clear();

                typed.clear();
                
                /*
                for(int i = 0; i < default_vm_len && typed.size() < typed.max_size(); ++i)
                {
                    typed.push_back(default_vm_input[i]);
                }
                */
                
            }


            clear_text(ui_sprites);

            if(dist2 <= interact_radius2)
            {
                draw_text(text_gen, 0, 60, "Press A to interact", ui_sprites);
            }
        }
        else
        {
            // Dialogue controls:
            // LEFT/RIGHT: select character
            // A: add selected char
            // B: backspace
            // START: RUN (Enter)
            // SELECT: exit

            if(bn::keypad::left_pressed())
            {
                cursor = (cursor - 1 + charset_len) % charset_len;
            }
            if(bn::keypad::right_pressed())
            {
                cursor = (cursor + 1) % charset_len;
            }

            if(bn::keypad::a_pressed())
            {
                if(typed.size() < typed.max_size())
                {
                    typed.push_back(charset[cursor]);
                }
            }

            if(bn::keypad::b_pressed())
            {
                if(!typed.empty())
                {
                    typed.pop_back();
                }
            }

            if(bn::keypad::start_pressed())
            {
                mb_output.clear();

                vm_ctx ctx;
                ctx.in = typed.data();
                ctx.in_len = typed.size();
                ctx.pos = 0;
                ctx.out = &mb_output;

                const bool ok = dantes::romvm::run(
                    dantes::romvm::challenge_image(),
                    vm_putc,
                    vm_getc,
                    &ctx,
                    100000
                );

                if(!ok)
                {
                    if(mb_output.empty())
                        mb_output = "Thou art wrongeth.";
                }
                else if(mb_output.empty())
                {
                    mb_output = "...";
                }
            }


            if(bn::keypad::select_pressed())
            {
                m = mode::play;
                clear_text(ui_sprites);
                bn::core::update();
                continue;
            }

            clear_text(ui_sprites);

            draw_text(text_gen, 0, 16, "You say:", ui_sprites);
            bn::string<20> line;
            line.append(">");

            constexpr int max_tail = 19;

            int start = 0;
            if(typed.size() > max_tail)
            {
                start = typed.size() - max_tail;
            }

            for(int i = start; i < typed.size(); ++i)
            {
                line.push_back(typed[i]);
            }

            draw_text(text_gen, 0, 40, line, ui_sprites);
        
            bn::string<96> sel;
            sel.append("Select: [");
            sel.push_back(charset[cursor]);
            sel.append("]");
            draw_text(text_gen, 0, 56, sel, ui_sprites);

            // draw_text(text_gen, 0, 72, "L/R A:add B:del START:run SEL:exit", ui_sprites);

            if(!mb_output.empty())
            {
                bn::string<80> out_line;
                out_line.append("G. says: ");
                for(int i = 0; i < int(mb_output.size()) && out_line.size() < out_line.max_size(); ++i)
                {
                    char c = mb_output[i];
                    if(c < 32 || c > 126) c = '.';
                    out_line.push_back(c);
                }
                draw_text(text_gen, 0, 72, out_line, ui_sprites);
            }
        }

        bn::core::update();
    }
}
