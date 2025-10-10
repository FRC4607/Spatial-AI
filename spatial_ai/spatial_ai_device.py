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
from spatial_ai import streamer


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
        # Logging
        self._logger = log

        # Tracking FPS
        self._fps_tracker = FPSTracker()

        # Get the mode and host from the local device environment
        self._mode = os.getenv("SPATIAL_AI_MODE", "dev")
        self._host = os.getenv("SPATIAL_AI_HOST", "host-spatial-ai")  # this is the name of the dev laptop
        self._logger.info("SPATIAL_AI_MODE %s, SPATIAL_AI_HOST %s", self._mode, self._host)

        # NT connection
        self._nt = ntcore.NetworkTableInstance.getDefault()
        self._nt.startClient4(identity="frc4607-spatial-ai")
        self._nt.setServerTeam(
            team=4607,
            port=ntcore.NetworkTableInstance.kDefaultPort4
        )
        self._logger.info("Waiting for NT4 connection...")
        while not self._nt.isConnected():
            time.sleep(1)
        self._logger.info("Connected to NT4!")
        self._spatial_ai_tbl = self._nt.getTable("frc4607-spatial-ai")
        self._logger.info("Using table %s", self._spatial_ai_tbl.__str__())

        # NT connection and pubs
        self._fps_pub = self._spatial_ai_tbl.getDoubleTopic("FPS").publish()
        self._fps_pub.setDefault(0.0)
        self._detection_pub = self._spatial_ai_tbl.getBooleanTopic("detection").publish()
        self._detection_pub.setDefault(False)
        self._label_pub = self._spatial_ai_tbl.getStringTopic("label").publish()
        self._label_pub.setDefault("")
        self._spatial_x_pub = self._spatial_ai_tbl.getDoubleTopic("spatial_X").publish()
        self._spatial_y_pub = self._spatial_ai_tbl.getDoubleTopic("spatial_Y").publish()
        self._spatial_z_pub = self._spatial_ai_tbl.getDoubleTopic("spatial_Z").publish()
        self._spatial_x_pub.setDefault(0.0)
        self._spatial_y_pub.setDefault(0.0)
        self._spatial_z_pub.setDefault(0.0)
        self.status_pub = self._spatial_ai_tbl.getStringTopic("status").publish()
        self.status_pub.setDefault("idle")

        # NT connection and subs
        self._record_sub = self._spatial_ai_tbl.getBooleanTopic("record").subscribe(False)
        self._inference_sub = self._spatial_ai_tbl.getBooleanTopic("inference").subscribe(False)

        # # Development mode
        # if self._mode == "dev":
        #     self._nt.setServer(
        #         server_name=self._host,
        #         port=ntcore.NetworkTableInstance.kDefaultPort4
        #     )

        # # Competition mode
        # elif self._mode == "comp":
        #     self._nt.setServerTeam(
        #         team=4607,
        #         port=ntcore.NetworkTableInstance.kDefaultPort4
        #     )
        # else:
        #     raise RuntimeError(f"Unknown mode {self._mode}")

        # Lazy-loaded attributes
        self.record: bool = None  # type: ignore
        self.inference: bool = None  # type: ignore

    def update(self):
        """
        Update the sub topics
        """
        if self._mode == "dev":
            self.record = self._record_sub.get()
            self.inference = self._inference_sub.get()

    def is_in_dev_mode(self):
        """Return true if in development mode."""
        return self._mode == "dev"

    def nn_detection_callback(self, packet: DetectionPacket):
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
            streamer.update_stream(frame)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("SpatialAiDevice")
    spatial_ai_device = SpatialAiDevice(log=logger)

    # Run the service in development mode
    if spatial_ai_device.is_in_dev_mode():
        while True:
            spatial_ai_device.status_pub.set("idle")
            spatial_ai_device.update()

            # Make a recording
            if spatial_ai_device.record:
                with OakCamera(usb_speed=UsbSpeed.HIGH) as oak:
                    logger.info("Configuring OAK device for recording")
                    oak_config = OakConfig(oak=oak)
                    oak_config.color_camera(resolution="med")
                    oak_config.recording(save_path="/media/RECORDINGS/dev")
                    oak.start()
                    spatial_ai_device.status_pub.set("recording")
                    while oak.running():
                        spatial_ai_device.update()

                        if not spatial_ai_device.record:
                            break
                        oak.poll()
                        time.sleep(1)

            # Run spatial inference
            elif spatial_ai_device.inference:
                streamer.start_streaming(port=5800)
                with OakCamera(usb_speed=UsbSpeed.HIGH) as oak:
                    logger.info("Configuring OAK device for spatial inference")
                    oak_config = OakConfig(oak=oak)
                    oak_config.color_camera(resolution="med")
                    oak_config.inference(model_path="./models/2025/07-25_15-28-56/yolov5n.json")
                    oak_config.detections_callback(callback=spatial_ai_device.nn_detection_callback)
                    oak.start()
                    spatial_ai_device.status_pub.set("inference")
                    while oak.running():
                        spatial_ai_device.update()
                        if not spatial_ai_device.inference:
                            break
                        oak.poll()
                        time.sleep(1)
                streamer.stop_streaming()
            else:
                time.sleep(1)

    # Run the service in competition mode
    else:
        with OakCamera(usb_speed=UsbSpeed.HIGH) as oak:
            logger.info("Configuring OAK device for spatial inference")
            oak_config = OakConfig(oak=oak)
            oak_config.color_camera(resolution="med")
            oak_config.inference(model_path="./models/2025/07-25_15-28-56/yolov5n.json")
            oak_config.detections_callback(callback=spatial_ai_device.nn_detection_callback)
            logger.info("Comp Mode: start publishing detctions")
            oak.start(blocking=True)
