"""Module for quantifying recorded video."""
import argparse
import os
import warnings
import logging
import shutil
import time
os.environ["DEPTHAI_LEVEL"] = "error"
os.environ["DEPTHAI_LOG_LEVEL"] = "error"
warnings.filterwarnings("ignore", category=FutureWarning, module="depthai_sdk")
logging.getLogger("depthai_sdk").setLevel(logging.ERROR)
logging.getLogger("depthai").setLevel(logging.ERROR)
# pylint: disable=wrong-import-position
import cv2
from tqdm import tqdm
from depthai_sdk import OakCamera
from spatial_ai.oak_config import OakConfig


class Analyze():
    """
    A class to quantify the inference performance against a recording,
    and track frames that were not detected.
    """
    def __init__(self):
        self._frames = 0
        self._detections = 0
        self._start_time = None
        self._end_time = None
        self._last_frame_time = None
        self._min_latency = float('inf')
        self._max_latency = 0.0
        self._total_latency = 0.0
        self._resolution = None
        self._total_video_frames = 0
        self._detected_folder = None
        self._undetected_folder = None
        self._pbar = None

    def _nn_detection_callback(self, packet):
        """Process callback for each frame."""
        if packet.frame is None:
            return

        self._frames += 1
        if self._pbar is not None:
            self._pbar.update(1)
        now = time.time()

        if self._start_time is None:
            self._start_time = now
            self._last_frame_time = now
        else:
            if self._last_frame_time is not None:
                latency = now - self._last_frame_time
                self._min_latency = min(self._min_latency, latency)
                self._max_latency = max(self._max_latency, latency)
                self._total_latency += latency
            self._last_frame_time = now

        # Track detections
        if packet.img_detections.detections:  # type: ignore
            self._detections += 1
            frame_bgr = cv2.cvtColor(packet.frame, cv2.COLOR_RGB2BGR)
            for det in packet.detections:
                bbox = packet.bbox.get_relative_bbox(det.bbox)
                # self._logger.debug("Detected %s at (%.2f, %.2f, %.2f)", det.label_str, coords.x, coords.y, coords.z)
                frame_height, frame_width = packet.frame.shape[:2]
                x1 = int(bbox.xmin * frame_width)
                y1 = int(bbox.ymin * frame_height)
                x2 = int(bbox.xmax * frame_width)
                y2 = int(bbox.ymax * frame_height)
                label = f"{det.label_str}: {det.confidence:.2f}"
                cv2.rectangle(frame_bgr, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame_bgr, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                break
            if self._detected_folder:
                filename = os.path.join(self._detected_folder, f"frame_{self._frames:04d}.png")
                cv2.imwrite(filename, frame_bgr)
        else:
            # No detection in this frame
            if self._undetected_folder:
                frame_bgr = cv2.cvtColor(packet.frame, cv2.COLOR_RGB2BGR)
                filename = os.path.join(self._undetected_folder, f"frame_{self._frames:04d}.png")
                cv2.imwrite(filename, frame_bgr)

    def start(self, video_path: str, model_path: str):
        """Start inference and track stats."""
        # Determine resolution from video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise IOError(f"Cannot open video file: {video_path}")
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self._total_video_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        if width == 640 and height == 360:
            self._resolution = "low"
        elif width == 768 and height == 432:
            self._resolution = "med"
        elif width == 1280 and height == 720:
            self._resolution = "high"
        else:
            self._resolution = "med"
            print(f"Warning: video resolution {width}x{height} not standard. Using 'med'.")

        # Determine folder for undetected frames based on video path
        video_dir = os.path.dirname(video_path)
        self._detected_folder = os.path.join(video_dir, "detected_frames")
        if os.path.exists(self._detected_folder):
            shutil.rmtree(self._detected_folder)
        os.makedirs(self._detected_folder)
        self._undetected_folder = os.path.join(video_dir, "undetected_frames")
        if os.path.exists(self._undetected_folder):
            shutil.rmtree(self._undetected_folder)
        os.makedirs(self._undetected_folder)

        print(f"\nModel: {model_path}")
        print(f"Video: {video_path}")
        print(f"Resolution: {width}x{height} -> OAK preset: {self._resolution}")
        print(f"Number of Frames: {self._total_video_frames}\n")

        # Create a progress bar
        self._pbar = tqdm(total=self._total_video_frames, desc="Processing", ncols=80)

        # Run inference
        with OakCamera(replay=video_path) as oak:
            oak_config = OakConfig(oak=oak)
            oak_config.color_camera(resolution=self._resolution)
            oak_config.inference(model_path=model_path)
            oak_config.detections_callback(callback=self._nn_detection_callback)
            oak.start(blocking=True)

        self._pbar.close()

        # Timing and stats
        self._end_time = time.time()
        elapsed = self._end_time - self._start_time if self._start_time else 0
        effective_fps = self._frames / elapsed if elapsed > 0 else 0.0
        avg_latency = (self._total_latency / (self._frames - 1)) if self._frames > 1 else 0.0
        detection_rate = (self._detections / self._frames) * 100 if self._frames > 0 else 0.0

        print(f"\nProcessed {self._frames} frames")
        print(f"Found {self._detections} detections")
        print(f"Detection rate: {detection_rate:.2f}%")
        print(f"Elapsed time: {elapsed:.2f}s")
        print(f"Effective FPS: {effective_fps:.2f}")
        print(f"Frame latency: min {self._min_latency*1000:.2f} ms, "
              f"max {self._max_latency*1000:.2f} ms, "
              f"avg {avg_latency*1000:.2f} ms")
        print(f"See {self._undetected_folder} for frames without detections")

def main():
    """Main function called by CLI."""
    parser = argparse.ArgumentParser(description="Spatial AI - Analyze CLI")
    parser.add_argument(
        "--video-path",
        type=str,
        default="./recordings/test.mp4",
        help="Path to the input video file (default: ./recordings/test.mp4)"
    )
    parser.add_argument(
        "--model-path",
        type=str,
        default="./models/2025/07-25_15-28-56/yolov5n.json",
        help="Path to the inference model file (default: ./models/2025/07-25_15-28-56/yolov5n.json)"
    )
    args = parser.parse_args()
    Analyze().start(video_path=args.video_path, model_path=args.model_path)
