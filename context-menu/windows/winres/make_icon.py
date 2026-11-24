#!/usr/bin/env python3
"""Genera icon.png (256x256) para el ejecutable de Windows. Requiere Pillow."""

from pathlib import Path

from PIL import Image, ImageDraw

SIZE = 256
SCALE = 4  # dibuja a mayor resolución y reduce para suavizar bordes
S = SIZE * SCALE


def p(x, y):
    return (x * SCALE, y * SCALE)


image = Image.new("RGBA", (S, S), (0, 0, 0, 0))
draw = ImageDraw.Draw(image)

draw.rounded_rectangle([p(8, 8), p(248, 248)], radius=48 * SCALE, fill=(33, 99, 196, 255))

# Cubo isométrico (modelo 3D)
top, left, right, center, bottom = p(118, 40), p(48, 80), p(188, 80), p(118, 120), p(118, 206)
left_bottom, right_bottom = p(48, 166), p(188, 166)
draw.polygon([top, right, center, left], fill=(255, 255, 255, 255))
draw.polygon([left, center, bottom, left_bottom], fill=(205, 222, 245, 255))
draw.polygon([center, right, right_bottom, bottom], fill=(160, 192, 236, 255))

# Insignia con marca de verificación
draw.ellipse([p(140, 140), p(240, 240)], fill=(46, 160, 67, 255), outline=(255, 255, 255, 255), width=8 * SCALE)
draw.line([p(162, 191), p(183, 211), p(219, 168)], fill=(255, 255, 255, 255), width=14 * SCALE, joint="curve")

image.resize((SIZE, SIZE), Image.LANCZOS).save(Path(__file__).with_name("icon.png"))
