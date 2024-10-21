# main.py

from server import Server
import cv2
import os

## TODO: 可以開關 opencv 

## async io for save jpg

## 降低 fps? to 5?

## https://medium.com/@JayantSBhati/crafting-advanced-video-processing-pipelines-setting-up-opencv-with-gstreamer-backend-using-mingw-4065839e200c

## 熱點問題 (要使用獨立分享器?) bit rate 4, 20 的差別?

## https://stackoverflow.com/questions/60816436/open-cv-rtsp-camera-buffer-lag
## https://blog.csdn.net/a545454669/article/details/129469324

# example callback
def my_frame_callback(frame, other_info):
    """
    Callback function to save the frame as a JPEG file in img/{ip}/{seq}.jpg

    Args:
        frame (numpy.ndarray): The captured frame.
        other_info (dict): Dictionary containing 'mac' and 'seq' keys.
    """
    ip = other_info.get('ip')
    seq = other_info.get('seq')

    if not ip or seq is None:
        print("Missing 'mac' or 'seq' information.")
        return

    # Define the save directory based on MAC address
    save_dir = os.path.join("img", ip)
    os.makedirs(save_dir, exist_ok=True)

    # Define the filename using the sequence number
    filename = f"{seq}.jpg"
    filepath = os.path.join(save_dir, filename)

    # Save the frame as a JPEG file
    try:
        success = cv2.imwrite(filepath, frame)
        if success:
            print(f"Frame saved to {filepath}")
        else:
            print(f"Failed to save frame to {filepath}")
    except Exception as e:
        print(f"Error saving frame to {filepath}: {e}")

if __name__ == "__main__":
    server = Server(frame_callback=my_frame_callback)
    server.start()
