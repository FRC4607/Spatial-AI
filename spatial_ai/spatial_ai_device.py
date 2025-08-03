"""Spatial AI local device module."""
import os
import time
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
    def __init__(self):
        # Get the mode and host from the local device environment
        self._mode = os.getenv("SPATIAL_AI_MODE", "dev")
        self._host = os.getenv("SPATIAL_AI_HOST", "host-spatial-ai")
        print(f"FRC4607 Spatial AI: mode {self._mode}, host {self._host}")

        # Setup NT connection and pubs/subs
        self._nt = ntcore.NetworkTableInstance.getDefault()
        self._nt.startClient4(identity="spatial-ai-dev")
        self._spatial_ai_tbl = self._nt.getTable("spatial-ai")

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
            # TODO: need to handle transform to robot-relative
            self._spatial_x_pub = self._spatial_ai_tbl.getDoubleTopic("spatial_X").publish()
            self._spatial_x_pub.setDefault(0.0)
            self._spatial_y_pub = self._spatial_ai_tbl.getDoubleTopic("spatial_Y").publish()
            self._spatial_y_pub.setDefault(0.0)
            self._spatial_z_pub = self._spatial_ai_tbl.getDoubleTopic("spatial_Z").publish()
            self._spatial_z_pub.setDefault(0.0)
        else:
            raise RuntimeError(f"Unknown mode {self._mode}")

        # Lazy setting attributes
        self._labels: list[str] = None # type: ignore

    def is_in_dev_mode(self):
        """Return true if in development mode."""
        return self._mode == "dev"

    def set_labels(self, labels: list[str]):
        """Set the labels of the NN model."""
        self._labels = labels

    def nn_detection_callback(self, packet: DetectionPacket):
        """Process callback."""
        for det in packet.img_detections.detections: # type: ignore
            self._detection_pub.set(True)
            self._label_pub.set(self._labels[det.label])
            self._spatial_x_pub.set(det.spatialCoordinates.x) # type: ignore
            self._spatial_y_pub.set(det.spatialCoordinates.y) # type: ignore
            self._spatial_z_pub.set(det.spatialCoordinates.z) # type: ignore
            #TODO: Only use the first entry for now
            break
        self._detection_pub.set(False)
        self._label_pub.set("")
        self._spatial_x_pub.set(0.0)
        self._spatial_y_pub.set(0.0)
        self._spatial_z_pub.set(0.0)

    def update(self):
        """
        Update the sub topics
        """
        if self._mode == "dev":
            self.rec = self._rec_sub.get()
            self.rec_time = self._rec_time_sub.get()


if __name__ == "__main__":
    spatial_ai_device = SpatialAiDevice()

    # Run the service in development mode
    if spatial_ai_device.is_in_dev_mode():
        while True:
            spatial_ai_device.update()
            if spatial_ai_device.rec and spatial_ai_device.rec_time > 0:
                print(f"Recording length in seconds: {spatial_ai_device.rec_time}")
                Recorder().start(
                    save_path="/media/RECORDINGS/practice",
                    rec_len_s=spatial_ai_device.rec_time,
                    resolution="med"
                )
                print("Recording video saved to: /media/RECORDINGS/practice")
            time.sleep(0.5)

    # Run the service in competition mode
    else:
        with OakCamera(usb_speed=UsbSpeed.HIGH) as oak:
            # Configure the OAK (color camera and NN)
            oak_config = OakConfig(oak=oak)
            oak_config.color_camera(resolution="med")
            lables = oak_config.inference(model_path="./models/2025/07-25_15-28-56/yolov5n.json")
            spatial_ai_device.set_labels(labels=lables)
            oak_config.inference_detections(callback=spatial_ai_device.nn_detection_callback)

            # TODO: Setup recording

            # Startup the pipeline and publish detections to the NT
            oak.start(blocking=True)
