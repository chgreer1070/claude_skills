#!/usr/bin/env -S uv --quiet run --active --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "Pillow>=10.0.0",
# ]
# ///
"""Render an RTFP artifact as a terminal-style PNG.

Input: JSON file (or stdin) with:
{
  "task": "short dry task summary",
  "assistant": "the assistant output that triggered the reaction",
  "user": "the user's emotional reply"
}

Output: PNG file ready to paste into social media.

Usage:
    render_artifact.py <input.json> [--out output.png] [--width 900]
    cat input.json | render_artifact.py - --out output.png
"""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Color scheme — dark terminal (Tokyo Night inspired)
# ---------------------------------------------------------------------------
BG = (26, 27, 38)  # #1a1b26 — background
CHROME_BG = (36, 40, 59)  # #24283b — titlebar
BORDER = (65, 72, 104)  # #414868 — subtle border
TEXT_DIM = (122, 130, 172)  # #7a82ac — dimmed labels
TEXT_TASK = (169, 177, 214)  # #a9b1d6 — task description
TEXT_ASST = (192, 202, 245)  # #c0caf5 — assistant text (slightly muted)
TEXT_USER = (255, 94, 94)  # #ff5e5e — user reaction (vivid)
DOT_RED = (247, 118, 142)  # #f7768e
DOT_YEL = (224, 175, 104)  # #e0af68
DOT_GRN = (158, 206, 106)  # #9ece6a

PADDING = 32
LINE_SPACING = 6
SECTION_GAP = 20
CHROME_H = 40

# ---------------------------------------------------------------------------
# Font loading
# ---------------------------------------------------------------------------

_MONO_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    "/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf",
    "/usr/share/fonts/truetype/hack/Hack-Regular.ttf",
    "/usr/share/fonts/truetype/fira/FiraMono-Regular.ttf",
    "/System/Library/Fonts/Menlo.ttc",
    "/Windows/Fonts/consola.ttf",
]

_BOLD_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSansMono-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
    "/usr/share/fonts/truetype/ubuntu/UbuntuMono-B.ttf",
    "/usr/share/fonts/truetype/hack/Hack-Bold.ttf",
]


AnyFont = ImageFont.FreeTypeFont | ImageFont.ImageFont


def _load_font(candidates: list[str], size: int) -> AnyFont:
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    # Pillow >= 10 supports size on load_default
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def load_fonts(base_size: int = 15) -> dict[str, AnyFont]:
    """Load the four font variants used by the renderer.

    Returns:
        Dict mapping variant names to loaded font objects.
    """
    # Find winning paths once to avoid scanning candidates twice per family
    mono_path = next((p for p in _MONO_CANDIDATES if Path(p).exists()), None)
    bold_path = next((p for p in _BOLD_CANDIDATES if Path(p).exists()), None)
    mono_candidates = [mono_path] if mono_path else []
    bold_candidates = [bold_path] if bold_path else []
    return {
        "regular": _load_font(mono_candidates, base_size),
        "bold": _load_font(bold_candidates, base_size),
        "small": _load_font(mono_candidates, base_size - 2),
        "label": _load_font(bold_candidates, base_size - 1),
    }


# ---------------------------------------------------------------------------
# Text wrapping
# ---------------------------------------------------------------------------


def wrap_text(text: str, font: AnyFont, max_width: int) -> list[str]:
    """Wrap text to fit within max_width pixels.

    Returns:
        List of wrapped text lines.
    """
    # Estimate chars per line using average char width
    try:
        avg_char_width = font.getlength("x")
    except AttributeError:
        avg_char_width = 8  # fallback
    chars_per_line = max(20, int(max_width / max(avg_char_width, 1)))

    lines = []
    for raw_line in text.splitlines():
        if not raw_line.strip():
            lines.append("")
            continue
        wrapped = textwrap.wrap(raw_line, width=chars_per_line, break_long_words=True)
        lines.extend(wrapped or [""])
    return lines


def text_block_height(lines: list[str], font_size: int) -> int:
    """Calculate the pixel height of a block of text lines.

    Returns:
        Height in pixels.
    """
    line_h = font_size + LINE_SPACING
    return max(1, len(lines)) * line_h


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------


def draw_chrome(draw: ImageDraw.ImageDraw, width: int, title: str, font: AnyFont) -> None:
    """Draw the terminal window chrome (title bar with traffic dots)."""
    draw.rectangle([0, 0, width, CHROME_H], fill=CHROME_BG)
    # Traffic light dots
    cx = PADDING
    cy = CHROME_H // 2
    r = 6
    for color in (DOT_RED, DOT_YEL, DOT_GRN):
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
        cx += 20

    # Title centered
    try:
        title_w = font.getlength(title)
    except AttributeError:
        title_w = len(title) * 8
    tx = max(PADDING, (width - title_w) // 2)
    draw.text((tx, (CHROME_H - int(getattr(font, "size", 13))) // 2), title, font=font, fill=TEXT_DIM)


def draw_divider(draw: ImageDraw.ImageDraw, y: int, width: int) -> None:
    """Draw a horizontal divider line across the image."""
    draw.line([(PADDING, y), (width - PADDING, y)], fill=BORDER, width=1)


def draw_label(draw: ImageDraw.ImageDraw, x: int, y: int, label: str, font: AnyFont) -> int:
    """Draw a section label and return its rendered height.

    Returns:
        Height in pixels consumed by the label.
    """
    draw.text((x, y), label, font=font, fill=TEXT_DIM)
    return int(getattr(font, "size", 13)) + LINE_SPACING + 4


def draw_lines(
    draw: ImageDraw.ImageDraw, x: int, y: int, lines: list[str], font: AnyFont, color: tuple[int, int, int]
) -> int:
    """Draw wrapped text lines and return total height consumed.

    Returns:
        Total height in pixels consumed by the drawn lines.
    """
    line_h = int(getattr(font, "size", 13)) + LINE_SPACING
    for line in lines:
        draw.text((x, y), line, font=font, fill=color)
        y += line_h
    return len(lines) * line_h


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------

MAX_ASSISTANT_LINES = 30  # truncate long assistant output for visual clarity
MAX_USER_LINES = 20


def render(task: str, assistant: str, user: str, output_path: Path, width: int = 900, base_font_size: int = 15) -> Path:
    """Render the RTFP artifact image and save it to output_path.

    Returns:
        The path to the written PNG file.
    """
    fonts = load_fonts(base_font_size)
    text_width = width - 2 * PADDING

    # Pre-wrap all sections
    task_lines = wrap_text(task, fonts["regular"], text_width - 60)
    asst_lines = wrap_text(assistant, fonts["regular"], text_width - 60)
    user_lines = wrap_text(user, fonts["bold"], text_width - 60)

    # Truncate with indicator if too long
    if len(asst_lines) > MAX_ASSISTANT_LINES:
        total_asst_lines = len(asst_lines)
        asst_lines = asst_lines[:MAX_ASSISTANT_LINES]
        asst_lines.append(f"… [{total_asst_lines - MAX_ASSISTANT_LINES} more lines]")

    if len(user_lines) > MAX_USER_LINES:
        total_user_lines = len(user_lines)
        user_lines = user_lines[:MAX_USER_LINES]
        user_lines.append(f"… [{total_user_lines - MAX_USER_LINES} more lines]")

    lh = base_font_size + LINE_SPACING
    label_h = base_font_size + LINE_SPACING + 4

    # Calculate total height
    height = (
        CHROME_H
        + PADDING
        + label_h
        + len(task_lines) * lh  # task section
        + SECTION_GAP
        + 1  # divider
        + SECTION_GAP
        + label_h
        + len(asst_lines) * lh  # assistant section
        + SECTION_GAP
        + 1  # divider
        + SECTION_GAP
        + label_h
        + len(user_lines) * lh  # user section
        + PADDING
    )

    img = Image.new("RGB", (width, height), color=BG)
    draw = ImageDraw.Draw(img)

    # Chrome
    draw_chrome(draw, width, "rtfp — Read The Fucking Prompt", fonts["small"])

    y = CHROME_H + PADDING
    x = PADDING

    # Task section
    draw_label(draw, x, y, "task:", fonts["label"])
    y += label_h
    draw_lines(draw, x + 16, y, task_lines, fonts["regular"], TEXT_TASK)
    y += len(task_lines) * lh

    y += SECTION_GAP
    draw_divider(draw, y, width)
    y += SECTION_GAP

    # Assistant section
    draw_label(draw, x, y, "claude:", fonts["label"])
    y += label_h
    draw_lines(draw, x + 16, y, asst_lines, fonts["regular"], TEXT_ASST)
    y += len(asst_lines) * lh

    y += SECTION_GAP
    draw_divider(draw, y, width)
    y += SECTION_GAP

    # User reaction section
    draw_label(draw, x, y, "user:", fonts["label"])
    y += label_h
    draw_lines(draw, x + 16, y, user_lines, fonts["bold"], TEXT_USER)

    img.save(str(output_path), "PNG", optimize=True)
    return output_path


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Parse CLI arguments and render an RTFP artifact PNG."""
    parser = argparse.ArgumentParser(description="Render RTFP terminal-style artifact as PNG")
    parser.add_argument("input", help="JSON file with task/assistant/user fields, or '-' for stdin")
    parser.add_argument("--out", "-o", default="rtfp_artifact.png", help="Output PNG path")
    parser.add_argument("--width", type=int, default=900, help="Image width in pixels")
    parser.add_argument("--font-size", type=int, default=15, help="Base font size")
    args = parser.parse_args()

    if args.input == "-":
        data = json.load(sys.stdin)
    else:
        with Path(args.input).open(encoding="utf-8") as fh:
            data = json.load(fh)

    task = data.get("task", "").strip()
    assistant = data.get("assistant", "").strip()
    user = data.get("user", "").strip()

    if not task or not user:
        print("Error: 'task' and 'user' fields are required in the input JSON.", file=sys.stderr)
        sys.exit(1)

    if not assistant:
        assistant = "(assistant output not available)"

    out_path = Path(args.out)
    result = render(task, assistant, user, out_path, width=args.width, base_font_size=args.font_size)
    print(f"Artifact written to: {result}")


if __name__ == "__main__":
    main()
