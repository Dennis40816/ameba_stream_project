# rtsp_client.py

import cv2
import time
import threading
import numpy as np


class RTSPClientOptions:
    """Configuration options for RTSPClient."""

    def __init__(self,
                 display_window=True,
                 resize_window=True,
                 window_width=640,
                 window_height=480,
                 retry_interval=5,
                 show_fps=False):
        """
        Initializes the RTSPClientOptions.

        Args:
            display_window (bool): Whether to display the video stream in a window.
            resize_window (bool): Whether to resize the window to specified dimensions.
            window_width (int): Width of the display window.
            window_height (int): Height of the display window.
            retry_interval (int): Seconds to wait before retrying connection after failure.
            show_fps (bool): Whether to display FPS on the video frames.
        """
        self.display_window = display_window
        self.resize_window = resize_window
        self.window_width = window_width
        self.window_height = window_height
        self.retry_interval = retry_interval
        self.show_fps = show_fps


class RTSPClient:
    """RTSP client to handle streaming and display."""

    def __init__(self, cam_ip, port, mac, options=None, frame_callback=None):
        """
        Initializes the RTSPClient.

        Args:
            cam_ip (str): Camera IP address.
            port (str): RTSP port.
            mac (str): MAC address of the camera.
            options (RTSPClientOptions, optional): Configuration options.
            frame_callback (function, optional): Function to call with each new frame.
        """
        self.cam_ip = cam_ip
        self.port = port
        self.mac = mac
        self.options = options if options else RTSPClientOptions()
        self.frame_callback = frame_callback
        self._stop_event = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        """Starts the RTSP client in a separate thread."""
        print(f"[{self.mac}] Starting RTSP client.")
        self.thread.start()

    def stop(self):
        """Stops the RTSP client."""
        print(f"[{self.mac}] Stopping RTSP client.")
        self._stop_event.set()
        self.thread.join()
        print(f"[{self.mac}] RTSP client stopped.")

    def _run(self):
        """Internal method to handle the RTSP stream."""
        rtsp_url = f"rtsp://{self.cam_ip}:{self.port}"
        cap = None

        while not self._stop_event.is_set():
            if cap is None or not cap.isOpened():
                print(f"[{self.mac}] Connecting to RTSP stream at {rtsp_url}")
                cap = cv2.VideoCapture(rtsp_url)
                if not cap.isOpened():
                    print(f"[{self.mac}] Failed to open RTSP stream. Retrying in {self.options.retry_interval} seconds...")
                    if cap:
                        cap.release()
                    cap = None
                    time.sleep(self.options.retry_interval)
                    continue

                if self.options.display_window:
                    window_name = f"RTSP Stream - {rtsp_url}"
                    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL if self.options.resize_window else cv2.WINDOW_AUTOSIZE)
                    if self.options.resize_window:
                        cv2.resizeWindow(window_name, self.options.window_width, self.options.window_height)

            ret, frame = cap.read()
            if not ret:
                print(f"[{self.mac}] Failed to retrieve frame. Reconnecting...")
                cap.release()
                cap = None
                time.sleep(self.options.retry_interval)
                continue

            if self.options.show_fps:
                frame = self._add_fps(frame)

            if self.frame_callback:
                other_info = {'mac': self.mac}
                self.frame_callback(frame, other_info)

            if self.options.display_window:
                cv2.imshow(window_name, frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print(f"[{self.mac}] Quit signal received. Terminating RTSP client.")
                    self.stop()
                    break

        if cap and cap.isOpened():
            cap.release()
        if self.options.display_window:
            cv2.destroyAllWindows()
        print(f"[{self.mac}] RTSP client process terminated.")

    def _add_fps(self, frame):
        """Adds FPS information to the frame."""
        if not hasattr(self, '_last_time'):
            self._last_time = time.time()
            self._fps = 0.0
        current_time = time.time()
        elapsed = current_time - self._last_time
        if elapsed > 0:
            self._fps = 1.0 / elapsed
        self._last_time = current_time
        cv2.putText(frame, f"FPS: {self._fps:.2f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        return frame
