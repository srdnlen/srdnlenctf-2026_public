import numpy as np
import requests
import json
import cv2
import os

from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont



def download_unicode_emoji_pool(url: str, save_path: str) -> list[dict[str, str]]:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        lines = response.text.splitlines()
    except requests.exceptions.RequestException as e:
        print(f"Error downloading emoji data: {e}")
        return []

    emoji_pool: list[dict[str, str]] = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "fully-qualified" not in line:
            continue

        if "E17.0" in line or "E18.0" in line:
            continue

        codepoints_str = line.split(";")[0].strip()
        hex_codes = codepoints_str.split()

        emoji_char = "".join(chr(int(h, 16)) for h in hex_codes)
        solution_format = "-".join(hex_codes)

        emoji_pool.append({"char": emoji_char, "solution": solution_format})

    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(emoji_pool, f, ensure_ascii=False, indent=4)

    return emoji_pool



def get_color_histogram(img_bgr: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    _, mask_inv = cv2.threshold(gray, 245, 255, cv2.THRESH_BINARY_INV)
    hist = cv2.calcHist([img_bgr], [0, 1, 2], mask_inv, [16, 16, 16], [0, 256, 0, 256, 0, 256])
    cv2.normalize(hist, hist, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
    return hist.flatten()



def align_and_crop(img_bgr: np.ndarray, canvas_size: int) -> np.ndarray:
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY_INV)
    coords = cv2.findNonZero(thresh)

    if coords is None:
        return np.full((canvas_size, canvas_size, 3), 255, dtype=np.uint8)

    x, y, w, h = cv2.boundingRect(coords)
    crop = img_bgr[y:y+h, x:x+w]

    canvas = np.full((canvas_size, canvas_size, 3), 255, dtype=np.uint8)
    if w > canvas_size or h > canvas_size:
        scale = canvas_size / max(w, h)
        new_w, new_h = int(w * scale), int(h * scale)
        crop = cv2.resize(crop, (new_w, new_h))
        w, h = new_w, new_h

    start_y = (canvas_size - h) // 2
    start_x = (canvas_size - w) // 2
    canvas[start_y:start_y+h, start_x:start_x+w] = crop
    return canvas



def rotate_image_cv2(image: np.ndarray, angle: float) -> np.ndarray:
    center = (image.shape[1] // 2, image.shape[0] // 2)
    rot_mat = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(image, rot_mat, image.shape[1::-1], flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(255,255,255))



def build_solver_cache(
    font_path: str,
    pool_path: str,
    font_size: int = 160,
    box_size: int = 256,
) -> tuple[list[str], np.ndarray, list[np.ndarray]]:
    if not os.path.exists(font_path):
        raise FileNotFoundError(f"Font not found: {font_path}")
    if not os.path.exists(pool_path):
        raise FileNotFoundError(f"Emoji pool file not found: {pool_path}")

    font = ImageFont.truetype(font_path, font_size, layout_engine=ImageFont.Layout.RAQM)
    with open(pool_path, "r", encoding="utf-8") as f:
        pool: list[dict[str, str]] = json.load(f)

    solutions: list[str] = []
    hist_matrix = np.zeros((len(pool), 16*16*16), dtype=np.float32)
    db_templates: list[np.ndarray] = []
    temp_size = int(box_size * 1.5)  # 384

    for idx, item in enumerate(pool):
        box = Image.new("RGB", (temp_size, temp_size), (255, 255, 255))
        draw = ImageDraw.Draw(box)
        bbox = draw.textbbox((0, 0), item["char"], font=font)

        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (temp_size - text_w) // 2 - bbox[0]
        y = (temp_size - text_h) // 2 - bbox[1]
        draw.text((x, y), item["char"], font=font, embedded_color=True)

        cv_img = cv2.cvtColor(np.array(box), cv2.COLOR_RGB2BGR)
        hist_matrix[idx] = get_color_histogram(cv_img)
        db_templates.append(align_and_crop(cv_img, 256))
        solutions.append(item["solution"])

    return solutions, hist_matrix, db_templates


def _process_single_box(
    args: tuple[int, np.ndarray, list[str], np.ndarray, list[np.ndarray], int, int]
) -> tuple[int, str | None]:
    pos_idx, target_box, solutions, hist_matrix, db_templates, top_k_color, coarse_step = args

    target_hist = get_color_histogram(target_box)
    diffs = np.sum((hist_matrix - target_hist) ** 2, axis=1)
    top_indices = np.argsort(diffs)[:top_k_color]

    target_padded = align_and_crop(target_box, 350)

    rotated_targets: dict[int, np.ndarray] = {}
    for angle in range(0, 360, coarse_step):
        rot = rotate_image_cv2(target_padded, angle)
        rotated_targets[angle] = align_and_crop(rot, 260)

    coarse_results: list[tuple[float, int, int, np.ndarray]] = []
    for idx in top_indices:
        template = db_templates[idx]
        best_c_err = float("inf")
        best_c_ang = 0

        for angle, rot_target in rotated_targets.items():
            res = cv2.matchTemplate(rot_target, template, cv2.TM_SQDIFF_NORMED)
            min_val = np.min(res)
            if min_val < best_c_err:
                best_c_err = min_val
                best_c_ang = angle

        coarse_results.append((best_c_err, best_c_ang, idx, template))

    coarse_results.sort(key=lambda x: x[0])
    top_2_coarse = coarse_results[:2]

    global_min_error = float("inf")
    best_match_code: str | None = None

    for coarse_err, coarse_ang, idx, template in top_2_coarse:
        candidate_code = solutions[idx]
        for offset in range(-(coarse_step-1), coarse_step):
            angle = (coarse_ang + offset) % 360
            if angle in rotated_targets:
                rot_target = rotated_targets[angle]
            else:
                rot = rotate_image_cv2(target_padded, angle)
                rot_target = align_and_crop(rot, 260)

            res = cv2.matchTemplate(rot_target, template, cv2.TM_SQDIFF_NORMED)
            min_val = np.min(res)

            if min_val < global_min_error:
                global_min_error = min_val
                best_match_code = candidate_code

    return pos_idx, best_match_code



def solve_captcha(
    image_data: bytes,
    cache_tuple: tuple[list[str], np.ndarray, list[np.ndarray]],
    rows: int = 2,
    cols: int = 4,
    box_size: int = 256,
    workers: int = 8,
) -> str:
    solutions_list, hist_matrix, db_templates = cache_tuple

    nparr = np.frombuffer(image_data, dtype=np.uint8)
    captcha_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    tasks: list[tuple[int, np.ndarray, list[str], np.ndarray, list[np.ndarray], int, int]] = []
    idx = 1
    for row in range(rows):
        for col in range(cols):
            x_start = col * box_size
            y_start = row * box_size
            target_box = captcha_img[y_start:y_start+box_size, x_start:x_start+box_size]

            tasks.append((idx, target_box, solutions_list, hist_matrix, db_templates, 12, 10))
            idx += 1

    results: list[tuple[int, str | None]] = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        for res in executor.map(_process_single_box, tasks):
            results.append(res)

    results.sort(key=lambda x: x[0])
    return " ".join(code for _, code in results)
