import os
import sys
import asyncio
import subprocess
import edge_tts
from anthropic import Anthropic

ANTHROPIC_BASE_URL = "https://agentrouter.org"
LLM_API_KEY = os.environ.get("LLM_API_KEY")
LLM_MODEL = os.environ.get("LLM_MODEL", "claude-3-5-sonnet-20241022")

if not LLM_API_KEY:
    print("Error: LLM_API_KEY environment variable is not set.")
    sys.exit(1)

# WAF bypass headers (mimics Codex CLI)
WAF_BYPASS_HEADERS = {
    "User-Agent": "codex_cli_rs/0.101.0",
    "Originator": "codex_cli_rs",
    "X-App": "cli",
}

# Use the SYNCHRONOUS Anthropic client
client = Anthropic(
    api_key=LLM_API_KEY,
    base_url=ANTHROPIC_BASE_URL,
    default_headers=WAF_BYPASS_HEADERS,
)

def _generate_script_sync(topic: str) -> str:
    print(f"Requesting script from AgentRouter using model: {LLM_MODEL}")
    response = client.messages.create(
        model=LLM_MODEL,
        max_tokens=1024,
        system="You are a professional technical YouTube scriptwriter. Write a short, engaging 1-minute script.",
        messages=[
            {
                "role": "user",
                "content": f"Write a script about: {topic}. Do not include scene directions, just the spoken text."
            }
        ]
    )
    return response.content[0].text

async def generate_script(topic: str) -> str:
    return await asyncio.to_thread(_generate_script_sync, topic)

async def generate_audio(text: str, output_file: str):
    print("Generating audio with Edge-TTS...")
    communicate = edge_tts.Communicate(text, "en-US-AndrewNeural")
    await communicate.save(output_file)
    print(f"Audio saved to {output_file}")

def create_video(audio_file: str, output_file: str):
    print("Rendering video with FFmpeg...")
    command = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=blue:s=1280x720:d=60",
        "-i", audio_file,
        "-shortest",
        "-c:v", "libx264", "-tune", "stillimage",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        output_file
    ]
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        print("FFmpeg Error Output:")
        print(result.stderr)
        raise RuntimeError(f"FFmpeg failed with exit code {result.returncode}")
    if not os.path.exists(output_file):
        raise FileNotFoundError(f"FFmpeg finished, but {output_file} was not created.")

def main():
    topic = "The new features in Python 3.14"
    audio_file = "voiceover.mp3"
    video_file = "final_video.mp4"
    print(f"Starting pipeline for topic: {topic}")
    try:
        script_text = asyncio.run(generate_script(topic))
        print("Script generated successfully.")
        asyncio.run(generate_audio(script_text, audio_file))
        print("Audio generated successfully.")
        create_video(audio_file, video_file)
        print(f"Pipeline completed. Output saved to {video_file}")
    except Exception as e:
        print(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
