"""
3MF Sanitizer - Main GUI Application
Automatically fixes negative parameter values in Makerworld 3MF files
"""

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
from pathlib import Path
from datetime import datetime
from sanitizer import ThreeMFSanitizer
from file_watcher import FolderWatcher


class ThreeMFSanitizerApp:
    """Main application window"""

    def __init__(self, root):
        self.root = root
        self.root.title("3MF Sanitizer for Makerworld Files")
        self.root.geometry("700x550")
        self.root.resizable(True, True)

        # Application state
        self.watcher = None
        self.sanitizer = ThreeMFSanitizer(create_backup=True)
        self.watch_folder = None
        self.is_monitoring = False

        # Setup UI
        self._create_widgets()

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _create_widgets(self):
        """Create all UI widgets"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="3MF Sanitizer",
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 5))

        subtitle_label = ttk.Label(
            main_frame,
            text="Fixes negative parameter values in Makerworld 3MF files",
            font=("Arial", 9)
        )
        subtitle_label.grid(row=1, column=0, columnspan=3, pady=(0, 15))

        # Folder selection section
        folder_frame = ttk.LabelFrame(main_frame, text="Watch Folder", padding="10")
        folder_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        folder_frame.columnconfigure(1, weight=1)

        self.folder_label = ttk.Label(folder_frame, text="No folder selected")
        self.folder_label.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))

        ttk.Button(
            folder_frame,
            text="Select Folder",
            command=self._select_folder
        ).grid(row=1, column=0, padx=(0, 5))

        ttk.Button(
            folder_frame,
            text="Process Existing Files",
            command=self._process_existing_files
        ).grid(row=1, column=1, sticky=tk.W)

        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        control_frame.columnconfigure(0, weight=1)

        button_container = ttk.Frame(control_frame)
        button_container.grid(row=0, column=0)

        self.start_button = ttk.Button(
            button_container,
            text="Start Monitoring",
            command=self._start_monitoring,
            state=tk.DISABLED
        )
        self.start_button.grid(row=0, column=0, padx=5)

        self.stop_button = ttk.Button(
            button_container,
            text="Stop Monitoring",
            command=self._stop_monitoring,
            state=tk.DISABLED
        )
        self.stop_button.grid(row=0, column=1, padx=5)

        # Status indicator
        status_container = ttk.Frame(control_frame)
        status_container.grid(row=1, column=0, pady=(10, 0))

        ttk.Label(status_container, text="Status:").grid(row=0, column=0, padx=(0, 5))

        self.status_label = ttk.Label(
            status_container,
            text="● Idle",
            foreground="gray"
        )
        self.status_label.grid(row=0, column=1)

        # Activity log section
        log_frame = ttk.LabelFrame(main_frame, text="Activity Log", padding="10")
        log_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        # Create scrolled text widget for log
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=15,
            width=80,
            state=tk.DISABLED,
            wrap=tk.WORD,
            font=("Consolas", 9)
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Clear log button
        ttk.Button(
            log_frame,
            text="Clear Log",
            command=self._clear_log
        ).grid(row=1, column=0, pady=(5, 0), sticky=tk.E)

        # Initial log message
        self._log("Application started. Select a folder to begin monitoring.")

    def _select_folder(self):
        """Open folder selection dialog"""
        folder = filedialog.askdirectory(
            title="Select folder to monitor for 3MF files"
        )

        if folder:
            self.watch_folder = folder
            self.folder_label.config(text=folder)
            self.start_button.config(state=tk.NORMAL)
            self._log(f"Selected folder: {folder}")

    def _start_monitoring(self):
        """Start monitoring the selected folder"""
        if not self.watch_folder:
            messagebox.showwarning("No Folder", "Please select a folder first.")
            return

        try:
            # Create and start watcher
            self.watcher = FolderWatcher(self._on_file_detected)
            self.watcher.start(self.watch_folder)

            self.is_monitoring = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.status_label.config(text="● Monitoring", foreground="green")

            self._log(f"Started monitoring: {self.watch_folder}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to start monitoring:\n{e}")
            self._log(f"ERROR: Failed to start monitoring - {e}")

    def _stop_monitoring(self):
        """Stop monitoring the folder"""
        if self.watcher:
            self.watcher.stop()
            self.watcher = None

        self.is_monitoring = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="● Idle", foreground="gray")

        self._log("Stopped monitoring")

    def _process_existing_files(self):
        """Process all existing 3MF files in the selected folder"""
        if not self.watch_folder:
            messagebox.showwarning("No Folder", "Please select a folder first.")
            return

        # Get list of 3MF files
        watcher = FolderWatcher(lambda x: None)
        files = watcher.process_existing_files(self.watch_folder)

        if not files:
            messagebox.showinfo("No Files", "No 3MF files found in the selected folder.")
            self._log("No 3MF files found to process")
            return

        # Confirm with user
        response = messagebox.askyesno(
            "Process Files",
            f"Found {len(files)} 3MF file(s).\n\nProcess all files now?"
        )

        if response:
            self._log(f"Processing {len(files)} existing file(s)...")

            # Process each file in a separate thread
            def process_all():
                for file in files:
                    self._process_file(file)

            thread = threading.Thread(target=process_all, daemon=True)
            thread.start()

    def _on_file_detected(self, file_path: str):
        """Callback when a new 3MF file is detected"""
        self._log(f"Detected new file: {Path(file_path).name}")
        self._process_file(file_path)

    def _process_file(self, file_path: str):
        """Process a single 3MF file"""
        file_name = Path(file_path).name

        try:
            # Sanitize the file
            success, message, fixes = self.sanitizer.sanitize_file(file_path)

            if success:
                if fixes:
                    self._log(f"✓ {file_name}: {len(fixes)} fix(es) applied")
                    for fix in fixes:
                        self._log(f"  - {fix}")
                else:
                    self._log(f"✓ {file_name}: No fixes needed")
            else:
                self._log(f"✗ {file_name}: {message}")

        except Exception as e:
            self._log(f"✗ {file_name}: ERROR - {e}")

    def _log(self, message: str):
        """Add a message to the activity log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"

        # Update log in main thread
        self.root.after(0, self._update_log, log_message)

    def _update_log(self, message: str):
        """Update the log text widget (must be called from main thread)"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _clear_log(self):
        """Clear the activity log"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self._log("Log cleared")

    def _on_closing(self):
        """Handle window close event"""
        if self.is_monitoring:
            response = messagebox.askyesno(
                "Exit",
                "Monitoring is active. Are you sure you want to exit?"
            )
            if not response:
                return

            self._stop_monitoring()

        self.root.destroy()


def main():
    """Main entry point"""
    root = tk.Tk()
    app = ThreeMFSanitizerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
