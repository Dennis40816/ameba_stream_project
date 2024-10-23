# main.py

from server import Server
import cv2
import os
import queue
import threading
from functools import lru_cache

## TODO: 可以開關 opencv 

# 2.4 G Wi-Fi 可能比較穩定?

## async io for save jpg

## 降低 fps? to 5?

## https://medium.com/@JayantSBhati/crafting-advanced-video-processing-pipelines-setting-up-opencv-with-gstreamer-backend-using-mingw-4065839e200c

## 熱點問題 (要使用獨立分享器?) bit rate 4, 20 的差別?

## https://stackoverflow.com/questions/60816436/open-cv-rtsp-camera-buffer-lag
## https://blog.csdn.net/a545454669/article/details/129469324

# example callback class

SAVE_PICTURE = True

import os
import cv2
import threading
import queue

class FrameCallback:
    def __init__(self, n=5):
        """
        Initialize the FrameCallback instance.

        Args:
            n (int): Process every n frames.
        """
        self.n = n
        self.frame_count = {}
        self.queue = None  # Queue to store frames for saving
        self.stop_thread = False
        self.worker_thread = None  # Initialize the worker thread as None (lazy initialization)
        self.condition = None
    
    @lru_cache(maxsize=1)
    def initialize_worker(self):
        self.queue = queue.Queue()  # Initialize the queue
        self.worker_thread = threading.Thread(target=self.save_frame_worker)
        self.worker_thread.start()


    def __call__(self, frame, other_info):
        """
        Callback function to process every n frames.

        Args:
            frame (numpy.ndarray): The captured frame.
            other_info (dict): Dictionary containing 'ip' and 'seq' keys.
        """
        # run only once
        self.initialize_worker()
        
        # Initialize the worker thread when the first frame is processed
        if self.worker_thread is None:
            print("Starting worker thread...")
            self.worker_thread = threading.Thread(target=self.save_frame_worker)
            self.worker_thread.start()

        ip = other_info.get('ip')
        seq = other_info.get('seq')

        if not ip or seq is None:
            print("Missing 'ip' or 'seq' information.")
            return

        # Initialize frame counter for the IP if not already done
        if ip not in self.frame_count:
            self.frame_count[ip] = 0

        self.frame_count[ip] += 1

        # Process every n frames
        if self.frame_count[ip] % self.n == 0:
            # Define the save directory based on IP address
            save_dir = os.path.join("img", ip)
            filename = f"{seq}.jpg"
            filepath = os.path.join(save_dir, filename)

            # Put frame and related information into the queue
            if SAVE_PICTURE:
                self.queue.put((frame, filepath))

            # For debugging, print the frame information
            # print(f"Frame {self.frame_count[ip]} for IP {ip} added to queue for saving at {filepath}")

    def save_frame_worker(self):
        """
        Worker thread to save frames from the queue.
        """
        while not self.stop_thread or not self.queue.empty():
            try:
                # Get the frame and filepath from the queue
                frame, filepath = self.queue.get(timeout=1)  # Use timeout to prevent blocking
                save_dir = os.path.dirname(filepath)

                # Ensure the save directory exists
                os.makedirs(save_dir, exist_ok=True)

                # Save the frame to the file
                success = cv2.imwrite(filepath, frame)
                if success:
                    pass
                    # print(f"Frame saved to {filepath}")
                else:
                    print(f"Failed to save frame to {filepath}")

                # Mark the task as done
                self.queue.task_done()

            except queue.Empty:
                continue  # If the queue is empty, continue to wait for new frames

    def stop(self):
        """
        Stop the worker thread and ensure all frames in the queue are saved before stopping.
        """
        if self.worker_thread is not None:
            # Wait until the queue is empty before stopping
            print("Waiting for the queue to be empty...")
            self.queue.join()  # Block until all tasks are done

            # Signal the thread to stop
            self.stop_thread = True
            self.worker_thread.join()
            print("Worker thread stopped after processing all frames.")



# def my_frame_callback(frame, other_info):
#     """
#     Callback function to save the frame as a JPEG file in img/{ip}/{seq}.jpg

#     Args:
#         frame (numpy.ndarray): The captured frame.
#         other_info (dict): Dictionary containing 'mac' and 'seq' keys.
#     """
#     ip = other_info.get('ip')
#     seq = other_info.get('seq')

#     if not ip or seq is None:
#         print("Missing 'mac' or 'seq' information.")
#         return

#     # Define the save directory based on MAC address
#     save_dir = os.path.join("img", ip)
#     os.makedirs(save_dir, exist_ok=True)

#     # Define the filename using the sequence number
#     filename = f"{seq}.jpg"
#     filepath = os.path.join(save_dir, filename)

#     # Save the frame as a JPEG file
#     try:
#         success = cv2.imwrite(filepath, frame)
#         if success:
#             print(f"Frame saved to {filepath}")
#         else:
#             print(f"Failed to save frame to {filepath}")
#     except Exception as e:
#         print(f"Error saving frame to {filepath}: {e}")

if __name__ == "__main__":
    # 2 pic per sec
    frame_callback = FrameCallback(n=15) 
    server = Server(frame_callback=frame_callback)
    server.start()
