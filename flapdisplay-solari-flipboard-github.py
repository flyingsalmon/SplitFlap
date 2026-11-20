"""
Split Flap or Solari Board Simulation
A Nostalgic Departure Board in Python

Renders a two-row split-flap departure board:
- Top row: destination and departure time
- Bottom row: track number ("TRK NN") and status (e.g., "BOARDING")

Exports an .mp4 video with optional synchronized sound.
Requires: pip install pillow moviepy numpy

Sound attribution:
Sound Effect by freesound_community from Pixabay

Author: Tony Rahman
Website: https://flyingsalmon.net

Copyright (c) 2026 Tony Rahman
This project was created for educational purposes.

Blog: https://flyingsalmon.net/building-a-nostalgic-split-flap-departure-board/

"""

import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import AudioFileClip, ImageSequenceClip

# --- Configuration ---
DEST_TEXT = "PADDINGTON"
TIME_TEXT = "08:15"
TRACK_NUM = "03"
STATUS_TEXT = "BOARDING"

AUDIO_FILE = "SplitFlag-SolariBoard-1shortBurst.mp3"  # Set to None for silent video
OUTPUT_FILE = "departure_board.mp4"

COLS = 20
FPS = 30
FLAP_W, FLAP_H = 56, 84
GAP = 8
ROW_GAP = 20
PAD_X, PAD_Y = 36, 40

# Warm vintage amber/cream palette
BG_COLOR = (18, 16, 13)
PANEL_COLOR = (36, 33, 28)
BORDER_COLOR = (64, 57, 46)
TEXT_COLOR = (255, 224, 168)
SPLIT_LINE_COLOR = (12, 10, 8)
FOLD_SHADE_COLOR = (26, 23, 18)

CHARSET = list(" ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789:")


def get_font(size):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "/System/Library/Fonts/Menlo.ttc",
        "C:\\Windows\\Fonts\\consolab.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def render_single_flap(char, font, fold_progress=0.0):
    cell = Image.new("RGB", (FLAP_W, FLAP_H), PANEL_COLOR)
    draw = ImageDraw.Draw(cell)

    bbox = draw.textbbox((0, 0), char, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (FLAP_W - tw) // 2 - bbox[0]
    ty = (FLAP_H - th) // 2 - bbox[1]
    draw.text((tx, ty), char, font=font, fill=TEXT_COLOR)

    mid = FLAP_H // 2
    if fold_progress > 0:
        top_half = cell.crop((0, 0, FLAP_W, mid))
        new_top_h = max(2, int(mid * (1.0 - 0.75 * fold_progress)))
        shrunk_top = top_half.resize((FLAP_W, new_top_h), Image.Resampling.BILINEAR)
        shaded_top = Image.new("RGB", (FLAP_W, new_top_h), FOLD_SHADE_COLOR)
        blended_top = Image.blend(shrunk_top, shaded_top, 0.35 * fold_progress)
        cell.paste(blended_top, (0, mid - new_top_h))

    draw.line([(0, mid), (FLAP_W, mid)], fill=SPLIT_LINE_COLOR, width=2)
    draw.rectangle([0, 0, FLAP_W - 1, FLAP_H - 1], outline=BORDER_COLOR, width=1)
    return cell


def build_board_frame(rows_chars, rows_folds, font, total_cols):
    num_rows = len(rows_chars)
    width = PAD_X * 2 + total_cols * FLAP_W + (total_cols - 1) * GAP
    height = PAD_Y * 2 + num_rows * FLAP_H + (num_rows - 1) * ROW_GAP
    board = Image.new("RGB", (width, height), BG_COLOR)

    for r in range(num_rows):
        y = PAD_Y + r * (FLAP_H + ROW_GAP)
        for idx in range(total_cols):
            x = PAD_X + idx * (FLAP_W + GAP)
            flap_img = render_single_flap(rows_chars[r][idx], font, rows_folds[r][idx])
            board.paste(flap_img, (x, y))

    return np.array(board)


def main():
    font = get_font(44)

    # Row 1: Destination + Departure Time
    time_str = TIME_TEXT[:5]
    dest_max = max(1, COLS - len(time_str) - 1)
    dest_str = DEST_TEXT.upper()[:dest_max].ljust(dest_max)
    target_row1 = list(f"{dest_str} {time_str}"[:COLS].ljust(COLS))

    # Row 2: Track Number + Status
    trk_digits = "".join(ch for ch in str(TRACK_NUM) if ch.isdigit())[:2].zfill(2)
    trk_str = f"TRK {trk_digits}"
    status_max = max(1, COLS - len(trk_str) - 1)
    status_str = STATUS_TEXT.upper()[:status_max]
    target_row2 = list(f"{trk_str} {status_str}"[:COLS].ljust(COLS))

    target_rows = [target_row1, target_row2]
    num_rows = len(target_rows)

    rng = random.Random(42)
    current_rows = [[" " for _ in range(COLS)] for _ in range(num_rows)]
    stop_steps = [[rng.randint(55, 120) for _ in range(COLS)] for _ in range(num_rows)]

    frames = []
    max_steps = max(max(row_steps) for row_steps in stop_steps)

    for step in range(max_steps):
        folds_step = []
        for r in range(num_rows):
            row_folds = []
            for col in range(COLS):
                if step < stop_steps[r][col]:
                    current_rows[r][col] = rng.choice(CHARSET)
                    row_folds.append(0.85)
                else:
                    current_rows[r][col] = target_rows[r][col]
                    row_folds.append(0.0)
            folds_step.append(row_folds)

        frames.append(build_board_frame(current_rows, folds_step, font, COLS))
        frames.append(build_board_frame(current_rows, [[0.0] * COLS for _ in range(num_rows)], font, COLS))

    settled_folds = [[0.0] * COLS for _ in range(num_rows)]
    final_frame = build_board_frame(target_rows, settled_folds, font, COLS)
    for _ in range(FPS * 3):
        frames.append(final_frame)

    clip = ImageSequenceClip(frames, fps=FPS)

    if AUDIO_FILE:
        try:
            audio = AudioFileClip(AUDIO_FILE)
            if audio.duration > clip.duration:
                audio = audio.subclipped(0, clip.duration)
            clip = clip.with_audio(audio)
        except Exception as e:
            print(f"Warning: Could not load '{AUDIO_FILE}' ({e}). Exporting without audio.")

    clip.write_videofile(OUTPUT_FILE, fps=FPS, codec="libx264", audio_codec="aac")


if __name__ == "__main__":
    main()