import json, wave, numpy as np, sys
from faster_whisper import WhisperModel
m = WhisperModel("medium", device="cpu", compute_type="int8", cpu_threads=4)
for n in sys.argv[1:]:
    w=wave.open(f"multi/v/a{n}.wav"); a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768
    segs,info = m.transcribe(a, word_timestamps=True, beam_size=5, vad_filter=True)
    words=[]; text=[]
    for s in segs:
        text.append(f"[{s.start:5.1f}-{s.end:5.1f}] {s.text}")
        words += [{"w":x.word,"s":x.start,"e":x.end} for x in s.words]
    json.dump(words, open(f"multi/v/g{n}.words.json","w"), ensure_ascii=False)
    print(f"=== g{n} ({info.language})"); print("\n".join(text), flush=True)
