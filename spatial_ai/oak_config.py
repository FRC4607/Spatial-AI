"""Common OAK configuration."""
import warnings
from depthai_sdk import OakCamera, RecordType, components
from depthai import SpatialLocationCalculatorAlgorithm


class OakConfig():
    """
    A class to configure the OAK device.

    Attributes:
        None
    Methods:
        color_camera - Configure the OAK color camera
    """
    RES_MAP = {
        "low": (1, 3),  # gets implmented as (640x360)
        "med": (2, 5),  # gets implmented as (768x432)
        "high": (2, 3), # gets implmented as (1280x720)
    }

    def __init__(self, oak: OakCamera):
        """
        Initialize the OakConfig class.

        Args:
            oak (OakCamera): An OAKCamera instance.
        """
        # Save the OAK instance
        self._oak = oak

        # Placeholders for lazy object creation
        self._cc: components.camera_component.CameraComponent = None # type: ignore
        self._nn: components.nn_component.NNComponent = None # type: ignore

    def color_camera(self, resolution: str):
        """
        Configure the OAK color camera.

        Args:
            resolution (str): Camera resolution
        """
        if resolution not in self.RES_MAP:
            raise ValueError(f"Unknownn resolution {resolution}")
        if self._cc:
            warnings.warn("Oak color camera already configured")
        else:
            self._cc = self._oak.camera(
                source='color',
                resolution='1080p',
                fps=30,
                encode='H265'
            )
            self._cc.config_color_camera(isp_scale=self.RES_MAP[resolution])

    def recording(self, save_path: str):
        """
        Configure the OAK recording.

        Args:
            save_path (str): Path to save the recording
        """
        if not self._cc:
            warnings.warn("Oak color camera not configured, configuring now")
            self.color_camera(resolution="med")
        self._oak.record(
            outputs=[self._cc.out.encoded],
            path=save_path,
            record_type=RecordType.VIDEO
        )

    def inference(self, model_path: str):
        """
        Configure the OAK NN for inference.

        Args:
            model_path (str): Path to the inference model
        """
        if self._nn:
            warnings.warn("Oak NN already configured")
        else:
            if not self._cc:
                warnings.warn("Oak color camera not configured, configuring now")
                self.color_camera(resolution="med")
            self._nn = self._oak.create_nn(
                model=model_path,
                input=self._cc,
                nn_type='yolo',
                spatial=True
            )
            calc_algo = SpatialLocationCalculatorAlgorithm.AVERAGE
            self._nn.config_spatial(
                bb_scale_factor=0.5,    # Scaling bounding box before averaging the depth in that ROI
                lower_threshold=300,    # Discard depth points below 30cm
                upper_threshold=10000,  # Discard depth pints above 10m
                calc_algo=calc_algo     # Average depth points before calculating X and Y spatial coordinates
            )
            self._oak.visualize(self._nn, fps=True)
