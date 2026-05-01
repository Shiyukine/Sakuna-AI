import asyncio
import sys
import os

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from src.main import run_pipeline

if __name__ == "__main__":
    asyncio.run(run_pipeline())