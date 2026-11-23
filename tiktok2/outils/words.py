# Mots horodatés (Whisper medium) d'un fichier wav : python3 words.py a1.wav c1.words.json
import json, sys, wave, numpy as np
from faster_whisper import WhisperModel
w = wave.open(sys.argv[1]); a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
m = WhisperModel("medium", device="cpu", compute_type="int8", cpu_threads=4)
segs, _ = m.transcribe(a, language="fr", word_timestamps=True, beam_size=5, vad_filter=True)
words = []
for s in segs:
    print(f"[{s.start:5.1f}-{s.end:5.1f}] {s.text}", flush=True)
    words += [{"w": x.word, "s": x.start, "e": x.end} for x in s.words]
json.dump(words, open(sys.argv[2], "w"), ensure_ascii=False)
