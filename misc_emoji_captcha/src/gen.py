import random
import json
import os

from PIL import Image, ImageDraw, ImageFont
from io import BytesIO


# --- Config ---
FONT_PATH = "AppleColorEmoji-160px.ttf"
FONT_SIZE = 160

assert os.path.exists(FONT_PATH), f"Font file not found at path: {FONT_PATH}"

FONT = ImageFont.truetype(FONT_PATH, FONT_SIZE, layout_engine=ImageFont.Layout.RAQM)

BOX_SIZE = 256
ROWS = 2
EMOJIS_PER_ROW = 4
TOTAL_EMOJIS = ROWS * EMOJIS_PER_ROW
BG_COLOR = (255, 255, 255)

EMOJI_POOL_PATH = "emojis_pool.json"

assert os.path.exists(EMOJI_POOL_PATH), f"Emoji pool file not found at path: {EMOJI_POOL_PATH}"

EMOJIS_POOL: list[dict[str, str]] = json.load(open(EMOJI_POOL_PATH, "r", encoding="utf-8"))



def create_emoji_box(emoji_char: str, font: ImageFont.ImageFont, size: int) -> Image.Image:
    box = Image.new("RGB", (size, size), BG_COLOR)

    temp_size = int(size * 1.5)
    temp_img = Image.new("RGBA", (temp_size, temp_size), (255, 255, 255, 0))
    draw_temp = ImageDraw.Draw(temp_img)

    bbox = draw_temp.textbbox((0, 0), emoji_char, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (temp_size - text_w) // 2 - bbox[0]
    y = (temp_size - text_h) // 2 - bbox[1]

    draw_temp.text((x, y), emoji_char, font=font, embedded_color=True)
    angle = random.uniform(0, 360)
    temp_img = temp_img.rotate(angle, resample=Image.BICUBIC, expand=False)

    paste_x = (size - temp_size) // 2
    paste_y = (size - temp_size) // 2

    box.paste(temp_img, (paste_x, paste_y), temp_img)
    return box



def generate_image(seed=None) -> tuple[bytes, str]:
    if seed is not None:
        random.seed(seed)
    else:
        random.seed()

    selected = random.sample(EMOJIS_POOL, TOTAL_EMOJIS)
    solution = " ".join(item["solution"] for item in selected)

    final_width = BOX_SIZE * EMOJIS_PER_ROW
    final_height = BOX_SIZE * ROWS
    final_image = Image.new("RGB", (final_width, final_height), BG_COLOR)

    emoji_idx = 0
    for row in range(ROWS):
        for col in range(EMOJIS_PER_ROW):
            item = selected[emoji_idx]
            box_img = create_emoji_box(item["char"], FONT, BOX_SIZE)

            paste_x = col * BOX_SIZE
            paste_y = row * BOX_SIZE

            final_image.paste(box_img, (paste_x, paste_y))
            emoji_idx += 1

    final_image_bytes = BytesIO()
    final_image.save(final_image_bytes, "PNG")
    final_image_bytes.seek(0)

    return final_image_bytes.getvalue(), solution



if __name__ == "__main__":
    generate_image()
