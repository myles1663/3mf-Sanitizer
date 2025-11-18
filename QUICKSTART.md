# Quick Start Guide

## For End Users

### Installation

**Option 1: Download Pre-built Executable (Easiest)**
1. Download `3MF-Sanitizer.exe` from the releases page
2. Save it anywhere on your computer
3. Double-click to run - no installation needed!

**Option 2: Run from Source**
1. Install Python 3.10 or higher
2. Download this folder
3. Open command prompt in the folder
4. Run: `pip install -r requirements.txt`
5. Run: `python main.py`

### Using the Application

1. **Launch** the application by double-clicking `3MF-Sanitizer.exe`

2. **Select Folder**: Click "Select Folder" and choose where you download 3MF files
   - Example: `C:\Users\YourName\Downloads`

3. **Start Monitoring**: Click "Start Monitoring"
   - The status will change to "Monitoring" (green)
   - Any new 3MF files added to the folder will be automatically fixed

4. **Process Existing Files** (Optional): Click "Process Existing Files"
   - Fixes all 3MF files already in the folder
   - Shows confirmation before processing

5. **Monitor Activity**: Watch the Activity Log to see what's happening
   - Shows which files were processed
   - Lists what fixes were applied
   - Reports any errors

### What Gets Fixed

The app automatically fixes these problematic parameters:
- `raft_first_layer_expansion = -1` becomes `= 0`
- `tree_support_wall_count = -1` becomes `= 0`

### Safety Features

- **Automatic Backup**: Original files are saved as `.3mf.bak`
- **Non-Destructive**: You can always restore from the backup
- **Clear Logging**: See exactly what was changed

### Restoring Original Files

If you need to restore an original file:
1. Delete the `.3mf` file
2. Remove `.bak` from the backup filename

Example:
- Delete: `model.3mf`
- Rename: `model.3mf.bak` → `model.3mf`

### Troubleshooting

**Files aren't being processed:**
- Make sure they have the `.3mf` extension
- Check that monitoring is running (status shows green)
- Look at the Activity Log for error messages

**Application won't start:**
- Windows may show a security warning for unknown apps
- Click "More info" then "Run anyway"
- Or right-click → Properties → Unblock

**Still getting slicer errors:**
- Check the Activity Log to confirm fixes were applied
- The issue might be a different parameter
- Try opening the `.3mf.bak` backup to compare

## For Developers

### Running from Source

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py

# Test the sanitizer alone
python sanitizer.py path/to/file.3mf

# Create a test file
python create_test_file.py

# Test the sanitizer on test file
python sanitizer.py test_file.3mf
```

### Building Executable

```bash
# Using the build script (recommended)
python build.py

# Or manually with PyInstaller
pyinstaller --onefile --windowed --name "3MF-Sanitizer" main.py
```

The executable will be in the `dist/` folder.

### Project Structure

```
3mf-sanitizer/
├── main.py                 # GUI application
├── sanitizer.py           # Core sanitization logic
├── file_watcher.py        # Folder monitoring
├── build.py               # Build script
├── create_test_file.py    # Test file generator
├── requirements.txt       # Dependencies
├── README.md              # Full documentation
└── QUICKSTART.md         # This file
```

### Testing

```bash
# Create a test file with problems
python create_test_file.py

# Run sanitizer on it
python sanitizer.py test_file.3mf

# Verify the fix
python -c "import zipfile; z = zipfile.ZipFile('test_file.3mf'); print(z.read('Metadata/model_settings.config').decode())"
```

### Adding New Parameters to Fix

Edit `sanitizer.py`:

```python
class ThreeMFSanitizer:
    FIXES = {
        'raft_first_layer_expansion': 0,
        'tree_support_wall_count': 0,
        'new_parameter_name': desired_value,  # Add here
    }
```

The sanitizer will automatically fix both INI-style (`param = -1`) and JSON-style (`"param": -1`) formats.

## Support

Found a bug? Have a suggestion?
- Check the README.md for detailed information
- Create an issue on GitHub
- Verify your 3MF file structure matches expected format

## License

MIT License - Free to use and modify
