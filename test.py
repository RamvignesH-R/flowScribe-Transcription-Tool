import os
from dotenv import load_dotenv
from pyannote.audio import Pipeline

load_dotenv()

token = os.getenv("HF_TOKEN")
print("Token loaded:", "yes" if token else "MISSING!")

try:
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
         token =os.getenv("HF_TOKEN")
    )
    print("SUCCESS: Model loaded!")
except Exception as e:
    print("ERROR:", str(e))