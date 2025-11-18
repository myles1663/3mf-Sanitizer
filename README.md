# 3MF Sanitizer for Makerworld Files

**Automatically fix problematic Makerworld 3MF files that cause errors in slicers like Anycubic Next, OrcaSlicer, and others.**

![Version](https://img.shields.io/badge/version-1.1-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)

## The Problem

When downloading 3MF files from Makerworld, many slicers (especially Anycubic Slicer Next) show this error:

```
tree_support_wall_count: -1 not in range [0,2]
```

or

```
raft_first_layer_expansion: -1 not valid
```

This prevents you from opening the files in your slicer. 😤

## The Solution

This app **automatically fixes** those files! Just point it at your downloads folder, and it monitors for new 3MF files and fixes them in real-time.

### What It Does

- ✅ Monitors a folder for new/modified 3MF files
- ✅ Automatically replaces `raft_first_layer_expansion = -1` with `0`
- ✅ Automatically replaces `tree_support_wall_count = -1` with `0`
- ✅ Creates backups before modifying (`.3mf.bak`)
- ✅ Works with batch processing for existing files
- ✅ Simple GUI - no technical knowledge needed

## Download

### Latest Release: v1.1

**[⬇️ Download 3MF-Sanitizer-v1.1.zip](../../releases/latest)**

- **Size:** ~10 MB
- **Platform:** Windows 10/11
- **No installation required** - just extract and run!

## Quick Start

1. **Download** `3MF-Sanitizer-v1.1.zip` from [Releases](../../releases)
2. **Extract** the ZIP file
3. **Run** `3MF-Sanitizer.exe`
4. **Select Folder** - Choose your downloads folder
5. **Start Monitoring** - App watches for new files
6. **Done!** - Download 3MF files from Makerworld and they're automatically fixed

## Screenshots

### Main Interface
```
┌─────────────────────────────────────────────┐
│           3MF Sanitizer                     │
│  Fixes negative parameter values in         │
│  Makerworld 3MF files                       │
├─────────────────────────────────────────────┤
│ Watch Folder                                │
│ C:\Users\YourName\Downloads                 │
│ [Select Folder] [Process Existing Files]    │
├─────────────────────────────────────────────┤
│ [Start Monitoring] [Stop Monitoring]        │
│ Status: ● Monitoring                        │
├─────────────────────────────────────────────┤
│ Activity Log                                │
│ [10:23:45] Detected: model.3mf              │
│ [10:23:46] ✓ Fixed 2 parameters             │
└─────────────────────────────────────────────┘
```

## Features

- 🔄 **Real-time Monitoring** - Automatically detects new files
- 📦 **Batch Processing** - Fix all existing files at once
- 💾 **Safe Backups** - Original files saved as `.3mf.bak`
- 📊 **Activity Log** - See exactly what was fixed
- 🎯 **Simple GUI** - User-friendly interface
- 🔒 **Offline** - No internet connection needed
- 🆓 **Free & Open Source** - MIT License

## Compatibility

### Works with 3MF files from:
- ✅ Makerworld
- ✅ BambuLab
- ✅ Prusa
- ✅ Other 3MF sources

### Tested with slicers:
- ✅ Anycubic Slicer Next
- ✅ OrcaSlicer
- ✅ BambuStudio
- ✅ PrusaSlicer

## How It Works

1. 3MF files are ZIP archives containing configuration files
2. The app extracts the archive
3. Searches for problematic parameters in config files
4. Replaces negative values with valid ones (0)
5. Re-compresses and saves the file
6. You can now open it in your slicer! 🎉

### Technical Details

**Parameters Fixed:**
- `raft_first_layer_expansion: -1` → `0`
- `tree_support_wall_count: -1` → `0`

**Files Modified:**
- `Metadata/model_settings.config`
- `Metadata/project_settings.config`
- `Metadata/slice_info.config`
- `Metadata/*.json`

**Formats Supported:**
- INI-style: `param = -1`
- JSON integer: `"param": -1`
- JSON string: `"param": "-1"` *(v1.1 fix)*

## Troubleshooting

**"Windows protected your PC" warning?**
- Click "More info" → "Run anyway"
- This warning appears because the app isn't digitally signed (costs $$$)
- The app is safe - source code is available for review!

**Files aren't being processed?**
- Ensure monitoring is started (status shows green)
- Check files have `.3mf` extension
- Look at Activity Log for errors

**Still getting slicer errors?**
- Check Activity Log to confirm fixes were applied
- The error might be unrelated to these parameters
- Try comparing with the `.3mf.bak` backup

## Building from Source

### Prerequisites
- Python 3.10 or higher
- Windows with Long Path support enabled

### Build Instructions

```bash
# Clone the repository
git clone https://github.com/yourusername/3mf-sanitizer.git
cd 3mf-sanitizer

# Install dependencies
pip install -r requirements.txt

# Run from source
python main.py

# Or build executable
python build.py
```

See [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md) for detailed build steps.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Changelog

### v1.1 (Latest)
- ✨ Fixed detection of JSON string values (`"param": "-1"`)
- ✅ Now works with real Makerworld files
- 🐛 Bug fixes for parameter detection

### v1.0
- 🎉 Initial release
- ✅ Core sanitization functionality
- ✅ GUI application
- ✅ Folder monitoring
- ✅ Batch processing

See [CHANGELOG.md](CHANGELOG.md) for full version history.

## FAQ

**Q: Is this safe?**
A: Yes! The app creates backups before modifying files, and the source code is open for review.

**Q: Will this work on Mac/Linux?**
A: Currently Windows-only, but the Python source can be adapted for other platforms.

**Q: Can I add more parameters to fix?**
A: Yes! Edit `sanitizer.py` and add parameters to the `FIXES` dictionary.

**Q: Does this need internet?**
A: No, it works completely offline.

**Q: Why isn't it signed?**
A: Code signing certificates cost hundreds of dollars per year. As a free open-source project, we don't have that budget. The source code is available for anyone to audit.

## Support

- 🐛 **Bug Reports:** [Open an Issue](../../issues)
- 💡 **Feature Requests:** [Open an Issue](../../issues)
- 📖 **Documentation:** See [QUICKSTART.md](QUICKSTART.md)

## Community

Help spread the word!
- Share on Reddit: [r/3Dprinting](https://reddit.com/r/3Dprinting), [r/anycubic](https://reddit.com/r/anycubic)
- Post in Makerworld forums
- Share in Facebook 3D printing groups

## License

MIT License - Free for personal and commercial use.

See [LICENSE](LICENSE) for details.

## Credits

Created to help the 3D printing community deal with incompatible 3MF files.

Special thanks to:
- The 3D printing community for reporting issues
- BambuLab for 3MF format documentation
- All contributors

---

**Made with ❤️ for the 3D printing community**

*If this tool helped you, consider giving it a ⭐ star on GitHub!*
