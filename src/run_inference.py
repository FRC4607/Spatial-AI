import cv2 
from depthai_sdk.visualize.visualizer_helper import FramePosition, VisualizerHelper
from depthai_sdk import OakCamera
import depthai as dai
from depthai_sdk.classes import SpatialBbMappingPacket, DetectionPacket
from depthai_sdk.visualize.visualizer import Visualizer

with OakCamera(usb_speed=dai.UsbSpeed.HIGH) as oak:
    color = oak.create_camera('color')

    # # List of models that are supported out-of-the-box by the SDK:
    # # https://docs.luxonis.com/projects/sdk/en/latest/features/ai_models/#sdk-supported-models
    # nn = oak.create_nn('yolov5n_coco_416x416', color, spatial=True)

    nn = oak.create_nn('./models/yolov8n_2025-05-17_00-11-26.json', color, nn_type='yolo', spatial=True)

    nn.config_spatial(
        bb_scale_factor=0.5, # Scaling bounding box before averaging the depth in that ROI
        lower_threshold=300, # Discard depth points below 30cm
        upper_threshold=10000, # Discard depth pints above 10m
        # Average depth points before calculating X and Y spatial coordinates:
        calc_algo=dai.SpatialLocationCalculatorAlgorithm.AVERAGE
    )

    def cb(packet: DetectionPacket):
        print("==========================================================")
        for det in packet.img_detections.detections:
            print(f"label={det.label}, x={det.spatialCoordinates.x}, y={det.spatialCoordinates.y}, z={det.spatialCoordinates.z}")

    oak.visualize([nn.out.passthrough], fps=True)
    # oak.callback(nn.out.passthrough, callback=cb)
    oak.start(blocking=True)