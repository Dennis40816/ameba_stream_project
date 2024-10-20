import socket
import threading
import multiprocessing
import cv2
import time

# Dictionary to maintain connected cameras
connected_cameras = {}

# Lock for thread safety
camera_lock = threading.Lock()

# Global Constants
DEBUG = False
SOCKET_TIMEOUT = 1.0
MAX_CAMERA_NUM = 12

def get_local_ip():
    """Returns the local IP address within the LAN."""
    try:
        # Create a UDP socket (no actual data is sent)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Attempt to connect to an external address (does not send data)
        s.connect(('8.8.8.8', 80))  # Using Google's public DNS server
        local_ip = s.getsockname()[0]  # Get the local IP address
    except Exception as e:
        print(f"Error obtaining local IP: {e}")
        local_ip = '127.0.0.1'  # Default to localhost if unable to get local IP
    finally:
        s.close()

    return local_ip

def handle_client(client_socket, addr, stop_event):
    """
    Handles communication with a connected camera client.

    Args:
        client_socket (socket.socket): The client's socket.
        addr (tuple): The client's address.
        stop_event (threading.Event): Event to signal thread termination.
    """
    print(f"New connection from {addr}")
    mac = None  # Initialize mac variable
    ip_address = addr[0]  # Client's IP address

    # Set a timeout for the client socket to periodically check the stop_event
    client_socket.settimeout(SOCKET_TIMEOUT)

    buffer = ''  # Initialize buffer for storing partial data

    try:
        while not stop_event.is_set():
            try:
                # Receive data from the client
                data = client_socket.recv(1024).decode()
                if not data:
                    continue

                buffer += data  # Append received data to buffer

                while '\r\n' in buffer:
                    # Split buffer into line and the rest
                    line, buffer = buffer.split('\r\n', 1)
                    line = line.strip()  # Remove any leading/trailing whitespace

                    if not line:
                        continue  # Skip empty lines

                    # Process the line
                    if line == "AliveHeartBeat":
                        with camera_lock:
                            if ip_address in connected_cameras:
                                mac = connected_cameras[ip_address]['mac']
                                connected_cameras[ip_address]['last_heartbeat'] = time.time()
                                if (DEBUG):
                                  print(f"Heartbeat received from {mac} at {ip_address}")
                            else:
                                print(f"Unknown heartbeat from {ip_address}")
                    else:
                        print(f"Received from {addr}: {line}")
                        parts = line.split(',')
                        if len(parts) == 3:
                            mac, cam_ip, port = parts

                            with camera_lock:
                                if ip_address in connected_cameras:
                                    # If camera is already connected, terminate the existing process
                                    existing_process = connected_cameras[ip_address]['process']
                                    if existing_process and existing_process.is_alive():
                                        existing_process.terminate()
                                        existing_process.join()

                                # Store the camera information
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
                            print(f"Invalid data format from {addr}: {line}")

            except socket.timeout:
                continue  # Timeout occurred, loop back to check stop_event
            except Exception as e:
                print(f"Receive error from {addr}: {e}")
                break  # Exit the loop on other exceptions

    except Exception as e:
        print(f"Error with client {addr}: {e}")
    finally:
        # Remove client on disconnection
        with camera_lock:
            if ip_address in connected_cameras:
                mac = connected_cameras[ip_address]['mac']
                process = connected_cameras[ip_address]['process']
                if process and process.is_alive():
                    process.terminate()
                    process.join()
                del connected_cameras[ip_address]
                print(f"Disconnected from {addr}, cam {mac} removed")
        client_socket.close()

def rtsp_client_process(cam_ip, port, mac):
    """
    RTSP client process to display the stream via OpenCV with reconnection and cache settings.

    Args:
        cam_ip (str): Camera IP address.
        port (str): RTSP port.
        mac (str): MAC address of the camera.
    """
    
    # workaround: use cv2 default rtsp 
    rtsp_url = f"rtsp://{cam_ip}:{port}"
    # GStreamer pipeline for H.264 with caps
    gst_pipeline = (
        f"rtspsrc location={rtsp_url} latency=300 ! "
        "rtph264depay ! h264parse ! avdec_h264 ! "
        "videoconvert ! appsink caps=\"video/x-raw, format=BGR\""
    )

    try:
        while True:
            # cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
            cap = cv2.VideoCapture(rtsp_url)
            if not cap.isOpened():
                print(f"[{mac}] Failed to open RTSP stream at {rtsp_url}. Retrying in 5 seconds...")
                cap.release()
                time.sleep(5)  # Cannot replace with stop_event.wait here as it's a separate process
                continue

            print(f"[{mac}] Displaying RTSP stream from {rtsp_url}")
            window_name = f"RTSP Stream from {mac}"

            while True:
                ret, frame = cap.read()
                if not ret:
                    print(f"[{mac}] Failed to get frame from {rtsp_url}. Reconnecting...")
                    break  # Exit the inner loop to attempt reconnection

                cv2.imshow(window_name, frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print(f"[{mac}] Quit signal received. Terminating RTSP client.")
                    cap.release()
                    cv2.destroyAllWindows()
                    return  # Exit the process

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

def check_heartbeats(stop_event, timeout=30):
    """
    Checks the heartbeats of connected cameras and removes inactive ones.

    Args:
        stop_event (threading.Event): Event to signal thread termination.
        timeout (int, optional): Heartbeat timeout in seconds. Defaults to 30.
    """
    while not stop_event.is_set():
        current_time = time.time()
        with camera_lock:
            for ip_address in list(connected_cameras.keys()):
                last_heartbeat = connected_cameras[ip_address]['last_heartbeat']
                if current_time - last_heartbeat > timeout:
                    # No heartbeat received within the timeout period
                    mac = connected_cameras[ip_address]['mac']
                    print(f"[{mac}] at {ip_address} timed out. Terminating RTSP process.")
                    process = connected_cameras[ip_address]['process']
                    if process and process.is_alive():
                        process.terminate()
                        process.join()
                    del connected_cameras[ip_address]
        # Replace time.sleep(10) with stop_event.wait(10) to allow early termination
        if stop_event.wait(10):
            break  # stop_event is set, exit the loop
    print('Heartbeat checking thread terminated!')

def main_server(host='0.0.0.0', port=12345):
    """
    Main server function to listen for camera client connections.

    Args:
        host (str, optional): Host IP address. Defaults to '0.0.0.0'.
        port (int, optional): Port number. Defaults to 12345.
    """
    stop_event = threading.Event()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(MAX_CAMERA_NUM)
    server_socket.settimeout(SOCKET_TIMEOUT)

    if host == '0.0.0.0':
        print(f"Server started, waiting for connections on {get_local_ip()}:{port}")
    else:
        print(f"Server started, waiting for connections on {host}:{port}")

    # Start heartbeat checking thread
    heartbeat_thread = threading.Thread(target=check_heartbeats, args=(stop_event,))
    heartbeat_thread.daemon = True
    heartbeat_thread.start()
    
    client_threads = []

    try:
        while not stop_event.is_set():
            try:
                client_socket, addr = server_socket.accept()
                client_thread = threading.Thread(
                    target=handle_client, args=(client_socket, addr, stop_event))
                client_thread.daemon = True
                client_thread.start()
                client_threads.append(client_thread)
            except socket.timeout:
                pass  # DO NOT USE continue!!!!
            
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt received. Shutting down server...")
        stop_event.set()
    finally:
        # Close the server socket to stop accepting new connections
        server_socket.close()
        print("Server socket closed.")

        # Wait for all client threads to finish
        for t in client_threads:
            t.join()
        print("All client threads have been terminated.")

        # Terminate all RTSP client processes
        with camera_lock:
            for ip_address, info in connected_cameras.items():
                process = info['process']
                mac = info['mac']
                if process and process.is_alive():
                    print(f"Terminating RTSP client for {mac} at {info['ip']}:{info['port']}")
                    process.terminate()
                    process.join()
            connected_cameras.clear()
        print("All RTSP client processes have been terminated.")

        # Ensure the heartbeat thread is also terminated
        heartbeat_thread.join()
        print("Heartbeat checking thread has been terminated.")

        print("Server shutdown complete.")

if __name__ == "__main__":
    main_server()
