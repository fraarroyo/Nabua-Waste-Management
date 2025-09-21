#!/usr/bin/env python3
"""
Simple script to get the local IP address of this device
"""
import socket

def get_local_ip():
    try:
        # Connect to a remote server to get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"

if __name__ == "__main__":
    ip = get_local_ip()
    print(f"Your device IP address: {ip}")
    print(f"Access the waste management system at: http://{ip}:5000")
    print(f"Or locally at: http://localhost:5000")
