"""Bande 1080x64 du 2e compte : DO (bleu) BRAZILLL (noir) [CLIPS] (cartouche vert incliné) + bouton ABONNE-TOI.
DO et BRAZILLL sont découpés dans brand/logo.png ; le cartouche est redessiné en police Bungee (celle du logo)."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
W, BH = 1080, 64
BUNGEE = "brand/fonts/Bungee-Regular.ttf"
logo = Image.open("brand/logo.png").convert("RGB")
a = np.asarray(logo).astype(int)
YEL = tuple(int(v) for v in a[20, 20]); BLK = (17, 17, 17); GRN = (0, 155, 58); WHT = (255, 255, 255)
mask = np.abs(a - np.array(YEL)).sum(2) > 80
def crop(x0, y0, x1, y1, pad=6):
    sub = mask[y0:y1, x0:x1]; ys = np.where(sub.any(1))[0]; xs = np.where(sub.any(0))[0]
    return logo.crop((x0 + xs[0] - pad, y0 + ys[0] - pad, x0 + xs[-1] + pad, y0 + ys[-1] + pad))
def fit(im, h): return im.resize((max(1, round(im.width * h / im.height)), h), Image.LANCZOS)

def cartouche(text, h, angle=4, s=4):
    """Rectangle vert à bord noir + ombre décalée, texte blanc Bungee, légèrement incliné (comme le logo)."""
    f = ImageFont.truetype(BUNGEE, int(h * 0.55 * s))
    tw = int(f.getlength(text)); bw, bh = tw + int(h * 0.9 * s), int(h * s)
    im = Image.new("RGBA", (bw + 6 * s, bh + 6 * s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle((5 * s, 5 * s, bw + 5 * s, bh + 5 * s), fill=BLK)          # ombre
    d.rectangle((0, 0, bw, bh), fill=BLK); d.rectangle((3 * s, 3 * s, bw - 3 * s, bh - 3 * s), fill=GRN)
    d.text((bw / 2, bh / 2), text, font=f, fill=WHT, anchor="mm")
    im = im.rotate(angle, resample=Image.BICUBIC, expand=True)
    return im.resize((im.width // s, im.height // s), Image.LANCZOS)

def bouton(text, h, s=4):
    f = ImageFont.truetype(BUNGEE, int(h * 0.45 * s))
    tw = int(f.getlength(text)); bw, bh = tw + int(h * 0.8 * s), int(h * s)
    im = Image.new("RGBA", (bw, bh), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, bw - 1, bh - 1), radius=bh // 2, fill=BLK)
    d.text((bw / 2, bh / 2 + s), text, font=f, fill=YEL, anchor="mm")
    return im.resize((bw // s, bh // s), Image.LANCZOS)

DO = crop(850, 600, 1320, 940); BRA = crop(200, 940, 1960, 1200)
b = Image.new("RGBA", (W, BH), YEL + (255,)); d = ImageDraw.Draw(b)
d.rectangle((0, 0, W, 3), fill=BLK); d.rectangle((0, BH - 4, W, BH), fill=BLK)
parts = [fit(DO, 30).convert("RGBA"), fit(BRA, 36).convert("RGBA"), cartouche("CLIPS", 34), bouton("ABONNE-TOI", 44)]
gaps = [14, 18, 26]; tot = sum(p.width for p in parts) + sum(gaps); x = (W - tot) // 2
for i, p in enumerate(parts):
    b.alpha_composite(p, (x, (BH - p.height) // 2)); x += p.width + (gaps[i] if i < len(gaps) else 0)
b.convert("RGB").save("brand/band.png"); print("ok", [p.size for p in parts])
