import os
import sys
import asyncio
import subprocess
import edge_tts
from openai import OpenAI

LLM_BASE_URL = "https://agentrouter.org/v1"
LLM_MODEL = "gpt-6.1-sol"
LLM_API_KEY = os.environ.get("sk-9tT8c3wNq03GNwFzaTmb1Y20XM7c5r9bcpHQVqYwmCs9m09U")

if not LLM_API_KEY:
    print("Error: LLM_API_KEY environment variable is not set.")
    sys.exit(1)

client = OpenAI(
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL
)

def generate_script(topic: str) -> str:
    """Generates a technical video script using the AgentRouter API."""
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system", 
                "content": "You are a professional technical YouTube scriptwriter. Write a short, engaging 1-minute script."
            },
            {
                "role": "user", 
                "content": f"Write a script about: {topic}. Do not include scene directions, just the spoken text."
            }
        ]
    )
    return response.choices[0].message.content

async def generate_audio(text: str, output_file: str):
    """Generates an MP3 voiceover from text using Edge-TTS."""
    communicate = edge_tts.Communicate(text, "en-US-AndrewNeural")
    await communicate.save(output_file)

def create_video(audio_file: str, output_file: str):
    """Uses FFmpeg to render a video by combining a background with the generated audio."""
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
    subprocess.run(command, check=True, capture_output=True, text=True)

def main():
    """Orchestrates the video generation pipeline."""
    topic = "The new features in Python 3.14"
    audio_file = "voiceover.mp3"
    video_file = "final_video.mp4"

    print(f"Starting pipeline for topic: {topic}")
    
    try:
        print("Generating script...")
        script_text = generate_script(topic)
        
        print("Generating audio...")
        asyncio.run(generate_audio(script_text, audio_file))
        
        print("Rendering video...")
        create_video(audio_file, video_file)
        
        print(f"Pipeline completed. Output saved to {video_file}")
        
    except Exception as e:
        print(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
