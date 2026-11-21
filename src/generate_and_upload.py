import os
import sys
import asyncio
import subprocess
import edge_tts
from anthropic import Anthropic

# AgentRouter's Anthropic-compatible endpoint
ANTHROPIC_BASE_URL = "https://agentrouter.org"
LLM_API_KEY = os.environ.get("LLM_API_KEY")
LLM_MODEL = os.environ.get("LLM_MODEL", "claude-3-5-sonnet-20240620") # Use an Anthropic model name, e.g., 'claude-3-5-sonnet'

if not LLM_API_KEY:
    print("Error: LLM_API_KEY environment variable is not set.")
    sys.exit(1)

# The sync Anthropic client is on AgentRouter's allowlist
client = Anthropic(
    api_key=LLM_API_KEY,
    base_url=ANTHROPIC_BASE_URL,
)

def _generate_script_sync(topic: str) -> str:
    """Synchronous call to the Anthropic-compatible endpoint."""
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
    """Asynchronously generates a script by running the sync call in a thread."""
    print(f"Requesting script from AgentRouter (Anthropic SDK) for model: {LLM_MODEL}")
    try:
        # Run the blocking synchronous call in a separate thread
        script = await asyncio.to_thread(_generate_script_sync, topic)
        return script
    except Exception as e:
        print(f"Error during API call: {e}")
        raise

# ... (keep your existing generate_audio, create_video, and main functions) ...
