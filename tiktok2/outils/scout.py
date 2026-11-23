# Transcription rapide d'une vidéo entière pour repérer les meilleurs moments
import sys, json
from faster_whisper import WhisperModel
src, out = sys.argv[1], sys.argv[2]
m = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=4)
segs, _ = m.transcribe(src, language="fr", vad_filter=True, beam_size=1)
with open(out, "w") as f:
    for s in segs:
        f.write(f"[{int(s.start//60):02d}:{s.start%60:04.1f}] {s.text.strip()}\n"); f.flush()
