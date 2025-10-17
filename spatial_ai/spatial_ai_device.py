"""Spatial AI local device module."""
import os
import time
import logging
from collections import deque
import ntcore
import cv2
from depthai import UsbSpeed
from depthai_sdk import OakCamera
from depthai_sdk.classes import DetectionPacket
from spatial_ai.oak_config import OakConfig
from spatial_ai.cscore_streamer import CSCoreStreamer


class FPSTracker:
    """Track FPS."""
    def __init__(self, max_samples=30):
        self.timestamps = deque(maxlen=max_samples)
        self.last_update = time.time()
        self.frame_count = 0

    def update(self):
        """Update with new timestamp."""
        current_time = time.time()
        self.timestamps.append(current_time)
        self.last_update = current_time
        self.frame_count += 1

    def get_fps(self):
        """Calculate and return the FPS."""
        if len(self.timestamps) < 2:
            return 0.0
        time_diff = self.timestamps[-1] - self.timestamps[0]
        return (len(self.timestamps) - 1) / time_diff if time_diff > 0 else 0.0


class SpatialAiDevice():
    """
    A spatial AI local device.
    """
    def __init__(self, log: logging.Logger):
        self._logger = log

        # Get the environment variables
        self._mode = os.getenv("SPATIAL_AI_MODE", "dev")
        self._host = os.getenv("SPATIAL_AI_HOST", "host-spatial-ai")  # this is the name of the dev laptop
        self._resolution = os.getenv("RESOLUTION", "med")
        self._model = os.getenv("MODEL", "./models/2025/07-25_15-28-56/yolov5n.json")
        self._logger.info("Read the following environment variables:")
        self._logger.info("  SPATIAL_AI_MODE %s", self._mode)
        self._logger.info("  SPATIAL_AI_HOST %s", self._host)
        self._logger.info("  RESOLUTION %s", self._resolution)
        self._logger.info("  MODEL %s", self._model)

        if self._resolution == "low":
            self._width = 640
            self._height = 360
        elif self._resolution == "med":
            self._width = 768
            self._height = 432
        elif self._resolution == "high":
            self._width = 1280
            self._height = 720
        else:
            raise RuntimeError(f"Unknown resolution {self._mode}")

        self._cs_streamer = CSCoreStreamer(width=self._width, height=self._height)
        self._fps_tracker = FPSTracker()

        # NT connection
        self._nt = ntcore.NetworkTableInstance.getDefault()
        self._nt.startClient4(identity="frc4607-spatial-ai")
        if self._mode == "dev":
            self._nt.setServer(
                server_name=self._host+".local",
                port=ntcore.NetworkTableInstance.kDefaultPort4
            )
        elif self._mode == "comp":
            self._nt.setServerTeam(
                team=4607,
                port=ntcore.NetworkTableInstance.kDefaultPort4
            )
        else:
            raise RuntimeError(f"Unknown mode {self._mode}")
        self._logger.info("Waiting for NT4 connection...")
        while not self._nt.isConnected():
            time.sleep(1)
        self._logger.info("Connected to NT4!")
        self._spatial_ai_tbl = self._nt.getTable("frc4607-spatial-ai")
        self._logger.info("Using table %s", self._spatial_ai_tbl.__str__())

        # NT pubs
        self._fps_pub = self._spatial_ai_tbl.getDoubleTopic("FPS").publish()
        self._fps_pub.setDefault(0.0)
        self._detection_pub = self._spatial_ai_tbl.getBooleanTopic("detection").publish()
        self._detection_pub.setDefault(False)
        self._label_pub = self._spatial_ai_tbl.getStringTopic("label").publish()
        self._label_pub.setDefault("")
        self._spatial_x_pub = self._spatial_ai_tbl.getDoubleTopic("spatial_X").publish()
        self._spatial_x_pub.setDefault(0.0)
        self._spatial_y_pub = self._spatial_ai_tbl.getDoubleTopic("spatial_Y").publish()
        self._spatial_y_pub.setDefault(0.0)
        self._spatial_z_pub = self._spatial_ai_tbl.getDoubleTopic("spatial_Z").publish()
        self._spatial_z_pub.setDefault(0.0)

        # NT subs
        self._record_sub = self._spatial_ai_tbl.getBooleanTopic("record").subscribe(False)

    def _nn_detection_callback(self, packet: DetectionPacket):
        """Process callback."""
        if packet.frame is None:
            self._logger.warning("Packet frame is None")
            return
        self._fps_tracker.update()
        frame = packet.frame.copy()

        # No detections to process
        if not packet.img_detections.detections: # type: ignore
            self._detection_pub.set(False)

        # Process the first detection
        else:
            # Publish the FPS
            if self._fps_tracker.frame_count % 15 == 0:
                self._fps_pub.set(self._fps_tracker.get_fps())
                self._logger.info(f"FPS {self._fps_tracker.get_fps():.1f}")

            for det in packet.detections:
                bbox = packet.bbox.get_relative_bbox(det.bbox)
                coords = det.img_detection.spatialCoordinates  # type: ignore
                self._detection_pub.set(True)
                self._label_pub.set(det.label_str)
                self._spatial_x_pub.set(coords.x)
                self._spatial_y_pub.set(coords.y)
                self._spatial_z_pub.set(coords.z)
                self._logger.debug("Detected %s at (%.2f, %.2f, %.2f)", det.label_str, coords.x, coords.y, coords.z)
                frame_height, frame_width = frame.shape[:2]
                x1 = int(bbox.xmin * frame_width)
                y1 = int(bbox.ymin * frame_height)
                x2 = int(bbox.xmax * frame_width)
                y2 = int(bbox.ymax * frame_height)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                label = f"{det.label_str}: {det.confidence:.2f}"
                cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                cv2.putText(frame, f"FPS {self._fps_tracker.get_fps():.1f}", (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                break
        self._cs_streamer.add_frame(frame)

    def run_inference_only(self):
        """Run inference-only until interrupted to record."""
        with OakCamera(usb_speed=UsbSpeed.HIGH) as oak:
            self._logger.info("Configuring OAK device for spatial inference only")
            oak_config = OakConfig(oak=oak)
            oak_config.color_camera(resolution=self._resolution)
            oak_config.inference(model_path=self._model)
            oak_config.detections_callback(callback=self._nn_detection_callback)
            oak.start()
            while oak.running():
                if self._record_sub.get():
                    break
                oak.poll()
                time.sleep(1)

    def run_inference_and_record(self):
        """Run inference-only until interrupted to stop recording."""
        with OakCamera(usb_speed=UsbSpeed.HIGH) as oak:
            self._logger.info("Configuring OAK device for spatial inference and recording")
            oak_config = OakConfig(oak=oak)
            oak_config.color_camera(resolution=self._resolution)
            oak_config.inference(model_path=self._model)
            oak_config.detections_callback(callback=self._nn_detection_callback)
            oak_config.recording(save_path="/media/RECORDINGS/dev")
            oak.start()
            while oak.running():
                if not self._record_sub.get():
                    break
                oak.poll()
                time.sleep(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("SpatialAiDevice")

    # Create spatial AI device
    spatial_ai_device = SpatialAiDevice(log=logger)

    while True:
        # Run inference-only until a recording is requested
        spatial_ai_device.run_inference_only()

        # # Run inference and record until stop recording is requested
        # spatial_ai_device.run_inference_and_record()
