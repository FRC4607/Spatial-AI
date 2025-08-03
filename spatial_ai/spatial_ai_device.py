"""Spatial AI local device module."""
import os
import threading
import time
import logging
from collections import deque
from pathlib import Path
from flask import Flask, Response
import cv2
import ntcore
from depthai import UsbSpeed
from depthai_sdk import OakCamera
from depthai_sdk.classes import DetectionPacket
from spatial_ai.oak_config import OakConfig
from spatial_ai.recorder import Recorder


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

# Global frame storage
CURRENT_FRAME = None
FRAME_LOCK = threading.Lock()

# Flask app
app = Flask(__name__)

@app.route('/')
def index():
    """Index."""
    return '''
    <html>
        <body style="text-align:center; font-family:Arial;">
            <h1>OAK Camera Stream</h1>
            <img src="/video" style="max-width:90%; height:auto;">
            <p>Press F11 for fullscreen</p>
        </body>
    </html>
    '''

@app.route('/video')
def video():
    """Video."""
    def generate():
        while True:
            with FRAME_LOCK:
                frame = CURRENT_FRAME
            if frame is not None:
                ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ret:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            time.sleep(0.03)  # ~30 FPS
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

def start_streaming(port=5000):
    """Start the HTTP server in background thread."""
    def run_server():
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    print(f"Stream: http://localhost:{port}")
    time.sleep(1)  # Let server start

def update_stream(frame):
    """Update the current frame for streaming."""
    global CURRENT_FRAME
    with FRAME_LOCK:
        CURRENT_FRAME = frame.copy() if frame is not None else None

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
        self._host = os.getenv("SPATIAL_AI_HOST", "host-spatial-ai")
        self._logger.info("SPATIAL_AI_MODE %s, SPATIAL_AI_HOST %s", self._mode, self._host)

        # Setup NT connection and pubs/subs
        self._nt = ntcore.NetworkTableInstance.getDefault()
        self._nt.startClient4(identity="spatial-ai-dev")
        self._spatial_ai_tbl = self._nt.getTable("spatial-ai")
        self._logger.info("Using table %s", self._spatial_ai_tbl.__str__())

        # Development mode
        if self._mode == "dev":
            self._nt.setServer(
                server_name=self._host,
                port=ntcore.NetworkTableInstance.kDefaultPort4
            )
            self._rec_sub = self._spatial_ai_tbl.getBooleanTopic("rec").subscribe(False)
            self._rec_time_sub = self._spatial_ai_tbl.getIntegerTopic("rec_time").subscribe(0)
            self.rec = False
            self.rec_time = 0

        # Competition mode
        elif self._mode == "comp":
            self._nt.setServerTeam(
                team=4607,
                port=ntcore.NetworkTableInstance.kDefaultPort4
            )
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
        else:
            raise RuntimeError(f"Unknown mode {self._mode}")

        # Lazy-loaded labels
        self._labels: list[str] = None  # type: ignore

    def is_in_dev_mode(self):
        """Return true if in development mode."""
        return self._mode == "dev"

    def set_labels(self, labels: list[str]):
        """Set the labels of the NN model."""
        self._labels = labels

    def nn_detection_callback(self, packet: DetectionPacket):
        """Process callback."""
        if not self._labels:
            self._logger.warning("Labels not set. Skipping detection callback.")
            return
        if not packet.img_detections.detections: # type: ignore
            self._detection_pub.set(False)
            return

        # cv_frame = packet.frame.getCvFrame()
        # # Draw detection boxes
        # for detection in packet.detections:
        #     bbox = detection.bbox
        #     x1 = int(bbox.xmin * cv_frame.shape[1])
        #     y1 = int(bbox.ymin * cv_frame.shape[0])
        #     x2 = int(bbox.xmax * cv_frame.shape[1])
        #     y2 = int(bbox.ymax * cv_frame.shape[0])
        #     # Green box
        #     cv2.rectangle(cv_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        #     # Label
        #     label = f"{detection.label}: {detection.confidence:.2f}"
        #     cv2.putText(cv_frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        # Send to stream
        update_stream(packet.frame)

        # Publish the FPS
        self._fps_tracker.update()
        if self._fps_tracker.frame_count % 15 == 0:
            self._fps_pub.set(self._fps_tracker.get_fps())

        # Publish the first detection
        for det in packet.img_detections.detections:  # type: ignore
            label_str = self._labels[det.label]
            coords = det.spatialCoordinates  # type: ignore

            self._detection_pub.set(True)
            self._label_pub.set(label_str)
            self._spatial_x_pub.set(coords.x)
            self._spatial_y_pub.set(coords.y)
            self._spatial_z_pub.set(coords.z)

            self._logger.info("Detected %s at (%.2f, %.2f, %.2f)", label_str, coords.x, coords.y, coords.z)
            break

    def update(self):
        """
        Update the sub topics
        """
        if self._mode == "dev":
            self.rec = self._rec_sub.get()
            self.rec_time = self._rec_time_sub.get()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("SpatialAiDevice")
    spatial_ai_device = SpatialAiDevice(log=logger)

    # Run the service in development mode
    if spatial_ai_device.is_in_dev_mode():
        start_streaming(port=5000)
        logger.info("Dev Mode: start listening for host instructions")
        while True:
            spatial_ai_device.update()
            if spatial_ai_device.rec and spatial_ai_device.rec_time > 0:
                logger.info(
                    "Dev Mode: recieved host instructions to make a %ds recording",
                    spatial_ai_device.rec_time
                )
                rec_path = Path("/media/RECORDINGS/dev")
                rec_path.mkdir(parents=True, exist_ok=True)

                Recorder().start(
                    save_path=str(rec_path),
                    rec_len_s=spatial_ai_device.rec_time,
                    resolution="med"
                )
                logger.info("Dev Mode: recording saved to %s", str(rec_path))

            time.sleep(0.5)

    # Run the service in competition mode
    else:
        with OakCamera(usb_speed=UsbSpeed.HIGH) as oak:
            # Configure the OAK (color camera and NN)
            logger.info("Configuring OAK:")
            oak_config = OakConfig(oak=oak)
            oak_config.color_camera(resolution="med")
            oak_config.stereo_cameras()
            logger.info("  Resolution: %s", "med")
            spatial_ai_device.set_labels(
                labels=oak_config.inference(model_path="./models/2025/07-25_15-28-56/yolov5n.json")
            )
            logger.info("  Model: %s", "./models/2025/07-25_15-28-56/yolov5n.json")
            oak_config.inference_detections(callback=spatial_ai_device.nn_detection_callback)

            # Startup the pipeline and publish detections to the NT
            logger.info("Comp Mode: start publishing detctions")
            oak.start(blocking=True)
