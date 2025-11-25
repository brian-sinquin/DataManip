"""Custom setup.py to copy assets into core package during build."""

import os
import shutil
from setuptools import setup
from setuptools.command.build_py import build_py as _build_py


class BuildPyWithAssets(_build_py):
    """Custom build_py that copies assets and examples into core package."""
    
    def run(self):
        # Copy assets/lang/*.json into core/assets/lang/ in the build directory
        assets_src = os.path.abspath("assets/lang")
        target_dir = os.path.join(self.build_lib, "core", "assets", "lang")
        
        # Create target directory
        self.mkpath(target_dir)
        
        # Copy all JSON files
        if os.path.exists(assets_src):
            for fname in os.listdir(assets_src):
                if fname.endswith(".json"):
                    src_path = os.path.join(assets_src, fname)
                    dst_path = os.path.join(target_dir, fname)
                    self.copy_file(src_path, dst_path)
                    print(f"Copied {fname} to {target_dir}")
        
        # Copy examples/*.dmw into core/examples/ in the build directory
        examples_src = os.path.abspath("examples")
        examples_target = os.path.join(self.build_lib, "core", "examples")
        
        # Create examples target directory
        self.mkpath(examples_target)
        
        # Copy all .dmw files
        if os.path.exists(examples_src):
            for fname in os.listdir(examples_src):
                if fname.endswith(".dmw"):
                    src_path = os.path.join(examples_src, fname)
                    dst_path = os.path.join(examples_target, fname)
                    self.copy_file(src_path, dst_path)
                    print(f"Copied {fname} to {examples_target}")
        
        # Run the standard build_py
        super().run()


# Use setup() with custom cmdclass
setup(
    cmdclass={"build_py": BuildPyWithAssets},
)
