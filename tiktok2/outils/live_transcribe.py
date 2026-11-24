"""Transcrit le live au fil de l'eau (Whisper small) pour repérer les histoires complètes.
Usage : python3 live_transcribe.py <dossier_live>  -> <dossier_live>/transcript.tsv (heure_de_diffusion<TAB>texte)
Ne traite un seg_*.mp4 qu'une fois terminé (un plus récent existe)."""
import os, sys, time, glob, subprocess, numpy as np
from faster_whisper import WhisperModel
live = sys.argv[1]
m = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=2)
done = set()
while True:
    files = sorted(glob.glob(os.path.join(live, "seg_*.mp4")))
    for p in files[:-1]:
        if p in done or not os.path.exists(p + ".map"): continue
        mp = [tuple(map(float, l.split())) for l in open(p + ".map")]
        raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", p, "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
        a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
        segs, _ = m.transcribe(a, language="fr", vad_filter=True, beam_size=1)
        with open(os.path.join(live, "transcript.tsv"), "a") as f:
            for s in segs:
                t = next((tt + (s.start - o) for o, tt in reversed(mp) if o <= s.start), mp[0][1] + s.start)
                f.write(f"{t:.1f}\t{s.text.strip()}\n")
        done.add(p)
        print("transcrit", os.path.basename(p), flush=True)
    time.sleep(30)
