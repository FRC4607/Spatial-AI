# 🧠 Spatial-AI

The goal of this project is to develop the tools and processes necessary to provide **timely and reliable robot-relative game piece detection** to the robot controller via WPILib NetworkTables.

> Simply put: if the robot stands still for a second, this system will detect game objects ***and where they are*** relative to the robot.

This system supports two primary modes: **Development** and **Competition**.

🔧 Development Mode

- SSH into the Raspberry Pi (frc4607@frc4607-spatial-ai) and run `spatial-inference` to view the stream at http://localhost:5000/
- Or run `recorder` to capture video and save it to an attached USB drive for later playback
- The FRC4607 Spatial AI service (connects to NT4 using host frc4607-spatial-ai) can also be used view spatial inferencing and recording via NT control

🏁 Competition Mode

- The FRC4607 Spatial AI service will connect to NT4 using team number 4607
- **Inferencing** is started and during bootup 
- **Recording** to the attached USB drive is triggered by start/stop signals received from the robot code.

🐞 Debugging

- Use `replay` on a laptop to play recorded video files and view inferencing results

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

This project uses the following hardware:

🔗 [**OAK-D Lite**](https://shop.luxonis.com/products/oak-d-lite-1?variant=42583102456031)  
- B&W Stereo + color camera in one compact device  
- Provides both object detection and 3D location (relative to the camera)

🔗 [**Raspberry Pi 5**](https://www.raspberrypi.com/products/raspberry-pi-5/)  
- Hosts the OAK-D Lite camera  
- Runs inference and publishes results to NetworkTables  
- Captures video streams to a connected USB drive

> ⚠️ More powerful host hardware is supported and may be explored in future implementations.

---

## 💻 Software

These tools are required:

- 🔗 [**Python 3**](https://www.python.org/) – Core runtime environment on the Pi
- 🔗 [**pyntcore**](https://pypi.org/project/pyntcore/) – NetworkTables client library
- 🔗 [**DepthAI & SDK**](https://github.com/luxonis/depthai/blob/main/depthai_sdk/README.md) – Interface to the OAK-D camera
- 🔗 [**Luxonis YOLO Converter**](https://tools.luxonis.com/) – Converts YOLOv5/v8 models to `.blob` format

---

## 🍓 1. Setting Up the Raspberry Pi 5

📝 Use a custom Raspberry Pi 5 image with:

- Raspberry Pi OS Lite (64-bit, headless)
- SSH enabled
- Bluetooth, WiFi, and Audio HW disabled
- Several unused services disabled
- This project is cloned and the virtual environment is setup

### ⚙️ Steps

1. Download and install Raspberry Pi OS Lite using [Raspberry Pi Imager](https://www.raspberrypi.com/documentation/computers/getting-started.html#raspberry-pi-imager)
   - In "Edit Settings":
     - **Hostname**: `frc4607-spatial-ai`
     - **Username**: `frc4607`
     - **Password**: `frc4607`
   - Under "Services":  
     ✅ Enable SSH and password authentication

2. Clone this repo to your PC

3. From a command prompt at the projects root, run `setup.bat` to setup the virtual environment

4. From a PowerShell on your PC, run the command below to completely setup the Raspberry PI:
```.\setup_pi.ps1 -User "you" -Email "you@example.com"```

5. Use the commands below to switch between the FRC4607 Spatial AI service modes:
```powershell .\set_dev_mode.ps1```
```powershell .\set_comp_mode.ps1```


🔗 [Raspberry Pi Docs](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html)  
🔗 [Embedded Pi Setup Resource](https://github.com/johnwinans/raspberry-pi-install)

---

## 📸 2. Gathering the Training Images

### Best Practices:

- Use the **robot-mounted OAK-D Lite** to capture all data
- Gather a core dataset on the BRIC field:
  - Vary lighting, backgrounds, and robot poses
- Supplement the dataset using curated screenshots from match video

🎯 **Goal**: Create a focused, high-quality dataset  
> “Don't try to boil the ocean.”

---

## 🧹 3. Preparing the Training Images

### Steps:

1. **Annotate** – Draw bounding boxes and assign class labels  
2. **Format** – Organize in a YOLO-compatible folder layout

> 📝 Use Roboflow for annotation and export:  
🔗 [Roboflow - FRC4607 Workspace](https://app.roboflow.com/frc4607)

🔗 [Ultralytics Data Annotation Guide](https://docs.ultralytics.com/guides/data-collection-and-annotation/#introduction)

---

## 🧠 4. Training the YOLO Model

We use **[YOLOv5](https://docs.ultralytics.com/yolov5/)** to train models on our dataset. As data grows throughout the season, we continuously retrain.

> ⚠️ YOLOv8 is newer and may be adopted in the future if it improves performance.

Training is done using **Google Colab**, with outputs saved to Google Drive. The GitHub auto-commit feature uses a GitHub token for uploads.

### 🔐 Setup:

- Create a folder: `Google Colab` at the root of your Google Drive
- Add a file: `github_token.txt` inside that folder

### ✅ Colab Training Steps:

1. Open the notebook from GitHub  
   ![Figure 1](resources/figure1.png)

2. Enable GPU:  
   `Runtime` → `Change runtime type` → `GPU`  
   ![Figure 2](resources/figure2.png)

3. Run cells and monitor progress actively  
   > Colab disconnects if idle  
   ![Figure 3](resources/figure3.png)

4. Once training finishes, the `.pt` file is saved to the `models/` directory

5. Convert the PyTorch model using the [Luxonis Model Converter](https://tools.luxonis.com/)  
   ![Figure 4](resources/figure4.png)

6. Download and extract the `results.zip` to the same directory as your `.pt` file  
   ![Figure 5](resources/figure5.png)

> ⚠️ Ignore deprecation warning and do **not** use [Luxonis HubAI](https://hub.luxonis.com/ai) for now. The DepthAI SDK v2 still depends on the older format.

---

## 🚀 5. Running the YOLO Model

🚧 _Coming soon: Real-time inference with DepthAI SDK and NetworkTables messaging._

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