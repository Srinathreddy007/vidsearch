from sentence_transformers import SentenceTransformer
from faster_whisper import WhisperModel
import subprocess, os, tempfile
import numpy as np


_model_st = None
_model_whisper = None

def get_st_model():
    global _model_st
    if _model_st is None:
        _model_st = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _model_st

def get_whisper_model():
    global _model_whisper
    if _model_whisper is None:
        _model_whisper = WhisperModel("small", device="cpu", compute_type="int8")
    return _model_whisper

def extract_audio(input_video_path: str) -> str:
    wav_path = tempfile.mktemp(suffix=".wav")
    command = [
        "ffmpeg",
        "-i",
        input_video_path,
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        wav_path
    ]
    subprocess.check_call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return wav_path
def transcribe_to_word_segments(video_path: str, language: str | None = None ):
    whisper = get_whisper_model()
    wav_path = extract_audio(video_path)
    try:
        segments, _ = whisper.transcribe(wav_path, beam_size=5, language=language, word_timestamps=True)

        words = []

        for segment in segments:
            for word in segment.words:
                words.append({"start": float(word.start), "end": float(word.end), "text": word.word})

            if not words:
                words.append({"start": float(segment.start), "end": float(segment.end), "text": segment.text})

        return words
    except Exception as e:
        print(f"Error transcribing video: {e}")
        return []

    finally:
        
        try:
            os.remove(wav_path)
        except Exception:
            pass
    
# def rechunk_words(words, target_window_s: float = 5.0, max_window_s: float = 8.0):
#     # pass
#     chunks = []
#     if not chunks:
#         return []

#     cur = {"start": words[0]["start"], "end": words[0]["end"], "texts": [words[0]["text"]]}
#     for word in words[1:]:
#         pass
#         if cur["end"] - cur["start"] + (word["end"] - word["start"]) <= max_window_s:
#             cur["end"] = word["end"]
#             cur["texts"].append(word["text"])
#         else:
#             chunks.append(cur)
#             cur = {"start": word["start"], "end": word["end"], "texts": [word["text"]]}
#     chunks.append({
#         "start": cur["start"], "end": cur["end"],
#         "text": " ".join(cur["texts"]).strip()
#     })
#     return [c for c in chunks if c["text"]]
def rechunk_words(words, target_window_s: float = 5.0, max_window_s: float = 8.0):
    """
    Merge consecutive words into short windows ~5s (cap at 8s).
    """
    chunks = []
    if not words: return chunks
    cur = {"start": words[0]["start"], "end": words[0]["end"], "texts": [words[0]["text"]]}
    for w in words[1:]:
        next_end = float(w["end"])
        # Extend if we are under target window or the next word still keeps us <= max window
        if (cur["end"] - cur["start"] < target_window_s) or (next_end - cur["start"] <= max_window_s):
            cur["end"] = next_end
            cur["texts"].append(w["text"])
        else:
            chunks.append({
                "start": cur["start"], "end": cur["end"],
                "text": " ".join(cur["texts"]).strip()
            })
            cur = {"start": float(w["start"]), "end": next_end, "texts": [w["text"]]}
    # last
    chunks.append({
        "start": cur["start"], "end": cur["end"],
        "text": " ".join(cur["texts"]).strip()
    })
    # prune empties
    return [c for c in chunks if c["text"]]


def embed_texts(texts: list[str]) -> list[list[float]]:
    st = get_st_model()
    vecs = st.encode(texts, normalize_embeddings=True)  # cosine-friendly
    return [v.tolist() for v in np.asarray(vecs)]

def cosine_sim(a: np.ndarray, B: np.ndarray) -> np.ndarray:
    # inputs assumed normalized
    return (B @ a)
    
