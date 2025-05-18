# Spatial-AI
The goal of this project is to develop the process necessary to provide timely and reliable robot-relative game piece detection to the robot controller via WPILib NetworkTables. Simply put, if the robot is standing still for a second, this system will be able to detect game objects ***and where they are*** relative to the robot.

### Hardware
The following are the hardware used to during development. Similar (more powerful variants, etc.) will also work on deployed systems.
- [OAK-D Lite](https://shop.luxonis.com/products/oak-d-lite-1?variant=42583102456031)
- [Raspberry Pi 4B](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/)

### Sofware
The following are the software tools used during development.
- [pyntcore](https://pypi.org/project/pyntcore/) - Used to create a NetworkTables client on the Raspberry Pi.
- [Python3](https://www.python.org/) - Used as the Raspberry Pi programming language for receiving the OAK-D inference packets, processing them, and sending them to the robot via NetworkTables. 
- [DepthAI and DepthAI SDK](https://github.com/luxonis/depthai/blob/main/depthai_sdk/README.md) - Used as API to the OAK-D Lite.
- [Luxonis Yolo Conversion Tool](https://tools.luxonis.com/) - Used to convert YOLO models trained using Ultralytics to a blob format suitable for loading onto the OAK-D Lite


### 1. Setting up the Raspberry Pi 4B
