"""Render a vertical TikTok edit from a 1920x1080 Twitch clip.

Usage: python3 render.py <job.json>
job = {src, out, words, segments:[[s,e],...], layout:"split"|"cam"|"camfocus", layouts:[per segment] (optional),
       cam:[x,y,w,h], game_x, face_x, hook, zooms:[[s,e],...] (output time),
       fixes:{"old":"new"}, drop:[word indices to drop]}
"""
import json, re, subprocess, sys

W, H = 1080, 1920
CAM_H = 640
BAND = "brand/band.png"
BAND_H = 64
FONT = "Inter Display Black"


def ts(t):
    t = max(t, 0)
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def remap(t, segs):
    off = 0.0
    for s, e in segs:
        if s <= t <= e:
            return off + t - s
        off += e - s
    return None


def build_words(job):
    words = json.load(open(job["words"]))
    out = []
    fixes = job.get("fixes", {})
    for w in words:
        if any(a <= w["s"] < b for a, b in job.get("drop_ranges", [])):
            continue
        key = re.sub(r"[^\w']", "", w["w"].strip().lower())
        if key in fixes:
            w = dict(w, w=re.sub(re.escape(key), fixes[key], w["w"], flags=re.I))
        s, e = remap(w["s"], job["segments"]), remap(w["e"], job["segments"])
        if s is None:
            continue
        if e is None:
            e = s + 0.3
        tok = w["w"].strip()
        if out and (tok[:1] in "'’-" or out[-1]["w"][-1:] in "'’-" or tok in ("?", "!")):
            out[-1]["w"] += tok; out[-1]["e"] = e
            continue
        out.append({"w": tok, "s": s, "e": e})
    return [w for w in out if w["w"]]


def chunks(words, maxw=3):
    cur = []
    for w in words:
        if cur and (len(cur) >= maxw or w["s"] - cur[-1]["e"] > 0.45
                    or re.search(r"[.!?,]$", cur[-1]["w"])):
            yield cur; cur = []
        cur.append(w)
    if cur:
        yield cur


def clean(t):
    return re.sub(r"[.,]", "", t).upper().replace("{", "").replace("}", "")


CF_Y = 420  # top of the enlarged webcam in "camfocus" layout


def seg_layouts(job):
    n = len(job["segments"])
    return job.get("layouts") or [job["layout"]] * n


def geometry(job, layout):
    """Return (band_y, caption_y) for a layout."""
    if layout == "split":
        return CAM_H, CAM_H + BAND_H + 120
    if layout == "camfocus":
        x, y, cw, ch = job["cam"]
        hc = round(W * ch / cw / 2) * 2
        return CF_Y + hc, CF_Y + hc + BAND_H + 130
    return CAM_H, 1450  # "cam": full-frame webcam source


def ass(job, words, dur):
    segs, lays = job["segments"], seg_layouts(job)
    bounds, off = [], 0.0
    for (s, e), lay in zip(segs, lays):
        bounds.append((off, off + e - s, geometry(job, lay)[1])); off += e - s
    def sub_y_at(t):
        for a, b, y in bounds:
            if a <= t < b:
                return y
        return bounds[-1][2]
    hdr = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{FONT},88,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,9,4,5,60,60,0,1
Style: Hook,{FONT},70,&H00000000,&H00000000,&H00FFFFFF,&H00FFFFFF,-1,0,0,0,100,100,0,0,3,18,0,8,70,70,120,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    if job.get("hook"):
        ev.append(f"Dialogue: 2,{ts(0)},{ts(3.2)},Hook,,0,0,0,,"
                  r"{\fad(0,250)\t(0,120,\fscx108\fscy108)\t(120,240,\fscx100\fscy100)}" + job["hook"])
    caps = []  # [start_cs, end_cs, text] in centiseconds
    for ch in chunks(words):
        end_chunk = ch[-1]["e"] + 0.25
        y = sub_y_at(ch[0]["s"])
        for i, w in enumerate(ch):
            st = w["s"]
            en = ch[i + 1]["s"] if i + 1 < len(ch) else end_chunk
            parts = []
            for j, x in enumerate(ch):
                t = clean(x["w"])
                if j == i:
                    parts.append(r"{\c&H00E5FF&\fscx112\fscy112\t(0,90,\fscx100\fscy100)}" + t + r"{\c&HFFFFFF&}")
                else:
                    parts.append(t)
            pop = r"{\t(0,80,\fscx104\fscy104)\t(80,160,\fscx100\fscy100)}" if i == 0 else ""
            caps.append([round(st * 100), round(min(en, dur) * 100),
                         r"{\an5\pos(540," + str(y) + ")}" + pop + " ".join(parts)])
    # Only one caption on screen at a time: each one ends exactly when the next begins.
    caps.sort(key=lambda c: c[0])
    for k in range(len(caps) - 1):
        caps[k][1] = min(caps[k][1], caps[k + 1][0])
    for s, e, text in caps:
        if e > s:
            ev.append(f"Dialogue: 1,{ts(s / 100)},{ts(e / 100)},Cap,,0,0,0,,{text}")
    return hdr + "\n".join(ev) + "\n"


def zoom_expr(zooms, amt=0.14):
    if not zooms:
        return "1"
    terms = "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in zooms)
    return f"(1+{amt}*min(1,{terms}))"


def layout_filter(job, layout, src, out, z):
    """Filter chain turning a 1920x1080 stream [src] into a 1080x1920 frame [out] (without band)."""
    f = []
    if layout == "split":
        x, y, cw, ch = job["cam"]
        gx = job.get("game_x", 504)
        f.append(f"[{src}]split[{out}c1][{out}c2]")
        f.append(f"[{out}c1]crop={cw}:{ch}:{x}:{y},scale={W}:{CAM_H}:force_original_aspect_ratio=increase,"
                 f"scale=w='trunc({W}*{z}/2)*2':h='trunc({CAM_H}*{z}/2)*2':eval=frame,crop={W}:{CAM_H}[{out}cam]")
        gh = H - CAM_H - BAND_H
        gw = round(1080 * W / gh)
        gx = min(max(gx + (911 - gw) // 2, 0), 1920 - gw)
        f.append(f"[{out}c2]crop={gw}:1080:{gx}:0,scale={W}:{gh},pad={W}:{H-CAM_H}:0:{BAND_H}[{out}game]")
        f.append(f"[{out}cam][{out}game]vstack[{out}]")
    elif layout == "camfocus":  # small webcam box enlarged, blurred copy as background
        x, y, cw, ch = job["cam"]
        hc = round(W * ch / cw / 2) * 2
        f.append(f"[{src}]crop={cw}:{ch}:{x}:{y},split[{out}b][{out}f]")
        f.append(f"[{out}b]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=24:2,eq=brightness=-0.18[{out}bg]")
        f.append(f"[{out}f]scale={W}:{hc},scale=w='trunc({W}*{z}/2)*2':h='trunc({hc}*{z}/2)*2':eval=frame,crop={W}:{hc}[{out}fg]")
        f.append(f"[{out}bg][{out}fg]overlay=0:{CF_Y}[{out}]")
    else:  # webcam-only source: tall crop around the face
        fx = job["face_x"]
        cw = 608
        f.append(f"[{src}]crop={cw}:1080:{fx - cw // 2}:0,scale={W}:{H},"
                 f"scale=w='trunc({W}*{z}/2)*2':h='trunc({H}*{z}/2)*2':eval=frame,crop={W}:{H}[{out}]")
    return f


def main():
    job = json.load(open(sys.argv[1]))
    segs, lays = job["segments"], seg_layouts(job)
    dur = sum(e - s for s, e in segs)
    words = build_words(job)
    assf = job["out"].replace(".mp4", ".ass")
    open(assf, "w").write(ass(job, words, dur))

    f, off = [], 0.0
    zooms = job.get("zooms") or []
    for k, ((s, e), lay) in enumerate(zip(segs, lays)):
        d = e - s
        local = [(max(a - off, 0), min(b - off, d)) for a, b in zooms if b > off and a < off + d]
        f.append(f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS,fps=30[r{k}]")
        f += layout_filter(job, lay, f"r{k}", f"l{k}", zoom_expr(local))
        f.append(f"[l{k}][{k + 1}:v]overlay=0:{geometry(job, lay)[0]}:shortest=1,setsar=1[v{k}]")
        f.append(f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st={d-0.03:.3f}:d=0.03[a{k}]")
        off += d
    f.append("".join(f"[v{k}][a{k}]" for k in range(len(segs))) + f"concat=n={len(segs)}:v=1:a=1[cv][ca]")
    f.append(f"[cv]ass={assf},format=yuv420p[vo]")
    f.append("[ca]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[ao]")
    bands = []
    for _ in segs:
        bands += ["-loop", "1", "-i", BAND]
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", job["src"], *bands, "-filter_complex", ";".join(f),
           "-map", "[vo]", "-map", "[ao]", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
           "-profile:v", "high", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", job["out"]]
    subprocess.run(cmd, check=True)
    print("ok", job["out"], f"{dur:.1f}s")


if __name__ == "__main__":
    main()
