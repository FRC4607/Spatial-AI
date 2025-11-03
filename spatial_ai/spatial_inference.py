"""Module for running live OAK inference."""
import argparse
import time
from collections import deque
import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="depthai_sdk")
# pylint: disable=wrong-import-position
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


class SpatialInference():
    """
    A class to run live inference with spatial coordinates on the OAK camera.
    
    Attributes:
    """
    def __init__(self, resolution: str):
        self._resolution = resolution
        if resolution == "low":
            self._width = 640
            self._height = 360
        elif resolution == "med":
            self._width = 768
            self._height = 432
        elif resolution == "high":
            self._width = 1280
            self._height = 720
        else:
            raise RuntimeError(f"Unknown resolution '{self._resolution}'")
        self._oak_config = None
        self._fps_tracker = FPSTracker()
        self._cs_streamer = CSCoreStreamer(width=self._width, height=self._height)
        self._frame_count = 0
        self._detection_count = 0
        self._last_log_time = time.time()
        self._fps = 0.0

    def _nn_detection_callback(self, packet: DetectionPacket):
        """Process callback."""
        if packet.frame is None:
            return
        self._fps_tracker.update()
        self._fps = self._fps_tracker.get_fps()
        frame = packet.frame.copy()
        self._frame_count += 1

        # Process the first detection
        if packet.img_detections.detections: # type: ignore
            self._detection_count += 1
            for det in packet.detections:
                bbox = packet.bbox.get_relative_bbox(det.bbox)
                # self._logger.debug("Detected %s at (%.2f, %.2f, %.2f)", det.label_str, coords.x, coords.y, coords.z)
                frame_height, frame_width = frame.shape[:2]
                x1 = int(bbox.xmin * frame_width)
                y1 = int(bbox.ymin * frame_height)
                x2 = int(bbox.xmax * frame_width)
                y2 = int(bbox.ymax * frame_height)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                label = f"{det.label_str}: {det.confidence:.2f}"
                cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                break
        cv2.putText(frame, f"FPS {self._fps:.1f}", (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        self._cs_streamer.add_frame(frame)

        # Log periodically
        current_time = time.time()
        if current_time - self._last_log_time >= 30.0:
            print("Status: Received %d frames, %.1f detections FPS: %.1f",
                  self._frame_count,
                  self._detection_count,
                  self._fps)
            self._last_log_time = current_time

    def start(self, model_path: str):
        """
        Start running live spatial inference.

        Args:
            model_path (str): Path to the in-ference model
            resolution (str): Camera resolution
        """
        with OakCamera(usb_speed=UsbSpeed.HIGH) as oak:
            oak_config = OakConfig(oak=oak)
            oak_config.color_camera(resolution=self._resolution)
            oak_config.inference(model_path=model_path)
            oak_config.detections_callback(callback=self._nn_detection_callback)

            # Startup the pipeline and wait for user interrupt
            print("------------------------------------------------")
            print("  Starting the OAK pipeline (press CTRL+C to quit)....")
            print("  View stream in browser at: http://frc4607-spatial-ai.local:1181/?action=stream")
            oak.start()
            while oak.running():
                oak.poll()
                time.sleep(0.1)
            print("  Stopping the OAK pipline...")
            print("------------------------------------------------")


def main():
    """Main function called by CLI."""
    parser = argparse.ArgumentParser(description="Spatial AI - Oak Live Spatial Inference CLI")
    parser.add_argument(
        "--model-path",
        type=str,
        default="./models/2025/07-25_15-28-56/yolov5n.json",
        help="Path to the inference model file (default: ./models/2025/07-25_15-28-56/yolov5n.json)"
    )
    parser.add_argument(
        "--resolution",
        type=str,
        default="med",
        help="Color camera resolution: low=640x360, med=768x432, high=1280x720"
    )
    args = parser.parse_args()
    print(f"Using model: {args.model_path}")
    print(f"Color camera resolution: {args.resolution}")

    SpatialInference(resolution=args.resolution).start(model_path=args.model_path)
