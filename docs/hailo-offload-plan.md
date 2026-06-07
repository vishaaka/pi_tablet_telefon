# Hailo Offload Plan

## What Hailo Can Accelerate Here

The Raspberry Pi 5 Hailo-8/8L module is useful for compiled neural-network inference. In this project, the practical target is the video side:

- Face or person detection during video calls
- Object detection for camera-aware interactions
- Pose or gesture detection
- Lightweight segmentation or background effects

These tasks can run on the Raspberry Pi OS host and expose results to the Android app through the backend API.

## What Should Stay Off Hailo-8/8L

The current voice loop should remain on CPU or external services:

- STT with Whisper Tiny
- Chat replies with scripted rules or Qwen
- TTS with Edge TTS or Piper

Hailo-8/8L is not a drop-in accelerator for Python code, llama.cpp, Whisper, or TTS. Models must be compiled for Hailo as HEF files, and the strongest supported Raspberry Pi path is camera/vision inference through `rpicam-apps`, Picamera2, HailoRT, and post-processing assets.

## First Integration Step

1. Keep Android/Waydroid as the UI layer.
2. Run Hailo only on the Raspberry Pi OS host backend.
3. Verify vision support:

```bash
bash device/scripts/check-hailo-vision.sh
```

4. Add a backend vision worker that consumes a camera stream and publishes:

```json
{
  "person_present": true,
  "face_present": true,
  "objects": ["person", "phone"],
  "confidence": 0.86
}
```

5. Let the Android call screen use those results for video-call state, avatar attention, and child-safe camera interactions.

## Current Backend Status

`GET /health` reports whether Hailo is visible, whether `/dev/hailo*` exists, whether `hailortcli` can identify the board, and whether Raspberry Pi Hailo camera assets are installed.
