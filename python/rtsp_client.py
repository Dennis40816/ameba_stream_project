# rtsp_client.py

import cv2
import time
import threading
import numpy as np
import os


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


class FreshestFrame(threading.Thread):
    """Thread that continuously captures the latest frame from a VideoCapture object."""

    def __init__(self, capture, callback=None, name='FreshestFrame'):
        """
        Initializes the FreshestFrame thread.

        Args:
            capture (cv2.VideoCapture): The VideoCapture object.
            callback (function, optional): Function to call with each new frame.
            name (str): Thread name.
        """
        super().__init__(name=name)
        self.capture = capture
        assert self.capture.isOpened(), "VideoCapture must be opened."
        self.cond = threading.Condition()
        self.running = False
        self.frame = None
        self.latestnum = 0
        self.callback = callback
        self.start()

    def start(self):
        """Starts the frame capturing thread."""
        self.running = True
        super().start()

    def release(self, timeout=None):
        """Stops the thread and releases the VideoCapture."""
        self.running = False
        self.join(timeout=timeout)
        self.capture.release()

    def run(self):
        """Continuously captures frames and updates the latest frame."""
        counter = 0
        while self.running:
            ret, img = self.capture.read()
            if not ret:
                print(
                    f"FreshestFrame: Failed to read frame. PID: {os.getpid()}")
                continue
            counter += 1

            with self.cond:
                self.frame = img
                self.latestnum = counter
                self.cond.notify_all()

            if self.callback:
                self.callback(img)

    def read(self, wait=True, seqnumber=None, timeout=None):
        """
        Retrieves the latest frame.

        Args:
            wait (bool): Whether to wait for a new frame.
            seqnumber (int, optional): Specific frame sequence number to wait for.
            timeout (float, optional): Timeout in seconds.

        Returns:
            tuple: (sequence_number, frame)
        """
        with self.cond:
            if wait:
                if seqnumber is None:
                    seqnumber = self.latestnum + 1
                if seqnumber < 1:
                    seqnumber = 1

                rv = self.cond.wait_for(
                    lambda: self.latestnum >= seqnumber, timeout=timeout)
                if not rv:
                    return (self.latestnum, self.frame)

            return (self.latestnum, self.frame)


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
        self.fps = 0.0  # Initialize FPS
        self.alpha = 0.1  # Low-pass filter coefficient

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
        freshest_frame = None

        while not self._stop_event.is_set():
            if cap is None or not cap.isOpened():
                print(f"[{self.mac}] Connecting to RTSP stream at {rtsp_url}")
                cap = cv2.VideoCapture(rtsp_url)
                if not cap.isOpened():
                    print(
                        f"[{self.mac}] Failed to open RTSP stream. Retrying in {self.options.retry_interval} seconds...")
                    if cap:
                        cap.release()
                    cap = None
                    time.sleep(self.options.retry_interval)
                    continue

                if self.options.display_window:
                    window_name = f"RTSP Stream - {rtsp_url}"
                    cv2.namedWindow(
                        window_name, cv2.WINDOW_NORMAL if self.options.resize_window else cv2.WINDOW_AUTOSIZE)
                    if self.options.resize_window:
                        cv2.resizeWindow(
                            window_name, self.options.window_width, self.options.window_height)

                # Initialize FreshestFrame
                freshest_frame = FreshestFrame(cap, callback=None)

            if freshest_frame:
                seq, frame = freshest_frame.read(wait=True, timeout=1.0)
                if frame is None:
                    print(f"[{self.mac}] No frame received. Reconnecting...")
                    freshest_frame.release()
                    cap = None
                    time.sleep(self.options.retry_interval)
                    continue

                # Process FPS with low-pass filter
                current_time = time.time()
                if not hasattr(self, '_last_time'):
                    self._last_time = current_time

                elapsed = current_time - self._last_time
                if elapsed > 0:
                    current_fps = 1.0 / elapsed
                    self.fps = self.alpha * current_fps + \
                        (1 - self.alpha) * self.fps
                self._last_time = current_time

                if self.options.show_fps:
                    frame = self._add_fps(frame)

                if self.frame_callback:
                    other_info = {'mac': self.mac,
                                  'rtsp': rtsp_url, 'seq': seq, 'ip': self.cam_ip}
                    self.frame_callback(frame, other_info)

                if self.options.display_window and freshest_frame:
                    cv2.imshow(window_name, frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        print(
                            f"[{self.mac}] Quit signal received. Terminating RTSP client.")
                        self.stop()
                        break

        # Cleanup
        if freshest_frame:
            freshest_frame.release()
        if cap and cap.isOpened():
            cap.release()
        if self.options.display_window:
            cv2.destroyAllWindows()
        print(f"[{self.mac}] RTSP client process terminated.")

    def _add_fps(self, frame):
        """Adds FPS information to the frame using low-pass filter."""
        fps_text = f"FPS: {self.fps:.2f}"
        cv2.putText(frame, fps_text, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        return frame
