#!/usr/bin/env python3
"""Render docs/demo.gif, an illustration of the hypercaffeinated workflow.

    python3 docs/make_demo.py            # writes docs/demo.gif
    python3 docs/make_demo.py --stills DIR   # also writes a few PNG stills into DIR

Needs Pillow and the macOS system fonts (SF Pro, SF Mono).
"""
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H, S, FPS, LENGTH = 800, 450, 2, 15, 13.0   # S = supersampling factor
OUT = Path(__file__).with_name("demo.gif")

BG = (23, 19, 17)
PANEL = (40, 34, 31)
BUBBLE = (56, 48, 44)
LINE = (74, 64, 58)
CREAM = (242, 230, 214)
MUTED = (150, 138, 126)
COFFEE = (212, 140, 76)
GREEN = (118, 204, 140)
GREY = (120, 113, 107)
ALU = (168, 160, 153)
ALU_DARK = (128, 121, 115)

FONT_UI = "/System/Library/Fonts/SFNS.ttf"
FONT_MONO = "/System/Library/Fonts/SFNSMono.ttf"
_fonts = {}


def font(size, mono=False, bold=False):
    key = (size, mono, bold)
    if key not in _fonts:
        f = ImageFont.truetype(FONT_MONO if mono else FONT_UI, int(size * S))
        if bold:
            try:
                f.set_variation_by_name("Bold")
            except Exception:
                pass
        _fonts[key] = f
    return _fonts[key]


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def ease(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def seg(t, a, b):
    """Eased progress 0..1 of time t through the window [a, b]."""
    return ease((t - a) / (b - a))


def mix(c1, c2, k):
    return tuple(int(a + (b - a) * clamp(k)) for a, b in zip(c1, c2))


class Canvas:
    def __init__(self, w=W, h=H, bg=BG):
        self.im = Image.new("RGB", (int(w * S), int(h * S)), bg)
        self.d = ImageDraw.Draw(self.im)

    def rr(self, box, r, fill=None, outline=None, width=1):
        self.d.rounded_rectangle([v * S for v in box], r * S, fill=fill,
                                 outline=outline, width=int(width * S))

    def ellipse(self, box, fill):
        self.d.ellipse([v * S for v in box], fill=fill)

    def line(self, pts, fill, width):
        self.d.line([(x * S, y * S) for x, y in pts], fill=fill, width=max(1, int(width * S)), joint="curve")

    def arc(self, box, a0, a1, fill, width):
        self.d.arc([v * S for v in box], a0, a1, fill=fill, width=int(width * S))

    def text(self, xy, txt, size, fill, mono=False, bold=False, anchor="la"):
        self.d.text((xy[0] * S, xy[1] * S), txt, font=font(size, mono, bold), fill=fill, anchor=anchor)

    def tlen(self, txt, size, mono=False, bold=False):
        return self.d.textlength(txt, font=font(size, mono, bold)) / S


def wrap(c, txt, size, maxw):
    lines, cur = [], ""
    for word in txt.split():
        trial = (cur + " " + word).strip()
        if c.tlen(trial, size) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    return lines + [cur]


# ---------------------------------------------------------------- pieces

def cup(c, x, y, sc, t, color=COFFEE, steam=True):
    """Coffee cup with animated steam; (x, y) is the top-left of the cup body."""
    w, h = 22 * sc, 18 * sc
    c.arc((x + w - 5 * sc, y + 3 * sc, x + w + 7 * sc, y + 13 * sc), -90, 90, color, 3 * sc)
    c.rr((x, y, x + w, y + h), 5 * sc, fill=color)
    if steam:
        for i in range(3):
            sx = x + 5 * sc + i * 6 * sc
            pts = [(sx + 1.8 * sc * math.sin(t * 5 + i * 1.7 + k * 0.9), y - 3 * sc - k * 2.4 * sc) for k in range(6)]
            c.line(pts, MUTED, 1.6 * sc)


LX, LY = 250, 318            # laptop centre x, hinge y
SW, SH = 300, 186            # screen size


def terminal(t):
    """The laptop's screen content as its own image (so the lid can squash it)."""
    c = Canvas(SW, SH, (14, 12, 11))
    for i, col in enumerate([(236, 95, 87), (245, 190, 80), (98, 196, 98)]):
        c.ellipse((12 + i * 14, 10, 21 + i * 14, 19), col)
    c.text((SW / 2, 9), "zsh", 10, MUTED, anchor="ma")
    cmd = "nosleep on"
    n = int(clamp((t - 0.4) / 1.0) * len(cmd) + 0.001)
    y = 38
    c.text((14, y), "~ $", 13, COFFEE, mono=True)
    typed = cmd[:n]
    c.text((48, y), typed, 13, CREAM, mono=True)
    if t < 1.6 and int(t * 3) % 2 == 0:
        cx = 48 + c.tlen(typed, 13, mono=True)
        c.rr((cx + 1, y + 1, cx + 8, y + 15), 1, fill=CREAM)
    if t >= 1.6:
        c.text((14, y + 24), "No-Sleep ON since 24.11. 09:42", 13, GREEN, mono=True)
        c.text((14, y + 48), "~ $", 13, COFFEE, mono=True)
    return c.im


def laptop(c, t):
    close = seg(t, 2.4, 3.4)
    if close < 1:
        h = SH * (1 - close)
        bez = 10
        c.rr((LX - SW / 2 - bez, LY - h - bez * (1 - close), LX + SW / 2 + bez, LY), 12, fill=(52, 48, 46))
        if h > 2:
            scr = terminal(t).resize((int(SW * S), max(1, int(h * S))), Image.LANCZOS)
            if close > 0:
                scr = Image.blend(scr, Image.new("RGB", scr.size, (10, 9, 8)), close * 0.8)
            c.im.paste(scr, (int((LX - SW / 2) * S), int((LY - h) * S)))
    else:
        c.rr((LX - 168, LY - 9, LX + 168, LY + 1), 5, fill=ALU)            # closed lid
    c.rr((LX - 180, LY, LX + 180, LY + 13), 6, fill=ALU_DARK)            # base
    c.rr((LX - 38, LY, LX + 38, LY + 4), 2, fill=(105, 99, 94))          # thumb notch

    if t < 3.4:
        return
    bag(c, seg(t, 3.5, 4.0))

    # status badge above the bag
    appear = seg(t, 3.9, 4.3)
    asleep = t >= 9.0
    batt = 64 - int(clamp((t - 3.9) / 5.1) * 3)
    label = "ASLEEP  ·  zZz" if asleep else f"AWAKE  ·  lid closed  ·  on battery {batt}%"
    tw = c.tlen(label, 12, bold=True)
    bw = tw + 40
    by = LY - 150 + (1 - appear) * 10
    col = mix(BG, GREY if asleep else GREEN, appear)
    c.rr((LX - bw / 2, by, LX + bw / 2, by + 28), 14, fill=mix(BG, PANEL, appear), outline=col, width=1.5)
    pulse = 0.5 + 0.5 * math.sin(t * (9 if 5.6 <= t < 8.6 else 4))
    r = 3.5 + (0 if asleep else 1.2 * pulse)
    c.ellipse((LX - bw / 2 + 16 - r, by + 14 - r, LX - bw / 2 + 16 + r, by + 14 + r), col)
    c.text((LX - bw / 2 + 28, by + 14), label, 12, mix(BG, CREAM, appear), bold=True, anchor="lm")

    # what the agent is doing inside the bag
    acts = [(5.6, "running tests… 31/42"), (6.3, "fixing auth_test.py"),
            (7.0, "git push · draft PR #17"), (8.5, "nosleep off")]
    cur = [a for a in acts if t >= a[0] and t < 9.6]
    if cur:
        txt = cur[-1][1]
        k = seg(t, cur[-1][0], cur[-1][0] + 0.25)
        c.text((LX, LY + 58), "agent: " + txt, 12, mix(BG, MUTED, k), mono=True, anchor="ma")


LEATHER = (110, 78, 54)
LEATHER_DARK = (82, 58, 40)


def bag(c, k):
    """A leather bag that rises around the closed laptop (k = 0 hidden .. 1 in place)."""
    if k <= 0:
        return
    dy = (1 - k) * 70
    body = mix(BG, LEATHER, k)
    dark = mix(BG, LEATHER_DARK, k)
    top, bot = LY - 26 + dy, LY + 42 + dy
    for hx in (LX - 120, LX + 40):                                   # handles
        c.arc((hx, top - 62, hx + 80, top + 30), 180, 360, dark, 7)
    c.rr((LX - 205, top, LX + 205, bot), 18, fill=body)
    c.rr((LX - 205, top, LX + 205, top + 30), 18, fill=dark)          # flap
    c.rr((LX - 205, top + 16, LX + 205, top + 30), 0, fill=dark)
    for x in range(int(LX - 190), int(LX + 190), 14):                 # stitching
        c.line([(x, top + 38), (x + 7, top + 38)], mix(BG, (150, 112, 82), k), 1.2)
    c.rr((LX - 14, top + 22, LX + 14, top + 40), 4, fill=mix(BG, (200, 170, 120), k))  # buckle
    c.rr((LX - 8, top + 27, LX + 8, top + 35), 2, fill=dark)


PX, PY, PW, PH = 560, 28, 204, 394   # phone box


def bubble(c, x0, x1, y, txt, me, k):
    size = 12
    lines = wrap(c, txt, size, 128)
    bw = max(c.tlen(line, size) for line in lines) + 22
    bh = len(lines) * 16 + 14
    if me:
        bx = x1 - bw
        fill = mix(PANEL, COFFEE, k)
        tcol = mix(PANEL, (30, 22, 16), k)
    else:
        bx = x0
        fill = mix(PANEL, BUBBLE, k)
        tcol = mix(PANEL, CREAM, k)
    y += (1 - k) * 8
    c.rr((bx, y, bx + bw, y + bh), 12, fill=fill)
    for i, line in enumerate(lines):
        c.text((bx + 11, y + 8 + i * 16), line, size, tcol)
    return bh


def phone(c, t):
    k = seg(t, 3.8, 4.3)
    if k <= 0:
        return
    ox = (1 - k) * 280
    x, y = PX + ox, PY
    c.rr((x, y, x + PW, y + PH), 30, fill=(10, 9, 8), outline=LINE, width=2)
    c.rr((x + 7, y + 7, x + PW - 7, y + PH - 7), 24, fill=PANEL)
    c.rr((x + PW / 2 - 30, y + 14, x + PW / 2 + 30, y + 30), 8, fill=(10, 9, 8))
    c.text((x + 22, y + 16), "09:43", 11, CREAM, bold=True)

    # header
    c.text((x + PW / 2, y + 44), "Remote Control", 13, CREAM, bold=True, anchor="ma")
    awake = t < 9.0
    dot = GREEN if awake else GREY
    status = "my-mac · awake in a bag" if awake else "my-mac · asleep"
    sw = c.tlen(status, 10)
    sx = x + PW / 2 - (sw + 10) / 2
    c.ellipse((sx, y + 66, sx + 6, y + 72), dot)
    c.text((sx + 10, y + 63), status, 10, MUTED)
    c.line([(x + 16, y + 84), (x + PW - 16, y + 84)], LINE, 1)

    x0, x1, cy = x + 16, x + PW - 16, y + 96
    msg = "run the tests, fix what fails, open a draft PR"
    if t >= 5.4:
        cy += bubble(c, x0, x1, cy, msg, True, seg(t, 5.4, 5.7)) + 10
    if 5.7 <= t < 7.7:
        bw = 46
        c.rr((x0, cy, x0 + bw, cy + 26), 12, fill=BUBBLE)
        for i in range(3):
            a = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(t * 8 - i * 0.9))
            c.ellipse((x0 + 11 + i * 10, cy + 10, x0 + 17 + i * 10, cy + 16), mix(BUBBLE, CREAM, a))
    if t >= 7.7:
        cy += bubble(c, x0, x1, cy, "42/42 tests green. Draft PR #17 is up.", False, seg(t, 7.7, 8.0)) + 10
    if t >= 8.5:
        cy += bubble(c, x0, x1, cy, "All done, so I ran nosleep off. Your Mac can sleep now.", False, seg(t, 8.5, 8.8)) + 10

    # input bar
    iy = y + PH - 50
    c.rr((x + 14, iy, x + PW - 14, iy + 32), 16, fill=(30, 25, 23), outline=LINE, width=1)
    n = int(clamp((t - 4.3) / 1.0) * len(msg))
    if 4.3 <= t < 5.4 and n:
        shown = msg[:n]
        while c.tlen(shown, 11) > PW - 62:
            shown = shown[1:]
        c.text((x + 26, iy + 16), shown, 11, CREAM, anchor="lm")
    else:
        c.text((x + 26, iy + 16), "Message", 11, GREY, anchor="lm")
    c.ellipse((x + PW - 44, iy + 5, x + PW - 22, iy + 27), COFFEE if 4.3 <= t < 5.5 else LINE)


def caption(c, t):
    steps = [(0.0, 2.4, "1", "nosleep on"),
             (2.4, 4.1, "2", "close the lid, unplug, into the bag"),
             (4.1, 9.0, "3", "keep steering your agent from your phone"),
             (9.0, 10.2, "4", "it switches itself off when the work is done")]
    for a, b, num, txt in steps:
        if a <= t < b:
            k = seg(t, a, a + 0.3) * (1 - seg(t, b - 0.25, b))
            x, y = 40, 400
            c.ellipse((x, y, x + 22, y + 22), mix(BG, COFFEE, k))
            c.text((x + 11, y + 11), num, 12, mix(BG, (30, 22, 16), k), bold=True, anchor="mm")
            c.text((x + 32, y + 11), txt, 15, mix(BG, CREAM, k), bold=True, anchor="lm")


def end_card(t):
    c = Canvas()
    cup(c, W / 2 - 30, 128, 2.6, t)
    c.text((W / 2, 220), "hypercaffeinated", 46, CREAM, bold=True, anchor="mm")
    c.text((W / 2, 266), "your Mac gets no sleep. not even in your bag.", 18, MUTED, anchor="mm")
    c.text((W / 2, 318), "github.com/n-athana/hypercaffeinated", 14, COFFEE, mono=True, anchor="mm")
    return c.im


def frame(t):
    c = Canvas()
    cup(c, 28, 34, 0.9, t)
    c.text((60, 30), "hypercaffeinated", 15, CREAM, bold=True)
    laptop(c, t)
    phone(c, t)
    caption(c, t)
    im = c.im
    k = seg(t, 10.0, 10.6)
    if k > 0:
        im = Image.blend(im, end_card(t), k)
    return im.resize((W, H), Image.LANCZOS)


def main():
    times = [i / FPS for i in range(int(LENGTH * FPS))]
    rgb = [frame(t) for t in times]

    # one shared palette, so colours don't flicker between frames
    sample = Image.new("RGB", (W, H * 6))
    for i, idx in enumerate([0, 25, 60, 110, 140, len(rgb) - 1]):
        sample.paste(rgb[idx], (0, H * i))
    pal = sample.quantize(colors=255, method=Image.Quantize.MEDIANCUT)

    frames, durs = [], []
    for im in rgb:
        q = im.quantize(palette=pal, dither=Image.Dither.NONE)
        if frames and q.tobytes() == frames[-1].tobytes():
            durs[-1] += 1000 / FPS          # merge identical frames into one longer one
        else:
            frames.append(q)
            durs.append(1000 / FPS)
    durs = [int(round(d)) for d in durs]
    frames[0].save(OUT, save_all=True, append_images=frames[1:], duration=durs, loop=0, disposal=1)
    print(f"{OUT}  {len(frames)} frames  {OUT.stat().st_size / 1024:.0f} KB")

    if "--stills" in sys.argv:
        out_dir = Path(sys.argv[sys.argv.index("--stills") + 1])
        for t in (1.8, 3.0, 3.7, 6.4, 9.2):
            p = out_dir / f"still_{t:04.1f}.png"
            rgb[int(t * FPS)].save(p)
            print(p)


if __name__ == "__main__":
    main()
