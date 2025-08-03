"""Spatial AI local device module."""
import time
import ntcore
from spatial_ai.recorder import Recorder


class SpatialAiDev():
    """
    A spatial AI local device.
    """
    def __init__(self, mode: str = "dev", host: str = "host-spatial-ai"):
        self.rec = False
        self.rec_time = 0
        self._nt = ntcore.NetworkTableInstance.getDefault()
        self._nt.startClient4(identity="spatial-ai-dev")
        if mode == "dev":
            self._nt.setServer(
                server_name=host,
                port=ntcore.NetworkTableInstance.kDefaultPort4
            )
        elif mode == "comp":
            print("Competition mode is not working.")
            # self._nt.setServerTeam(
            #     team=4607,
            #     port=ntcore.NetworkTableInstance.kDefaultPort4
            # )
        else:
            raise RuntimeError(f"Unknown mode {mode}")

        # All topics will be pub/sub under spatial-ai table
        self._spatial_ai_tbl = self._nt.getTable("spatial-ai")

        # Use topics "rec" and "rec_time" to receive signal to start recording
        self._rec_sub = self._spatial_ai_tbl.getBooleanTopic("rec").subscribe(False)
        self._rec_time_sub = self._spatial_ai_tbl.getIntegerTopic("rec_time").subscribe(0)

    def update(self):
        """
        Update the topics
        """
        self.rec = self._rec_sub.get()
        self.rec_time = self._rec_time_sub.get()


if __name__ == "__main__":
    local_dev = SpatialAiDev()
    while True:
        local_dev.update()
        if local_dev.rec and local_dev.rec_time > 0:
            # This will block...not final implementation
            print(f"Recording length in seconds: {local_dev.rec_time}")
            Recorder().start(
                save_path="/media/RECORDINGS/practice",
                rec_len_s=local_dev.rec_time,
                resolution="med"
            )
            print("Recording video saved to: /media/RECORDINGS/practice")
        time.sleep(0.5)
