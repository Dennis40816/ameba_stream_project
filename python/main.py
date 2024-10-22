# main.py

from server import Server
import cv2
import os

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
        初始化 FrameCallback 實例。

        Args:
            n (int): 每隔 n 幀處理一次。
        """
        self.n = n
        self.frame_count = {}

    def __call__(self, frame, other_info):
        """
        回調函數，每隔 n 幀進行一次操作。

        Args:
            frame (numpy.ndarray): 捕獲的幀。
            other_info (dict): 包含 'ip' 和 'seq' 鍵的字典。
        """
        ip = other_info.get('ip')
        seq = other_info.get('seq')

        if not ip or seq is None:
            print("Missing 'ip' or 'seq' information.")
            return

        # 初始化該 IP 的計數器
        if ip not in self.frame_count:
            self.frame_count[ip] = 0

        self.frame_count[ip] += 1

        # 每隔 n 幀處理一次
        if self.frame_count[ip] % self.n == 0:
            # 定義保存目錄基於 IP 地址
            save_dir = os.path.join("img", ip)
            if SAVE_PICTURE == False:
                # 此處使用 print 代替實際儲存
                print(f"Frame {self.frame_count[ip]} for IP {ip} would be saved to {save_dir}/{seq}.jpg")
            else:
                # 如果要實際保存，可以取消以下註釋
                os.makedirs(save_dir, exist_ok=True)
                filename = f"{seq}.jpg"
                filepath = os.path.join(save_dir, filename)
                try:
                    success = cv2.imwrite(filepath, frame)
                    if success:
                        print(f"Frame saved to {filepath}")
                    else:
                        print(f"Failed to save frame to {filepath}")
                except Exception as e:
                    print(f"Error saving frame to {filepath}: {e}")


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
