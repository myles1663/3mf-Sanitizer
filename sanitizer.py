"""
3MF File Sanitizer - Core functionality
Fixes negative values in Makerworld 3MF files that cause slicer errors
"""

import zipfile
import os
import tempfile
import shutil
import re
from pathlib import Path
from typing import Tuple, List


class ThreeMFSanitizer:
    """Handles sanitization of 3MF files by fixing problematic parameter values"""

    # Parameters to fix, their problematic values, and their replacements
    FIXES = {
        'raft_first_layer_expansion': (-1, 0),
        'tree_support_wall_count': (-1, 0),
        'solid_infill_filament': (0, 1),
        'sparse_infill_filament': (0, 1),
        'wall_filament': (0, 1)
    }

    def __init__(self, create_backup=True):
        """
        Initialize the sanitizer

        Args:
            create_backup: If True, creates .bak file before modifying original
        """
        self.create_backup = create_backup
        self.fixes_applied = []

    def sanitize_file(self, file: str) -> Tuple[bool, str, List[str]]:
        """
        Sanitize a 3MF file by fixing negative parameter values

        Args:
            file_path: Path to the .3mf file

        Returns:
            Tuple of (success, message, list of fixes applied)
        """
        self.fixes_applied = []
        file_path = Path(file)

        # Validate input
        if not file_path.exists():
            return False, f"File not found: {file_path}", []

        if not file_path.suffix.lower() == '.3mf':
            return False, f"Not a 3MF file: {file_path}", []

        # Create backup if requested
        if self.create_backup:
            backup_path = file_path.with_suffix('.3mf.bak')
            try:
                shutil.copy2(file_path, backup_path)
            except Exception as e:
                return False, f"Failed to create backup: {e}", []
        
        # Create temporary directory for extraction
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Extract 3MF (ZIP) file
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)

                # Process all files in the archive
                modified = self._process_directory(temp_dir)

                if not modified:
                    # No changes needed, remove backup if created
                    if self.create_backup and backup_path.exists():
                        backup_path.unlink()
                    return True, "No problematic parameters found", []

                # Re-compress to 3MF
                self._create_3mf(temp_dir, file_path)

                return True, f"Successfully sanitized: {len(self.fixes_applied)} fix(es) applied", self.fixes_applied

            except zipfile.BadZipFile:
                return False, f"Invalid 3MF file (not a valid ZIP): {file_path}", []
            except Exception as e:
                return False, f"Error processing file: {e}", []

    def _process_directory(self, directory: str) -> bool:
        """
        Recursively process all files in directory looking for problematic parameters

        Args:
            directory: Directory to process

        Returns:
            True if any modifications were made
        """
        modified = False

        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = Path(root) / file

                # Process text-based files that might contain config parameters
                if self._should_process_file(file):
                    if self._sanitize_text_file(file_path):
                        modified = True

        return modified

    def _should_process_file(self, filename: str) -> bool:
        """Check if file should be processed for sanitization"""
        # Process config files, JSON files, and XML files
        processable_extensions = {'.config', '.json', '.xml', '.model'}
        processable_names = {'model_settings.config', 'project_settings.config',
                           'slice_info.config', '3dmodel.model'}

        file_lower = filename.lower()
        return (any(file_lower.endswith(ext) for ext in processable_extensions) or
                filename in processable_names)

    def _sanitize_text_file(self, file_path: Path) -> bool:
        """
        Sanitize a text file by replacing problematic parameter values

        Args:
            file_path: Path to the file to sanitize

        Returns:
            True if file was modified
        """
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            # Fix each problematic parameter
            for param, (old_value, new_value) in self.FIXES.items():
                # Using str() for values to handle different types
                old_value_str = str(old_value)
                new_value_str = str(new_value)
                
                # Pattern 1: INI-style (param = old_value)
                pattern1 = rf'{param}\s*=\s*{re.escape(old_value_str)}\b'
                replacement1 = f'{param} = {new_value_str}'
                new_content = re.sub(pattern1, replacement1, content)

                if new_content != content:
                    self.fixes_applied.append(f"{file_path.name}: {param} = {old_value_str} -> {new_value_str}")
                    content = new_content

                # Pattern 2: JSON-style ("param": old_value)
                pattern2 = rf'"{param}"\s*:\s*{re.escape(old_value_str)}\b'
                replacement2 = f'"{param}": {new_value_str}'
                new_content = re.sub(pattern2, replacement2, content)

                if new_content != content:
                    self.fixes_applied.append(f"{file_path.name}: \"{param}\": {old_value_str} -> {new_value_str}")
                    content = new_content

                # Pattern 3: JSON-style with quoted string ("param": "old_value")
                pattern3 = rf'"{param}"\s*:\s*"{re.escape(old_value_str)}"'
                replacement3 = f'"{param}": "{new_value_str}"'
                new_content = re.sub(pattern3, replacement3, content)

                if new_content != content:
                    self.fixes_applied.append(f"{file_path.name}: \"{param}\": \"{old_value_str}\" -> \"{new_value_str}\"")
                    content = new_content

            # Write back if modified
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True

            return False

        except UnicodeDecodeError:
            # Skip binary files
            return False
        except Exception as e:
            # Log error but don't fail entire operation
            print(f"Warning: Could not process {file_path}: {e}")
            return False

    def _create_3mf(self, source_dir: str, output_path: Path):
        """
        Create a 3MF (ZIP) file from directory contents

        Args:
            source_dir: Directory containing extracted 3MF contents
            output_path: Path where to save the 3MF file
        """
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(source_dir)
                    zipf.write(file_path, arcname)


def sanitize_3mf_file(file_path: str, create_backup: bool = True) -> Tuple[bool, str, List[str]]:
    """
    Convenience function to sanitize a 3MF file

    Args:
        file_path: Path to the .3mf file
        create_backup: If True, creates .bak file before modifying original

    Returns:
        Tuple of (success, message, list of fixes applied)
    """
    sanitizer = ThreeMFSanitizer(create_backup=create_backup)
    return sanitizer.sanitize_file(file_path)


if __name__ == "__main__":
    # Test the sanitizer
    import sys

    if len(sys.argv) < 2:
        print("Usage: python sanitizer.py <path_to_3mf_file>")
        sys.exit(1)

    success, message, fixes = sanitize_3mf_file(sys.argv[1])
    status = "[OK]" if success else "[ERROR]"
    print(f"{status} {message}")
    if fixes:
        print("\nFixes applied:")
        for fix in fixes:
            print(f"  - {fix}")
