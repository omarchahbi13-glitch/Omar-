"""Montage « présentation podcast » (vidéo 16:9 au centre, fond flou, gros titre en cartouches blancs en haut).
Usage : python3 outils/render_podcast.py job.json   (lancer depuis tiktok2/)
job = {src, out, words, segments:[[s,e]], title:"LIGNE 1|LIGNE 2|...", zooms:[[s,e]] (temps de sortie),
       fixes:{}, drop_ranges:[], vid_y:640, title_dur:5 (optionnel : le titre disparaît après N s, en fondu)}
"""
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(__file__))
import render as R

W, H = 1080, 1920
FONT = os.popen("fc-match -f '%{file}' 'Inter Display:style=Black'").read()
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

def is_emoji(ch): return ord(ch) >= 0x2600

def title_png(lines, path, size=66, top_space=640):
    f = ImageFont.truetype(FONT, size); fe = ImageFont.truetype(EMOJI, 109)
    def emoji_img(ch):
        im = Image.new("RGBA", (136, 128), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((0, 0), ch, font=fe, embedded_color=True)
        im = im.crop(im.getbbox()); return im.resize((round(im.width * size * 1.05 / im.height), round(size * 1.05)), Image.LANCZOS)
    pad_x, pad_y, lh = 30, 16, int(size * 1.22) + 32
    canvas = Image.new("RGBA", (W, top_space), (0, 0, 0, 0)); d = ImageDraw.Draw(canvas)
    rows = []
    for line in lines:
        parts, buf = [], ""
        for ch in line:
            if is_emoji(ch) or ch == "️":
                if ch == "️": continue
                if buf: parts.append(("t", buf)); buf = ""
                parts.append(("e", emoji_img(ch)))
            else: buf += ch
        if buf: parts.append(("t", buf))
        w = sum(int(f.getlength(p)) if k == "t" else p.width + 4 for k, p in parts)
        rows.append((parts, w))
    total_h = len(rows) * lh - 6
    y = (top_space - total_h) // 2 + 30
    for parts, w in rows:  # cartouches blancs arrondis, qui se chevauchent légèrement comme sur TikTok
        x0 = (W - w) // 2 - pad_x
        d.rounded_rectangle((x0, y, x0 + w + 2 * pad_x, y + lh), radius=22, fill="white")
        x = x0 + pad_x
        for k, p in parts:
            if k == "t":
                d.text((x, y + lh // 2), p, font=f, fill="black", anchor="lm"); x += int(f.getlength(p))
            else:
                canvas.alpha_composite(p, (x + 2, y + (lh - p.height) // 2)); x += p.width + 4
        y += lh - 8
    canvas.save(path)

def main():
    job = json.load(open(sys.argv[1]))
    job.setdefault("layout", "cam"); job.pop("hook", None)
    segs = job["segments"]; dur = sum(e - s for s, e in segs)
    words = R.build_words(job)
    vid_y = job.get("vid_y", 640); vh = 608
    assf = job["out"].replace(".mp4", ".ass")
    open(assf, "w").write(R.ass(job, words, dur).replace(r"\pos(540,1450)", rf"\pos(540,{vid_y + vh + R.BAND_H + 140})"))
    tpng = job["out"].replace(".mp4", "_titre.png"); title_png(job["title"].split("|"), tpng, top_space=vid_y)
    z = R.zoom_expr(job.get("zooms") or [], amt=0.18)
    s0, e0 = segs[0][0], segs[-1][1]
    sel = "+".join(f"between(t,{s},{e})" for s, e in segs)
    f = [f"[0:v]select='{sel}',setpts=N/FRAME_RATE/TB,fps=30,scale=1920:1080,split[a][b]",
         f"[0:a]aselect='{sel}',asetpts=N/SR/TB[ra]",
         f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=30:3,eq=brightness=-0.25[bg]",
         f"[b]scale={W}:{vh},scale=w='trunc({W}*{z}/2)*2':h='trunc({vh}*{z}/2)*2':eval=frame,crop={W}:{vh}[fg]",
         f"[bg][fg]overlay=0:{vid_y}[v1]",
         f"[v1][1:v]overlay=0:{vid_y + vh}[v2]",
         (f"[2:v]format=rgba,fade=t=out:st={job['title_dur'] - 0.3}:d=0.3:alpha=1[tt]" if job.get("title_dur") else "[2:v]null[tt]"),
         f"[v2][tt]overlay=0:0:shortest=1,ass={assf},format=yuv420p[vo]",
         "[ra]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[ao]"]
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", job["src"], "-loop", "1", "-i", R.BAND, "-loop", "1", "-i", tpng,
           "-filter_complex", ";".join(f), "-map", "[vo]", "-map", "[ao]", "-t", f"{dur:.3f}",
           "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-profile:v", "high",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", job["out"]]
    subprocess.run(cmd, check=True); os.remove(assf); os.remove(tpng)
    print("ok", job["out"], f"{dur:.1f}s")

if __name__ == "__main__":
    main()
