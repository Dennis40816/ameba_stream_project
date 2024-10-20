import socket
import threading
import multiprocessing
import cv2
import time

# Dictionary to maintain connected cameras
connected_cameras = {}

# Lock for thread safety
camera_lock = threading.Lock()


def get_local_ip():
    """返回局域網中的本地 IP 地址"""
    try:
        # 創建一個 UDP 套接字（這裡我們不會真的發送任何數據）
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 嘗試連接到一個不會真的發送任何數據的外部地址
        s.connect(('8.8.8.8', 80))  # 使用 Google 的公共 DNS 服務器作為目標
        local_ip = s.getsockname()[0]  # 獲取本地的 IP 地址
    except Exception as e:
        print(f"Error obtaining local IP: {e}")
        local_ip = '127.0.0.1'  # 如果無法獲取本地 IP，則默認為 localhost
    finally:
        s.close()

    return local_ip

# Handle the client connection


def handle_client(stop_event, client_socket, addr, check_interval=10):

    print(f"New connection from {addr}")
    mac = None  # Initialize mac variable
    ip_address = addr[0]  # Client's IP address

    try:
        while not stop_event.wait(check_interval):
            # Receive data from the client
            data = client_socket.recv(1024).decode().strip()
            if not data:
                continue

            # Example data: "AA:BB:CC:DD:EE:FF,192.168.1.10,554"
            if data == "AliveHeartBeat":
                with camera_lock:
                    if ip_address in connected_cameras:
                        mac = connected_cameras[ip_address]['mac']
                        connected_cameras[ip_address]['last_heartbeat'] = time.time(
                        )
                        print(f"Heartbeat received from {mac} at {ip_address}")
                    else:
                        print(f"Unknown heartbeat from {ip_address}")
            else:
                print(f"Received from {addr}: {data}")
                parts = data.split(',')
                if len(parts) == 3:
                    mac, cam_ip, port = parts

                    # Store the camera information
                    with camera_lock:
                        connected_cameras[ip_address] = {
                            'mac': mac,
                            'ip': cam_ip,
                            'port': port,
                            'last_heartbeat': time.time(),
                            'process': None  # To store RTSP process handle
                        }

                    # Start RTSP client in a new process
                    p = multiprocessing.Process(
                        target=rtsp_client_process, args=(cam_ip, port, mac))
                    p.start()
                    with camera_lock:
                        connected_cameras[ip_address]['process'] = p
                    print(f"RTSP client started for {mac} ({cam_ip}:{port})")
                else:
                    print(f"Invalid data format from {addr}: {data}")

    except Exception as e:
        print(f"Error with client {addr}: {e}")
    finally:
        # Remove client on disconnection
        with camera_lock:
            if ip_address in connected_cameras:
                mac = connected_cameras[ip_address]['mac']
                connected_cameras[ip_address]['process'].terminate()
                connected_cameras[ip_address]['process'].join()
                del connected_cameras[ip_address]
                print(f"Disconnected from {addr}, cam {mac} removed")
        client_socket.close()

# RTSP client to display the stream via OpenCV


def rtsp_client_process(cam_ip, port, mac):
    rtsp_url = f"rtsp://{cam_ip}:{port}"
    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        print(f"Failed to open RTSP stream from {mac} at {rtsp_url}")
        return

    print(f"Displaying RTSP stream for {mac} at {rtsp_url}")
    while True:
        ret, frame = cap.read()
        if not ret:
            print(f"Failed to get frame from {mac} at {rtsp_url}")
            break
        cv2.imshow(f"RTSP Stream from {mac}", frame)
        if cv2.waitKey(1) == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"RTSP client for {mac} at {rtsp_url} terminated")

# Function to check heartbeats and remove inactive cameras


def check_heartbeats(stop_event, timeout=30, check_interval=10):
    """
    定期檢查攝像頭心跳，若心跳超過 timeout 時間，則終止對應的攝像頭。
    stop_event: 用於停止這個心跳檢查的事件
    timeout: 超過該時間未收到心跳則認為攝像頭失效
    check_interval: 每次檢查心跳的間隔
    """
    while not stop_event.wait(check_interval):  # 每次等待 check_interval 秒，並檢查事件是否已觸發
        current_time = time.time()
        with camera_lock:
            for mac in list(connected_cameras.keys()):
                if current_time - connected_cameras[mac]['last_heartbeat'] > timeout:
                    # 没有收到心跳，移除攝像頭
                    print(f"Camera {mac} timed out, terminating process")
                    connected_cameras[mac]['process'].terminate()
                    connected_cameras[mac]['process'].join()
                    del connected_cameras[mac]
    print('Thread check hearbeats terminated!')

# Main server to listen for cam clients


def main_server(host='0.0.0.0', port=12345):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    server_socket.settimeout(1.0)  # 设置超时时间

    if host == '0.0.0.0':
        print(
            f"Server started, waiting for connections on {get_local_ip()}:{port}")
        get_local_ip
    else:
        print(f"Server started, waiting for connections on {host}:{port}")

    # 创建用于停止线程的事件对象
    stop_event = threading.Event()

    # 启动心跳检查线程
    heartbeat_thread = threading.Thread(
        target=check_heartbeats, args=(stop_event,))
    heartbeat_thread.daemon = True
    heartbeat_thread.start()

    client_threads = []

    try:
        while True:
            try:
                client_socket, addr = server_socket.accept()
                client_thread = threading.Thread(
                    target=handle_client, args=(stop_event, client_socket, addr, ))
                client_thread.start()
                client_threads.append(client_thread)
            except socket.timeout:
                # 超时，继续检查是否有 KeyboardInterrupt
                pass
    except KeyboardInterrupt:
        print("Shutting down server...")
        stop_event.set()  # info thread to stop
    finally:
        # 清理工作
        server_socket.close()
        with camera_lock:
            for mac, info in connected_cameras.items():
                if info['process']:
                    info['process'].terminate()
                    info['process'].join()
        for t in client_threads:
            t.join()
        heartbeat_thread.join()  # 等待心跳线程结束
        print("Server and all processes terminated")


if __name__ == "__main__":
    main_server()
