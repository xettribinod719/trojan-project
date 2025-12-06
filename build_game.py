
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
