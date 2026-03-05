from fastapi import FastAPI
from fastapi import BackgroundTasks
from pydantic import BaseModel
from .processor import StreamProcessor
from .utils import log_message
import threading

app = FastAPI(title="FlowScribe Backend")

processors = {}  # url -> processor
lock = threading.Lock()

class KeywordAction(BaseModel):
    keyword: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/start_stream")
async def start_stream(
    url: str,
    background_tasks: BackgroundTasks,
    source_type: str = "rtsp"  # default last
):
    print(f"Starting {source_type} stream: {url}")
    with lock:
        if url in processors:
            return {"message": "already running"}
        proc = StreamProcessor(url, source_type)
        processors[url] = proc
        background_tasks.add_task(proc.start)  # non-blocking
    return {"message": "started", "url": url}

@app.post("/stop_stream")
def stop_stream(url: str):
    with lock:
        if url in processors:
            processors[url].stop()
            del processors[url]
    return {"message": "stopped"}

@app.get("/transcript")
def get_transcript():
    lines = []
    alerts = []
    for proc in processors.values():
        lines.append(proc.get_latest_transcript())
        alerts.extend(proc.get_alerts())
    return {
        "transcript": "\n\n".join(lines),
        "alerts": alerts
    }

@app.post("/add_keyword")
def add_keyword(action: KeywordAction):
    for proc in processors.values():
        proc.add_keyword(action.keyword)
    return {"message": f"added {action.keyword}"}

@app.post("/remove_keyword")
def remove_keyword(action: KeywordAction):
    for proc in processors.values():
        proc.remove_keyword(action.keyword)
    return {"message": f"removed {action.keyword}"}

@app.get("/keywords")
def get_keywords():
    if not processors:
        return {"keywords": []}
    # return from first processor (they share)
    return {"keywords": processors[next(iter(processors))].keywords}

@app.post("/stop_all")
def stop_all():
    with lock:
        stopped_count = 0
        for url, proc in list(processors.items()):
            proc.stop()
            del processors[url]
            stopped_count += 1
    log_message(f"Stopped {stopped_count} streams")
    return {"message": f"Stopped {stopped_count} active streams"}