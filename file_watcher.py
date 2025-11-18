"""
File Watcher Module
Monitors a directory for new or modified 3MF files and processes them automatically
"""

import time
import threading
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from typing import Callable, Optional


class ThreeMFFileHandler(FileSystemEventHandler):
    """Handles file system events for 3MF files"""

    def __init__(self, callback: Callable[[str], None], delay: float = 1.0):
        """
        Initialize the file handler

        Args:
            callback: Function to call when a 3MF file is detected
            delay: Delay in seconds before processing (to allow file to finish writing)
        """
        super().__init__()
        self.callback = callback
        self.delay = delay
        self.processing = set()
        self.lock = threading.Lock()

    def _should_process(self, file_path: str) -> bool:
        """Check if file should be processed"""
        path = Path(file_path)

        # Check if it's a 3MF file
        if path.suffix.lower() != '.3mf':
            return False

        # Check if it's a backup file
        if path.suffix == '.bak' or '.3mf.bak' in path.name:
            return False

        # Check if file exists and is not empty
        if not path.exists() or path.stat().st_size == 0:
            return False

        return True

    def _schedule_processing(self, file_path: str):
        """Schedule file processing with a delay"""
        with self.lock:
            if file_path in self.processing:
                return  # Already scheduled
            self.processing.add(file_path)

        def process_after_delay():
            # Wait for file to finish writing
            time.sleep(self.delay)

            # Check if file still exists and is valid
            if self._should_process(file_path):
                try:
                    self.callback(file_path)
                finally:
                    with self.lock:
                        self.processing.discard(file_path)
            else:
                with self.lock:
                    self.processing.discard(file_path)

        thread = threading.Thread(target=process_after_delay, daemon=True)
        thread.start()

    def on_created(self, event: FileSystemEvent):
        """Called when a file is created"""
        if not event.is_directory and self._should_process(event.src_path):
            self._schedule_processing(event.src_path)

    def on_modified(self, event: FileSystemEvent):
        """Called when a file is modified"""
        if not event.is_directory and self._should_process(event.src_path):
            self._schedule_processing(event.src_path)


class FolderWatcher:
    """Watches a folder for new or modified 3MF files"""

    def __init__(self, callback: Callable[[str], None]):
        """
        Initialize the folder watcher

        Args:
            callback: Function to call when a 3MF file is detected
        """
        self.callback = callback
        self.observer: Optional[Observer] = None
        self.watch_path: Optional[str] = None
        self.is_running = False

    def start(self, folder_path: str):
        """
        Start watching a folder

        Args:
            folder_path: Path to folder to watch

        Raises:
            ValueError: If folder doesn't exist
            RuntimeError: If watcher is already running
        """
        if self.is_running:
            raise RuntimeError("Watcher is already running. Stop it first.")

        path = Path(folder_path)
        if not path.exists() or not path.is_dir():
            raise ValueError(f"Invalid folder path: {folder_path}")

        self.watch_path = str(path)

        # Create observer and event handler
        event_handler = ThreeMFFileHandler(self.callback, delay=1.0)
        self.observer = Observer()
        self.observer.schedule(event_handler, self.watch_path, recursive=False)

        # Start observing
        self.observer.start()
        self.is_running = True

    def stop(self):
        """Stop watching the folder"""
        if self.observer and self.is_running:
            self.observer.stop()
            self.observer.join(timeout=5)
            self.is_running = False
            self.watch_path = None

    def process_existing_files(self, folder_path: str) -> list:
        """
        Process all existing 3MF files in the folder

        Args:
            folder_path: Path to folder to scan

        Returns:
            List of 3MF file paths found
        """
        path = Path(folder_path)
        if not path.exists() or not path.is_dir():
            return []

        # Find all 3MF files
        three_mf_files = []
        for file in path.glob('*.3mf'):
            # Skip backup files
            if '.bak' not in file.name:
                three_mf_files.append(str(file))

        return three_mf_files

    def __del__(self):
        """Cleanup when object is destroyed"""
        if self.is_running:
            self.stop()


if __name__ == "__main__":
    # Test the watcher
    def test_callback(file_path):
        print(f"Detected: {file_path}")

    watcher = FolderWatcher(test_callback)

    import sys
    if len(sys.argv) < 2:
        print("Usage: python file_watcher.py <folder_to_watch>")
        sys.exit(1)

    folder = sys.argv[1]
    print(f"Watching folder: {folder}")
    print("Press Ctrl+C to stop...")

    try:
        watcher.start(folder)
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        watcher.stop()
