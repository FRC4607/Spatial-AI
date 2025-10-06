"""Module for running live OAK inference."""
import argparse
import time
from collections import deque
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


class SpatialInference():
    """
    A class to run live inference with spatial coordinates on the OAK camera.
    
    Attributes:
    """
    def __init__(self):
        self._oak_config = None
        self._fps_tracker = FPSTracker()

    def _nn_detection_callback(self, packet: DetectionPacket):
        """Process callback."""
        if packet.frame is None:
            return
        self._fps_tracker.update()
        frame = packet.frame.copy()

        # Process the first detection
        if packet.img_detections.detections: # type: ignore
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
                cv2.putText(frame, f"FPS {self._fps_tracker.get_fps():.1f}", (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                break
        streamer.update_stream(frame)

    def start(self, model_path: str, resolution: str):
        """
        Start running live spatial inference.

        Args:
            model_path (str): Path to the inference model
            resolution (str): Camera resolution
        """
        streamer.start_streaming(port=5800)
        with OakCamera(usb_speed=UsbSpeed.HIGH) as oak:
            oak_config = OakConfig(oak=oak)
            oak_config.color_camera(resolution=resolution)
            oak_config.inference(model_path=model_path)
            oak_config.detections_callback(callback=self._nn_detection_callback)

            # Startup the pipeline and record until time expires
            print("------------------------------------------------")
            print("  Starting the OAK pipeline (press CTRL+C to quit)....")
            oak.start()
            while oak.running():
                oak.poll()
                time.sleep(0.1)
            print("  Stopping the OAK pipline...")
            print("------------------------------------------------")
        streamer.stop_streaming()


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

    SpatialInference().start(
        model_path=args.model_path,
        resolution=args.resolution
    )
