import edge_tts
import asyncio
import os
import nest_asyncio

# Apply nest_asyncio to allow nested event loops in Streamlit
nest_asyncio.apply()

OUTPUT_DIR = "temp_audio"

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

async def _generate_worker(text, filename, voice):
    """
    Async worker to communicate with Edge TTS service.
    """
    print(f"[Audio] Starting generation for: {text[:15]}...")
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(filename)
    print(f"[Audio] File saved: {filename}")

def generate_audio(text, filename, voice="ja-JP-NanamiNeural"):
    """
    Synchronous wrapper for generating audio.
    """
    filepath = os.path.join(OUTPUT_DIR, filename)
    abs_filepath = os.path.abspath(filepath)
    
    print(f"[Audio] Request: {text[:20]} -> {filename}")
    
    try:
        # With nest_asyncio, we can typically just call asyncio.run() 
        # or use the current loop safely.
        loop = asyncio.get_event_loop()
        if loop.is_running():
            print("[Audio] Using existing loop")
            loop.run_until_complete(_generate_worker(text, abs_filepath, voice))
        else:
            print("[Audio] Creating new loop")
            asyncio.run(_generate_worker(text, abs_filepath, voice))
             
        if os.path.exists(abs_filepath):
            return abs_filepath
        else:
            print("[Audio] Error: File not found after generation attempt.")
            return None
            
    except Exception as e:
        print(f"[Audio] Critical Error: {e}")
        return None
