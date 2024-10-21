# main.py

from server import Server
import cv2

## TODO: 可以開關 opencv 

## async io for save jpg

## 降低 fps? to 5?

## https://medium.com/@JayantSBhati/crafting-advanced-video-processing-pipelines-setting-up-opencv-with-gstreamer-backend-using-mingw-4065839e200c

## 熱點問題 (要使用獨立分享器?) bit rate 4, 20 的差別?

## https://stackoverflow.com/questions/60816436/open-cv-rtsp-camera-buffer-lag
## https://blog.csdn.net/a545454669/article/details/129469324

# example callback
def my_frame_callback(frame, other_info):
    # print(f"write {other_info['mac']} into pic")
    pass

if __name__ == "__main__":
    server = Server(frame_callback=my_frame_callback)
    server.start()
