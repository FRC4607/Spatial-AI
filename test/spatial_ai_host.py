"""NT host test module."""
import time
import ntcore


class SpatialAiHost():
    """
    A class to test NT connection to the local spatial AI device.
    """
    def __init__(self):
        self.nt = ntcore.NetworkTableInstance.getDefault()
        self.nt.startServer()
        self.spatial_ai_tbl = self.nt.getTable("spatial-ai")

        # Use topics "rec" and "rec_time" to receive signal to start recording
        self.rec_pub = self.spatial_ai_tbl.getBooleanTopic("rec").publish()
        self.rec_pub.setDefault(False)
        self.rec_time_pub = self.spatial_ai_tbl.getIntegerTopic("rec_time").publish()
        self.rec_time_pub.setDefault(0)


    def start_recording(self):
        """
        Signal to the RPI to start recording.
        """
        self.rec_time_pub.set(20)
        self.rec_pub.set(True)

    def stop_recording(self):
        """
        Signal to the RPI to stop recording.
        """
        self.rec_time_pub.set(0)
        self.rec_pub.set(False)


if __name__ == "__main__":
    host = SpatialAiHost()
    time.sleep(5)
    host.start_recording()
    time.sleep(5)
    host.stop_recording()
