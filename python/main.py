# main.py

from server import Server
import cv2

# example callback
def my_frame_callback(frame, other_info):
    # print(f"write {other_info['mac']} into pic")
    pass

if __name__ == "__main__":
    server = Server(frame_callback=my_frame_callback)
    server.start()
