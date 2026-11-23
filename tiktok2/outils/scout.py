# Transcription rapide d'une vidéo entière pour repérer les meilleurs moments
import sys, subprocess, numpy as np
from faster_whisper import WhisperModel
src, out = sys.argv[1], sys.argv[2]
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                     check=True, capture_output=True).stdout
audio = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
m = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=4)
segs, _ = m.transcribe(audio, language="fr", vad_filter=True, beam_size=1)
with open(out, "w") as f:
    for s in segs:
        f.write(f"[{int(s.start//60):02d}:{s.start%60:04.1f}] {s.text.strip()}\n"); f.flush()
