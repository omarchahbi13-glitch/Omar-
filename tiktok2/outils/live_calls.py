"""Repère les appels dans la transcription d'un live (« allô ») et les classe par réaction du chat.
Usage : python3 live_calls.py <dossier_live> [déjà_vus.txt]
Affiche pour chaque appel : début, fin estimée (prochain appel ou +180 s), messages du chat/min pendant l'appel, rires dans le chat, extrait."""
import os, re, sys
live = sys.argv[1]
seen = set(open(sys.argv[2]).read().split()) if len(sys.argv) > 2 and os.path.exists(sys.argv[2]) else set()
tr = [(float(t), x) for t, x in (l.rstrip("\n").split("\t", 1) for l in open(os.path.join(live, "transcript.tsv")))]
chat = [(float(p[0]), p[2]) for p in (l.rstrip("\n").split("\t", 2) for l in open(os.path.join(live, "chat.tsv"))) if len(p) == 3]
starts = []
for t, x in tr:
    if re.search(r"\ball[oô]\b", x, re.I) and (not starts or t - starts[-1] > 90):
        starts.append(t)
for i, s in enumerate(starts):
    e = min(starts[i + 1] if i + 1 < len(starts) else s + 180, s + 240)
    if e > tr[-1][0]: e = tr[-1][0]
    if e - s < 25 or str(int(s)) in seen: continue
    msgs = [m for t, m in chat if s + 5 <= t <= e + 15]
    laughs = sum(bool(re.search(r"(mdr|ptdr|xd|kekw|lul|😂|🤣|💀|ahah|haha|jpp)", m, re.I)) for m in msgs)
    rate = len(msgs) / max((e - s + 10) / 60, 0.5)
    txt = " ".join(x for t, x in tr if s <= t <= e)
    print(f"{int(s)}\t{int(e)}\t{rate:.0f}/min\trires={laughs}\t{txt[:400]}")
