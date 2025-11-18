# Build Instructions

## Building the Standalone Executable

This guide explains how to build `3MF-Sanitizer.exe` from the source code.

### Prerequisites

1. **Python 3.10 or higher**
   - Download from: https://www.python.org/downloads/
   - During installation, check "Add Python to PATH"

2. **Enable Windows Long Path Support** (Required for PyInstaller)

   **Option A: Via Registry (Recommended)**
   1. Press `Win + R`, type `regedit`, press Enter
   2. Navigate to: `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem`
   3. Find or create a DWORD value named `LongPathsEnabled`
   4. Set its value to `1`
   5. Restart your computer

   **Option B: Via Group Policy (Windows 10/11 Pro)**
   1. Press `Win + R`, type `gpedit.msc`, press Enter
   2. Navigate to: Computer Configuration → Administrative Templates → System → Filesystem
   3. Double-click "Enable Win32 long paths"
   4. Select "Enabled"
   5. Click OK and restart

   **Option C: Via PowerShell (Windows 10/11)**
   ```powershell
   # Run PowerShell as Administrator
   New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" `
   -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
   ```

### Build Steps

#### Method 1: Using the Build Script (Easiest)

1. Open Command Prompt or PowerShell
2. Navigate to the project folder:
   ```bash
   cd C:\Users\YourName\3mf-sanitizer
   ```

3. Run the build script:
   ```bash
   python build.py
   ```

4. Follow the prompts. The script will:
   - Install required dependencies (PyInstaller, watchdog)
   - Build the executable
   - Optionally clean up temporary files

5. Find your executable in the `dist` folder:
   ```
   dist/3MF-Sanitizer.exe
   ```

#### Method 2: Manual Build

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Build with PyInstaller:
   ```bash
   pyinstaller --onefile --windowed --name "3MF-Sanitizer" main.py
   ```

3. The executable will be in `dist/3MF-Sanitizer.exe`

### Build Options

**Create a one-file executable (recommended for distribution):**
```bash
pyinstaller --onefile --windowed --name "3MF-Sanitizer" main.py
```

**Create a one-folder bundle (faster startup):**
```bash
pyinstaller --onedir --windowed --name "3MF-Sanitizer" main.py
```

**Include an icon (if you have one):**
```bash
pyinstaller --onefile --windowed --name "3MF-Sanitizer" --icon=icon.ico main.py
```

**Show console for debugging:**
```bash
pyinstaller --onefile --console --name "3MF-Sanitizer" main.py
```

### Troubleshooting

**"ERROR: Could not install packages due to an OSError... Long Path support"**
- You need to enable Windows Long Path support (see Prerequisites above)
- Restart your computer after enabling
- Try installing again

**"Python is not recognized as an internal or external command"**
- Python is not in your PATH
- Reinstall Python and check "Add Python to PATH"
- Or use the full path: `C:\Python310\python.exe`

**"ModuleNotFoundError: No module named 'watchdog'"**
- Install dependencies first:
  ```bash
  pip install -r requirements.txt
  ```

**Executable won't run on other computers:**
- Make sure you used `--onefile` flag
- The target computer doesn't need Python installed
- Windows may show a security warning (this is normal for unsigned executables)

**Antivirus flags the executable:**
- This is a false positive (common with PyInstaller)
- You can submit it to your antivirus vendor as a false positive
- Or sign the executable with a code signing certificate

### Distribution

Once built, you can distribute just the `.exe` file:

1. **Simple Distribution:**
   - Share `dist/3MF-Sanitizer.exe` directly
   - Users can run it without installing anything

2. **With Documentation:**
   - Create a ZIP file containing:
     ```
     3MF-Sanitizer.exe
     README.md
     QUICKSTART.md
     LICENSE
     ```

3. **Installer (Optional):**
   - Use tools like Inno Setup or NSIS to create an installer
   - This adds polish but isn't necessary

### Building on Different Platforms

**Note:** PyInstaller builds are platform-specific.

- Windows executable: Build on Windows
- Mac executable: Build on macOS
- Linux executable: Build on Linux

### File Size

The executable will be approximately:
- **One-file mode:** ~15-20 MB (includes Python runtime)
- **One-folder mode:** ~20-30 MB (spread across multiple files)

### Reducing Build Size

To create a smaller executable:

```bash
# Use UPX compression (requires UPX to be installed)
pyinstaller --onefile --windowed --upx-dir=/path/to/upx --name "3MF-Sanitizer" main.py
```

Download UPX from: https://upx.github.io/

### Next Steps

After building:

1. **Test the executable:**
   - Run it from the `dist` folder
   - Try all features (folder selection, monitoring, processing)
   - Test with actual 3MF files from Makerworld

2. **Create a release:**
   - Tag your version in Git
   - Upload the executable to GitHub Releases
   - Include README and documentation

3. **Share with users:**
   - Provide download link
   - Include QUICKSTART.md for user instructions

## Continuous Integration (Optional)

You can automate builds using GitHub Actions:

```yaml
# .github/workflows/build.yml
name: Build Executable

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: pyinstaller --onefile --windowed --name "3MF-Sanitizer" main.py
      - uses: actions/upload-artifact@v2
        with:
          name: 3MF-Sanitizer
          path: dist/3MF-Sanitizer.exe
```

This will automatically build and upload the executable when you create a new version tag.
