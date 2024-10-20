# camera_manager.py

import threading
import time
from datetime import datetime

class CameraManager:
    """Manages connected cameras and their heartbeats."""

    def __init__(self, timeout=30):
        self.connected_cameras = {}
        self.camera_lock = threading.Lock()
        self.timeout = timeout  # Heartbeat timeout
        self.stop_event = threading.Event()

    def add_camera(self, ip_address, mac, cam_ip, port, process):
        """Adds or updates a camera in the connected_cameras dictionary."""
        with self.camera_lock:
            self.connected_cameras[ip_address] = {
                'mac': mac,
                'ip': cam_ip,
                'port': port,
                'last_heartbeat': time.time(),
                'process': process  # RTSP process handle
            }

    def remove_camera(self, ip_address):
        """Removes a camera from the connected_cameras dictionary."""
        with self.camera_lock:
            if ip_address in self.connected_cameras:
                mac = self.connected_cameras[ip_address]['mac']
                process = self.connected_cameras[ip_address]['process']
                if process and process.is_alive():
                    process.terminate()
                    process.join()
                del self.connected_cameras[ip_address]
                print(f"Camera {mac} at {ip_address} removed.")

    def update_heartbeat(self, ip_address):
        """Updates the last heartbeat time of a camera."""
        with self.camera_lock:
            if ip_address in self.connected_cameras:
                self.connected_cameras[ip_address]['last_heartbeat'] = time.time()

    def get_camera(self, ip_address):
        """Retrieves camera information."""
        with self.camera_lock:
            return self.connected_cameras.get(ip_address)

    def check_heartbeats(self):
        """Checks the heartbeats of connected cameras and removes inactive ones."""
        while not self.stop_event.is_set():
            current_time = time.time()
            with self.camera_lock:
                for ip_address in list(self.connected_cameras.keys()):
                    last_heartbeat = self.connected_cameras[ip_address]['last_heartbeat']
                    if current_time - last_heartbeat > self.timeout:
                        # No heartbeat received within the timeout period
                        mac = self.connected_cameras[ip_address]['mac']
                        print(f"[{mac}] at {ip_address} timed out. Terminating RTSP process.")
                        process = self.connected_cameras[ip_address]['process']
                        if process and process.is_alive():
                            process.terminate()
                            process.join()
                        del self.connected_cameras[ip_address]
            if self.stop_event.wait(10):
                break  # stop_event is set, exit the loop
        print('Heartbeat checking thread terminated!')

    def update_camera_table(self, update_interval=5):
        """Periodically updates and prints the camera table."""
        while not self.stop_event.is_set():
            with self.camera_lock:
                if self.connected_cameras:
                    print("\n=== Connected Cameras ===")
                    print(f"{'Process ID':<12} {'IP':<15} {'RTSP URL':<30} {'Heartbeat':<20} {'MAC':<20}")
                    print("-" * 100)
                    for ip, info in self.connected_cameras.items():
                        process_id = info['process'].pid if info['process'] else 'N/A'
                        ip_addr = info['ip']
                        rtsp_url = f"rtsp://{info['ip']}:{info['port']}"
                        heartbeat_time = datetime.fromtimestamp(info['last_heartbeat']).strftime('%Y-%m-%d %H:%M:%S')
                        mac = info['mac']
                        print(f"{process_id:<12} {ip_addr:<15} {rtsp_url:<30} {heartbeat_time:<20} {mac:<20}")
                    print("==========================\n")
                else:
                    print("\nNo cameras connected.\n")
            if self.stop_event.wait(update_interval):
                break
        print('Camera table update thread terminated!')

    def stop(self):
        """Signals all threads to stop."""
        self.stop_event.set()
