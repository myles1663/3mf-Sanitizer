"""
Create a test 3MF file with problematic parameters for testing the sanitizer
"""

import zipfile
import tempfile
import os
from pathlib import Path


def create_test_3mf(output_path="test_file.3mf"):
    """
    Create a minimal 3MF file with problematic parameters

    Args:
        output_path: Where to save the test file
    """
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create directory structure
        (temp_path / "Metadata").mkdir(parents=True)
        (temp_path / "3D").mkdir(parents=True)
        (temp_path / "_rels").mkdir(parents=True)

        # Create [Content_Types].xml
        content_types = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
  <Default Extension="config" ContentType="text/plain"/>
  <Default Extension="json" ContentType="application/json"/>
</Types>"""
        (temp_path / "[Content_Types].xml").write_text(content_types, encoding="utf-8")

        # Create minimal 3D model file
        model_xml = """<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
  <resources>
    <object id="1" type="model">
      <mesh>
        <vertices>
          <vertex x="0" y="0" z="0"/>
          <vertex x="10" y="0" z="0"/>
          <vertex x="5" y="10" z="0"/>
          <vertex x="5" y="5" z="10"/>
        </vertices>
        <triangles>
          <triangle v1="0" v2="1" v3="2"/>
          <triangle v1="0" v2="1" v3="3"/>
          <triangle v1="1" v2="2" v3="3"/>
          <triangle v1="2" v2="0" v3="3"/>
        </triangles>
      </mesh>
    </object>
  </resources>
  <build>
    <item objectid="1"/>
  </build>
</model>"""
        (temp_path / "3D" / "3dmodel.model").write_text(model_xml, encoding="utf-8")

        # Create model_settings.config with problematic parameters
        model_settings = """# Model Settings
layer_height = 0.2
wall_loops = 2
raft_first_layer_expansion = -1
support_type = tree
tree_support_wall_count = -1
infill_density = 20%
print_speed = 50"""
        (temp_path / "Metadata" / "model_settings.config").write_text(model_settings, encoding="utf-8")

        # Create project_settings.config
        project_settings = """# Project Settings
printer = Generic Printer
filament_type = PLA
nozzle_temperature = 210
bed_temperature = 60"""
        (temp_path / "Metadata" / "project_settings.config").write_text(project_settings, encoding="utf-8")

        # Create slice_info.json with problematic parameters in JSON format
        slice_info = """{
  "slicer": "BambuStudio",
  "version": "1.9.0",
  "raft_first_layer_expansion": -1,
  "tree_support_wall_count": -1,
  "layer_height": 0.2,
  "wall_count": 2
}"""
        (temp_path / "Metadata" / "slice_info.json").write_text(slice_info, encoding="utf-8")

        # Create .rels file
        rels = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>"""
        (temp_path / "_rels" / ".rels").write_text(rels, encoding="utf-8")

        # Create the 3MF (ZIP) file
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(temp_dir)
                    zipf.write(file_path, arcname)

    print(f"[OK] Created test file: {output_path}")
    print("\nThis file contains the following problematic parameters:")
    print("  - raft_first_layer_expansion = -1 (in model_settings.config)")
    print("  - tree_support_wall_count = -1 (in model_settings.config)")
    print('  - "raft_first_layer_expansion": -1 (in slice_info.json)')
    print('  - "tree_support_wall_count": -1 (in slice_info.json)')
    print("\nUse this file to test the sanitizer!")


if __name__ == "__main__":
    import sys

    output = "test_file.3mf"
    if len(sys.argv) > 1:
        output = sys.argv[1]

    create_test_3mf(output)
