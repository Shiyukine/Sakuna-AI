import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# AI Models
VLM_MODEL_ID = os.getenv("VLM_MODEL_ID", "mlx-community/Qwen3.5-9B-MLX-4bit")
VAD_SENSITIVITY = float(os.getenv("VAD_SENSITIVITY", 0.5))

# VTube Studio Settings
VTS_HOST = os.getenv("VTS_HOST", "127.0.0.1")
VTS_PORT = int(os.getenv("VTS_PORT", 8001))
VTS_NAME = os.getenv("VTS_NAME", "Sakuna-AI")
VTS_DEVELOPER = os.getenv("VTS_DEVELOPER", "User")
