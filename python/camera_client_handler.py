# camera_client_handler.py

import threading
import socket
import time
from rtsp_client import RTSPClientProcess
import multiprocessing
from utils import DEBUG

class CameraClientHandler(threading.Thread):
    """Handles communication with a connected camera client."""

    def __init__(self, client_socket, addr, camera_manager, frame_callback):
        super().__init__()
        self.client_socket = client_socket
        self.addr = addr
        self.camera_manager = camera_manager
        self.stop_event = threading.Event()
        self.ip_address = addr[0]
        self.mac = None
        self.frame_callback = frame_callback

    def run(self):
        print(f"New connection from {self.addr}")
        self.client_socket.settimeout(1.0)
        buffer = ''

        try:
            while not self.stop_event.is_set():
                try:
                    data = self.client_socket.recv(1024).decode()
                    if not data:
                        continue

                    buffer += data

                    while '\r\n' in buffer:
                        line, buffer = buffer.split('\r\n', 1)
                        line = line.strip()
                        if not line:
                            continue

                        if line == "AliveHeartBeat":
                            self.camera_manager.update_heartbeat(self.ip_address)
                            if DEBUG:
                              print(f"Heartbeat received from {self.mac} at {self.ip_address}")
                        else:
                            print(f"Received from {self.addr}: {line}")
                            parts = line.split(',')
                            if len(parts) == 3:
                                mac, cam_ip, port = parts

                                # Terminate existing process if any
                                existing_camera = self.camera_manager.get_camera(self.ip_address)
                                if existing_camera:
                                    existing_process = existing_camera['process']
                                    if existing_process and existing_process.is_alive():
                                        existing_process.terminate()
                                        existing_process.join()

                                # Start RTSP client in a new process
                                p = multiprocessing.Process(
                                    target=RTSPClientProcess.run, args=(cam_ip, port, mac, self.frame_callback))
                                p.start()

                                # Add camera to manager
                                self.camera_manager.add_camera(
                                    self.ip_address, mac, cam_ip, port, p)
                                print(f"RTSP client started for {mac} ({cam_ip}:{port})")
                            else:
                                print(f"Invalid data format from {self.addr}: {line}")

                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Receive error from {self.addr}: {e}")
                    break
        except Exception as e:
            print(f"Error with client {self.addr}: {e}")
        finally:
            self.camera_manager.remove_camera(self.ip_address)
            self.client_socket.close()
            print(f"Disconnected from {self.addr}")

    def stop(self):
        self.stop_event.set()
