"""Turn SPEECH_SCRIPT.md into a single MP3 to listen to while learning the talk.

Uses Kokoro (an open neural text-to-speech model, Apache 2.0) through kokoro-onnx, run locally.
The model files are large and are not kept in the repository; download them once:

    https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0
        kokoro-v1.0.onnx   voices-v1.0.bin

Usage:
    python make_speech_audio.py MODEL_DIR OUT_DIR [voice] [speed]
    e.g. python make_speech_audio.py ~/kokoro ../ bm_george 0.95

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

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "SPEECH_SCRIPT.md")
LINE_GAP, SLIDE_GAP, PAUSE = 0.40, 1.30, 1.20  # seconds of silence

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
    (r"\b1990\b", "nineteen ninety"),
    (r"\bKolmogorov-Arnold\b", "Kolmo-gorov Arnold"),
]


def speakable(text):
    text = re.sub(r"\*\[[^\]]*\]\*", "", text)  # *[point]* etc.
    text = text.replace("**", "").replace("*", "")
    for pat, rep in SUBS:
        text = re.sub(pat, rep, text)
    text = re.sub(r"(?<=\d),(?=\d{3}\b)", "", text)  # 3,093 -> 3093
    return re.sub(r"\s+", " ", text).strip()


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
    kokoro = Kokoro(os.path.join(model_dir, "kokoro-v1.0.onnx"), os.path.join(model_dir, "voices-v1.0.bin"))
    slides = parse(SCRIPT)
    sr = 24000

    def silence(sec):
        return np.zeros(int(sr * sec), dtype=np.float32)

    chunks, marks, t = [], [], 0.0

    def add(samples):
        nonlocal t
        chunks.append(samples)
        t += len(samples) / sr

    for n, title, lines in slides:
        marks.append((n, title, t))
        add(kokoro.create(f"Slide {NUM_WORDS.get(n, n)}. {title}.", voice=voice, speed=speed, lang="en-gb")[0])
        add(silence(0.8))
        for text, pause in lines:
            add(kokoro.create(text, voice=voice, speed=speed, lang="en-gb")[0])
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
                        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-codec:a", "libmp3lame", "-b:a", "96k", "-ac", "1", mp3], check=True)

    mm = lambda x: f"{int(x // 60)}:{int(x % 60):02d}"
    with open(os.path.join(out_dir, "SPEECH_AUDIO_INDEX.md"), "w", encoding="utf-8") as f:
        f.write(f"# Speech audio: where each slide starts\n\nVoice: {voice}, speed {speed}. Total length {mm(t)}.\n\n| Slide | Title | Starts at |\n|---|---|---|\n")
        for n, title, start in marks:
            f.write(f"| {n} | {title} | {mm(start)} |\n")
    print("wrote", mp3, "length", mm(t))


if __name__ == "__main__":
    main()
