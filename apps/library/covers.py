"""
Original placeholder covers for the seed data.

Each book gets a deterministic cover (same slug -> same picture): the palette
comes from its first category and the geometric pattern from a hash of the slug.
Only the genre is written on it, so the cover never imitates a real edition.
"""
import hashlib
import io
import random
import unicodedata

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 400, 600

# (background, shape colour, accent) per category code. Tuned to the site's
# ink / parchment / brass palette.
PALETTES = {
    'ROM': ('#7a3b3b', '#a65a50', '#f2ead9'),
    'FIC': ('#2f3e52', '#4a5f7a', '#c9a45c'),
    'FAN': ('#3a5744', '#5c7d5f', '#e3d3a4'),
    'FC': ('#1c2430', '#33506e', '#7fc4d6'),
    'TER': ('#1a1a1a', '#5a1f1f', '#d8c8a8'),
    'SUS': ('#2b2b3a', '#4b4b66', '#e0a090'),
    'POL': ('#262626', '#4d4d4d', '#e5c35c'),
    'HIS': ('#6b4f2a', '#8c6d3f', '#f2ead9'),
    'NF': ('#4a4a3f', '#6d6d5c', '#f2ead9'),
    'BIO': ('#5a4636', '#7d6450', '#f2ead9'),
    'FIL': ('#3d3550', '#5c5175', '#e6d7a8'),
    'PSI': ('#4f3d5c', '#735a85', '#f0d9e0'),
    'AUT': ('#b5833a', '#d4a65c', '#1c2430'),
    'NEG': ('#24414f', '#3d6375', '#f2ead9'),
    'TEC': ('#1e3a3a', '#2f5c5c', '#8fe0c8'),
    'INF': ('#3f7fa8', '#f2c14e', '#fdf6e3'),
    'JUV': ('#6a3d7a', '#9c5fb0', '#f9e79f'),
    'POE': ('#4a3a5c', '#7a6390', '#f2ead9'),
    'QUA': ('#b23a3a', '#f2c14e', '#fdf6e3'),
}
DEFAULT_PALETTE = ('#263140', '#3d4c60', '#c9a45c')


def _rng_for(seed_text):
    digest = hashlib.sha256(seed_text.encode('utf-8')).hexdigest()
    return random.Random(int(digest[:16], 16))


# System fonts with accented capitals (macOS, Linux, Windows), tried in order.
FONT_CANDIDATES = [
    '/System/Library/Fonts/Supplemental/Arial.ttf',
    '/System/Library/Fonts/Helvetica.ttc',
    '/Library/Fonts/Arial.ttf',
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    '/usr/share/fonts/opentype/inter/Inter-Regular.otf',
    'C:/Windows/Fonts/arial.ttf',
]


def _font(size):
    """Return (font, has_accents). Falls back to Pillow's built-in font."""
    for path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size), True
        except OSError:
            continue
    # Pillow's default font has no accented capitals.
    try:
        return ImageFont.load_default(size=size), False
    except TypeError:
        return ImageFont.load_default(), False


def _strip_accents(text):
    normalized = unicodedata.normalize('NFD', text)
    return ''.join(ch for ch in normalized if unicodedata.category(ch) != 'Mn')


def _pattern(draw, rng, shape, accent):
    style = rng.choice(['circles', 'bands', 'arcs', 'grid'])
    if style == 'circles':
        for _ in range(rng.randint(3, 6)):
            r = rng.randint(40, 170)
            x, y = rng.randint(-40, WIDTH + 40), rng.randint(-40, HEIGHT - 160)
            draw.ellipse((x - r, y - r, x + r, y + r), fill=shape)
        r = rng.randint(30, 60)
        x, y = rng.randint(80, WIDTH - 80), rng.randint(110, 300)
        draw.ellipse((x - r, y - r, x + r, y + r), fill=accent)
    elif style == 'bands':
        angle_offset = rng.randint(-200, 200)
        for i in range(rng.randint(4, 7)):
            y = rng.randint(0, HEIGHT - 180)
            h = rng.randint(14, 60)
            draw.polygon(
                [(0, y), (WIDTH, y + angle_offset // 4),
                 (WIDTH, y + h + angle_offset // 4), (0, y + h)],
                fill=accent if i == 0 else shape,
            )
    elif style == 'arcs':
        cx, cy = rng.choice([0, WIDTH]), rng.randint(120, 360)
        for i, r in enumerate(range(rng.randint(260, 360), 30, -rng.randint(28, 45))):
            colour = accent if i % 3 == 0 else shape
            draw.arc((cx - r, cy - r, cx + r, cy + r), 0, 360, fill=colour, width=rng.randint(6, 14))
    else:  # grid
        step = rng.choice([40, 50, 60])
        for gx in range(0, WIDTH, step):
            for gy in range(0, HEIGHT - 170, step):
                if rng.random() < 0.45:
                    pad = rng.randint(4, 12)
                    colour = accent if rng.random() < 0.12 else shape
                    draw.rectangle((gx + pad, gy + pad, gx + step - pad, gy + step - pad), fill=colour)


def generate_cover(seed_text, category_code=None, label=''):
    """Return PNG bytes for an original cover."""
    background, shape, accent = PALETTES.get(category_code, DEFAULT_PALETTE)
    rng = _rng_for(seed_text)

    image = Image.new('RGB', (WIDTH, HEIGHT), background)
    draw = ImageDraw.Draw(image)
    _pattern(draw, rng, shape, accent)

    # Bottom panel with the genre label.
    panel_top = HEIGHT - 150
    draw.rectangle((0, panel_top, WIDTH, HEIGHT), fill=background)
    draw.line((36, panel_top + 34, WIDTH - 36, panel_top + 34), fill=accent, width=2)
    if label:
        font, has_accents = _font(26)
        text = label.upper() if has_accents else _strip_accents(label).upper()
        width = draw.textlength(text, font=font)
        draw.text(((WIDTH - width) / 2, panel_top + 60), text, font=font, fill=accent)

    # Thin frame, like a printed cover.
    draw.rectangle((14, 14, WIDTH - 15, HEIGHT - 15), outline=accent, width=2)

    buffer = io.BytesIO()
    image.save(buffer, 'PNG', optimize=True)
    return buffer.getvalue()