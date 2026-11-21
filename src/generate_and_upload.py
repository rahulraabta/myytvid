import os
import sys
import asyncio
import subprocess
import edge_tts
import json
from curl_cffi import requests

# AgentRouter's OpenAI-compatible endpoint
LLM_BASE_URL = "https://agentrouter.org/v1"
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-6.1-sol")
LLM_API_KEY = os.environ.get("LLM_API_KEY")

if not LLM_API_KEY:
    print("Error: LLM_API_KEY environment variable is not set.")
    sys.exit(1)

def generate_script(topic: str) -> str:
    """Generates a technical video script using AgentRouter with a browser TLS fingerprint."""
    print(f"Requesting script from AgentRouter using model: {LLM_MODEL}")
    
    url = f"{LLM_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": LLM_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are a professional technical YouTube scriptwriter. Write a short, engaging 1-minute script."
            },
            {
                "role": "user",
                "content": f"Write a script about: {topic}. Do not include scene directions, just the spoken text."
            }
        ]
    }

    try:
        # impersonate="chrome110" mimics the TLS handshake of a real browser
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            impersonate="chrome110",
            timeout=120
        )
        
        if response.status_code != 200:
            print(f"HTTP Error {response.status_code}: {response.text[:500]}")
            raise RuntimeError(f"API request failed with status {response.status_code}")
            
        data = response.json()
        return data["choices"][0]["message"]["content"]
        
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
