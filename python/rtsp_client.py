# rtsp_client.py

import cv2
import time
import threading
import numpy as np

class RTSPClientProcess:
    """RTSP client process to display the stream via OpenCV."""

    @staticmethod
    def run(cam_ip, port, mac, frame_callback=None):
        """
        Starts the RTSP client process.

        Args:
            cam_ip (str): Camera IP address.
            port (str): RTSP port.
            mac (str): MAC address of the camera.
            frame_callback (function, optional): Function to call with each new frame.
        """
        rtsp_url = f"rtsp://{cam_ip}:{port}"
        try:
            while True:
                cap = cv2.VideoCapture(rtsp_url)
                if not cap.isOpened():
                    print(f"[{mac}] Failed to open RTSP stream at {rtsp_url}. Retrying in 5 seconds...")
                    cap.release()
                    time.sleep(5)
                    continue

                print(f"[{mac}] Displaying RTSP stream from {rtsp_url}")
                window_name = f"RTSP Stream from {rtsp_url}"
                cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
                
                # Set window size to 1/4 of the screen
                screen_width = cv2.getWindowImageRect(window_name)[2]
                screen_height = cv2.getWindowImageRect(window_name)[3]
                cv2.resizeWindow(window_name, int(screen_width / 2), int(screen_height / 2))

                # Enable window resizing
                cv2.setWindowProperty(window_name, cv2.WND_PROP_ASPECT_RATIO, cv2.WINDOW_KEEPRATIO)

                while True:
                    ret, frame = cap.read()
                    if not ret:
                        print(f"[{mac}] Failed to get frame from {rtsp_url}. Reconnecting...")
                        break

                    # Resize frame to fit the window
                    frame_height, frame_width = frame.shape[:2]
                    window_size = cv2.getWindowImageRect(window_name)[2:4]
                    if window_size[0] > 0 and window_size[1] > 0:
                        frame = cv2.resize(frame, window_size, interpolation=cv2.INTER_AREA)

                    # Call the user-provided callback function
                    if frame_callback:
                        other_info = {
                          'mac': mac,
                        }
                        frame_callback(frame, other_info)

                    cv2.imshow(window_name, frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        print(f"[{mac}] Quit signal received. Terminating RTSP client.")
                        cap.release()
                        cv2.destroyAllWindows()
                        return

                cap.release()
                cv2.destroyAllWindows()
                print(f"[{mac}] RTSP stream disconnected. Reconnecting in 5 seconds...")
                time.sleep(5)
        except Exception as e:
            print(f"[{mac}] Exception in RTSP client process: {e}")
        finally:
            if 'cap' in locals():
                cap.release()
            cv2.destroyAllWindows()
            print(f"[{mac}] RTSP client process terminated.")
