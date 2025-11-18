"""
Build script for creating standalone executable
"""

import subprocess
import sys
import shutil
from pathlib import Path


def check_pyinstaller():
    """Check if PyInstaller is installed"""
    try:
        import PyInstaller
        return True
    except ImportError:
        return False


def install_requirements():
    """Install required packages"""
    print("Installing requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install requirements: {e}")
        return False


def build_executable():
    """Build the standalone executable using PyInstaller"""
    print("\nBuilding executable...")

    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",              # Create a single executable
        "--windowed",             # No console window (GUI app)
        "--name", "3MF-Sanitizer",  # Name of the executable
        "--clean",                # Clean PyInstaller cache
        "main.py"                 # Main script
    ]

    try:
        subprocess.check_call(cmd)
        print("✓ Build completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Build failed: {e}")
        return False


def cleanup_build_files():
    """Clean up temporary build files"""
    print("\nCleaning up temporary files...")

    # Directories to remove
    dirs_to_remove = ["build", "__pycache__"]

    for dir_name in dirs_to_remove:
        dir_path = Path(dir_name)
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"✓ Removed {dir_name}/")

    # Files to remove
    files_to_remove = ["3MF-Sanitizer.spec"]

    for file_name in files_to_remove:
        file_path = Path(file_name)
        if file_path.exists():
            file_path.unlink()
            print(f"✓ Removed {file_name}")


def main():
    """Main build process"""
    print("=" * 60)
    print("3MF Sanitizer - Build Script")
    print("=" * 60)

    # Check if PyInstaller is installed
    if not check_pyinstaller():
        print("\nPyInstaller not found. Installing requirements...")
        if not install_requirements():
            print("\n✗ Build failed: Could not install requirements")
            sys.exit(1)

    # Build the executable
    if not build_executable():
        print("\n✗ Build failed")
        sys.exit(1)

    # Clean up
    response = input("\nClean up temporary build files? (y/n): ")
    if response.lower() in ['y', 'yes']:
        cleanup_build_files()

    print("\n" + "=" * 60)
    print("✓ Build completed successfully!")
    print("=" * 60)
    print(f"\nExecutable location: {Path('dist/3MF-Sanitizer.exe').absolute()}")
    print("\nYou can now distribute the executable from the dist/ folder.")
    print("No installation required - users can run it directly!")


if __name__ == "__main__":
    main()
