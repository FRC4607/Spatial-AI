import cv2
import depthai as dai
import time
from depthai_sdk import OakCamera, RecordType
from depthai_sdk.classes import DetectionPacket

with OakCamera(usb_speed=dai.UsbSpeed.HIGH) as oak:
    color = oak.camera(source='color', resolution='1080p', fps=30)
    color.config_color_camera(isp_scale=(2, 3)) # 720P
    # oak.stereo(
    #     left=oak.camera(source='left', resolution='480p'),
    #     right=oak.camera(source='right', resolution='480p')      
    #     )

    nn = oak.create_nn('./models/yolov5n.json', color, nn_type='yolo', spatial=True)

    nn.config_spatial(
        bb_scale_factor=0.5, # Scaling bounding box before averaging the depth in that ROI
        lower_threshold=300, # Discard depth points below 30cm
        upper_threshold=10000, # Discard depth pints above 10m
        # Average depth points before calculating X and Y spatial coordinates:
        calc_algo=dai.SpatialLocationCalculatorAlgorithm.AVERAGE
    )

    # def cb(packet: DetectionPacket):
    #     for det in packet.img_detections.detections:
    #         print("==========================================================")
    #         print(
    #             f"label={det.label}, "
    #             f"x={det.spatialCoordinates.x}, "
    #             f"y={det.spatialCoordinates.y}, "
    #             f"z={det.spatialCoordinates.z}"
    #             )

    def cb(packet: DetectionPacket):
        visualizer = packet.visualizer
        frame = visualizer.draw(packet.frame)
        cv2.imshow('Visualizer', frame)
        # video_writer.write(resized_frame)

    # vis = oak.visualize(nn.out.passthrough, fps=True)
    # vis.detections().text(auto_scale=True, font_scale=0.5, font_thickness=1)

    # oak.visualize(nn.out.passthrough, fps=True, callback=cb).detections().text(auto_scale=False, font_position=22, font_scale=0.4, font_thickness=1) 
    oak.record([color.out.encoded], '/media/ejmccalla/RECORDINGS/Match_1/', RecordType.VIDEO)
    #oak.record([color], '/media/ejmccalla/RECORDINGS/Match_1/', RecordType.VIDEO)
    
    oak.start(blocking=True)
