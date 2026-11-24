"""Transcrit un candidat de live (Whisper medium, mots horodatés) : python3 review.py cand.mp4 -> cand.words.json + texte."""
import json, sys, subprocess, numpy as np
from faster_whisper import WhisperModel
src = sys.argv[1]
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
m = WhisperModel("medium", device="cpu", compute_type="int8", cpu_threads=4)
segs, _ = m.transcribe(a, language="fr", word_timestamps=True, beam_size=5, vad_filter=False, condition_on_previous_text=False)
words = []
for s in segs:
    print(f"[{s.start:5.1f}-{s.end:5.1f}] {s.text}", flush=True)
    words += [{"w": x.word, "s": x.start, "e": x.end} for x in s.words]
json.dump(words, open(src.replace(".mp4", ".words.json"), "w"), ensure_ascii=False)
