## Models

This folder contains models built for various FRC games. They are organized by game year and training date. The symbolic link `model` points to the model that will be loaded by the inference engine at runtime. This design allows you to switch models simply by updating the symbolic link, without modifying any of the Python scripts.

> ⚠️ Note: This assumes the model family (e.g. YOLOv5 vs YOLOv8) has not changed.

## 📂 Models Structure

```
models/
├── 2025/       # YOLO models for Reefscape
├── 2026/       # YOLO models for Rebuilt
├── model       # Symbolic link to the model to load at runtime
└── README.md
```