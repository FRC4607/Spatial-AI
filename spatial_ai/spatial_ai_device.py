"""Spatial AI local device module."""
import os
import time
import logging
from pathlib import Path
import ntcore
from depthai import UsbSpeed
from depthai_sdk import OakCamera
from depthai_sdk.classes import DetectionPacket
from spatial_ai.oak_config import OakConfig
from spatial_ai.recorder import Recorder


class SpatialAiDevice():
    """
    A spatial AI local device.
    """
    def __init__(self, log: logging.Logger):
        # Logging
        self._logger = log

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

        for det in packet.img_detections.detections:  # type: ignore
            label_str = self._labels[det.label]
            coords = det.spatialCoordinates  # type: ignore

            self._detection_pub.set(True)
            self._label_pub.set(label_str)
            self._spatial_x_pub.set(coords.x)
            self._spatial_y_pub.set(coords.y)
            self._spatial_z_pub.set(coords.z)

            self._logger.info("Detected %s at (%.2f, %.2f, %.2f)", label_str, coords.x, coords.y, coords.z)
            break  # Only handle the first detection for now

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
