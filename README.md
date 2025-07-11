# 🧠 Spatial-AI

The goal of this project is to develop a process to provide **timely and reliable robot-relative game piece detection** to the robot controller via **WPILib NetworkTables**.

> Simply put: if the robot stands still for a second, this system will detect game objects ***and where they are*** relative to the robot.

---

## 🔧 Hardware

The following hardware was used during development. More powerful variants may also work in deployed systems:

- [OAK-D Lite](https://shop.luxonis.com/products/oak-d-lite-1?variant=42583102456031)
- [Raspberry Pi 4B](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/)

---

## 💻 Software

These are the software tools used in development:

- [Python 3](https://www.python.org/)  
  Used on the Raspberry Pi for processing OAK-D inference packets and sending them to the robot via NetworkTables.

- [pyntcore](https://pypi.org/project/pyntcore/)  
  Enables NetworkTables client communication on the Raspberry Pi.

- [DepthAI & DepthAI SDK](https://github.com/luxonis/depthai/blob/main/depthai_sdk/README.md)  
  Provides the API interface to the OAK-D Lite.

- [Luxonis YOLO Conversion Tool](https://tools.luxonis.com/)  
  Converts YOLO models (e.g. from Ultralytics) into `.blob` format for OAK-D Lite inference.

---

## 🍓 Setting Up the Raspberry Pi 4B

📝 Build a custom image with the following features:

- Raspberry Pi OS Lite (headless)
- SSH enabled
- Unused services (e.g., Bluetooth) disabled
- Power-hardened (e.g., read-only filesystem)
- Preloaded with all necessary software

📝 Create a document with step-by-step instructions on how this image was created.

> 🔗 [Official Raspberry Pi Docs](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html)  
> 🔗 [Embedded Pi Setup Resource](https://github.com/johnwinans/raspberry-pi-install)

---

## 📸 1. Gathering the Training Images

During development, training images were sourced from [FRC 118 - Robonauts](https://universe.roboflow.com/robonauts-2025). For competition use, the process will involve:

- Capturing a base set of images from the BRIC
  - Consider variations: lighting, background, robot pose, object presence
- Supplementing the base set with curated images from match recordings

🎯 The goal is a focused, high-quality dataset optimized for **our specific detection use case**.  
> As the saying goes: “Don’t try to boil the ocean.”

---

## 🧹 2. Preparing the Training Images

The image prep process includes:

1. **Annotation**: Draw bounding boxes and label objects
2. **Formatting**: Organize the data into YOLO-compatible structure

📝 Create a **2026 - Rebuilt Data Collection and Annotation** document to define this team-wide process.

🔗 [Ultralytics Data Collection & Annotation Guide](https://docs.ultralytics.com/guides/data-collection-and-annotation/#introduction)

---

## 🧠 3. Training the YOLO Model

We’ll use [Ultralytics YOLOv5](https://docs.ultralytics.com/yolov5/) as the starting model. The custom dataset will fine-tune this model for our task.

> ⚠️ YOLOv8 is the successor to v5 — we may consider switching based on performance vs. inference speed tradeoffs.

### Using Google Colab

[Google Colab](https://colab.research.google.com/) provides a Jupyter Notebook environment with CPU/GPU access to train the model.

![Figure 1](resources/figure1.png)  
*Figure 1: Opening a GitHub Jupyter Notebook using Google Colab*

---

## 🚀 4. Running the YOLO Model

_(Work in progress — to be completed based on deployment process and pipeline)_

---

## 📂 Project Structure (WIP)
spatial-ai/
├── models/ # YOLO model blobs
├── notebooks/ # Colab training notebooks
├── pi-setup/ # Raspberry Pi images and setup scripts
├── resources/ # Documentation resources
├── training_data/ # Labeled and annotated training data
├── src/ # Main Python code for inference and comms
