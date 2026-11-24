"""Enregistre un live Twitch (sans pubs) en morceaux de 5 min + horodatage.
Usage : python3 live_record.py <chaine> <dossier>
Écrit <dossier>/seg_<epoch>.mp4 (un fichier par tranche de 5 min) et <dossier>/index.tsv (epoch_debut, fichier, durée).
Python pur (requests passe par le proxy ; ffmpeg ne sait pas le faire).
"""
import os, sys, time, subprocess, requests
ch, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
S = requests.Session()
def media_url():
    r = subprocess.run(["yt-dlp", "-g", "-f", "best[height<=720]/best", f"https://www.twitch.tv/{ch}"],
                       capture_output=True, text=True, timeout=90)
    return r.stdout.strip().splitlines()[-1] if r.returncode == 0 and r.stdout.strip() else None
seen, cur, cur_start, url = set(), None, 0, None
init_url, init_data = None, b""
idx = open(os.path.join(out, "index.tsv"), "a")
fails = 0
while True:
    try:
        if not url:
            url = media_url()
            if not url:
                fails += 1
                if fails > 20: print("live terminé ?", flush=True); break
                time.sleep(30); continue
        txt = S.get(url, timeout=15).text
        if "#EXTM3U" not in txt: url = None; continue
        fails = 0
        lines = txt.splitlines()
        for l in lines:  # segments fMP4 : l'en-tête (EXT-X-MAP) doit commencer chaque fichier
            if l.startswith("#EXT-X-MAP:"):
                u = l.split('URI="')[1].split('"')[0]
                if u != init_url: init_url, init_data = u, S.get(u, timeout=20).content
        for i, l in enumerate(lines):
            if l.startswith("#EXTINF") and i + 1 < len(lines):
                seg = lines[i + 1]
                if seg in seen: continue
                seen.add(seg)
                if not l.rstrip().endswith(",live"): continue  # pubs Twitch
                dur = float(l.split(":")[1].split(",")[0])
                now = time.time()
                if cur is None or now - cur_start > 300:
                    if cur: cur.close()
                    cur_start = now; name = f"seg_{int(now)}.mp4"
                    cur = open(os.path.join(out, name), "ab"); cur.write(init_data)
                    idx.write(f"{int(now)}\t{name}\n"); idx.flush()
                cur.write(S.get(seg, timeout=20).content); cur.flush()
        if len(seen) > 5000: seen = set(list(seen)[-500:])
        time.sleep(2)
    except Exception as e:
        print("erreur", e, flush=True); url = None; time.sleep(5)
