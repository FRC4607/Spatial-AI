import cv2
import depthai as dai
import time
from depthai_sdk import OakCamera, RecordType
from depthai_sdk.classes import DetectionPacket

class OakRecorder():
    """
    A class to record the color camera to an MP4 video file.
    
    Attributes:
        video_path (str): Path to the input MP4 video file
        output_dir (str): Directory where extracted frames will be saved
        frame_format (str): Format for saved frame images (default: 'jpg')
    """
    RES_MAP = {
        "low": (1, 3),
        "med": (2, 5),
        "high": (2, 3),
    }

    def __init__(self, save_path: str="", rec_len_s: int = None, res: str=""):
        """
        Initialize the OakRecorder object.

        All recordings are saved to the attachd USB drive. The input `save_path` defines
        the path appended to the USB mount point. The resolution input can be one of the
        following (note - the OAK Lite color camera defaults to 1920x1080):
            "low" - which gets implmented as (640x360)
            "med" - which gets implmented as (768x432)
            "high" - which gets implmented as (1280x720)            

        Args:
            save_path (str, optional): Path to save the recording. (default="Practice/")
            rec_len_s (str, optional): Number of seconds to record. (default=30)
            res (str, optional): Camera resolution. (default="med")
        """
        self.save_path = "Practice/"
        if save_path:
            self.save_path = save_path

        self.rec_len_s = 30
        if rec_len_s:
            self.rec_len_s = rec_len_s

        self.res = "med"
        if res:
            if res not in self.RES_MAP:
                raise ValueError(f"Unknownn resolution {res}")
            self.res = res


    def start(self):
        print("------------------------------------------------")
        print("OakRecorder:start")

        with OakCamera(usb_speed=dai.UsbSpeed.HIGH) as oak:
            # Configure the color camera
            color = oak.camera(source='color', resolution='1080p', fps=30)
            color.config_color_camera(isp_scale=self.RES_MAP[self.res])

            # Setup the recording
            oak.record(
                [color.out.encoded],
                f"/media/ejmccalla/RECORDINGS/{self.save_path}",
                RecordType.VIDEO
            )
        
            # Startup the pipeline and record until time expires
            print("------------------------------------------------")
            print("  Starting the OAK pipeline....")
            oak.start()
            start_time = time.monotonic()
            while oak.running():
                running_time = time.monotonic() - start_time
                if round(running_time) % 5 == 0:
                    print(f"  Running time: {running_time}") 
                if running_time > self.rec_len_s:
                    break
                oak.poll()
            print("  Stopping the OAK pipline...")
            print("------------------------------------------------")


if __name__ == "__main__":
    recorder = OakRecorder(rec_len_s=30)
    recorder.start()
