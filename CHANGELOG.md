# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1] - 2025-01-17

### Fixed
- Fixed detection of JSON parameters with quoted string values (`"param": "-1"`)
- Now correctly processes real Makerworld 3MF files from production
- Updated regex patterns to handle all three parameter formats:
  - INI-style: `param = -1`
  - JSON integer: `"param": -1`
  - JSON string: `"param": "-1"` (NEW)

### Changed
- Improved parameter detection reliability
- Enhanced sanitizer.py with additional pattern matching

### Tested
- Verified with real Makerworld file: "RJ Design - V2 - Christmas Cone Type 1"
- Confirmed fixes apply correctly to `project_settings.config`
- Tested with Anycubic Slicer Next - files now open without errors

## [1.0] - 2025-01-17

### Added
- Initial release
- Core 3MF sanitization engine
- GUI application with tkinter
- Real-time folder monitoring using watchdog
- Batch processing for existing files
- Automatic backup creation (`.3mf.bak`)
- Activity logging with timestamps
- Start/Stop monitoring controls
- Support for INI and JSON parameter formats
- Test file generator for development
- Build script for PyInstaller
- Comprehensive documentation:
  - README.md
  - QUICKSTART.md
  - BUILD_INSTRUCTIONS.md
  - PROJECT_SUMMARY.md

### Features
- Fixes `raft_first_layer_expansion = -1` → `0`
- Fixes `tree_support_wall_count = -1` → `0`
- Processes files in Metadata folder:
  - `model_settings.config`
  - `project_settings.config`
  - `slice_info.config`
  - `*.json` files

### Platform
- Windows 10/11
- Standalone executable (no Python required)
- ~10 MB single-file distribution

### License
- Released under MIT License
- Free for personal and commercial use

---

## Version History Summary

- **v1.1** - Production-ready with real Makerworld file support
- **v1.0** - Initial release with core functionality

## Upgrade Notes

### From v1.0 to v1.1

No breaking changes. Simply replace the executable with the new version.

If you built from source:
1. Pull latest changes
2. Rebuild with `python build.py`
3. No code changes needed in your workflow

## Known Issues

### All Versions

- Windows may show security warning for unsigned executable (see README for details)
- PyInstaller build requires Windows Long Path support to be enabled
- Some antivirus software may flag as false positive

### Planned Features

Future versions may include:
- User-configurable parameter list
- System tray integration
- Auto-start with Windows
- Multiple folder monitoring
- Dark mode UI
- Undo functionality
- Update checker
