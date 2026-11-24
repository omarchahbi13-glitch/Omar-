"""Détecte les moments forts d'un live d'après le chat et découpe les extraits.
Usage : python3 live_watch.py <dossier_live> <dossier_sortie>
- chat.tsv (live_chat.py) : messages par fenêtre de 10 s ; pic = fenêtre >= max(2,5 x médiane des 10 dernières min, médiane + 12)
  ou beaucoup de messages « rire / hype » (MDR, PTDR, KEKW, OMEGALUL, LUL, 😂, 💀, W, GG, OH…).
- Pour chaque pic (un toutes les 2 min max) : extrait [pic - 40 s, pic + 10 s] depuis les seg_*.mp4 (live_record.py)
  -> <sortie>/cand_<epoch>.mp4 + cand_<epoch>.chat.txt (messages autour du pic) ; liste dans <sortie>/candidats.tsv
- Son : volume seconde par seconde ; pic = au moins 3 s sur 6 s à +10 dB au-dessus de la médiane des 10 dernières min
  (cris, gros fous rires, choc). Même découpe.
- Supprime les seg_*.mp4 de plus de 25 min (place disque).
"""
import os, re, sys, time, glob, statistics, subprocess, math
import numpy as np
live, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
HYPE = re.compile(r"(mdr|ptdr|xd|kekw|omegalul|lul|lmao|😂|🤣|💀|😭|ahah|haha|jpp|wtf|oh+ |dinguerie|incroyable|pog|w+$|gg)", re.I)
done = set(float(l.split("\t")[0]) for l in open(os.path.join(out, "candidats.tsv"))) if os.path.exists(os.path.join(out, "candidats.tsv")) else set()
last_peak = max(done) if done else 0
def segs():
    r = []
    for l in open(os.path.join(live, "index.tsv")):
        e, n = l.split(); p = os.path.join(live, n)
        if os.path.exists(p): r.append((int(e), p))
    return sorted(r)
def cut(t0, t1, dst):
    parts = [(e, p) for e, p in segs() if e <= t1 and e + 330 >= t0]
    if not parts: return False
    tmp = []
    for k, (e, p) in enumerate(parts):
        q = dst + f".p{k}.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", p, "-c", "copy", "-avoid_negative_ts", "make_zero", q])
        tmp.append((e, q))
    lst = dst + ".txt"
    open(lst, "w").write("".join(f"file '{os.path.abspath(q)}'\n" for _, q in tmp))
    joined = dst + ".join.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined])
    ss = max(t0 - tmp[0][0], 0)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{ss:.2f}", "-i", joined, "-t", f"{t1 - t0:.2f}",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-c:a", "aac", "-b:a", "192k", dst])
    for _, q in tmp: os.remove(q)
    os.remove(lst); os.remove(joined)
    return os.path.exists(dst)
loud = {}  # epoch (s) -> dB
def update_loudness():
    for e, p in segs()[-2:]:
        raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", p, "-vn", "-ac", "1", "-ar", "8000", "-f", "s16le", "-"],
                             capture_output=True).stdout
        a = np.frombuffer(raw, np.int16).astype(np.float32)
        for k in range(len(a) // 8000):
            x = a[k * 8000:(k + 1) * 8000]
            loud[e + k] = 20 * math.log10(float(np.sqrt((x * x).mean())) + 1)
    for t in [t for t in loud if t < time.time() - 900]: del loud[t]
def audio_peaks():
    if len(loud) < 300: return []
    med = statistics.median(loud.values()); ks = sorted(loud); res = []
    for t in ks[-60:]:
        w = [loud.get(t + i, 0) for i in range(6)]
        if sum(v > med + 10 for v in w) >= 3: res.append((t, med))
    return res
while True:
    try:
        update_loudness()
        for t, med in audio_peaks():
            b = t + 3
            if b - last_peak < 120 or time.time() - b < 25: continue
            dst = os.path.join(out, f"cand_{b}.mp4")
            if cut(b - 40, b + 15, dst):
                open(dst.replace(".mp4", ".chat.txt"), "w").write("(pic de son : cris / rires)")
                open(os.path.join(out, "candidats.tsv"), "a").write(f"{b}\tSON\t{loud[t]:.0f}dB\t{med:.0f}dB\t{time.strftime('%H:%M:%S', time.localtime(b))}\n")
                done.add(b); last_peak = b
                print("pic son", b, flush=True)
        now = time.time(); msgs = []
        for l in open(os.path.join(live, "chat.tsv")):
            p = l.rstrip("\n").split("\t", 2)
            if len(p) == 3 and float(p[0]) > now - 900: msgs.append((float(p[0]), p[2]))
        bins = {}
        for t, m in msgs:
            b = int(t // 10) * 10; c = bins.setdefault(b, [0, 0]); c[0] += 1; c[1] += bool(HYPE.search(m))
        keys = sorted(bins)
        if len(keys) > 12:
            med = statistics.median(bins[k][0] for k in keys[:-1]) or 1
            for b in keys[-6:-1]:  # fenêtres complètes récentes
                n, h = bins[b]
                if b in done or b - last_peak < 120: continue
                if (n >= max(2.5 * med, med + 12)) or (h >= 8 and h >= 0.5 * n):
                    dst = os.path.join(out, f"cand_{b}.mp4")
                    if now - b < 25: continue  # attendre que la vidéo suive
                    if cut(b - 40, b + 15, dst):
                        around = [m for t, m in msgs if b - 15 <= t <= b + 20]
                        open(dst.replace(".mp4", ".chat.txt"), "w").write("\n".join(around))
                        open(os.path.join(out, "candidats.tsv"), "a").write(f"{b}\t{n}\t{h}\t{med:.1f}\t{time.strftime('%H:%M:%S', time.localtime(b))}\n")
                        done.add(b); last_peak = b
                        print("pic", b, n, h, med, flush=True)
        for e, p in segs():
            if now - e > 1500: os.remove(p)
    except Exception as ex:
        print("erreur", ex, flush=True)
    time.sleep(20)
