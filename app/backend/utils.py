import os
import datetime
import logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
PRODUCT_DIR = os.path.join(BASE_DIR, "product_created")
TRANSCRIPTS_DIR = os.path.join(PRODUCT_DIR, "transcripts")
LOGS_DIR = os.path.join(PRODUCT_DIR, "logs")

os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(LOGS_DIR, "system_log.txt"),
    level=logging.INFO,
    format="[%(asctime)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def get_session_filename():
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d_%H-%M_session.txt")

def log_message(msg):
    logging.info(msg)
    print(msg)  # also console for debugging