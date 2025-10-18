"""NT host test module."""
import time
import ntcore
import cv2
from cscore import CameraServer


class SpatialAiHost():
    """
    A class to test NT connection to the local spatial AI device.
    """
    def __init__(self):
        self.nt = ntcore.NetworkTableInstance.getDefault()
        self.nt.startServer()
        self.spatial_ai_tbl = self.nt.getTable("frc4607-spatial-ai")

        # NT pubs
        self.record_pub = self.spatial_ai_tbl.getBooleanTopic("record").publish()
        self.record_pub.setDefault(False)

        # NT subs
        self.fps_sub = self.spatial_ai_tbl.getDoubleTopic("FPS").subscribe(0.0)
        self.detection_sub = self.spatial_ai_tbl.getBooleanTopic("detection").subscribe(False)
        self.label_sub = self.spatial_ai_tbl.getStringTopic("label").subscribe("")
        self.spatial_x_sub = self.spatial_ai_tbl.getDoubleTopic("spatial_X").subscribe(0.0)
        self.spatial_y_sub = self.spatial_ai_tbl.getDoubleTopic("spatial_Y").subscribe(0.0)
        self.spatial_z_sub = self.spatial_ai_tbl.getDoubleTopic("spatial_Z").subscribe(0.0)

        while True:
            time.sleep(1)

    #     # Open the HTTP stream from Pi
    #     print("Connecting to camera stream...")
    #     self.cap = cv2.VideoCapture("http://frc4607-spatial-ai:1181/stream.mjpg")

    #     if not self.cap.isOpened():
    #         print("ERROR: Could not open camera stream!")
    #         return
    #     print("Camera stream opened successfully!")

    #     # Get the actual frame dimensions from the stream
    #     width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    #     height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    #     print(f"Stream resolution: {width}x{height}")

    #     # Camera server - create video sink with actual dimensions
    #     CameraServer.enableLogging()
    #     self._stream = CameraServer.putVideo("Spatial-AI", width, height)

    #     # Wait a moment for CameraServer to set things up
    #     time.sleep(0.5)

    #     # Check what CameraServer published automatically
    #     camera_table = self.nt.getTable("CameraPublisher").getSubTable("Spatial-AI")
    #     print(f"CameraPublisher entries: {camera_table.getKeys()}")

    #     # Print the streams that were auto-published
    #     streams = camera_table.getStringArray("streams", [])
    #     print(f"Auto-published streams: {streams}")

    #     # Override with localhost URL for Elastic
    #     camera_table.putStringArray("streams", [
    #         "mjpg:http://localhost:1181/?action=stream",
    #         "mjpg:http://127.0.0.1:1181/?action=stream"
    #     ])

    #     # Main loop - read and push frames
    #     while True:
    #         ret, frame = self.cap.read()
    #         if ret:
    #             self._stream.putFrame(frame)
    #         else:
    #             print("WARNING: Failed to read frame, attempting to reconnect...")
    #             self.cap.release()
    #             time.sleep(1)
    #             self.cap = cv2.VideoCapture("http://frc4607-spatial-ai:1181/stream.mjpg")

    #         time.sleep(0.01)  # Small delay to prevent CPU overload

    # def __del__(self):
    #     """Cleanup on exit"""
    #     if hasattr(self, 'cap'):
    #         self.cap.release()


if __name__ == "__main__":
    host = SpatialAiHost()
