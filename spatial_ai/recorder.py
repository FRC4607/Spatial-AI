"""Module for recording OAK video to attached USB drive."""
import argparse
import time
import depthai as dai
from depthai_sdk import OakCamera
from spatial_ai.oak_config import OakConfig


class Recorder():
    """
    A class to record the color camera to an MP4 video file.
    
    Attributes:
    """
    def __init__(self):
        self._oak_config = None

    def start(self, save_path: str, rec_len_s: int, resolution: str):
        """
        Start recording video.

        All recordings are saved to the attachd USB drive. The input `save_path` defines
        the full path to save the recording (NOTE - the label of the USB drive may be
        different than the default RECORDINGS). The input `rec_len_s` defines how long
        to record video in seconds. The `resolution` input can be one of the following:
            "tiny" - which gets implmented as (320x180)
            "low" - which gets implmented as (640x360)
            "med" - which gets implmented as (768x432)
            "high" - which gets implmented as (1280x720)
            (NOTE - the OAK Lite color camera defaults to 1920x1080)

        Args:
            save_path (str): Path to save the recording
            rec_len_s (str): Number of seconds to record
            resolution (str): Camera resolution
        """
        with OakCamera(usb_speed=dai.UsbSpeed.HIGH) as oak:

            # Configure the OAK (color camera and recording)
            self._oak_config = OakConfig(oak=oak)
            self._oak_config.color_camera(resolution=resolution)
            self._oak_config.recording(save_path=save_path)

            # Startup the pipeline and record until time expires
            oak.start()
            start_time = time.monotonic()
            last_print_time = 5
            while oak.running():
                running_time = time.monotonic() - start_time
                if running_time > last_print_time:
                    last_print_time+=5
                    print(f"  Running time: {running_time}")
                if running_time > rec_len_s:
                    break
                oak.poll()

def main():
    """Main function called by CLI."""
    parser = argparse.ArgumentParser(description="Spatial AI - Oak Recorder CLI")
    parser.add_argument(
        "--save-path",
        type=str,
        default="/media/RECORDINGS/practice",
        help="Path to save the video file (default: /media/RECORDINGS/practice)"
    )
    parser.add_argument(
        "--rec-len",
        type=int,
        default=30,
        help="Recording length in seconds (default: 30)"
    )
    parser.add_argument(
        "--resolution",
        type=str,
        default="med",
        help="Color camera resolution: low=640x360, med=768x432, high=1280x720"
    )
    args = parser.parse_args()
    print(f"Recording video to: {args.save_path}")
    print(f"Recording length in seconds: {args.rec_len}")
    print(f"Color camera resolution: {args.resolution}")

    Recorder().start(
        save_path=args.save_path,
        rec_len_s=args.rec_len,
        resolution=args.resolution
    )
