""" Extract frames from MP4 video file. """
import os
from pathlib import Path
from dataclasses import dataclass
import cv2


@dataclass
class VideoProperties:
    """
    Container for video properties extracted from OpenCV VideoCapture.
    
    Attributes:
        fps: Frames per second of the video
        frame_count: Total number of frames in the video
        width: Width of video frames in pixels
        height: Height of video frames in pixels
    """
    fps: float
    frame_count: int
    width: int
    height: int

    @property
    def duration(self) -> float:
        """Calculate video duration in seconds"""
        return self.frame_count / self.fps if self.fps > 0 else 0.0

    @property
    def resolution(self) -> tuple[int, int]:
        """Get resolution as (width, height) tuple"""
        return (self.width, self.height)

    def __str__(self) -> str:
        """String representation of video properties"""
        return (f"VideoProperties(fps={self.fps}, resolution={self.width}x{self.height}, "
                f"frames={self.frame_count}, duration={self.duration:.2f}s)")

    @classmethod
    def from_capture(cls, cap: cv2.VideoCapture) -> 'VideoProperties':
        """Create VideoProperties from OpenCV VideoCapture object"""
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        return cls(fps=fps, frame_count=frame_count, width=width, height=height)

class ExtractFrames:
    """
    A class to extract all frames from an MP4 video file.
    
    Attributes:
        video_path (str): Path to the input MP4 video file
        output_dir (str): Directory where extracted frames will be saved
        frame_format (str): Format for saved frame images (default: 'jpg')
    """
    def __init__(self, video_path: str, output_dir: str = "", frame_format: str = ""):
        """
        Initialize the ExtractFrames object.

        Args:
            video_path (str): Path to the MP4 video file
            output_dir (str, optional): Output directory for frames. If None, creates a folder
                                        named after the video file
            frame_format (str, optional): Image format for saved frames ('jpg', 'png', etc.)
        """
        self.video_path = video_path

        # Set output directory
        if not output_dir:
            video_name = Path(video_path).stem
            self.output_dir = f"{video_name}_frames"
        else:
            self.output_dir = output_dir

        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)

        # Set the frame format
        if not frame_format:
            self.frame_format = "jpg"
        else:
            self.frame_format = frame_format.lower()

    def get_video_info(self) -> VideoProperties:
        """
        Get basic information about the video file.
        
        Returns:
            class[VideoProperties]: Dataclass containing video properties
        """
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {self.video_path}")
        video_props = VideoProperties.from_capture(cap)
        cap.release()
        return video_props

    def extract_all_frames(self, prefix: str = "frame"):
        """
        Extract all frames from the video and save to disk.
        
        Args:
            prefix (str): Prefix for saved frame filenames
            
        Returns:
            None
        """
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {self.video_path}")
        video_props = VideoProperties.from_capture(cap)

        print(f"Extracting {video_props.frame_count} frames from {self.video_path}")
        print(f"Video info: {video_props.width}x{video_props.height}, {video_props.fps:.2f} FPS, {video_props.duration:.2f}s")

        frame_number = 0
        while True:
            # Get a frame
            ret, frame = cap.read()
            if not ret:
                break

            # # Generate filename with zero-padded frame number
            # filename = f"{prefix}_{frame_number:06d}.{self.frame_format}"
            # filepath = os.path.join(self.output_dir, filename)
            # cv2.imwrite(filepath, frame)

            # Progress indicator
            frame_number += 1
            if frame_number % 20 == 0:
                print(f"  Processed {frame_number}/{video_props.frame_count} frames...")
                # Generate filename with zero-padded frame number
                filename = f"{prefix}_{frame_number:06d}.{self.frame_format}"
                filepath = os.path.join(self.output_dir, filename)
                cv2.imwrite(filepath, frame)

        # Release the video file
        cap.release()
        print(f"Extraction complete! {frame_number} frames extracted.")
        print(f"Frames saved to: {self.output_dir}")

    # def extract_frames_at_intervals(self, interval_seconds: float, save_frames: bool = True,
    #                               prefix: str = "frame") -> List[np.ndarray]:
    #     """
    #     Extract frames at specific time intervals.

    #     Args:
    #         interval_seconds (float): Time interval between extracted frames
    #         save_frames (bool): Whether to save frames to disk
    #         prefix (str): Prefix for saved frame filenames

    #     Returns:
    #         List[np.ndarray]: List of extracted frames
    #     """
    #     cap = cv2.VideoCapture(self.video_path)

    #     if not cap.isOpened():
    #         raise ValueError(f"Could not open video file: {self.video_path}")

    #     fps = cap.get(cv2.CAP_PROP_FPS)
    #     frame_interval = int(fps * interval_seconds)

    #     frames = []
    #     frame_number = 0
    #     saved_count = 0

    #     print(f"Extracting frames every {interval_seconds} seconds (every {frame_interval} frames)")

    #     while True:
    #         ret, frame = cap.read()

    #         if not ret:
    #             break

    #         if frame_number % frame_interval == 0:
    #             frames.append(frame.copy())

    #             if save_frames:
    #                 timestamp = frame_number / fps
    #                 filename = f"{prefix}_{saved_count:04d}_t{timestamp:.2f}s.{self.frame_format}"
    #                 filepath = os.path.join(self.output_dir, filename)
    #                 cv2.imwrite(filepath, frame)

    #             saved_count += 1

    #         frame_number += 1
    #     cap.release()

    #     print(f"Extraction complete! {len(frames)} frames extracted at {interval_seconds}s intervals.")
    #     if save_frames:
    #         print(f"Frames saved to: {self.output_dir}")

    #     return frames

    # def extract_frame_at_time(self, time_seconds: float) -> Optional[np.ndarray]:
    #     """
    #     Extract a single frame at a specific time.

    #     Args:
    #         time_seconds (float): Time in seconds where to extract the frame

    #     Returns:
    #         np.ndarray or None: The extracted frame, or None if unsuccessful
    #     """
    #     cap = cv2.VideoCapture(self.video_path)

    #     if not cap.isOpened():
    #         raise ValueError(f"Could not open video file: {self.video_path}")

    #     fps = cap.get(cv2.CAP_PROP_FPS)
    #     frame_number = int(fps * time_seconds)

    #     # Set the frame position
    #     cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

    #     ret, frame = cap.read()
    #     cap.release()

    #     if ret:
    #         return frame
    #     else:
    #         print(f"Could not extract frame at {time_seconds} seconds")
    #         return None


# Example usage
if __name__ == "__main__":
    # Example usage
    extractor = ExtractFrames("CAM_A_video.mp4", output_dir="extracted_frames")

    # Get video information
    print(extractor.get_video_info())

    # # Extract all frames
    # extractor.extract_all_frames()
