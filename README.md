# 🧠 Spatial-AI

The goal of this project is to develop a process that provides **timely and reliable robot-relative game piece detection** to the robot controller via **WPILib NetworkTables**.

> Simply put: if the robot stands still for a second, this system will detect game objects ***and where they are*** relative to the robot.

---

## 📚 Table of Contents
- [🔧 Hardware](#-hardware)
- [💻 Software](#-software)
- [🍓 1. Setting Up the Raspberry Pi 4B](#-1-setting-up-the-raspberry-pi-4b)
- [📸 2. Gathering the Training Images](#-2-gathering-the-training-images)
- [🧹 3. Preparing the Training Images](#-3-preparing-the-training-images)
- [🧠 4. Training the YOLO Model](#-4-training-the-yolo-model)
- [🚀 5. Running the YOLO Model](#-5-running-the-yolo-model)
- [📂 Project Structure](#-project-structure-wip)

---

## 🔧 Hardware

The following hardware was used during development. More powerful variants may also work in deployed systems:

🔗 [OAK-D Lite](https://shop.luxonis.com/products/oak-d-lite-1?variant=42583102456031) – AI depth camera
🔗 [Raspberry Pi 4B](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/) – Onboard inference and communication

---

## 💻 Software

These are the software tools used in development:

- [Python 3](https://www.python.org/)  
  Runs on the Raspberry Pi to process OAK-D inference packets and send data to the robot.

- [pyntcore](https://pypi.org/project/pyntcore/)  
  Enables NetworkTables client communication from the Pi to the robot controller.

- [DepthAI & DepthAI SDK](https://github.com/luxonis/depthai/blob/main/depthai_sdk/README.md)  
  Provides the API interface to the OAK-D Lite camera.

- [Luxonis YOLO Conversion Tool](https://tools.luxonis.com/)  
  Converts YOLO models (e.g. from Ultralytics) into `.blob` format for use with OAK-D.

---

## 🍓 1. Setting Up the Raspberry Pi 4B

📝 Build a custom image with the following features:

- Raspberry Pi OS Lite (headless)
- SSH enabled
- Unused services (e.g., Bluetooth) disabled
- Power-hardened (e.g., read-only filesystem)
- Preloaded with all required software and scripts

> 📝 A separate step-by-step document should be created to detail the image creation process.

🔗 [Official Raspberry Pi Docs](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html)  
🔗 [Embedded Pi Setup Resource](https://github.com/johnwinans/raspberry-pi-install)

---

## 📸 2. Gathering the Training Images

During development, training images were sourced from [FRC 118 - Robonauts](https://universe.roboflow.com/robonauts-2025). For competition use, follow this data-gathering strategy:

- Capture a base dataset using the BRIC field environment  
  (Vary lighting, background, robot pose, and object presence)
- Supplement the dataset with curated match footage screenshots

🎯 **Goal**: Build a focused, high-quality dataset optimized for our detection task.  
> "Don't try to boil the ocean."

---

## 🧹 3. Preparing the Training Images

The image preparation process includes:

1. **Annotation** – Draw bounding boxes and label object types  
2. **Formatting** – Organize files into a YOLO-compatible directory structure

📝 A dedicated document (`2026 - Rebuilt Data Collection and Annotation`) should define the team-wide standard for this process.

🔗 [Ultralytics Data Collection & Annotation Guide](https://docs.ultralytics.com/guides/data-collection-and-annotation/#introduction)

---

## 🧠 4. Training the YOLO Model

We use [Ultralytics YOLOv5](https://docs.ultralytics.com/yolov5/) as our base model. The training notebook fine-tunes the model on our custom dataset.

> ⚠️ Note: [YOLOv8](https://docs.ultralytics.com) is the successor to v5 and may be adopted if performance and speed tradeoffs are favorable.

Training is performed using **Google Colab** and stores artifacts in Google Drive. The GitHub auto-commit feature requires a valid GitHub token in the Colab environment.

**Setup requirements**:
- A folder named `Google Colab` at the root of your Google Drive
- A `github_token.txt` file placed inside that folder

---

### Using Google Colab

[Google Colab](https://colab.research.google.com/) provides a Jupyter Notebook environment with access to GPUs for faster training. CPU-only training is extremely slow and is **not supported**.

#### ✅ Steps:
1. Open the training notebook from GitHub using **"Open in Colab"**  
   ![Figure 1](resources/figure1.png)  
   *Figure 1: Opening a GitHub notebook in Google Colab*

2. Enable GPU runtime  
   Go to `Runtime` → `Change runtime type` → Select **GPU**  
   ![Figure 2](resources/figure2.png)  
   *Figure 2: Setting GPU runtime in Google Colab*

3. Run the training script and **actively monitor the progress**.  
   If the window becomes inactive or your machine goes to sleep, Colab may disconnect. If this happens, resume training by setting the global variable:
   ```python
   RESUME = True
   ```

   ![Figure 3](resources/figure3.png)  
   *Figure 3: YOLO training progress output in Colab*

4. Once complete, the notebook will copy the PyTorch weights (a *.pt file) to the `models/` directory.

5. Use the online [Luxonis Model Converter](https://tools.luxonis.com/) to convert the PyTorch weights model to a blob file format suitable for the Oak-D Lite. See Figure 4 below for an example of the model conversion inputs. Refer to the Colab training above to determine the input image size. Click the Submit button to begin the model conversion process.

> ⚠️ Note: Until the DepthAI SDK migrates from v2 to v3, using the [Luxonis HubAI](https://hub.luxonis.com/ai) conversion tool will not work. Ignore the deprecation warning and continue to use the model converter linked above.

![Figure 4](resources/figure4.png)
*Figure 4: Luxonis YOLO Model Conversion Tool*

6. Once conversino is complete, the tool will prompt to save `results.zip` to your local PC. Save the file to a location on your PC which isn't the Spatial-AI repository. Extract all of zipped files and copy these into the `models/` directory of the Spatial-AI repository. See Figure 5 below for an example of all of the zipped files from the model conversion.

![Figure 5](resources/figure5.png)
*Figure 5: Converted PyTorch Model Files*

---

## 🚀 5. Running the YOLO Model

_(Coming soon: real-time inference pipeline using DepthAI SDK and NetworkTables messaging)_

---

## 📂 Project Structure (WIP)

```
spatial-ai/
├── models/           # YOLO model blobs (PyTorch, OpenVINO)
├── notebooks/        # Google Colab training notebooks
├── pi-setup/         # Raspberry Pi setup scripts and image tools
├── resources/        # Figures and documentation resources
├── training_data/    # Annotated YOLO training datasets
├── src/              # Python code for inference and NetworkTables communication
└── README.md
```