import os
import sys
import asyncio
import subprocess
import edge_tts
import requests
from openai import OpenAI

# =====================================================================
# ⚠️ SECURITY WARNING: DO NOT COMMIT YOUR ACTUAL "sk-..." KEY HERE
# If you paste it here and push to GitHub, GitHub will auto-revoke it.
# Instead, put it in GitHub Settings -> Secrets -> Actions as LLM_API_KEY
# =====================================================================

# 1. Setup AgentRouter Credentials
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://agentrouter.org/v1")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "sk-9tT8c3wNq03GNwFzaTmb1Y20XM7c5r9bcpHQVqYwmCs9m09U")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-6.1-sol")

# 2. Setup n8n Webhook (Optional - if you want to route data there)
N8N_WEBHOOK_URL = os.environ.get("N8N_WEBHOOK_URL", "https://your-n8n-instance.com/webhook/your-id")

# Initialize the AgentRouter client (OpenAI compatible)
client = OpenAI(
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL
)

def generate_script(topic: str) -> str:
    """Uses AgentRouter (gpt-6.1-sol) to generate a video script."""
    print(f"🧠 Generating script for topic: {topic}")
    
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": "You are a professional technical YouTube scriptwriter. Write a short, engaging 1-minute script."},
            {"role": "user", "content": f"Write a script about: {topic}. Do not include scene directions, just the spoken text."}
        ]
    )
    
    script = response.choices[0].message.content
    print("✅ Script generated successfully.")
    return script

async def generate_audio(text: str, output_file: str):
    """Uses free Edge-TTS to generate voiceover."""
    print("🎙️ Generating audio with Edge-TTS...")
    # Using a standard, high-quality Microsoft voice
    communicate = edge_tts.Communicate(text, "en-US-AndrewNeural")
    await communicate.save(output_file)
    print(f"✅ Audio saved to {output_file}")

def create_video(audio_file: str, output_file: str):
    """Uses FFmpeg to combine a static background with the audio."""
    print("🎬 Rendering video with FFmpeg...")
    
    # We use FFmpeg to generate a simple blue background with the text/audio
    # In a full pipeline, you would download stock footage here
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
    
    subprocess.run(command, check=True)
    print(f"✅ Video saved to {output_file}")

def trigger_n8n_webhook(video_path: str, script_text: str):
    """Sends the finished assets to n8n for further routing/uploading."""
    if N8N_WEBHOOK_URL == "https://your-n8n-instance.com/webhook/your-id":
        print("⏭️ Skipping n8n webhook (URL not configured).")
        return
        
    print("🔗 Triggering n8n webhook...")
    payload = {
        "status": "success",
        "video_path": video_path,
        "script_preview": script_text[:100] + "..."
    }
    
    try:
        response = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=10)
        response.raise_for_status()
        print("✅ n8n webhook triggered successfully.")
    except Exception as e:
        print(f"⚠️ Failed to trigger n8n webhook: {e}")

def main():
    print("🚀 Starting YouTube Video Generation Pipeline...")
    
    topic = "The new features in Python 3.14"
    audio_file = "voiceover.mp3"
    video_file = "final_video.mp4"

    try:
        # Step 1: Generate Script via AgentRouter
        script_text = generate_script(topic)
        
        # Step 2: Generate Audio via Edge-TTS
        asyncio.run(generate_audio(script_text, audio_file))
        
        # Step 3: Render Video via FFmpeg
        create_video(audio_file, video_file)
        
        # Step 4: Trigger n8n Router
        trigger_n8n_webhook(video_file, script_text)
        
        print("🎉 Pipeline completed successfully!")
        
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
