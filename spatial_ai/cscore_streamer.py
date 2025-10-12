"""Stream OAK-D to robot via CameraServer"""
from cscore import CameraServer


class CSCoreStreamer():
    """
    CS Core Streamer.
    """
    def __init__(self, width: int = 768, height: int = 432):
        CameraServer.enableLogging()
        self._stream = CameraServer.putVideo("OAK-D Camera", width, height)

    def add_frame(self, frame):
        """Add frame to the camera server"""
        self._stream.putFrame(frame)
