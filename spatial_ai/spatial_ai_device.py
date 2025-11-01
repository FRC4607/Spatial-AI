"""Spatial AI local device module."""
import os
import time
import logging
from collections import deque
import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="depthai_sdk")
# pylint: disable=wrong-import-position
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
        self._host = os.getenv("SPATIAL_AI_HOST", "host-spatial-ai")
        self._resolution = os.getenv("RESOLUTION", "med")
        self._model = os.getenv("MODEL", "./models/2025/07-25_15-28-56/yolov5n.json")

        self._logger.info("=" * 60)
        self._logger.info("Spatial AI Device Initialization")
        self._logger.info("=" * 60)
        self._logger.info("Environment Variables:")
        self._logger.info("  SPATIAL_AI_MODE: %s", self._mode)
        self._logger.info("  SPATIAL_AI_HOST: %s", self._host)
        self._logger.info("  RESOLUTION: %s", self._resolution)
        self._logger.info("  MODEL: %s", self._model)

        # Set resolution
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
            raise RuntimeError(f"Unknown resolution '{self._resolution}'")
        self._logger.info("Camera Resolution: %dx%d", self._width, self._height)

        # Initialize CameraServer streamer
        self._logger.info("Initializing CameraServer streamer...")
        self._cs_streamer = CSCoreStreamer(width=self._width, height=self._height)
        self._logger.info("CameraServer initialized successfully")

        self._fps_tracker = FPSTracker()
        self._frame_counter = 0
        self._last_log_time = time.time()

        # NT connection
        self._logger.info("-" * 60)
        self._logger.info("NetworkTables Configuration")
        self._logger.info("-" * 60)
        self._nt = ntcore.NetworkTableInstance.getDefault()
        self._nt.startClient4(identity="frc4607-spatial-ai")

        if self._mode == "dev":
            server_address = f"{self._host}.local"
            self._logger.info("Mode: Development")
            self._logger.info("Connecting to: %s:%d",
                              server_address,
                              ntcore.NetworkTableInstance.kDefaultPort4)
            self._nt.setServer(
                server_name=server_address,
                port=ntcore.NetworkTableInstance.kDefaultPort4
            )
        elif self._mode == "comp":
            self._logger.info("Mode: Competition")
            self._logger.info("Connecting to: Team 4607 NetworkTables")
            self._nt.setServerTeam(
                team=4607,
                port=ntcore.NetworkTableInstance.kDefaultPort4
            )
        else:
            raise RuntimeError(f"Unknown mode '{self._mode}' (expected 'dev' or 'comp')")

        self._logger.info("Waiting for NT4 connection...")
        connection_start = time.time()
        while not self._nt.isConnected():
            elapsed = time.time() - connection_start
            time.sleep(1)
            if int(elapsed) % 30 == 0:
                self._logger.info("Still waiting for NT connection... (%ds)", int(elapsed))

        self._spatial_ai_tbl = self._nt.getTable("frc4607-spatial-ai")
        self._logger.info("Using NetworkTables: %s", self._spatial_ai_tbl.getPath())

        # NT publishers
        self._logger.info("Setting up NetworkTables publishers...")
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
        self._logger.info("Publishers configured: FPS, detection, label, spatial_X/Y/Z")

        # NT subscribers
        self._logger.info("Setting up NetworkTables subscribers...")
        self._record_sub = self._spatial_ai_tbl.getBooleanTopic("record").subscribe(False)
        self._logger.info("Subscribers configured: record")

        self._logger.info("=" * 60)
        self._logger.info("Initialization Complete - Ready to start")
        self._logger.info("=" * 60)

    def _nn_detection_callback(self, packet: DetectionPacket):
        """Process callback for each frame with detections."""
        if packet.frame is None:
            self._logger.warning("Callback received packet with None frame")
            return

        # Update the FPS tracker and get a copy of the frame
        self._fps_tracker.update()
        self._frame_counter += 1
        frame = packet.frame.copy()

        # Log periodically to show we're receiving frames
        current_time = time.time()
        if current_time - self._last_log_time >= 30.0:
            self._logger.info("Status: Received %d frames, FPS: %.1f",
                              self._frame_counter,
                              self._fps_tracker.get_fps())
            self._last_log_time = current_time

        # No detections
        if not packet.img_detections.detections: # type: ignore
            self._detection_pub.set(False)
            self._cs_streamer.add_frame(frame)
            return

        # Process first detection only
        for det in packet.detections:
            bbox = packet.bbox.get_relative_bbox(det.bbox)
            coords = det.img_detection.spatialCoordinates # type: ignore

            # Publish detection data
            self._detection_pub.set(True)
            self._label_pub.set(det.label_str)
            self._spatial_x_pub.set(coords.x)
            self._spatial_y_pub.set(coords.y)
            self._spatial_z_pub.set(coords.z)

            self._logger.debug("Detection: %s at (%.2f, %.2f, %.2f) conf=%.2f",
                               det.label_str, coords.x, coords.y, coords.z, det.confidence)

            # Draw bounding box
            frame_height, frame_width = frame.shape[:2]
            x1 = int(bbox.xmin * frame_width)
            y1 = int(bbox.ymin * frame_height)
            x2 = int(bbox.xmax * frame_width)
            y2 = int(bbox.ymax * frame_height)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # Add label text
            label = f"{det.label_str}: {det.confidence:.2f}"
            cv2.putText(frame, label, (x1, y1-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # Add FPS overlay
            fps = self._fps_tracker.get_fps()
            cv2.putText(frame, f"FPS {fps:.1f}", (5, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # Push frame to CameraServer
            self._cs_streamer.add_frame(frame)

            # Only processing first detection
            break

    def run_inference_only(self):
        """Run inference-only until interrupted to record."""
        self._logger.info("-" * 60)
        self._logger.info("Starting Inference-Only Mode")
        self._logger.info("-" * 60)

        try:
            with OakCamera(usb_speed=UsbSpeed.HIGH) as oak:
                self._logger.info("OAK camera opened successfully")
                self._logger.info("Configuring camera for inference...")

                oak_config = OakConfig(oak=oak)
                oak_config.color_camera(resolution=self._resolution)
                oak_config.inference(model_path=self._model)
                oak_config.detections_callback(callback=self._nn_detection_callback)

                self._logger.info("Starting camera pipeline...")
                oak.start()
                self._logger.info("✓ Camera pipeline started - streaming and inferencing")

                # Reset counters
                self._frame_counter = 0
                self._last_log_time = time.time()

                while oak.running():
                    if self._record_sub.get():
                        self._logger.info("Recording requested - switching modes")
                        break
                    oak.poll()
                    time.sleep(0.1)

                self._logger.info("Inference-only mode ending")

        except Exception as e:
            self._logger.error("Error in inference-only mode: %s", str(e), exc_info=True)
            raise

    def run_inference_and_record(self):
        """Run inference and recording until interrupted."""
        self._logger.info("-" * 60)
        self._logger.info("Starting Inference + Recording Mode")
        self._logger.info("-" * 60)

        try:
            with OakCamera(usb_speed=UsbSpeed.HIGH) as oak:
                self._logger.info("OAK camera opened successfully")
                self._logger.info("Configuring camera for inference and recording...")

                oak_config = OakConfig(oak=oak)
                oak_config.color_camera(resolution=self._resolution)
                oak_config.inference(model_path=self._model)
                oak_config.detections_callback(callback=self._nn_detection_callback)
                oak_config.recording(save_path="/media/RECORDINGS/dev")

                self._logger.info("Starting camera pipeline with recording...")
                oak.start()
                self._logger.info("✓ Camera pipeline started - streaming, inferencing, and recording")

                # Reset counters
                self._frame_counter = 0
                self._last_log_time = time.time()

                while oak.running():
                    if not self._record_sub.get():
                        self._logger.info("Recording stop requested - switching modes")
                        break
                    oak.poll()
                    time.sleep(0.1)

                self._logger.info("Recording mode ending")

        except Exception as e:
            self._logger.error("Error in recording mode: %s", str(e), exc_info=True)
            raise


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger = logging.getLogger("SpatialAiDevice")
    logger.info("Starting Spatial AI Device application")

    try:
        # Create spatial AI device
        spatial_ai_device = SpatialAiDevice(log=logger)

        # Main loop
        while True:
            # Run inference-only until a recording is requested
            spatial_ai_device.run_inference_only()

            # Run inference and record until stop recording is requested
            spatial_ai_device.run_inference_and_record()

    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.critical("Fatal error: %s", str(e), exc_info=True)
        raise
