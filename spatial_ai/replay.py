"""Module for replaying OAK video and running inference."""
import argparse
from depthai_sdk import OakCamera
from .oak_config import OakConfig


class Replay():
    """
    A class to replay the color camera video recording and running inference.
    
    Attributes:
    """
    def __init__(self):
        self._oak_config = None

    def start(self, video_path: str, model_path: str, resolution: str):
        """
        Start replaying video.

        Args:
            video_path (str): Path to the file to replay
            model_path (str): Path to the inference model
            resolution (str): Camera resolution
        """
        with OakCamera(replay=video_path) as oak:

            # Configure the OAK (color camera and NN)
            self._oak_config = OakConfig(oak=oak)
            self._oak_config.color_camera(resolution=resolution)
            self._oak_config.inference(model_path=model_path)

            # Start the replay and wait for it to finish
            oak.start(blocking=True)


def main():
    """Main function called by CLI."""
    parser = argparse.ArgumentParser(description="Spatial AI - Oak Replay CLI")
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
    parser.add_argument(
        "--resolution",
        type=str,
        default="med",
        help="Color camera resolution: low=640x360, med=768x432, high=1280x720"
    )
    args = parser.parse_args()
    print(f"Running inference on: {args.video_path}")
    print(f"Using model: {args.model_path}")
    print(f"Color camera resolution: {args.resolution}")

    Replay().start(
        video_path=args.video_path,
        model_path=args.model_path,
        resolution=args.resolution
    )
