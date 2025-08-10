"""Module for running live OAK inference."""
import argparse
from depthai import UsbSpeed
from depthai_sdk import OakCamera
from spatial_ai.oak_config import OakConfig


class SpatialInference():
    """
    A class to run live inference with spatial coordinates on the OAK camera.
    
    Attributes:
    """
    def __init__(self):
        self._oak_config = None

    def start(self, model_path: str, resolution: str):
        """
        Start running live spatial inference.

        Args:
            model_path (str): Path to the inference model
            resolution (str): Camera resolution
        """

        with OakCamera(usb_speed=UsbSpeed.HIGH) as oak:

            # Configure the OAK (color camera and NN)
            self._oak_config = OakConfig(oak=oak)
            self._oak_config.color_camera(resolution=resolution)
            self._oak_config.stereo_cameras()
            self._oak_config.inference(model_path=model_path)
            self._oak_config.visualize()

            # vis = oak.visualize(nn.out.passthrough, fps=True)
            # vis.detections().text(auto_scale=True, font_scale=0.5, font_thickness=1)
            # oak.visualize(nn.out.passthrough, fps=True, callback=cb).detections().text(auto_scale=False, font_position=22, font_scale=0.4, font_thickness=1)

            # Startup the pipeline and record until time expires
            print("------------------------------------------------")
            print("  Starting the OAK pipeline (press q to quit)....")
            oak.start(blocking=True)
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

    SpatialInference().start(
        model_path=args.model_path,
        resolution=args.resolution
    )
