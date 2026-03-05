import queue
import threading
import time
import os
import datetime
import numpy as np
import soundfile as sf
import subprocess
import torch
from faster_whisper import WhisperModel
from pyannote.audio import Pipeline
from dotenv import load_dotenv
import ffmpeg

from .utils import log_message, TRANSCRIPTS_DIR, get_session_filename


load_dotenv()

class StreamProcessor:
    def __init__(self, source_url, source_type="rtsp", model_size="tiny.en"):
        self.source_url = source_url
        self.source_type = source_type.lower()
        self.model_size = model_size
        self.transcript_lines = []
        self.full_audio = []
        self.keywords = ["vote", "motion", "objection", "bill passed", "adjourned"]
        self.alerts = []
        self.running = False
        self.thread = None
        self.audio_queue = queue.Queue()
        self.transcript_file = os.path.join(TRANSCRIPTS_DIR, get_session_filename())

        log_message(f"Processor initialized for {source_url} ({source_type})")

        self.asr_model = WhisperModel(
            self.model_size,
            device="cuda" if torch.cuda.is_available() else "cpu",
            compute_type="float16" if torch.cuda.is_available() else "int8"
        )
        self.diarization = None

    def start(self):
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self._process_loop, daemon=True)
        self.thread.start()
        log_message(f"Stream started: {self.source_url}")

    def stop(self):
        self.running = False
        if self.thread: self.thread.join(timeout=10.0)
        self._run_diarization()
        self._save_transcript()
        log_message(f"Stream stopped: {self.source_url}")

    def _process_loop(self):
        try:
            audio_gen, sr = self._get_audio_stream()
            chunk_duration = 2
            samples_per_chunk = int(sr * chunk_duration)
            buffer = np.array([], dtype=np.float32)

            for raw_chunk in audio_gen:
                if not self.running: break
                buffer = np.append(buffer, raw_chunk)

                while len(buffer) >= samples_per_chunk:
                    chunk = buffer[:samples_per_chunk]
                    buffer = buffer[samples_per_chunk:]
                    self.full_audio.extend(chunk)

                    segments, _ = self.asr_model.transcribe(
                        chunk,
                        beam_size=1,
                        language="en",
                        vad_filter=True,
                        vad_parameters=dict(min_silence_duration_ms=500)
                    )

                    timestamp = time.strftime("%H:%M:%S")
                    for seg in segments:
                        text = seg.text.strip()
                        if text:
                            line = f"[{timestamp}] Speaker ?: {text}"
                            self.transcript_lines.append(line)

                            lower_text = text.lower()
                            for kw in self.keywords:
                                if kw in lower_text:
                                    alert = f"ALERT: '{kw}' at {timestamp}"
                                    self.alerts.append(alert)
                                    log_message(alert)

                    time.sleep(0.05)

        except Exception as e:
            log_message(f"Processing error: {str(e)}")
        finally:
            self.running = False

    def _get_audio_stream(self):
        sr = 16000
        if self.source_type == "youtube":
            yt_cmd = [
                "yt-dlp",
                "--remote-components", "ejs:github",
                "--js-runtimes", "deno:C:/Users/ramvi/.deno/bin/deno.exe",
                "-f", "bestaudio/best",
                "--get-url",
                self.source_url
            ]
            try:
                audio_url = subprocess.check_output(yt_cmd, stderr=subprocess.STDOUT).decode().strip()
                log_message(f"yt-dlp extracted URL: {audio_url}")
            except subprocess.CalledProcessError as e:
                log_message(f"yt-dlp FAILED: {e.output.decode()}")
                raise

            process = (
                ffmpeg
                .input(audio_url)
                .output('pipe:', format='s16le', acodec='pcm_s16le', ac=1, ar=sr)
                .run_async(pipe_stdout=True, pipe_stderr=subprocess.PIPE)
            )

            # Debug ffmpeg errors
            def log_stderr():
                for line in process.stderr:
                    log_message(f"ffmpeg stderr: {line.decode().strip()}")
            threading.Thread(target=log_stderr, daemon=True).start()

        else:  # rtsp
            process = (
                ffmpeg
                .input(self.source_url)
                .output('pipe:', format='s16le', acodec='pcm_s16le', ac=1, ar=sr)
                .run_async(pipe_stdout=True, pipe_stderr=subprocess.PIPE)
            )

            def log_stderr():
                for line in process.stderr:
                    log_message(f"ffmpeg stderr: {line.decode().strip()}")
            threading.Thread(target=log_stderr, daemon=True).start()

        def generator():
            chunk_count = 0
            while True:
                in_bytes = process.stdout.read(4096)
                if not in_bytes:
                    log_message("ffmpeg pipe closed - no more data")
                    break
                chunk_count += 1
                if chunk_count % 10 == 0:
                    log_message(f"Received {chunk_count} chunks from ffmpeg")
                yield np.frombuffer(in_bytes, np.int16).astype(np.float32) / 32768.0

        return generator(), sr

    def add_keyword(self, kw: str):
        kw = kw.lower().strip()
        if kw and kw not in self.keywords:
            self.keywords.append(kw)

    def remove_keyword(self, kw: str):
        kw = kw.lower().strip()
        self.keywords = [k for k in self.keywords if k != kw]

    def _run_diarization(self):
        if not self.full_audio or len(self.full_audio) < 16000:
            return

        try:
            if self.diarization is None:
                token = os.getenv("HF_TOKEN")
                if not token:
                    log_message("No HF_TOKEN – skipping diarization")
                    return
                self.diarization = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    token=token
                )
                log_message("Diarization loaded")

            temp_wav = os.path.join(TRANSCRIPTS_DIR, "temp.wav")
            sf.write(temp_wav, np.array(self.full_audio), 16000)

            if self.diarization is not None:
                diarization_result = self.diarization(temp_wav)
                speakers = set()
                for turn, _, spk in diarization_result.itertracks(yield_label=True):
                    speakers.add(spk)
                log_message(f"Diarization done – {len(speakers)} speakers")
            else:
                log_message("Diarization skipped (not loaded)")

            os.remove(temp_wav)

        except Exception as e:
            log_message(f"Diarization failed: {str(e)}")

    def _save_transcript(self):
        try:
            with open(self.transcript_file, "w", encoding="utf-8") as f:
                f.write("\n".join(self.transcript_lines))
            log_message(f"Saved: {self.transcript_file}")
        except Exception as e:
            log_message(f"Save failed: {e}")

    def get_latest_transcript(self):
        return "\n".join(self.transcript_lines[-50:])

    def get_alerts(self):
        return self.alerts[-10:]