import asyncio
import pyvts
import logging
from .config import VTS_HOST, VTS_PORT, VTS_NAME, VTS_DEVELOPER

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VTSManager:
    def __init__(self):
        plugin_info = {
            "plugin_name": VTS_NAME,
            "developer": VTS_DEVELOPER,
            "authentication_token_path": "./vts_token.txt",
        }
        vts_api_info = {
            "version": "1.0",
            "name": "VTubeStudioPublicAPI",
            "host": VTS_HOST,
            "port": VTS_PORT
        }
        self.vts = pyvts.vts(plugin_info=plugin_info, vts_api_info=vts_api_info)
        self.connected = False
        
    async def connect(self):
        """
        Connect to VTube Studio websocket and authenticate.
        """
        try:
            await self.vts.connect()
            
            # This handles both cases if we already have a token or need one
            await self.vts.request_authenticate_token()
            await self.vts.request_authenticate()
            
            self.connected = True
            logger.info("Successfully connected to VTube Studio.")
            
        except ConnectionRefusedError:
            logger.error("VTube Studio is not running or WebSockets are not enabled. Continuing without Live2D support.")
            self.connected = False
        except Exception as e:
            logger.error(f"Failed to connect to VTube Studio: {e}")
            self.connected = False

    async def trigger_emotion(self, emotion: str):
        """
        Triggers a VTS Expression Hotkey mapping to an emotion.
        The hotkey name in VTS must match the emotion string exactly (or mapped internally).
        """
        if not self.connected:
            logger.warning("VTS not connected. Cannot trigger emotion.")
            return

        logger.info(f"Triggering emotion hotkey: {emotion}")
        
        # In pyvts, you typically trigger hotkeys via the item instance ID or hotkey ID
        # Since we're using a simple emotion mapping, we assume they match custom hotkeys setup in your model.
        hotkey_msg = self.vts.vts_request.requestHotKeyList()
        # This is a bit simplified; typically you query hotkeys, find the ID mapping to the string, and request to trigger.
        hotkeys_response = await self.vts.request(hotkey_msg)
        
        hotkeys = hotkeys_response.get("data", {}).get("availableHotkeys", [])
        
        hotkey_item = next((hk for hk in hotkeys if hk["name"].lower() == emotion.lower()), None)
        
        if hotkey_item:
            trigger_msg = self.vts.vts_request.requestTriggerHotKey(hotkey_item["hotkeyID"])
            await self.vts.request(trigger_msg)
            logger.info(f"Emotion '{emotion}' triggered successfully.")
        else:
            logger.warning(f"No hotkey found in VTS named '{emotion}'.")
