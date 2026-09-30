"""Text on the Pi screen that can be read from across a room.

The words are laid out here, not by mpv, so the service knows exactly what fits:
large monospace type, wrapped at spaces, and cut after the last whole word that
fits rather than scrolling or ending in an ellipsis. mpv then draws the lines as
an OSD overlay above a plain black picture.
"""

from __future__ import annotations

import struct
import unicodedata
import zlib


FONT = "DejaVu Sans Mono"
# libass sizes a font by its full line height; one DejaVu Sans Mono cell is about
# 0.52 of that wide. The factors below leave room in case a wider font stands in.
CHAR_WIDTH = 0.6
LINE_HEIGHT = 1.2
TEXT_OVERLAY_ID = 7


def text_width(text: str) -> int:
    """Width in monospace cells: wide East Asian characters take two, accents none."""
    width = 0
    for char in text:
        if unicodedata.combining(char):
            continue
        width += 2 if unicodedata.east_asian_width(char) in ("W", "F") else 1
    return width


def _split_to_width(word: str, cols: int) -> tuple[str, str]:
    head, used = "", 0
    for char in word:
        step = text_width(char)
        if used + step > cols and head:
            break
        head, used = head + char, used + step
    return head, word[len(head):]


def _wrap(paragraph: str, cols: int) -> list[tuple[str, bool]]:
    """Greedy wrap at spaces. Each line carries whether it ends on a whole word.

    A single word wider than the screen is the one thing broken mid-word, because
    it cannot be shown any other way; the cut at the end never lands inside it.
    """
    lines: list[tuple[str, bool]] = []
    current = ""
    for word in paragraph.split():
        while text_width(word) > cols:
            if current:
                lines.append((current, True))
                current = ""
            head, word = _split_to_width(word, cols)
            lines.append((head, False))
        if not current:
            current = word
        elif text_width(current) + 1 + text_width(word) <= cols:
            current += " " + word
        else:
            lines.append((current, True))
            current = word
    if current:
        lines.append((current, True))
    return lines


def _paragraphs(text: str, cols: int) -> list[tuple[str, bool]]:
    lines: list[tuple[str, bool]] = []
    for paragraph in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if paragraph.strip():
            lines.extend(_wrap(paragraph, cols))
        elif lines and lines[-1][0]:
            lines.append(("", True))
    while lines and not lines[-1][0]:
        lines.pop()
    return lines


def layout(title: str | None, text: str, width: int, height: int) -> dict:
    """Choose the largest type that fits the whole text, or cut it at a whole word.

    Returns the font size, the lines to draw, how many of them are the title,
    and whether the text had to be cut.
    """
    usable_w, usable_h = width * 0.88, height * 0.84
    largest, smallest = max(20, height // 7), max(20, height // 18)
    step = max(1, height // 270)

    def build(size: int) -> tuple[list[tuple[str, bool]], int, int]:
        cols = max(1, int(usable_w // (size * CHAR_WIDTH)))
        rows = max(1, int(usable_h // (size * LINE_HEIGHT)))
        head = _paragraphs(title, cols) if title else []
        body = _paragraphs(text, cols)
        return head + ([("", True)] if head and body else []) + body, len(head), rows

    for size in range(largest, smallest - 1, -step):
        lines, title_lines, rows = build(size)
        if len(lines) <= rows:
            return {"size": size, "lines": [line for line, _ in lines],
                    "titleLines": title_lines, "cut": False}
    lines, title_lines, rows = build(smallest)
    lines = lines[:rows]
    while lines and (not lines[-1][1] or not lines[-1][0]):
        lines.pop()
    return {"size": smallest, "lines": [line for line, _ in lines],
            "titleLines": min(title_lines, len(lines)), "cut": True}


def _escape(line: str) -> str:
    # mpv's own escaping: a word joiner after a backslash stops libass reading
    # \N or \h, and an escaped brace cannot open an override block.
    return line.replace("\\", "\\⁠").replace("{", "\\{")


def ass_event(laid_out: dict, width: int, height: int, rotate: int) -> str:
    """One centred ASS event for mpv's osd-overlay, turned to match the screen's rotation."""
    rendered = []
    for index, line in enumerate(laid_out["lines"]):
        text = _escape(line)
        rendered.append("{\\b1}" + text + "{\\b0}" if index < laid_out["titleLines"] else text)
    # video-rotate turns the picture clockwise; ASS \frz turns anticlockwise.
    style = (f"{{\\an5\\pos({width // 2},{height // 2})\\q2\\fn{FONT}\\fs{laid_out['size']}"
             f"\\bord2\\shad0\\1c&HFFFFFF&\\3c&H000000&\\frz{-rotate % 360}}}")
    return style + "\\N".join(rendered)


def blank_png(width: int = 16, height: int = 9) -> bytes:
    """A small solid black PNG for mpv to hold on screen beneath the text."""
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    rows = b"".join(b"\x00" + b"\x00\x00\x00" * width for _ in range(height))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) +
            chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))


def short_name(title: str | None, text: str, limit: int = 40) -> str:
    """A name for the player state: the title, or the opening words of the text."""
    if title and title.strip():
        return title.strip()[:120]
    words = text.split()
    if not words:
        return "Text"
    name = ""
    for word in words:
        if len(name) + len(word) + (1 if name else 0) > limit:
            break
        name = f"{name} {word}" if name else word
    return name or words[0][:limit]
