import asyncio
import os
import sys

from .ai_engine import AIEngine
from .vts_manager import VTSManager
from .tools.vision import capture_screen, resize_image_for_llm
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def process_user_input(engine, vts_manager, user_text, screenshot_path=None):
    images = []
    if screenshot_path and os.path.exists(screenshot_path):
        resized = resize_image_for_llm(screenshot_path)
        images.append(resized)
    
    # Send to VLM
    response = engine.generate_response(user_text, images)
    text = response.get("response", "[Error thinking]")
    emotion = response.get("emotion", "neutral")
    think_process = response.get("think", "")
    
    return text, emotion, think_process

async def run_pipeline():
    vts = VTSManager()
    await vts.connect()
    
    engine = AIEngine()
    
    print("\n===============================")
    print("Welcome to Sakuna AI.")
    print("Type your message or type 'q' to quit.")
    print("If you ask about 'screen', it will take a screenshot.")
    print("===============================\n")
    
    # Dummy loop substituting for Voice Activity Detection for now
    # until VAD is fully tested
    while True:
        try:
            # Placeholder for VAD: Using standard input
            user_text = input("\nYou: ")
            
            if user_text.lower() in ('q', 'quit', 'exit'):
                break
                
            screenshot_path = None
            if 'screen' in user_text.lower():
                print("Taking screen capture...")
                screenshot_path = capture_screen("capture.png")
            
            print("Thinking...")
            text, emotion, think_process = process_user_input(engine, vts, user_text, screenshot_path)
            
            if think_process.strip():
                # Print the AI's internal monologue in gray purely out of curiosity (this is never spoken aloud)
                print(f"\033[90m[Sakuna Inner Thought]: {think_process}\033[0m")
            
            print(f"\nSakuna: {text} | Mood: [{emotion}]")
            
            # Map emotion to Live2D
            await vts.trigger_emotion(emotion)
            
            # Play TTS
            print("Playing TTS (using mac say temporarily)...")
            
            # Clean up the text text so 'say' command doesn't misinterpret " or ' or backticks
            safe_text = text.replace("'", "").replace('"', "")
            os.system(f'say -v "Kyoko" "{safe_text}"')
            
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    asyncio.run(run_pipeline())
