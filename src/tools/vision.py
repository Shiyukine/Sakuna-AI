import mss
import mss.tools
import os
from PIL import Image

def capture_screen(output_path="screenshot.png") -> str:
    """
    Captures the primary monitor screen and saves it as an image.
    Returns the path to the saved screenshot.
    """
    with mss.mss() as sct:
        # The screen part to capture
        monitor = sct.monitors[1]  # 1 is primary monitor
        
        # Grab the data
        sct_img = sct.grab(monitor)
        
        # Save to the picture file
        mss.tools.to_png(sct_img.rgb, sct_img.size, output=output_path)
        
        return output_path

def resize_image_for_llm(image_path: str, max_size=(1024, 1024)) -> str:
    """
    Resizes the screenshot so it doesn't overwhelm the VLM token context.
    """
    img = Image.open(image_path)
    img.thumbnail(max_size, Image.Resampling.LANCZOS)
    resized_path = image_path.replace(".png", "_resized.jpg")
    img.save(resized_path, "JPEG", quality=85)
    return resized_path
