# AmebaCam: A Real-Time Embedded Camera Streaming and Capture Platform

[English](README.md) | [Chinese](README_zh.md)

This project aims to establish communication between a central server and up to 12 sets of AMB82-MINI development boards, capturing real-time images from the onboard camera of each board via RTSP streaming. The system features built-in image storage, saving images into folders named after the camera IP, and provides a frame callback example that allows users to perform additional processing on each image.

## Experimental Video

**[Watch on YouTube](https://youtu.be/PGFpv_XXGeo)**

https://github.com/user-attachments/assets/8ebd3582-642d-42e5-9c9c-998134e5b559

## System Requirements

### Python

- cv2 (opencv-python) @ 4.11.0.86
- zeroconf @ 0.146.1

You can install these packages using the following commands:

```bash
pip install opencv-python==4.11.0.86
pip install zeroconf==0.146.1
```

### Arduino IDE

- [Download Arduino IDE](https://www.arduino.cc/en/software/)
- [Install Ameba82 plugin](https://www.amebaiot.com/zh/amebapro2-amb82-mini-arduino-getting-started/)

## Project Structure

- `RTSP.ino`: Firmware for the AMB82-MINI. This can be flashed using the Arduino IDE or the Arduino Community Edition in VSCode. Please refer to [Flashing Instructions](#flashing-instructions) for the flashing procedure.
- `python/v1/main.py`: The main server program with adjustable parameters. When the server starts, it also launches an mDNS service named `ic-ameba.local` on the local network. The AMB82-MINI boards will search for this domain to obtain the server's IP, allowing dynamic retrieval of the current server IP. Adjustable parameters include:

  - `SHOW_STREAM`: True/False, determines whether to display the RTSP stream using CV2. When enabled, each camera opens its own CV window to display the RTSP video. **Disable if CPU usage is too high.**
  - `SAVE_PICTURE`: True/False, determines whether to save images.
  - `SAVE_EVERY_N_FRAME`: Captures one image every n frames. The default is 15, meaning an image is captured every 15 frames. With the current RTSP FPS of 30, approximately two images are captured per second. Setting this value too low may cause display delays.

  To run the program, execute `conda activate base` followed by `python python/v1/main.py`. Make sure to open the folder using VSCode via File → Open Folder → `C:\develop\cam4silicon\ameba82\firmware\RTSP`, and verify the current directory by entering `pwd` in the terminal:

  ```bash
  pwd

  # It should display:
  Path
  ----
  # if you cloned to your laptop
  <Your-Path-To-This-Repo>\ameba_stream_project
  # if you're using a current development laptop, for example:
  C:\develop\cam4silicon\ameba82\firmware\RTSP
  ```

  To stop the server, press `Ctrl+C` in the terminal.

- `python-test`: Testing scripts.
- `data`: Stores data, images for documentation, and other resources.
- `img`: When `SAVE_PICTURE` is True, images are saved in folders named after the Camera IP, with the current frame ID as the file name in `.jpg` format.

## Flashing Instructions

1. Connect the A-side of a micro USB cable to your computer and the other end to the CH340 side (for flashing) of the AMB82-MINI.
2. Before flashing, since the AMB82-MINI does not have an automatic flashing mode, you must manually put it into flashing mode. The button sequence is as follows:

   - Press and hold the button on the 8735 side (BOOT button).
   - Then press and hold the button on the CH340 side (RESET button).
   - Release the button on the CH340 side.
   - Release the button on the 8735 side.

   When the blue LED on the AMB82-MINI gradually lights up, you can start the flashing process, as shown in the image below:

   <img src="data/img/AMB82-MINI-pic.png" alt="blue-led">

## Version

- **v1.2 stable**: This is the current main version, which has been experimentally validated on three AMB82-MINI boards equipped with JX-FP37(P) cameras. For experimental results, please refer to [Experimental Video](#experimental-video).
- **v2**: Planned for future release.

## Notes

1. The AMB82-MINI requires an **installed antenna** to access the Internet and can receive both 2.4G and 5G signals.
2. Updating the Wi-Fi Access Point requires re-flashing, with updated SSID and PASSWORD macros (OTA functionality is not yet implemented).
3. The current version has only been tested on 3 AMB82-MINI boards connected via AP or mobile hotspot; testing with 12 cameras is still pending.
4. Avoid using an AP that is already heavily connected by many computers as your Wi-Fi access point. Use an unused Wi-Fi network or mobile hotspot if possible.
5. When using a mobile hotspot, try to avoid data-intensive activities such as watching YouTube to prevent data congestion.
6. **The maximum number of devices for a mobile hotspot seems to be limited to 10 (depending on the phone and manufacturer). With one device serving as the server, a maximum of 9 cameras can be connected.**
7. In the future, consider using a USB hub to provide sufficient power to the group of AMB82-MINI boards, as most computers do not have enough USB ports.
8. It is recommended to move or delete stored images before each execution to avoid mixing images from different test sessions.
