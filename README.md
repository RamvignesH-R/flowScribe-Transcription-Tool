## FlowScribe -- Real-time Legislative Transcription and Alert System

FlowScribe is a web-based application that transcribes live video streams such as YouTube Live broadcasts or RTSP/IP camera feeds in near real time. The system continuously converts speech to text, detects custom keywords, triggers alerts, performs speaker diarization, and automatically saves transcripts.

The application is designed for monitoring legislative sessions, parliamentary debates, public hearings, or any live discussions where instant transcription and keyword-based notifications are useful.

* * * * *

Live Deployment

FlowScribe is publicly accessible through the following deployment:

<https://flowscribe-transcription-tool.onrender.com/>

You can open the dashboard in your browser and test the system by providing a live YouTube stream URL or RTSP stream. The application will begin processing the stream and display near real-time transcripts while triggering alerts when configured keywords are detected.

Note: The public deployment runs on limited compute resources. Performance may be slower compared to running the application locally with GPU acceleration.

* * * * *

Features

- Near real-time speech-to-text transcription with approximately 2--5 seconds latency using the tiny.en model\
- Support for YouTube Live streams and RTSP/IP camera feeds\
- Custom keyword detection (for example: "vote", "bill passed", or "objection") with automatic alerts\
- Visual alerts in the dashboard and audio alerts in the browser\
- Speaker diarization using pyannote.audio (executed after the stream stops in the MVP version)\
- Live scrolling transcript interface\
- Automatic saving of transcripts as text files\
- Downloadable transcripts stored in a project folder\
- Lightweight Streamlit dashboard connected to a FastAPI backend\
- Docker support with optional NVIDIA GPU acceleration

* * * * *

Technology Stack

Backend\
FastAPI (Python)

Transcription Engine\
faster-whisper using the tiny.en model for faster inference

Speaker Diarization\
pyannote.audio version 3.1

Audio Extraction\
yt-dlp and ffmpeg-python

Frontend\
Streamlit dashboard interface

Deployment\
Docker containers with optional NVIDIA CUDA GPU acceleration

* * * * *

System Requirements

- Python version 3.10 or higher\
- NVIDIA GPU recommended for faster transcription (CPU is supported but slower)\
- FFmpeg installed and available in the system PATH\
- Deno installed for yt-dlp YouTube extraction support\
- Hugging Face access token for pyannote audio models

Create an environment file named ".env" in the project root and add your Hugging Face token.

Example configuration:

HF_TOKEN = your_huggingface_token_here

* * * * *

Quick Local Setup

Step 1 --- Clone the repository

Clone the GitHub repository and navigate to the project directory on your system.

Step 2 --- Install dependencies

Install all required Python packages using the requirements file.

Step 3 --- Create environment configuration

Create a ".env" file in the project root directory and add your Hugging Face token.

Step 4 --- Start the backend server

Run the FastAPI backend using Uvicorn.

Step 5 --- Start the dashboard

Run the Streamlit dashboard in a separate terminal window.

Step 6 --- Access the application

Open a browser and navigate to the following address:

<http://localhost:8501>

Paste a currently live YouTube stream URL that shows a red LIVE badge, choose "youtube" as the stream type, and click "Start Stream".

* * * * *

Docker Setup (Recommended)

The system can also be deployed using Docker containers.

Build and start the services using Docker Compose.

After the containers start successfully, open the browser and access the dashboard at:

<http://localhost:8501>

If GPU acceleration is required, make sure the NVIDIA Container Toolkit is installed on the host system.

* * * * *

Project Structure

flowscribe

app\
 backend -- FastAPI server and stream processing logic\
 frontend -- Streamlit dashboard interface

product_created\
 transcripts -- saved transcription text files\
 logs -- system log file

docker -- Dockerfile and docker-compose configuration

.env.example -- example environment configuration\
requirements.txt -- list of project dependencies\
beep.wav -- optional alert sound file\
README -- project documentation

* * * * *

Troubleshooting

Problem: No transcript appears after starting the stream\
Solution: Ensure the YouTube stream is actually live and displays the red LIVE badge with active chat.

Problem: yt-dlp errors occur\
Solution: Upgrade yt-dlp and confirm that Deno is installed and accessible in the system PATH.

Problem: ffmpeg command not found\
Solution: Install FFmpeg and add the ffmpeg bin directory to the system PATH.

Problem: Backend server timeout or connection error\
Solution: Ensure the backend URL in dashboard.py is set to <http://127.0.0.1:8502>.

Problem: Transcription is slow\
Solution: Use the tiny.en model with GPU acceleration if available.

Problem: Transcript file not saved after stopping\
Solution: Check backend logs for the "Saved:" message and confirm that audio was processed correctly.

* * * * *

Future Improvements

- WebSocket integration for true real-time streaming updates instead of polling\
- Continuous speaker diarization using rolling audio buffers\
- Direct transcript download button from the dashboard\
- Improved user interface using NiceGUI or React\
- Support for monitoring multiple streams simultaneously\
- Keyword highlighting within transcripts
