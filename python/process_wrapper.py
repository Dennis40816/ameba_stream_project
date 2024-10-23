# process_wrapper.py

from rtsp_client import RTSPClient, RTSPClientOptions
import time


def run_rtsp_client(cam_ip, port, mac, frame_callback=None, show_stream=True, show_fps=True):
    """
    包裝函數，用於在獨立進程中啟動 RTSPClient。

    Args:
        cam_ip (str): Camera IP address.
        port (str): RTSP port.
        mac (str): MAC address of the camera.
        frame_callback: User's callback
        show_fps (bool): Whether to display FPS on the video frames.
    """

    options = RTSPClientOptions(
        display_window=show_stream,      # 是否顯示視窗
        resize_window=True,       # 是否調整視窗大小
        window_width=800,         # 視窗寬度
        window_height=600,        # 視窗高度
        retry_interval=5,         # 連線失敗後重試間隔（秒）
        show_fps=show_fps         # 是否顯示 FPS
    )

    client = RTSPClient(
        cam_ip=cam_ip,
        port=port,
        mac=mac,
        options=options,
        frame_callback=frame_callback
    )

    client.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('Close owing to KeyboardInterrupt from run_rtsp_client')
        client.stop()
