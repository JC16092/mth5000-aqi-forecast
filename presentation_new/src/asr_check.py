"""Listen to synthesised speech and compare it with the text it was meant to say.

Used by make_speech_audio.py (when ASR_DIR is set) to re-speak any chunk the recogniser cannot understand.
Needs: pip install sherpa-onnx jiwer num2words, and the Whisper small.en model from
https://github.com/k2-fsa/sherpa-onnx/releases/tag/asr-models  (sherpa-onnx-whisper-small.en).
"""
import re

import jiwer
import numpy as np
import sherpa_onnx
from num2words import num2words


def _digits(t):
    t = re.sub(r"(?<=\d),(?=\d{3})", "", t)

    def f(m):
        x = m.group(0)
        if "." in x:
            a, b = x.split(".")
            return num2words(int(a)) + " point " + " ".join(num2words(int(d)) for d in b)
        if len(x) == 4 and x[:2] in ("19", "20"):
            return num2words(int(x), to="year")
        return num2words(int(x))

    return re.sub(r"\d+(?:\.\d+)?", f, t)


def normalise(text):
    t = _digits(text.lower().replace("%", " percent"))
    t = re.sub(r"[^a-z' ]", " ", t.replace("-", " "))
    t = (t.replace("modelling", "modeling").replace("optimiser", "optimizer").replace("characterised", "characterized")
          .replace("colour", "color").replace("metres", "meters").replace("metre", "meter").replace("kilometres", "kilometers")
          .replace("favourable", "favorable").replace("vermillion", "vermilion").replace("organised", "organized"))
    toks, out, i = t.split(), [], 0
    while i < len(toks):  # collapse spelled-out letters: "p m" -> "pm"
        j = i
        while j < len(toks) and len(toks[j]) == 1 and toks[j] not in ("a", "i"):
            j += 1
        if j - i >= 2:
            out.append("".join(toks[i:j]))
            i = j
        else:
            out.append(toks[i])
            i += 1
    return " ".join(out)


class Checker:
    def __init__(self, model_dir):
        m = model_dir.rstrip("/") + "/"
        self.rec = sherpa_onnx.OfflineRecognizer.from_whisper(
            encoder=m + "small.en-encoder.int8.onnx", decoder=m + "small.en-decoder.int8.onnx",
            tokens=m + "small.en-tokens.txt", language="en", task="transcribe", num_threads=4)

    def hear(self, samples_24k):
        w16 = np.interp(np.arange(0, len(samples_24k), 1.5), np.arange(len(samples_24k)), samples_24k).astype(np.float32)
        st = self.rec.create_stream()
        st.accept_waveform(16000, w16)
        self.rec.decode_stream(st)
        return st.result.text

    def wer(self, ref_text, samples_24k):
        hyp = self.hear(samples_24k)
        return jiwer.wer(normalise(ref_text), normalise(hyp)), hyp
