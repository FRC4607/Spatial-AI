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
        self.spatial_ai_tbl = self.nt.getTable("frc4607-spatial-ai")

        # NT connection and pubs
        self.command_pub = self.spatial_ai_tbl.getBooleanTopic("record").publish()
        self.command_pub.setDefault(False)
        self.command_pub = self.spatial_ai_tbl.getBooleanTopic("inference").publish()
        self.command_pub.setDefault(False)

        # NT connection and subs
        self.fps_sub = self.spatial_ai_tbl.getDoubleTopic("FPS").subscribe(0.0)
        self.detection_sub = self.spatial_ai_tbl.getBooleanTopic("detection").subscribe(False)
        self.label_sub = self.spatial_ai_tbl.getStringTopic("label").subscribe("")
        self.spatial_x_sub = self.spatial_ai_tbl.getDoubleTopic("spatial_X").subscribe(0.0)
        self.spatial_y_sub = self.spatial_ai_tbl.getDoubleTopic("spatial_Y").subscribe(0.0)
        self.spatial_z_sub = self.spatial_ai_tbl.getDoubleTopic("spatial_Z").subscribe(0.0)
        self.status_sub = self.spatial_ai_tbl.getStringTopic("status").subscribe("")

        while True:
            time.sleep(1)

if __name__ == "__main__":
    host = SpatialAiHost()
