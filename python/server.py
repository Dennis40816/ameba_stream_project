# server.py

import socket
import threading
from utils import get_local_ip, MAX_CAMERA_NUM, SOCKET_TIMEOUT
from camera_manager import CameraManager
from camera_client_handler import CameraClientHandler


class Server:
    """Main server class to listen for camera client connections."""

    def __init__(self, host='0.0.0.0', port=12345, frame_callback=None):
        self.host = host
        self.port = port
        self.server_socket = None
        self.camera_manager = CameraManager()
        self.client_threads = []
        self.heartbeat_thread = None
        self.camera_table_thread = None
        self.frame_callback = frame_callback

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(MAX_CAMERA_NUM)
        self.server_socket.settimeout(SOCKET_TIMEOUT)

        if self.host == '0.0.0.0':
            print(
                f"Server started, waiting for connections on {get_local_ip()}:{self.port}")
        else:
            print(
                f"Server started, waiting for connections on {self.host}:{self.port}")

        # Start heartbeat checking thread
        self.heartbeat_thread = threading.Thread(
            target=self.camera_manager.check_heartbeats)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()

        # Start camera table update thread
        self.camera_table_thread = threading.Thread(
            target=self.camera_manager.update_camera_table)
        self.camera_table_thread.daemon = True
        self.camera_table_thread.start()

        try:
            while not self.camera_manager.stop_event.is_set():
                try:
                    client_socket, addr = self.server_socket.accept()
                    client_handler = CameraClientHandler(
                        client_socket, addr, self.camera_manager, self.frame_callback)
                    client_handler.daemon = True
                    client_handler.start()
                    self.client_threads.append(client_handler)
                except socket.timeout:
                    pass  # Do not continue
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt received. Shutting down server...")
            self.camera_manager.stop_event.set()
        finally:
            self.shutdown()

    def shutdown(self):
        # Close the server socket to stop accepting new connections
        self.server_socket.close()
        print("Server socket closed.")

        # Signal all client handlers to stop
        for handler in self.client_threads:
            handler.stop()
        # Wait for all client threads to finish
        for handler in self.client_threads:
            handler.join()
        print("All client threads have been terminated.")

        # Terminate all RTSP client processes
        with self.camera_manager.camera_lock:
            for ip_address, info in self.camera_manager.connected_cameras.items():
                process = info['process']
                mac = info['mac']
                if process and process.is_alive():
                    print(
                        f"Terminating RTSP client for {mac} at {info['ip']}:{info['port']}")
                    process.terminate()
                    process.join()
            self.camera_manager.connected_cameras.clear()
        print("All RTSP client processes have been terminated.")

        # Ensure the heartbeat and camera table threads are also terminated
        self.camera_manager.stop()
        self.heartbeat_thread.join()
        self.camera_table_thread.join()
        print("Heartbeat checking and camera table update threads have been terminated.")

        print("Server shutdown complete.")
