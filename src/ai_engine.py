import json
import mlx_whisper
from mlx_vlm import load, generate, stream_generate
from mlx_vlm.prompt_utils import get_message_json
from mlx_vlm.utils import ThinkingBudgetCriteria, load_config
from .config import VLM_MODEL_ID
from .tools.tool_registry import registry

class AIEngine:
    def __init__(self, model_id=VLM_MODEL_ID):
        print(f"Loading Vision-Language Model: {model_id}...")
        # Load the MLX VLM model and processor
        self.model, self.processor = load(model_id)
        self.config = load_config(model_id)
        print("VLM Model loaded successfully.")
        
        # Note: mlx_whisper automatically downloads/loads the model on first transcribe call,
        # but we can optionally specify a path. We'll use the default base/small for performance.
        self.whisper_model = "mlx-community/whisper-small-mlx-fp16"
        print(f"Whisper Model will use: {self.whisper_model}")

        self.system_prompt = """You are Sakuna, a helpful and expressive anime-style virtual assistant.

TOOLS AND THINKING:
You have access to tools that you can call to gather information or perform actions.
Since your thinking budget is restricted in your final JSON output, you MUST rely on your `think` tool if you need to reason extensively.
If you want to use a tool, output a JSON object exactly like this and NOTHING else:
{"tool": "tool_name", "kwargs": {"arg_name": "arg_value"}}
Do NOT output the final response when you call a tool. Wait for the tool result to be provided to you.

FINAL RESPONSE:
When you have finished gathering information or thinking (or if you don't need to use a tool), you must return EXACTLY ONE valid JSON object.
Your very first output MUST be the { character.
The JSON MUST contain these exact three keys:
"think": Keep this short. For casual chat, leave it empty (""). If you already used the `think` tool, don't repeat the thoughts.
"response": The text of your spoken answer to the user.
"emotion": A single word describing your current emotion (neutral, happy, sad, angry, surprised, thinking).

Example - Simple:
{"think": "", "response": "Hey there! How's your day going?", "emotion": "happy"}
"""
        self.tool_registry = registry

    def transcribe_audio(self, audio_file_path: str) -> str:
        """
        Transcribes an audio file into text using mlx-whisper.
        """
        print(f"Transcribing {audio_file_path}...")
        result = mlx_whisper.transcribe(audio_file_path, path_or_hf_repo=self.whisper_model)
        text = result.get("text", "").strip()
        print(f"Transcription: {text}")
        return text

    def generate_response(self, user_text: str, image_cctables=None) -> dict:
        """
        Generates a JSON response from the VLM based on user text and an optional image (screenshot).
        """
        # Append tool descriptions to the system prompt dynamically
        available_tools = "\\nAvailable Tools:\\n"
        for t in self.tool_registry.get_tool_definitions():
            available_tools += f"- {t['name']}: {t['description']}\\n"
            
        messages = [
            {"role": "system", "content": self.system_prompt + available_tools}
        ]
        
        user_message = {"role": "user", "content": [{"type": "text", "text": user_text}]}
        
        if image_cctables and len(image_cctables) > 0:
            # If screenshots are provided, attach the first one
            user_message["content"].insert(0, {"type": "image", "image": image_cctables[0]})
            
        messages.append(user_message)
        
        max_tool_calls = 5
        for loop_idx in range(max_tool_calls):
            prompt = self.processor.apply_chat_template(messages, add_generation_prompt=True)
            
            print(f"Generating response (Turn {loop_idx+1})...")
            
            output = ""
            for stream_chunk in stream_generate(
                self.model, 
                self.processor, 
                prompt,
                max_tokens=8192,
                verbose=False,
                thinking_budget=1,
                enable_thinking=True,
            ):
                print(stream_chunk.text, end="", flush=True)
                output += stream_chunk.text
            
            print("\\n\\nGeneration complete.")
            text_output = str(output).strip()
            
            try:
                # First check for a tool call
                parsed = json.loads(text_output, strict=False)
                if "tool" in parsed:
                    tool_name = parsed["tool"]
                    kwargs = parsed.get("kwargs", {})
                    print(f"\\n> LLM requested tool call: {tool_name} with {kwargs}")
                    
                    tool_result = self.tool_registry.execute(tool_name, kwargs)
                    print(f"> Tool result: {tool_result}\\n")
                    
                    # Append response and tool result to messages
                    messages.append({"role": "assistant", "content": text_output})
                    messages.append({"role": "user", "content": f"Tool Result: {tool_result}"})
                    continue
                elif "response" in parsed and "emotion" in parsed:
                    return parsed
            except Exception:
                pass
            
            clean_output = text_output.strip()
            
            # Extract JSON robustly
            if "{" in clean_output and "}" in clean_output:
                start_idx = clean_output.find("{")
                
                import re
                matches = re.findall(r'(\{"think":\s*".*?"emotion":\s*"[^"]*"\s*\})', clean_output, re.DOTALL)
                if matches:
                    clean_output = matches[-1]
                else:
                    think_idx = clean_output.rfind('{"think"')
                    if think_idx == -1: think_idx = clean_output.rfind('{ "think"')
                    if think_idx == -1: think_idx = clean_output.rfind('{\\n"think"')
                    if think_idx == -1: think_idx = clean_output.rfind('{\\n  "think"')
                    
                    if think_idx != -1:
                        start_idx = think_idx
                        
                    end_idx = clean_output.rfind("}") + 1
                    if end_idx > start_idx:
                        clean_output = clean_output[start_idx:end_idx]

            try:
                # Use strict=False to allow unescaped newlines in the string
                response_data = json.loads(clean_output.strip(), strict=False)
                return response_data
            except Exception as e:
                print("Failed to parse JSON. Error:", str(e))
                # Fallback safe response so TTS doesn't read the whole error or thinking process
                return {
                    "think": text_output.strip(), 
                    "response": "My thoughts got mixed up, could you ask me that again?", 
                    "emotion": "sad"
                }
