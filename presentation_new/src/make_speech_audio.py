"""Turn SPEECH_SCRIPT.md into a single MP3 to listen to while learning the talk.

Uses Kokoro (an open neural text-to-speech model, Apache 2.0) through kokoro-onnx, run locally.
The model files are large and are not kept in the repository; download them once:

    https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0
        kokoro-v1.0.onnx   voices-v1.0.bin

Usage:
    python make_speech_audio.py MODEL_DIR OUT_DIR [voice] [speed] [lang] [natural]
    e.g. python make_speech_audio.py ~/kokoro ../ bm_george 0.95
         python make_speech_audio.py ~/kokoro ../ hf_beta 0.88 en-gb 1
         python make_speech_audio.py ~/kokoro ../ hf_beta:0.75,af_heart:0.25 0.88 en-us 1   (a blend of two voices)

"natural" = 1 speaks it the way a person would: contractions ("it is" becomes "it's") in the audio only (the
written script is unchanged), two or three sentences voiced together so the intonation flows across them, and
slightly varied pace and pauses instead of identical gaps.

Needs: pip install kokoro-onnx soundfile numpy, and ffmpeg on the PATH.
Stage directions in the script ([point], [slow]) are not spoken; [pause] becomes a short silence.
Each slide is announced ("Slide 7. Two defects in the data.") so you always know where you are.
Writes SPEECH_AUDIO.mp3 (with chapters, one per slide) and SPEECH_AUDIO_INDEX.md (slide start times).
"""
import os
import re
import subprocess
import sys
import tempfile

import json
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro
from num2words import num2words

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "SPEECH_SCRIPT.md")
LINE_GAP, SLIDE_GAP, PAUSE = 0.40, 1.30, 1.20  # seconds of silence
CHUNK_LIMIT = int(os.environ.get("CHUNK_LIMIT", "230"))  # characters per spoken chunk; shorter is crisper
SAVE_CHUNKS = os.environ.get("SAVE_CHUNKS")  # a directory: keep each spoken chunk and its text for a recognition check
# Loud and clear: remove rumble, even out quiet words, lift the consonant range, then normalise louder than a podcast.
CLEAR_CHAIN = "highpass=f=70,acompressor=threshold=-26dB:ratio=3:attack=5:release=80:makeup=5,equalizer=f=3200:t=q:w=1:g=2.5,loudnorm=I=-14:TP=-1.0:LRA=7"

NUM_WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten"}

# Spoken forms of things a text-to-speech engine would otherwise get wrong.
SUBS = [
    (r"PM2\.5", "P M two point five"),
    (r"\bARIMA\b", "Arima"),
    (r"\bGRU\b", "G R U"),
    (r"\bLSTM\b", "L S T M"),
    (r"\brMAE\b", "R M A E"),
    (r"\bOpenAQ\b", "Open A Q"),
    (r"\bCPCB\b", "C P C B"),
    (r"\bERA5\b", "E R A five"),
    (r"\bM4\b", "M four"),
    (r"Diebold-Mariano", "Dee-bold Mariano"),
        (r"\bKolmogorov-Arnold\b", "Kolmogorov Arnold"),
    (r"\bAirNow\b", "Air Now"),
    (r"\bcalmer\b", "quieter"),  # "calm" is easily misheard; "quiet" says the same thing
    (r"\bcalm\b", "quiet"),
    (r"Six extensions follow from the report\.", "There are six extensions in the report."),
    (r"uses attention across the window", "uses self-attention across the window"),
    (r"forecast-then-threshold", "forecast then threshold"),
]


def say_number(m):
    """Read numbers the way a careful speaker would: decimals digit by digit, years as years."""
    x = m.group(0).replace(",", "")
    if "." in x:
        a, b = x.split(".")
        return num2words(int(a)).replace("-", " ").replace(",", "") + " point " + " ".join(num2words(int(d)) for d in b)
    if len(x) == 4 and x[:2] in ("19", "20") and "," not in m.group(0):
        return num2words(int(x), to="year").replace("-", " ").replace(",", "")
    return num2words(int(x)).replace("-", " ").replace(",", "")


def speakable(text):
    text = re.sub(r"\*\[[^\]]*\]\*", "", text)  # *[point]* etc.
    text = text.replace("**", "").replace("*", "")
    for pat, rep in SUBS:
        text = re.sub(pat, rep, text)
    text = re.sub(r"\d[\d,]*(?:\.\d+)?", say_number, text)
    return re.sub(r"\s+", " ", text).strip()


CONTRACTIONS = [
    (r"\bI will\b", "I'll"), (r"\bI would\b", "I'd"), (r"\bI have\b", "I've"), (r"\bI am\b", "I'm"),
    (r"\bwe will\b", "we'll"), (r"\bdo not\b", "don't"), (r"\bdoes not\b", "doesn't"), (r"\bdid not\b", "didn't"),
    (r"\bis not\b", "isn't"), (r"\bare not\b", "aren't"), (r"\bwas not\b", "wasn't"), (r"\bwill not\b", "won't"),
    (r"\bcannot\b", "can't"), (r"\bcould not\b", "couldn't"), (r"\bwould not\b", "wouldn't"),
    (r"\bIt is\b", "It's"), (r"\bit is\b", "it's"), (r"\bThat is\b", "That's"), (r"\bthat is\b", "that's"),
    (r"\bThere is\b", "There's"), (r"\bHere is\b", "Here's"), (r"\bWhat is\b", "What's"), (r"\bwhat is\b", "what's"),
]


def contract(text):
    for pat, rep_ in CONTRACTIONS:
        text = re.sub(pat, rep_, text)
    return text


def chunk(lines, limit=CHUNK_LIMIT):
    """Group consecutive lines into chunks of a few sentences so intonation carries across them."""
    out, cur, cur_pause = [], "", False
    for text, pause in lines:
        if cur and (len(cur) + len(text) + 1 > limit or cur_pause):
            out.append((cur, cur_pause))
            cur, cur_pause = "", False
        cur = (cur + " " + text).strip()
        cur_pause = cur_pause or pause
    if cur:
        out.append((cur, cur_pause))
    return out


def voice_style(kokoro, spec):
    """'bm_george' or a blend such as 'hf_beta:0.75,af_heart:0.25'."""
    if ":" not in spec:
        return spec
    parts = [p.split(":") for p in spec.split(",")]
    return sum(float(w) * kokoro.get_voice_style(name) for name, w in parts)


def parse(path):
    """Return [(slide_number, title, [(line, pause_after), ...]), ...] for slides 1 to 33."""
    s = open(path, encoding="utf-8").read()
    parts = re.split(r"\n## Slide (\d+)\. ", s)
    slides = []
    for i in range(1, len(parts), 2):
        n = int(parts[i])
        head, *rest = parts[i + 1].split("\n")
        title = re.sub(r"\s*\(about[^)]*\)\s*$", "", head).strip()
        body = "\n".join(rest).split("\n---")[0]
        if n >= 34:  # the questions slide is a note to self, not speech
            continue
        lines = []
        for raw in body.split("\n"):
            if not raw.strip():
                continue
            pause = "[pause]" in raw
            t = speakable(raw)
            if t:
                lines.append((t, pause))
        slides.append((n, title, lines))
    return slides


def main():
    model_dir, out_dir = sys.argv[1], sys.argv[2]
    voice = sys.argv[3] if len(sys.argv) > 3 else "bm_george"
    speed = float(sys.argv[4]) if len(sys.argv) > 4 else 0.95
    lang = sys.argv[5] if len(sys.argv) > 5 else "en-gb"
    natural = len(sys.argv) > 6 and sys.argv[6] == "1"
    kokoro = Kokoro(os.path.join(model_dir, "kokoro-v1.0.onnx"), os.path.join(model_dir, "voices-v1.0.bin"))
    style = voice_style(kokoro, voice)
    rng = np.random.default_rng(7)  # fixed seed: the same "natural" variation every run
    slides = parse(SCRIPT)
    sr = 24000

    def silence(sec):
        return np.zeros(int(sr * sec), dtype=np.float32)

    chunks, marks, t = [], [], 0.0
    manifest = []
    if SAVE_CHUNKS:
        os.makedirs(SAVE_CHUNKS, exist_ok=True)

    checker = None
    if os.environ.get("ASR_DIR"):
        from asr_check import Checker
        checker = Checker(os.environ["ASR_DIR"])
    weak = []

    def speak(text, sp, slide):
        samples = kokoro.create(text, voice=style, speed=sp, lang=lang)[0]
        if checker:  # listen to it; if the recogniser hears different words, speak it again at another pace
            best, best_wer = samples, checker.wer(text, samples)[0]
            for alt in (speed, speed + 0.03, speed - 0.03, speed + 0.06, speed - 0.06, 0.92):
                if best_wer <= 0.04:
                    break
                cand = kokoro.create(text, voice=style, speed=float(alt), lang=lang)[0]
                w = checker.wer(text, cand)[0]
                if w < best_wer:
                    best, best_wer = cand, w
            samples = best
            if best_wer > 0.08:
                weak.append((slide, round(best_wer, 2), text[:80]))
        if SAVE_CHUNKS:
            name = f"c{len(manifest):04d}.wav"
            sf.write(os.path.join(SAVE_CHUNKS, name), samples, sr)
            manifest.append({"file": name, "slide": slide, "text": text})
        return samples

    def add(samples):
        nonlocal t
        chunks.append(samples)
        t += len(samples) / sr

    for n, title, lines in slides:
        marks.append((n, title, t))
        add(kokoro.create(f"Slide {NUM_WORDS.get(n, n)}. {title}.", voice=style, speed=speed, lang=lang)[0])
        add(silence(0.8))
        if natural:
            for text, pause in chunk([(contract(t), p) for t, p in lines]):
                sp = float(np.clip(speed + rng.uniform(-0.03, 0.03), 0.6, 1.2))
                add(speak(text, sp, n))
                gap = LINE_GAP + rng.uniform(-0.08, 0.12) + (0.25 if text.rstrip().endswith("?") else 0)
                add(silence(gap + (PAUSE if pause else 0)))
        else:
            for text, pause in lines:
                add(speak(text, speed, n))
                add(silence(LINE_GAP + (PAUSE if pause else 0)))
        add(silence(SLIDE_GAP))
        print(f"slide {n:>2} done at {t / 60:5.1f} min", flush=True)

    audio = np.concatenate(chunks)
    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, "speech.wav")
        sf.write(wav, audio, sr)
        meta = os.path.join(tmp, "chapters.txt")
        with open(meta, "w", encoding="utf-8") as f:
            f.write(";FFMETADATA1\ntitle=MTH5000 oral presentation: speech\nartist=Jaykumar Vinodbhai Chauhan\n")
            for k, (n, title, start) in enumerate(marks):
                end = marks[k + 1][2] if k + 1 < len(marks) else t
                f.write(f"[CHAPTER]\nTIMEBASE=1/1000\nSTART={int(start * 1000)}\nEND={int(end * 1000)}\ntitle=Slide {n}. {title}\n")
        mp3 = os.path.join(out_dir, "SPEECH_AUDIO.mp3")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-i", meta, "-map_metadata", "1", "-map_chapters", "1",
                        "-af", CLEAR_CHAIN, "-codec:a", "libmp3lame", "-b:a", "96k", "-ac", "1", mp3], check=True)

    if SAVE_CHUNKS:
        json.dump(manifest, open(os.path.join(SAVE_CHUNKS, "manifest.json"), "w"), indent=1)
    if checker:
        print(f"chunks still above 8% word error after retries: {len(weak)}")
        for w in weak:
            print("  ", w)
    mm = lambda x: f"{int(x // 60)}:{int(x % 60):02d}"
    with open(os.path.join(out_dir, "SPEECH_AUDIO_INDEX.md"), "w", encoding="utf-8") as f:
        f.write(f"# Speech audio: where each slide starts\n\nVoice: {voice}, speed {speed}. Total length {mm(t)}.\n\n| Slide | Title | Starts at |\n|---|---|---|\n")
        for n, title, start in marks:
            f.write(f"| {n} | {title} | {mm(start)} |\n")
    print("wrote", mp3, "length", mm(t))


if __name__ == "__main__":
    main()
