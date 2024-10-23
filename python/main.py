# main.py

from server import Server
import cv2
import os
import queue
import threading

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
        self.condition = None  # Condition variable for event-driven logic
        self.initialized = False
    
    def initialize_worker(self):
        """
        Initialize the worker thread and queue only once using lru_cache to ensure single execution.
        """
        # variable init
        self.initialized = True
        self.queue = queue.Queue()  # Initialize the queue
        self.worker_thread = threading.Thread(target=self.save_frame_worker)
        self.condition = threading.Condition()
        
        # thread starts
        self.worker_thread.start()


    def __call__(self, frame, other_info):
        """
        Callback function to process every n frames.

        Args:
            frame (numpy.ndarray): The captured frame.
            other_info (dict): Dictionary containing 'ip' and 'seq' keys.
        """
        # Ensure worker thread is initialized only once
        if self.initialized == False:
            self.initialize_worker()
        
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

            # Use the condition to notify the worker thread when a new frame is ready
            if SAVE_PICTURE:
                with self.condition:
                    self.queue.put((frame, filepath))
                    self.condition.notify()  # Notify worker thread

    def save_frame_worker(self):
        """
        Worker thread to save frames from the queue.
        """
        while True:
            with self.condition:
                while self.queue.empty() and not self.stop_thread:
                    self.condition.wait()  # Wait until notified or stop_thread is set

                # If stop_thread is set and queue is empty, exit the loop
                if self.stop_thread and self.queue.empty():
                    break

                # Get the frame and filepath from the queue
                frame, filepath = self.queue.get()

            # Process the frame outside of the lock
            save_dir = os.path.dirname(filepath)

            # Ensure the save directory exists
            os.makedirs(save_dir, exist_ok=True)

            # Save the frame to the file
            success = cv2.imwrite(filepath, frame)
            if success:
                pass
            else:
                print(f"Failed to save frame to {filepath}")

            # Mark the task as done
            self.queue.task_done()

    def stop(self):
        """
        Stop the worker thread and ensure all frames in the queue are saved before stopping.
        """
        with self.condition:
            self.stop_thread = True
            self.condition.notify_all()  # Wake up the worker thread if it's waiting
            
        print(f'frame count: {self.frame_count}')

        if self.worker_thread is not None:
            # Wait until the queue is empty before stopping
            print("Waiting for the queue to be empty...")
            self.queue.join()  # Block until all tasks are done

            # Signal the thread to stop
            self.worker_thread.join()
            print("Worker thread stopped after processing all frames.")


if __name__ == "__main__":
    # 2 pic per sec
    frame_callback = FrameCallback(n=15) 
    server = Server(frame_callback=frame_callback)
    server.start()