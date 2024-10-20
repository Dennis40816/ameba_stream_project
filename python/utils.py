# utils.py

import socket

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
