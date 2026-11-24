"""Build brand bands (1080xBH) from the DO BRAZILLL CLIPS logo + mockups."""
import numpy as np, os
from PIL import Image, ImageDraw, ImageFilter, ImageFont
BG = (7, 9, 12); YEL = (255, 221, 0); GRN = (0, 226, 90)
W, BH = 1080, 110
logo = Image.open("brand/logo.png").convert("RGB")
a = np.asarray(logo).astype(int); mask = np.abs(a - np.array(BG)).sum(2) > 60
def crop(y0, y1, x0, x1, pad=4):
    sub = mask[y0:y1, x0:x1]; ys = np.where(sub.any(1))[0]; xs = np.where(sub.any(0))[0]
    return logo.crop((x0 + xs[0] - pad, y0 + ys[0] - pad, x0 + xs[-1] + pad, y0 + ys[-1] + pad))
DO = crop(670, 900, 900, 1250); BRA = crop(1005, 1225, 300, 1860)
# CLIPS letters only (skip neon dashes): find column groups in band 3
sub = mask[1320:1465, :]; cols = np.where(sub.any(0))[0]
groups = []; s = p = cols[0]
for c in cols[1:]:
    if c - p > 25: groups.append((s, p)); s = c
    p = c
groups.append((s, p))
letters = [g for g in groups if g[1] - g[0] < 200]  # dashes are long
CLIPS = crop(1320, 1465, letters[0][0] - 2, letters[-1][1] + 3)
DASH = crop(1320, 1465, groups[0][0], groups[0][1] + 1, pad=14)
def fit(im, h): return im.resize((max(1, round(im.width * h / im.height)), h), Image.LANCZOS)
def glow_line(d_img, y, color, x0=0, x1=W, t=3):
    layer = Image.new("RGBA", d_img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    d.line((x0, y, x1, y), fill=color + (255,), width=t * 3)
    d_img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(6)))
    ImageDraw.Draw(d_img).line((x0, y, x1, y), fill=color + (255,), width=t)
def avatar(size):
    m = min(logo.size); av = logo.crop((260, 260, m - 260, m - 260)).resize((size, size), Image.LANCZOS)
    mk = Image.new("L", (size, size)); ImageDraw.Draw(mk).ellipse((0, 0, size - 1, size - 1), fill=255)
    out = Image.new("RGBA", (size + 8, size + 8), (0, 0, 0, 0)); ImageDraw.Draw(out).ellipse((0, 0, size + 7, size + 7), fill=YEL + (255,))
    out.paste(av, (4, 4), mk); return out
FONT = os.popen("fc-match -f '%{file}' 'Inter Display:style=Black'").read()

def band_A(BH=64, scale=1.0):  # Néon : logo complet en ligne + filets verts lumineux (version fine)
    b = Image.new("RGBA", (W, BH), BG + (255,))
    t=max(2,round(2*scale)); glow_line(b, 2, GRN, t=t); glow_line(b, BH - 3, GRN, t=t)
    parts = [fit(DO, round(32*scale)), fit(BRA, round(32*scale)), fit(CLIPS, round(24*scale))]
    gap = round(16*scale); tot = sum(p.width for p in parts) + gap * 2; x = (W - tot) // 2
    for p in parts:
        b.paste(p, (x, (BH - p.height) // 2)); x += p.width + gap
    return b

def band_B():  # Rayures : fond rayé jaune (comme les lettres) + cartouche noir central
    b = Image.new("RGBA", (W, BH), BG + (255,)); d = ImageDraw.Draw(b)
    for y in range(8, BH - 4, 16): d.line((0, y, W, y), fill=YEL, width=5)
    av = avatar(BH - 34); parts0 = [fit(DO, 40), fit(BRA, 40)]
    pill_w = 10 + av.width + 14 + sum(p.width for p in parts0) + 14 + 40
    x0 = (W - pill_w) // 2
    d.rounded_rectangle((x0, 10, x0 + pill_w, BH - 10), radius=(BH - 20) // 2, fill=BG, outline=YEL, width=4)
    b.alpha_composite(av, (x0 + 10, (BH - av.height) // 2))
    parts = [fit(DO, 40), fit(BRA, 40)]; x = x0 + 24 + av.width
    for p in parts: b.paste(p, (x, (BH - p.height) // 2 - 9)); x += p.width + 14
    cl = fit(CLIPS, 22); b.paste(cl, (x0 + 24 + av.width, BH // 2 + 16))
    return b

def band_C():  # Abonne-toi : avatar + nom + bouton vert néon
    b = Image.new("RGBA", (W, BH), BG + (255,)); d = ImageDraw.Draw(b)
    glow_line(b, 2, YEL, t=3); glow_line(b, BH - 3, YEL, t=3)
    av = avatar(BH - 26); b.alpha_composite(av, (26, (BH - av.height) // 2))
    x = 26 + av.width + 18
    for p in (fit(DO, 44), fit(BRA, 44)): b.paste(p, (x, (BH - p.height) // 2)); x += p.width + 12
    f = ImageFont.truetype(FONT, 34); txt = "ABONNE-TOI"; tw = int(f.getlength(txt))
    bx1 = W - 26; bx0 = bx1 - tw - 50
    glow = Image.new("RGBA", b.size, (0, 0, 0, 0)); ImageDraw.Draw(glow).rounded_rectangle((bx0, 24, bx1, BH - 24), radius=30, fill=GRN + (200,))
    b.alpha_composite(glow.filter(ImageFilter.GaussianBlur(9)))
    d = ImageDraw.Draw(b); d.rounded_rectangle((bx0, 24, bx1, BH - 24), radius=30, fill=GRN)
    d.text(((bx0 + bx1) / 2, BH / 2), txt, font=f, fill=BG, anchor="mm")
    return b

os.makedirs("brand/bands", exist_ok=True)
for name, fn in (("A_neon", band_A), ("B_rayures", band_B), ("C_abonne", band_C)):
    fn().save(f"brand/bands/{name}.png")
print("ok")
