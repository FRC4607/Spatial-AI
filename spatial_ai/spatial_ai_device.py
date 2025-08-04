"""Spatial AI local device module."""
import os
import time
import logging
from collections import deque
import ntcore
from depthai import UsbSpeed
from depthai_sdk import OakCamera
from depthai_sdk.classes import DetectionPacket
from spatial_ai.oak_config import OakConfig
from spatial_ai.recorder import Recorder
import time
import threading
import cv2
from flask import Flask, Response


current_frame = None  # pylint: disable=C0103
frame_lock = threading.Lock()
app = Flask(__name__)

@app.route('/')
def index():
    """Flask index decorator."""
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
    """Flask video decorator."""
    def generate():
        while True:
            with frame_lock:
                frame = current_frame
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
    global current_frame  # pylint: disable=W0603
    with frame_lock:
        current_frame = frame.copy() if frame is not None else None


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
        self._host = os.getenv("SPATIAL_AI_HOST", "host-spatial-ai")
        self._logger.info("SPATIAL_AI_MODE %s, SPATIAL_AI_HOST %s", self._mode, self._host)

        # Setup NT connection and pubs/subs
        self._nt = ntcore.NetworkTableInstance.getDefault()
        self._nt.startClient4(identity="spatial-ai-dev")
        self._spatial_ai_tbl = self._nt.getTable("spatial-ai")
        self._logger.info("Using table %s", self._spatial_ai_tbl.__str__())
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
        self._command_sub = self._spatial_ai_tbl.getStringTopic("command").subscribe("inference")
        self._inference_model_path_sub = self._spatial_ai_tbl.getStringTopic("inference_model").subscribe("./models/2025/07-25_15-28-56/yolov5n.json")
        self._inference_time_sub = self._spatial_ai_tbl.getIntegerTopic("inference_time").subscribe(60)
        self._record_path_sub = self._spatial_ai_tbl.getStringTopic("record_path").subscribe("/media/RECORDINGS/dev")
        self._record_time_sub = self._spatial_ai_tbl.getIntegerTopic("record_time").subscribe(15)

        # Development mode
        if self._mode == "dev":
            self._nt.setServer(
                server_name=self._host,
                port=ntcore.NetworkTableInstance.kDefaultPort4
            )

        # Competition mode
        elif self._mode == "comp":
            self._nt.setServerTeam(
                team=4607,
                port=ntcore.NetworkTableInstance.kDefaultPort4
            )
        else:
            raise RuntimeError(f"Unknown mode {self._mode}")

        # Lazy-loaded attributes
        self.labels: list[str] = None  # type: ignore
        self.command: str = None  # type: ignore
        self.inference_model_path: str = None  # type: ignore
        self.inference_time: int = None  # type: ignore
        self.record_time: int = None  # type: ignore
        self.record_path: str = None  # type: ignore

    def update(self):
        """
        Update the sub topics
        """
        if self._mode == "dev":
            self.command = self._command_sub.get()
            self.inference_model_path = self._inference_model_path_sub.get()
            self.inference_time = self._inference_time_sub.get()
            self.record_time = self._record_time_sub.get()
            self.record_path = self._record_path_sub.get()

    def is_in_dev_mode(self):
        """Return true if in development mode."""
        return self._mode == "dev"

    def set_labels(self, labels: list[str]):
        """Set the labels of the NN model."""
        self.labels = labels

    def nn_detection_callback(self, packet: DetectionPacket):
        """Process callback."""
        if not self.labels:
            self._logger.warning("Labels not set. Skipping detection callback.")
            return
        if not packet.img_detections.detections: # type: ignore
            self._detection_pub.set(False)
            return

        frame = packet.frame
        for det in packet.img_detections.detections:  # type: ignore
            x1 = int(det.xmin * 768)
            y1 = int(det.ymin * 432)
            x2 = int(det.xmax * 768)
            y2 = int(det.ymax * 432)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f"{self.labels[det.label]}: {det.confidence:.2f}"
            cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        update_stream(frame)

        # Publish the FPS
        self._fps_tracker.update()
        if self._fps_tracker.frame_count % 15 == 0:
            self._fps_pub.set(self._fps_tracker.get_fps())

        # Publish the first detection
        for det in packet.img_detections.detections:  # type: ignore
            label_str = self.labels[det.label]
            coords = det.spatialCoordinates  # type: ignore
            self._detection_pub.set(True)
            self._label_pub.set(label_str)
            self._spatial_x_pub.set(coords.x)
            self._spatial_y_pub.set(coords.y)
            self._spatial_z_pub.set(coords.z)
            self._logger.info("Detected %s at (%.2f, %.2f, %.2f)", label_str, coords.x, coords.y, coords.z)
            break


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("SpatialAiDevice")
    spatial_ai_device = SpatialAiDevice(log=logger)

    # Run the service in competition mode
    if not spatial_ai_device.is_in_dev_mode():
        with OakCamera(usb_speed=UsbSpeed.HIGH) as oak:
            logger.info("Configuring OAK device for spatial inference")
            oak_config = OakConfig(oak=oak)
            oak_config.color_camera(resolution="med")
            oak_config.stereo_cameras()
            label_list = oak_config.inference(model_path="./models/2025/07-25_15-28-56/yolov5n.json")
            spatial_ai_device.set_labels(labels=label_list)
            oak_config.detections_callback(callback=spatial_ai_device.nn_detection_callback)
            logger.info("Comp Mode: start publishing detctions")
            oak.start(blocking=True)

    # Run the service in development mode
    else:
        while True:
            spatial_ai_device.update()

            # Make a recording
            if spatial_ai_device.command == "record":
                logger.info("Configuring OAK device for recording")
                Recorder().start(
                    save_path=spatial_ai_device.record_path,
                    rec_len_s=spatial_ai_device.record_time,
                    resolution="med"
                )
                logger.info("Recording saved to %s", spatial_ai_device.record_path)

            # Run spatial inference
            elif spatial_ai_device.command == "inference":
                start_streaming(port=5000)
                with OakCamera(usb_speed=UsbSpeed.HIGH) as oak:
                    logger.info("Configuring OAK device for spatial inference")
                    oak_config = OakConfig(oak=oak)
                    oak_config.color_camera(resolution="med")
                    oak_config.stereo_cameras()
                    label_list = oak_config.inference(model_path=spatial_ai_device.inference_model_path)
                    spatial_ai_device.set_labels(labels=label_list)
                    oak_config.detections_callback(callback=spatial_ai_device.nn_detection_callback)

                    oak.start()
                    start_time = time.monotonic()  # pylint: disable=C0103
                    last_print_time = 5  # pylint: disable=C0103
                    while oak.running():
                        running_time = time.monotonic() - start_time
                        if running_time > last_print_time:
                            last_print_time+=5
                            print(f"  Running time: {running_time}")
                        if running_time > spatial_ai_device.inference_time:
                            break
                        oak.poll()
            else:
                time.sleep(1)
