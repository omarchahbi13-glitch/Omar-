"""Build brand/badge.png: round avatar + @handle pill. Uses brand/avatar.(png|jpg) if present."""
import os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
handle = sys.argv[1] if len(sys.argv) > 1 else "@gta_vice.clips"
S = 4  # supersampling
AV = 96 * S
font = ImageFont.truetype(os.popen("fc-match -f '%{file}' 'Inter Display:style=Black'").read(), 44 * S)
src = next((f"brand/avatar.{e}" for e in ("png", "jpg", "jpeg") if os.path.exists(f"brand/avatar.{e}")), None)
if src:
    av = Image.open(src).convert("RGB")
    m = min(av.size); av = av.crop(((av.width-m)//2, (av.height-m)//2, (av.width+m)//2, (av.height+m)//2)).resize((AV, AV))
else:  # placeholder: gradient circle with initials
    av = Image.new("RGB", (AV, AV))
    for y in range(AV):
        for x in range(0, AV, 4):
            t = (x + y) / (2 * AV)
            av.paste((int(255*(1-t) + 37*t), int(0*(1-t) + 244*t), int(80*(1-t) + 238*t)), (x, y, x+4, y+1))
    d = ImageDraw.Draw(av); f2 = ImageFont.truetype(font.path, 42 * S)
    d.text((AV/2, AV/2), "GV", font=f2, fill="white", anchor="mm")
mask = Image.new("L", (AV, AV)); ImageDraw.Draw(mask).ellipse((0, 0, AV-1, AV-1), fill=255)
tw = int(font.getlength(handle))
pad = 14 * S
Wd, Hd = AV + 2*pad + tw + 18*S + pad, AV + 2*pad
img = Image.new("RGBA", (Wd, Hd), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
d.rounded_rectangle((0, 0, Wd-1, Hd-1), radius=Hd//2, fill=(0, 0, 0, 150))
ring = 5 * S
d.ellipse((pad-ring, pad-ring, pad+AV+ring, pad+AV+ring), fill=(255, 255, 255, 255))
img.paste(av, (pad, pad), mask)
d.text((pad + AV + 18*S, Hd/2), handle, font=font, fill="white", anchor="lm")
img = img.resize((Wd // S, Hd // S), Image.LANCZOS)
img.save("brand/badge.png"); print("badge", img.size, "photo" if src else "placeholder")
