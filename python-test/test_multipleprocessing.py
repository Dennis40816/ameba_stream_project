import os
import cv2
import multiprocessing
import numpy as np
import time

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
            # 此處使用 print 代替實際儲存
            print(f"Frame {self.frame_count[ip]} for IP {ip} would be saved to {save_dir}/{seq}.jpg")
            # 如果要實際保存，可以取消以下註釋
            """
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
            """
def run_rtsp_client(cam_ip, port, mac, frame_callback, total_frames=20, delay=0.1):
    """
    模擬 RTSP 客戶端，生成假幀並調用回調函數。

    Args:
        cam_ip (str): 攝像頭 IP 地址。
        port (int): 端口號。
        mac (str): MAC 地址。
        frame_callback (callable): 幀回調函數。
        total_frames (int): 要生成的總幀數。
        delay (float): 生成幀之間的延遲（秒）。
    """
    for seq in range(1, total_frames + 1):
        # 生成假幀（例如，一個 640x480 的黑色圖片）
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        other_info = {
            'ip': cam_ip,
            'seq': seq,
            'mac': mac
        }

        # 調用回調函數
        frame_callback(frame, other_info)

        # 模擬幀捕獲的延遲
        time.sleep(delay)

def main():
    # 定義要啟動的攝像頭資訊
    cameras = [
        {'cam_ip': '192.168.1.10', 'port': 554, 'mac': 'AA:BB:CC:DD:EE:01'},
        {'cam_ip': '192.168.1.11', 'port': 554, 'mac': 'AA:BB:CC:DD:EE:02'},
        {'cam_ip': '192.168.1.12', 'port': 554, 'mac': 'AA:BB:CC:DD:EE:03'},
    ]

    # 定義每隔 n 幀處理一次
    n = 5

    processes = []

    for cam in cameras:
        # 為每個攝像頭創建一個 FrameCallback 實例
        frame_callback = FrameCallback(n=n)

        # 創建並啟動一個進程
        p = multiprocessing.Process(
            target=run_rtsp_client,
            args=(cam['cam_ip'], cam['port'], cam['mac'], frame_callback)
        )
        p.start()
        processes.append(p)

    # 等待所有進程完成
    for p in processes:
        p.join()

if __name__ == "__main__":
    main()