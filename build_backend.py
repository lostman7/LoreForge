import os
import sys
import subprocess
import shutil
from pathlib import Path

def build():
    print("🚀 Starting LoreForge Backend Build...")
    
    # Paths
    base_dir = Path(__file__).parent
    server_script = base_dir / "src" / "server.py"
    build_dir = base_dir / "build_temp"
    dist_dir = base_dir / "src" / "bin"
    
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir(parents=True, exist_ok=True)

    # PyInstaller Command
    # We use --onedir for better performance/reliability in sidecars, 
    # but --onefile is cleaner for distribution. Let's go with --onefile 
    # for a simpler "sidecar" binary.
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--console",
        "--name", "loreforge-server",
        "--distpath", str(dist_dir),
        "--workpath", str(build_dir),
        "--specpath", str(build_dir),
        str(server_script)
    ]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("✅ Backend Build Successful!")
        # Cleanup temp
        if build_dir.exists():
            shutil.rmtree(build_dir)
    else:
        print("❌ Backend Build Failed!")
        sys.exit(1)

if __name__ == "__main__":
    build()
