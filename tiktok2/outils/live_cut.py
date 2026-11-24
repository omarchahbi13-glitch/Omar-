"""Découpe un passage du live par heure de diffusion : python3 live_cut.py <dossier_live> <t0> <t1> <sortie.mp4>
Aussi : python3 live_cut.py <dossier_live> resume [minutes]  -> transcript + messages du chat par minute (pour choisir les histoires)."""
import os, sys, time, subprocess
live = sys.argv[1]
def segs():
    r = []
    for l in open(os.path.join(live, "index.tsv")):
        e, n = l.split(); p = os.path.join(live, n)
        if os.path.exists(p): r.append((int(e), p))
    return sorted(r)
def file_map(p):
    m = []
    if os.path.exists(p + ".map"):
        for l in open(p + ".map"):
            o, t = l.split(); m.append((float(o), float(t)))
    return m
def cut(t0, t1, dst):
    """Découpe [t0, t1] (heure de diffusion) grâce aux .map ; un morceau par fichier, puis assemblage."""
    pieces = []
    for e, p in segs():
        m = file_map(p)
        inside = [o for o, t in m if t0 <= t <= t1]
        if not inside: continue
        a, b = min(inside), max(inside) + 2.0
        q = dst + f".p{len(pieces)}.mp4"
        tmp = dst + ".remux.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", p, "-c", "copy", "-avoid_negative_ts", "make_zero", tmp])
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.2f}", "-i", tmp, "-t", f"{b - a:.2f}",
                        "-vf", "fps=30", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-c:a", "aac", "-ar", "48000", "-b:a", "192k", q])
        os.remove(tmp)
        if os.path.exists(q): pieces.append(q)
    if not pieces: return False
    if len(pieces) == 1: os.replace(pieces[0], dst)
    else:
        lst = dst + ".txt"; open(lst, "w").write("".join(f"file '{os.path.abspath(q)}'\n" for q in pieces))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", dst])
        for q in pieces: os.remove(q)
        os.remove(lst)
    return os.path.exists(dst) and os.path.getsize(dst) > 100000

if sys.argv[2] == "resume":
    mins = float(sys.argv[3]) if len(sys.argv) > 3 else 20
    since = time.time() - mins * 60
    chat = {}
    for l in open(os.path.join(live, "chat.tsv")):
        p = l.split("\t", 2)
        if len(p) == 3 and float(p[0]) > since: chat[int(float(p[0]) // 60)] = chat.get(int(float(p[0]) // 60), 0) + 1
    last = None
    for l in open(os.path.join(live, "transcript.tsv")):
        t, txt = l.rstrip("\n").split("\t", 1); t = float(t)
        if t < since: continue
        mn = int(t // 60)
        if mn != last:
            print(f"--- {time.strftime('%H:%M', time.localtime(t))}  chat {chat.get(mn + 0, 0)}/min"); last = mn
        print(f"{t:.0f} {txt}")
else:
    print(cut(float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]))
