"""Render a vertical TikTok edit from a 1920x1080 Twitch clip.

Usage: python3 render.py <job.json>
job = {src, out, words, segments:[[s,e],...], layout:"split"|"cam",
       cam:[x,y,w,h], game_x, face_x, hook, zooms:[[s,e],...] (output time),
       fixes:{"old":"new"}, drop:[word indices to drop]}
"""
import json, re, subprocess, sys

W, H = 1080, 1920
CAM_H = 640
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


def ass(job, words, dur):
    sub_y = CAM_H if job["layout"] == "split" else 1300
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
    for ch in chunks(words):
        end_chunk = ch[-1]["e"] + 0.25
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
            ev.append(f"Dialogue: 1,{ts(st)},{ts(min(en, dur))},Cap,,0,0,0,,"
                      + r"{\an5\pos(540," + str(sub_y) + ")}" + pop + " ".join(parts))
    return hdr + "\n".join(ev) + "\n"


def zoom_expr(zooms, amt=0.14):
    if not zooms:
        return "1"
    terms = "+".join(f"between(t,{a},{b})" for a, b in zooms)
    return f"(1+{amt}*min(1,{terms}))"


def main():
    job = json.load(open(sys.argv[1]))
    segs = job["segments"]
    dur = sum(e - s for s, e in segs)
    words = build_words(job)
    assf = job["out"].replace(".mp4", ".ass")
    open(assf, "w").write(ass(job, words, dur))

    f = []
    for k, (s, e) in enumerate(segs):
        f.append(f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS,fps=30[v{k}]")
        f.append(f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st={e-s-0.03:.3f}:d=0.03[a{k}]")
    f.append("".join(f"[v{k}][a{k}]" for k in range(len(segs))) + f"concat=n={len(segs)}:v=1:a=1[cv][ca]")
    z = zoom_expr(job.get("zooms"))
    if job["layout"] == "split":
        x, y, cw, ch = job["cam"]
        gx = job.get("game_x", 504)
        f.append("[cv]split[c1][c2]")
        f.append(f"[c1]crop={cw}:{ch}:{x}:{y},scale={W}:{CAM_H}:force_original_aspect_ratio=increase,"
                 f"scale=w='trunc({W}*{z}/2)*2':h='trunc({CAM_H}*{z}/2)*2':eval=frame,crop={W}:{CAM_H}[cam]")
        f.append(f"[c2]crop=911:1080:{gx}:0,scale={W}:{H-CAM_H}[game]")
        f.append("[cam][game]vstack[st]")
    else:  # webcam-only source: tall crop around the face
        fx = job["face_x"]
        cw = 608
        f.append(f"[cv]crop={cw}:1080:{fx - cw // 2}:0,scale={W}:{H},"
                 f"scale=w='trunc({W}*{z}/2)*2':h='trunc({H}*{z}/2)*2':eval=frame,crop={W}:{H}[st]")
    f.append(f"[st]ass={assf},format=yuv420p[vo]")
    f.append("[ca]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[ao]")
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", job["src"], "-filter_complex", ";".join(f),
           "-map", "[vo]", "-map", "[ao]", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
           "-profile:v", "high", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", job["out"]]
    subprocess.run(cmd, check=True)
    print("ok", job["out"], f"{dur:.1f}s")


if __name__ == "__main__":
    main()
