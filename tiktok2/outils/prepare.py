"""Prépare un extrait d'une vidéo YouTube 480p/720p pour render.py.
Usage : python3 prepare.py <source.mp4> <debut_s> <fin_s> <nom>
Crée travail/<nom>.mp4 (agrandi en 1920x1080), travail/<nom>.wav,
et affiche les segments normaux / gros plans (détectés via la barre bleue « POUR LES 25K » sous la webcam).
"""
import subprocess, sys, json, numpy as np
src, a, b, nom = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
clip, wav = f"travail/{nom}.mp4", f"travail/{nom}.wav"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(a), "-t", str(b - a), "-i", src, "-map", "0:0", "-map", "0:1",
                "-vf", "scale=1920:1080:flags=lanczos,unsharp=5:5:0.6", "-c:v", "libx264", "-crf", "16", "-preset", "fast",
                "-c:a", "aac", "-b:a", "192k", clip], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", clip, "-ac", "1", "-ar", "16000", wav], check=True)
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", clip, "-vf", "fps=10,crop=300:20:1450:345,scale=1:1",
                      "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
px = np.frombuffer(raw, np.uint8).reshape(-1, 3)
normal = [(p[2] > 150 and p[0] < 120) for p in px]
# lisser : ignorer les changements de moins de 0,3 s
bounds, cur, start = [], normal[0], 0
for i, v in enumerate(normal + [not normal[-1]]):
    if v != cur:
        if (i - start) >= 3 or not bounds:
            bounds.append([start / 10, i / 10, "split" if cur else "camfocus"])
        else:
            bounds[-1][1] = i / 10
        cur, start = v, i
merged = []
for s, e, l in bounds:
    if merged and merged[-1][2] == l: merged[-1][1] = e
    else: merged.append([s, e, l])
print(json.dumps(merged))
