import os
import sys
import asyncio
import subprocess
import edge_tts
from anthropic import Anthropic

# AgentRouter's Anthropic-compatible endpoint
ANTHROPIC_BASE_URL = "https://agentrouter.org"
LLM_API_KEY = os.environ.get("LLM_API_KEY")
# Use a valid Anthropic model name
LLM_MODEL = os.environ.get("LLM_MODEL", "claude-3-5-sonnet-20240620")

if not LLM_API_KEY:
    print("Error: LLM_API_KEY environment variable is not set.")
    sys.exit(1)

# These headers mimic the official Claude Code CLI, which is required to bypass AgentRouter's WAF.
# This is the equivalent of what your local LLM proxy does.
claude_code_headers = {
    "User-Agent": "claude-cli/2.1.137 (external, sdk-cli)",
    "anthropic-beta": "claude-code-20250219,interleaved-thinking-2025-05-14,effort-2025-11-24",
    "x-app": "cli",
    "x-stainless-lang": "js",
    "x-stainless-package-version": "0.60.0",
    "x-stainless-os": "MacOS",
    "x-stainless-arch": "arm64",
    "x-stainless-runtime": "node",
    "x-stainless-runtime-version": "v22.14.0",
}

client = Anthropic(
    api_key=LLM_API_KEY,
    base_url=ANTHROPIC_BASE_URL,
    default_headers=claude_code_headers,
)

def generate_script(topic: str) -> str:
    """Generates a technical video script using the AgentRouter (Anthropic SDK)."""
    print(f"Requesting script from AgentRouter using model: {LLM_MODEL}")
    
    try:
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
        
        # The anthropic SDK returns a different structure
        return response.content[0].text
        
    except Exception as e:
        print(f"Error during API call: {e}")
        raise

async def generate_audio(text: str, output_file: str):
    """Generates an MP3 voiceover from text using Edge-TTS."""
    print("Generating audio...")
    communicate = edge_tts.Communicate(text, "en-US-AndrewNeural")
    await communicate.save(output_file)

def create_video(audio_file: str, output_file: str):
    """Uses FFmpeg to render a video by combining a background with the generated audio."""
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
    """Orchestrates the video generation pipeline."""
    topic = "The new features in Python 3.14"
    audio_file = "voiceover.mp3"
    video_file = "final_video.mp4"

    print(f"Starting pipeline for topic: {topic}")
    
    try:
        script_text = generate_script(topic)
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
